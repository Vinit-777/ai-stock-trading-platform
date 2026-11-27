import json
from datetime import datetime, timezone
from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import yfinance as yf

from app import (
    HEALTH_FEATURE_COLS,
    STOCK_CATALOG,
    build_health_feature_frame,
    enrich_technical_indicators,
)

ROOT_DIR = Path(__file__).resolve().parent
MODELS_DIR = ROOT_DIR / "models"


def collect_3y_panel_dataset(symbols: list[str], period: str = "3y") -> tuple[pd.DataFrame, int]:
    frames: list[pd.DataFrame] = []
    ok_tickers = 0
    for start in range(0, len(symbols), 25):
        chunk = symbols[start : start + 25]
        try:
            raw = yf.download(chunk, period=period, group_by="ticker", threads=True, progress=False)
        except Exception as exc:
            print(f"Chunk {start} failed: {exc}", flush=True)
            continue
        if raw is None or raw.empty:
            continue
        top_cols = set(raw.columns.get_level_values(0)) if isinstance(raw.columns, pd.MultiIndex) else set()
        for sym in chunk:
            if sym not in top_cols:
                continue
            sub = raw[sym].dropna(subset=["Close", "High", "Low"]).copy()
            if len(sub) < 90:
                continue
            try:
                enriched = enrich_technical_indicators(sub)
                feat = build_health_feature_frame(enriched, include_targets=True)
                if feat.empty:
                    continue
                feat["symbol"] = sym
                feat["date"] = pd.to_datetime(feat.index)
                frames.append(feat)
                ok_tickers += 1
            except Exception:
                continue
    if not frames:
        raise RuntimeError("No historical training rows could be collected from Yahoo Finance.")
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["date", "symbol"]).reset_index(drop=True)
    return panel, ok_tickers


