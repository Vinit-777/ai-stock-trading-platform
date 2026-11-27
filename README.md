# FinanceSight — AI Market Analytics, ML Forecasting & Paper Trading Platform

**FinanceSight** is a full-stack FinTech analytics, machine learning forecasting, strategy backtesting, and paper trading simulation platform covering **345+ verified Indian (NSE) and US (NASDAQ/NYSE) equities** with company brand icons along with live market indices (**NIFTY 50, SENSEX, NASDAQ, S&P 500**) and real-time **USD/INR FX conversion**.

## Key Features

- **Real-Time Marketwatch & Global Indices**: Batched parallel market data ingestion via Yahoo Finance (`yfinance`) with Wilder 14-day RSI, 20-SMA, 50-EMA, Bollinger Bands, MACD, ATR, and 20-day sparklines.
- **SuperChart Technical Terminal**: Interactive multi-panel Candlestick/Line charts with selectable timeframes (`1mo` to `5y`), overlay indicators, company fundamentals (Market Cap, P/E, EPS, 52W Range, Beta), and normalized **Peer Comparison**.
- **Smart Basket (4-Stock ML Auto Builder) & Traffic-Light Stock Health (`models/`)**:
  - Offline-trained `scikit-learn` models trained via [train_models.py](train_models.py) on **3 years of daily historical Yahoo Finance data (242,370 labeled stock-day samples across 345 NSE & US equities)** using a strict chronological split (`models/traffic_light_model.joblib`, `models/smart_basket_model.joblib`, `models/training_metrics.json`, `models/dataset_preview.csv`).
  - **Traffic-Light Stock Health**: Translates 17 scale-invariant momentum, trend, and volatility features into a **0–100 Health Meter** (`Healthy` / `Moderate` / `High Risk`, 72.49% test ROC-AUC) with plain-English explanations for beginners.
  - **Smart Basket (Default 4 Stocks)**: Combines trained ML risk-adjusted suitability scoring (`75.26%` test hit rate), 1-stock-per-sector diversity constraints, and live **6-month Return Covariance Inverse-Volatility Risk Parity ($w_i \propto 1/\sigma_i$)** with 1-click portfolio deployment and interactive Correlation Heatmap.
- **Leak-Free ML Price Forecasting & Model Evaluation**:
  - Uses stationary technical & momentum features (multi-horizon returns, SMA/EMA ratios, RSI, MACD histogram, Bollinger %B, volatility, volume ratio) to predict next-day returns (eliminating Random Forest level-extrapolation bias).
  - Chronological **80/20 train/test split** comparing **Random Forest**, **Gradient Boosting**, and **Ridge Regression** with out-of-sample **RMSE, MAE, MAPE (%), R², and Directional Accuracy (%)**, plus Feature Importance and ±1σ uncertainty bands for 7-day projections.
- **No-Code Quantitative Strategy Backtester**:
  - Simulates **SMA 20/50 Crossover**, **RSI Oversold Reversal**, **Bollinger Mean Reversion**, and **MACD Bullish Crossover** with configurable Stop-Loss, Take-Profit, and Capital.
  - Reports daily mark-to-market **Equity Curve vs. Buy-and-Hold Benchmark**, **Alpha (%)**, **Annualized Sharpe Ratio**, **Max Drawdown (%)**, **Win Rate (%)**, **Profit Factor**, and interactive entry/exit markers.
- **Multi-Currency Paper Trading & Order Book**:
  - Supports **CNC (Delivery 1x)** and **MIS (Intraday 5x leverage)** orders, **MARKET** and genuine **PENDING LIMIT** orders, live **USD → INR (`USDINR=X`)** margin conversion, market-hours validation (IST & US Eastern Time with automatic DST via `zoneinfo`), custom per-user Watchlist, and CSV exports.
- **Agentic AI Advisor (Groq LLaMA 3.3 + Quant RAG Engine)**:
  - Multi-turn conversational assistant with live account awareness, stock screener, margin/tax calculator, safe command-based order execution, and an offline-capable Quantitative Analysis Engine when no LLM API key is configured.
- **Brokerage & Statutory Charges Calculator**: Calculates exact Indian discount brokerage (`₹0` CNC, flat `₹20` / `0.03%` MIS), STT, exchange fees, SEBI turnover charges, GST, stamp duty, and breakeven points.

## Tech Stack

- **Frontend / Framework**: Streamlit (`st.navigation`, `st.Page`, `@st.fragment`, `@st.cache_data`, `st.metric` sparklines)
- **Market Data**: `yfinance` (batched multithreaded downloads + FX + fundamentals)
- **Machine Learning**: `scikit-learn` (`RandomForestRegressor`, `GradientBoostingRegressor`, `Ridge`)
- **Visualization**: `plotly`, `altair`
- **LLM Integration**: Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`)
- **Database**: Thread-safe SQLite (`WAL` mode) with salted `PBKDF2-HMAC-SHA256` password hashing

## Setup & Deployment

### 1. Local Installation

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` (gitignored) with your Groq API key:

```toml
GROQ_API_KEY = "gsk_your_actual_groq_api_key"
```

Run the app:

```bash
streamlit run app.py
```

### 2. Streamlit Community Cloud Deployment

1. Push `app.py`, `requirements.txt`, `.streamlit/config.toml`, `.gitignore`, and `README.md` to GitHub (**never commit `.streamlit/secrets.toml` or hardcode API keys in `app.py`**).
2. On Streamlit Cloud, open **App Settings → Secrets** and add:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_groq_api_key"
   ```

## Testing

```bash
pytest -q
```
