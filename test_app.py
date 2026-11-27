import hashlib
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app as fs  # noqa: E402


def _make_synthetic_ohlcv(n: int = 160, start_price: float = 1000.0) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2025-01-02", periods=n)
    rets = rng.normal(0.001, 0.015, size=n)
    close = start_price * np.cumprod(1.0 + rets)
    open_p = np.roll(close, 1)
    open_p[0] = start_price
    high = np.maximum(open_p, close) * (1.0 + rng.uniform(0.001, 0.012, size=n))
    low = np.minimum(open_p, close) * (1.0 - rng.uniform(0.001, 0.012, size=n))
    vol = rng.integers(100_000, 1_500_000, size=n)
    raw = pd.DataFrame({"Open": open_p, "High": high, "Low": low, "Close": close, "Volume": vol}, index=dates)
    return fs.enrich_technical_indicators(raw)


class FinanceSightCoreTests(unittest.TestCase):
    def test_auth_pbkdf2_and_legacy_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = str(Path(tmp) / "test_auth.db")
            fs.init_db(db_file)

            ok, msg = fs.register_new_user("Alice Dev", "alice_01", "alice@example.com", "secret123", db_path=db_file)
            self.assertTrue(ok)
            self.assertEqual(msg, "alice_01")

            ok_short, _ = fs.register_new_user("Bob", "bob_01", "bob@example.com", "123", db_path=db_file)
            self.assertFalse(ok_short)
            ok_dup, _ = fs.register_new_user("Alice 2", "ALICE_01", "a2@example.com", "secret123", db_path=db_file)
            self.assertFalse(ok_dup)

            ok_login, u, full = fs.authenticate_user("alice_01", "secret123", db_path=db_file)
            self.assertTrue(ok_login)
            self.assertEqual(u, "alice_01")
            self.assertEqual(full, "Alice Dev")

            legacy_hash = hashlib.sha256(b"oldpass99").hexdigest()
            with fs.db_conn(db_file) as conn:
                conn.execute(
                    "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                    ("legacy_u", "Legacy User", "leg@example.com", legacy_hash, 100000.0),
                )
            ok_leg, lu, _ = fs.authenticate_user("legacy_u", "oldpass99", db_path=db_file)
            self.assertTrue(ok_leg)
            self.assertEqual(lu, "legacy_u")
            with fs.db_conn(db_file) as conn:
                new_hash = conn.execute("SELECT password_hash FROM users WHERE username='legacy_u'").fetchone()[0]
            self.assertTrue(new_hash.startswith("pbkdf2$100000$"))

    def test_multicurrency_trading_and_limit_orders(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = str(Path(tmp) / "test_trade.db")
            fs.init_db(db_file)

            ok, msg = fs.execute_trade(
                "Trader_XYZ", "AAPL", "BUY", 5, 200.0,
                product_type="CNC (Delivery)", order_type="MARKET",
                usdinr_rate=90.0, allow_after_hours=True, db_path=db_file,
            )
            self.assertTrue(ok, msg)
            self.assertTrue(math.isclose(fs.get_user_balance("Trader_XYZ", db_path=db_file), 10000.0, abs_tol=0.01))

            ok_lim, msg_lim = fs.execute_trade(
                "Trader_XYZ", "RELIANCE.NS", "BUY", 5, 1400.0,
                product_type="CNC (Delivery)", order_type="LIMIT", limit_price=500.0,
                usdinr_rate=90.0, allow_after_hours=True, db_path=db_file,
            )
            self.assertTrue(ok_lim)
            self.assertIn("PENDING", msg_lim)
            self.assertTrue(math.isclose(fs.get_user_balance("Trader_XYZ", db_path=db_file), 7500.0, abs_tol=0.01))

            with fs.db_conn(db_file) as conn:
                oid = conn.execute("SELECT id FROM pending_orders WHERE status='PENDING'").fetchone()[0]
            ok_can, _ = fs.cancel_pending_order("Trader_XYZ", oid, db_path=db_file)
            self.assertTrue(ok_can)
            self.assertTrue(math.isclose(fs.get_user_balance("Trader_XYZ", db_path=db_file), 10000.0, abs_tol=0.01))

            ok_slim, _ = fs.execute_trade(
                "Trader_XYZ", "AAPL", "SELL", 5, 200.0,
                product_type="CNC (Delivery)", order_type="LIMIT", limit_price=250.0,
                usdinr_rate=90.0, allow_after_hours=True, db_path=db_file,
            )
            self.assertTrue(ok_slim)

            ok_dup_sell, _ = fs.execute_trade(
                "Trader_XYZ", "AAPL", "SELL", 5, 200.0,
                product_type="CNC (Delivery)", order_type="MARKET",
                usdinr_rate=90.0, allow_after_hours=True, db_path=db_file,
            )
            self.assertFalse(ok_dup_sell)

            filled = fs.sync_pending_orders(
                "Trader_XYZ", {"AAPL": {"price": 255.0}}, usdinr_rate=90.0, allow_after_hours=True, db_path=db_file
            )
            self.assertEqual(len(filled), 1)
            self.assertTrue(math.isclose(fs.get_user_balance("Trader_XYZ", db_path=db_file), 10000.0 + 5 * 255.0 * 90.0, abs_tol=0.01))

    def test_math_parser_and_safe_trade_command_parser(self):
        expr, ans = fs.try_solve_math_query("What is 250 * 4 + 100?")
        self.assertEqual(expr, "250 * 4 + 100")
        self.assertEqual(ans, 1100)

        self.assertEqual(fs.try_solve_math_query("Compare 2024-2025 Nifty returns"), (None, None))
        self.assertEqual(fs.try_solve_math_query("What is the tax on 100?"), (None, None))

        self.assertIsNone(fs.parse_trade_command("Should I buy Reliance?"))
        self.assertIsNone(fs.parse_trade_command("Would you buy 10 Apple?"))
        self.assertIsNone(fs.parse_trade_command("Don't buy TCS"))

        cmd = fs.parse_trade_command("buy 10 reliance mis")
        self.assertEqual(cmd, {"action": "BUY", "ticker": "RELIANCE.NS", "qty": 10, "product": "MIS (Intraday 5x)", "limit_price": None})

        cmd_lim = fs.parse_trade_command("sell 4 aapl at 220")
        assert_eq = {"action": "SELL", "ticker": "AAPL", "qty": 4, "product": "CNC (Delivery)", "limit_price": 220.0}
        self.assertEqual(cmd_lim, assert_eq)
        self.assertIsNone(fs.parse_trade_command("Compare TCS vs Infosys"))
        self.assertEqual(fs.detect_all_stocks_from_text("Compare TCS vs Infosys and Reliance"), ["RELIANCE.NS", "TCS.NS", "INFY.NS"])

    def test_ml_forecast_and_backtester_on_synthetic_data(self):
        df = _make_synthetic_ohlcv(160)
        self.assertTrue({"SMA_20", "EMA_50", "RSI", "BB_Upper", "BB_Lower", "MACD", "ATR_14"}.issubset(df.columns))
        self.assertFalse(df["RSI"].isna().any())

        ml_res = fs._run_ml_forecast_core(df, horizon=7)
        self.assertIsNotNone(ml_res)
        self.assertEqual(len(ml_res["eval_df"]), 3)
        self.assertEqual(len(ml_res["forecast_prices"]), 7)
        self.assertIn(ml_res["best_model"], {"Random Forest", "Gradient Boosting", "Ridge Regression"})

        for strat in fs.BACKTEST_STRATEGIES:
            bt = fs.run_backtest(df, strat, 100000.0, 3.0, 6.0, "₹")
            self.assertFalse(bt["empty"])
            self.assertEqual(len(bt["eq_series"]), len(bt["bt_df"]))
            self.assertEqual(len(bt["bh_series"]), len(bt["bt_df"]))

    def test_brokerage_calculator_and_timezone_hours(self):
        cnc = fs.compute_brokerage_breakdown("Equity Delivery (CNC)", 1000.0, 1100.0, 10)
        mis = fs.compute_brokerage_breakdown("Equity Intraday (MIS)", 1000.0, 1100.0, 10)
        self.assertEqual(cnc["brokerage"], 0.0)
        self.assertGreater(mis["brokerage"], 0.0)
        self.assertLess(cnc["net_pnl"], cnc["gross_pnl"])

        is_open, msg = fs.check_market_trading_hours("AAPL")
        self.assertIsInstance(is_open, bool)
        self.assertTrue("ET" in msg or "EDT" in msg or "EST" in msg or "US" in msg)

    def test_300_plus_catalog_icons_and_aliases(self):
        self.assertGreaterEqual(len(fs.STOCK_CATALOG), 300)
        nse_n = sum(1 for v in fs.STOCK_CATALOG.values() if v["exchange"] == "NSE")
        us_n = len(fs.STOCK_CATALOG) - nse_n
        self.assertGreaterEqual(nse_n, 150)
        self.assertGreaterEqual(us_n, 150)

        for sym in fs.STOCK_CATALOG:
            url = fs.get_logo_url(sym)
            self.assertTrue(url.startswith("https://") or url.startswith("data:image/svg+xml;base64,"), f"Invalid icon for {sym}: {url}")

        self.assertIn("COST", fs.detect_all_stocks_from_text("Should I analyze Costco stock?"))
        self.assertIn("DIXON.NS", fs.detect_all_stocks_from_text("Analyze Dixon Technologies"))
        self.assertIn("CRWD", fs.detect_all_stocks_from_text("CrowdStrike technical analysis"))

    def test_autonomous_ai_autopilot_and_portfolio_audit(self):
        self.assertIsNone(fs.parse_auto_invest_command("Which is the best stock to buy right now?"))
        self.assertIsNone(fs.parse_auto_invest_command("Should I auto invest 10000 in NSE?"))

        cmd = fs.parse_auto_invest_command("Find the best NSE IT stock and invest ₹15000")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd["market"], "NSE")
        self.assertEqual(cmd["sector_hint"], "it")
        self.assertEqual(cmd["budget_inr"], 15000.0)

        with tempfile.TemporaryDirectory() as tmp:
            db_file = str(Path(tmp) / "test_autopilot.db")
            fs.init_db(db_file)
            synth_df = _make_synthetic_ohlcv(160, start_price=1500.0)
            with (
                patch.object(fs, "fetch_ticker_batch", return_value={}),
                patch.object(fs, "fetch_stock_history", return_value=synth_df),
                patch.object(fs, "fetch_stock_fundamentals", return_value={"marketCap": 1e12, "trailingPE": 25.0}),
            ):
                ok, report, title, logo, steps = fs.execute_ai_auto_pick_trade(
                    "Trader_XYZ",
                    fs.DEFAULT_STOCKS_SNAPSHOTS,
                    90.0,
                    market="NSE",
                    sector_hint="it",
                    budget_inr=15000.0,
                    allow_after_hours=True,
                    db_path=db_file,
                )
                self.assertTrue(ok, report)
                self.assertIn("Selected Asset:", report)
                self.assertTrue(logo.startswith("https://") or logo.startswith("data:image/svg+xml;base64,"))
                self.assertLess(fs.get_user_balance("Trader_XYZ", db_path=db_file), 100000.0)

                audit_md, _ = fs.build_portfolio_risk_audit(
                    "Trader_XYZ", fs.DEFAULT_STOCKS_SNAPSHOTS, 90.0, db_path=db_file
                )
                self.assertIn("Diversification Score:", audit_md)
                self.assertIn("AI Risk Action", audit_md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