def train_and_save() -> None:
    t0 = time.time()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    all_syms = list(STOCK_CATALOG.keys())
    print(f"Downloading 3y daily historical data across {len(all_syms)} NSE & US equities...", flush=True)

    panel, ok_tickers = collect_3y_panel_dataset(all_syms, period="3y")
    split_date = pd.Timestamp(panel["date"].quantile(0.80))
    train_df = panel[panel["date"] <= split_date].copy()
    test_df = panel[panel["date"] > split_date].copy()

    X_train = train_df[HEALTH_FEATURE_COLS].values
    X_test = test_df[HEALTH_FEATURE_COLS].values
    y_cls_train = train_df["health_class"].values
    y_cls_test = test_df["health_class"].values

    y_reg_train = train_df["fwd_suitability"].values
    y_reg_test = test_df["fwd_suitability"].values

    print(
        f"Dataset built: {len(panel):,} rows across {ok_tickers} stocks "
        f"| Split date: {split_date.strftime('%Y-%m-%d')} "
        f"| Train: {len(train_df):,} | Test: {len(test_df):,}",
        flush=True,
    )

    classifiers = {
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=140,
            max_depth=6,
            learning_rate=0.06,
            min_samples_leaf=80,
            class_weight="balanced",
            random_state=42,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=75,
            max_depth=9,
            min_samples_leaf=50,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ),
        "LogisticRegression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=600, class_weight="balanced", random_state=42),
        ),
    }

    cls_benchmarks = []
    trained_cls = {}
    for name, est in classifiers.items():
        est.fit(X_train, y_cls_train)
        preds = est.predict(X_test)
        probs = est.predict_proba(X_test)
        acc = float(accuracy_score(y_cls_test, preds) * 100.0)
        macro_f1 = float(f1_score(y_cls_test, preds, average="macro") * 100.0)
        weighted_f1 = float(f1_score(y_cls_test, preds, average="weighted") * 100.0)
        try:
            roc_auc = float(roc_auc_score(y_cls_test, probs, multi_class="ovr") * 100.0)
        except Exception:
            roc_auc = 50.0
        cls_benchmarks.append(
            {
                "Model": name,
                "Test Accuracy (%)": round(acc, 2),
                "Macro F1 (%)": round(macro_f1, 2),
                "Weighted F1 (%)": round(weighted_f1, 2),
                "ROC-AUC (%)": round(roc_auc, 2),
            }
        )
        trained_cls[name] = (est, preds, macro_f1, roc_auc)
        print(f"  Classifier {name}: Acc={acc:.2f}%, MacroF1={macro_f1:.2f}%, AUC={roc_auc:.2f}%", flush=True)

    cls_benchmarks.sort(key=lambda r: (r["Macro F1 (%)"], r["ROC-AUC (%)"]), reverse=True)
    best_cls_name = cls_benchmarks[0]["Model"]
    best_cls_est, best_cls_preds, _, _ = trained_cls[best_cls_name]
    cm = confusion_matrix(y_cls_test, best_cls_preds, labels=[0, 1, 2]).tolist()

    rf_est = trained_cls["RandomForest"][0]
    feat_imp = {
        col: round(float(val) * 100.0, 2)
        for col, val in zip(HEALTH_FEATURE_COLS, rf_est.feature_importances_)
    }
    feat_imp_sorted = dict(sorted(feat_imp.items(), key=lambda kv: kv[1], reverse=True))

    regressors = {
        "HistGradientBoostingRegressor": HistGradientBoostingRegressor(
            max_iter=140,
            max_depth=6,
            learning_rate=0.05,
            min_samples_leaf=80,
            random_state=42,
        ),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=70,
            max_depth=9,
            min_samples_leaf=50,
            random_state=42,
            n_jobs=-1,
        ),
        "RidgeRegression": make_pipeline(StandardScaler(), Ridge(alpha=2.0)),
    }

    reg_benchmarks = []
    trained_reg = {}
    for name, est in regressors.items():
        est.fit(X_train, y_reg_train)
        preds = est.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_reg_test, preds)))
        mae = float(mean_absolute_error(y_reg_test, preds))
        dir_acc = float(np.mean((preds > 0) == (y_reg_test > 0)) * 100.0)
        reg_benchmarks.append(
            {
                "Model": name,
                "Test RMSE": round(rmse, 4),
                "Test MAE": round(mae, 4),
                "Directional Hit Rate (%)": round(dir_acc, 2),
            }
        )
        trained_reg[name] = (est, dir_acc, rmse)
        print(f"  Regressor {name}: RMSE={rmse:.4f}, MAE={mae:.4f}, DirAcc={dir_acc:.2f}%", flush=True)

    reg_benchmarks.sort(key=lambda r: (r["Directional Hit Rate (%)"], -r["Test RMSE"]), reverse=True)
    best_reg_name = reg_benchmarks[0]["Model"]
    best_reg_est = trained_reg[best_reg_name][0]

    health_bundle = {
        "model": best_cls_est,
        "model_name": best_cls_name,
        "feature_cols": HEALTH_FEATURE_COLS,
        "class_labels": {0: "High Risk", 1: "Moderate", 2: "Healthy"},
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    basket_bundle = {
        "model": best_reg_est,
        "model_name": best_reg_name,
        "feature_cols": HEALTH_FEATURE_COLS,
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    health_path = MODELS_DIR / "traffic_light_model.joblib"
    basket_path = MODELS_DIR / "smart_basket_model.joblib"
    joblib.dump(health_bundle, health_path, compress=3)
    joblib.dump(basket_bundle, basket_path, compress=3)

    cls_counts = panel["health_class"].value_counts().to_dict()
    metrics_payload = {
        "dataset_source": "Yahoo Finance Daily OHLCV (3-Year Multi-Market Panel)",
        "period": "3y",
        "tickers_trained": int(ok_tickers),
        "total_rows": int(len(panel)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "date_start": str(panel["date"].min().strftime("%Y-%m-%d")),
        "date_end": str(panel["date"].max().strftime("%Y-%m-%d")),
        "split_date": str(split_date.strftime("%Y-%m-%d")),
        "feature_columns": HEALTH_FEATURE_COLS,
        "class_distribution": {
            "High Risk (0)": int(cls_counts.get(0, 0)),
            "Moderate (1)": int(cls_counts.get(1, 0)),
            "Healthy (2)": int(cls_counts.get(2, 0)),
        },
        "label_definitions": {
            "Healthy (2)": "Forward 20D volatility <= 27% annualized, max drawdown <= 5.5%, and return >= -1%",
            "Moderate (1)": "Balanced risk/return swings without severe turbulence or steep drawdowns",
            "High Risk (0)": "Forward 20D volatility >= 37% annualized OR max drawdown <= -9.5%",
        },
        "best_classifier": best_cls_name,
        "classifier_benchmarks": cls_benchmarks,
        "confusion_matrix_labels": ["High Risk", "Moderate", "Healthy"],
        "confusion_matrix": cm,
        "feature_importance_pct": feat_imp_sorted,
        "best_regressor": best_reg_name,
        "regressor_benchmarks": reg_benchmarks,
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "training_seconds": round(time.time() - t0, 2),
    }
    metrics_path = MODELS_DIR / "training_metrics.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    sample_df = (
        panel.groupby("symbol", group_keys=False)
        .tail(2)[["date", "symbol"] + HEALTH_FEATURE_COLS + ["fwd_ret_20d", "fwd_vol_20d", "fwd_mdd_20d", "fwd_suitability", "health_class"]]
        .head(400)
    )
    sample_df.to_csv(MODELS_DIR / "dataset_preview.csv", index=False)

    print(
        f"Saved artifacts cleanly in {MODELS_DIR} ({time.time() - t0:.1f}s):\n"
        f"  - traffic_light_model.joblib: {health_path.stat().st_size / 1024:.1f} KB\n"
        f"  - smart_basket_model.joblib: {basket_path.stat().st_size / 1024:.1f} KB\n"
        f"  - training_metrics.json & dataset_preview.csv",
        flush=True,
    )


if __name__ == "__main__":
    train_and_save()
