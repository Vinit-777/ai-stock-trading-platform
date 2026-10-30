import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
import sqlite3
import hashlib
import json
import urllib.request
from datetime import datetime, timedelta
from groq import Groq

# ==========================================================
# 🔑 BUILT-IN GROQ API KEY + KEYLESS LIVE AI BACKUP
# ==========================================================
GROQ_API_KEY = "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"

# ==========================================================
# 1. PAGE CONFIG & ZERODHA + TRADINGVIEW DYNAMIC CSS
# ==========================================================
st.set_page_config(
    page_title="Zerodha × StreakPulse AI | Complete Trading Ecosystem",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #05070d;
    }

    .block-container {
        padding-top: 3.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 96% !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: clamp(1.15rem, 1.5vw, 1.55rem) !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        word-break: break-word !important;
    }

    @keyframes tickerMove {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, #070b14, #0f172a, #070b14);
        border: 1px solid rgba(56, 189, 248, 0.25);
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.12);
        padding: 11px 0;
        margin-top: 6px;
        margin-bottom: 18px;
        white-space: nowrap;
        border-radius: 12px;
    }
    .ticker-move {
        display: inline-block;
        animation: tickerMove 24s linear infinite;
    }
    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin: 0 24px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        color: #f1f5f9;
    }
    .ticker-logo {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #ffffff;
        padding: 2px;
        object-fit: contain;
    }

    .kpi-box {
        border-radius: 16px;
        padding: 18px 20px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        margin-bottom: 12px;
    }
    .kpi-cyan {
        background: linear-gradient(135deg, #091526 0%, #0a2738 100%);
        border-left: 4px solid #06b6d4;
    }
    .kpi-violet {
        background: linear-gradient(135deg, #130d26 0%, #24123d 100%);
        border-left: 4px solid #8b5cf6;
    }
    .kpi-emerald {
        background: linear-gradient(135deg, #071918 0%, #0b2e26 100%);
        border-left: 4px solid #10b981;
    }
    .kpi-white {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        color: #0f172a !important;
        border-left: 5px solid #387ed1;
    }
    .kpi-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.78;
        margin-bottom: 6px;
    }
    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: clamp(1.2rem, 1.55vw, 1.65rem);
        font-weight: 800;
        line-height: 1.2;
    }
    .kpi-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        margin-top: 6px;
        font-weight: 600;
    }

    .stock-card {
        background: linear-gradient(145deg, #0f172a 0%, #090d16 100%);
        border: 1px solid #1e293b;
        border-radius: 18px;
        padding: 18px;
        transition: all 0.25s ease;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        margin-bottom: 12px;
    }
    .stock-card:hover {
        border-color: #387ed1;
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(56, 126, 209, 0.22);
    }
    .company-header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 12px;
    }
    .company-logo {
        width: 46px;
        height: 46px;
        border-radius: 12px;
        object-fit: contain;
        background: #ffffff;
        padding: 5px;
        border: 1px solid #334155;
    }
    .company-logo-lg {
        width: 64px;
        height: 64px;
        border-radius: 16px;
        object-fit: contain;
        background: #ffffff;
        padding: 6px;
        border: 2px solid #06b6d4;
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.35);
    }
    .mono-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem;
        font-weight: 800;
        color: #f8fafc;
    }
    .badge-up {
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        padding: 5px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 800;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .badge-down {
        background: rgba(244, 63, 94, 0.18);
        color: #fb7185;
        padding: 5px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 800;
        border: 1px solid rgba(244, 63, 94, 0.35);
    }

    /* Zerodha Clone Specific Sections */
    .z-section-card {
        background: linear-gradient(145deg, #0d1322, #070b14);
        border: 1px solid #1e293b;
        border-radius: 20px;
        padding: 28px 32px;
        margin: 22px 0;
        box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    }
    .z-support-hero {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 55%, #0f172a 100%);
        border: 1px solid #60a5fa;
        border-radius: 20px;
        padding: 32px 36px;
        color: #ffffff;
        margin-bottom: 24px;
    }
    .z-universe-card {
        background: #0b1120;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 22px;
        text-align: center;
        height: 100%;
        transition: all 0.25s ease;
    }
    .z-universe-card:hover {
        border-color: #38bdf8;
        transform: translateY(-4px);
    }
    .z-footer {
        background: #060911;
        border-top: 1px solid #1e293b;
        padding: 36px 28px 20px 28px;
        margin-top: 42px;
        border-radius: 18px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

def render_kpi(title, value, subtext="", theme="kpi-cyan", sub_color="#38bdf8"):
    text_color = "#0f172a" if theme == "kpi-white" else "#f8fafc"
    st.markdown(f"""
    <div class="kpi-box {theme}">
        <div class="kpi-title" style="color:{text_color};">{title}</div>
        <div class="kpi-val" style="color:{text_color};">{value}</div>
        <div class="kpi-sub" style="color:{sub_color};">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. STOCK CATALOG & SMART ENTITY DETECTOR
# ==========================================================
STOCK_CATALOG = {
    "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Energy & Telecom", "domain": "ril.com", "exchange": "NSE", "currency": "₹"},
    "TCS.NS": {"name": "Tata Consultancy Services", "sector": "IT Services", "domain": "tcs.com", "exchange": "NSE", "currency": "₹"},
    "HDFCBANK.NS": {"name": "HDFC Bank Ltd.", "sector": "Private Banking", "domain": "hdfcbank.com", "exchange": "NSE", "currency": "₹"},
    "INFY.NS": {"name": "Infosys Limited", "sector": "IT Consulting", "domain": "infosys.com", "exchange": "NSE", "currency": "₹"},
    "SBIN.NS": {"name": "State Bank of India", "sector": "PSU Banking", "domain": "sbi.co.in", "exchange": "NSE", "currency": "₹"},
    "ICICIBANK.NS": {"name": "ICICI Bank Ltd.", "sector": "Financial Services", "domain": "icicibank.com", "exchange": "NSE", "currency": "₹"},
    "TATAMOTORS.NS": {"name": "Tata Motors Ltd.", "sector": "Automotive & EV", "domain": "tatamotors.com", "exchange": "NSE", "currency": "₹"},
    "WIPRO.NS": {"name": "Wipro Limited", "sector": "Information Tech", "domain": "wipro.com", "exchange": "NSE", "currency": "₹"},
    "ITC.NS": {"name": "ITC Limited", "sector": "FMCG & Conglomerate", "domain": "itcportal.com", "exchange": "NSE", "currency": "₹"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel Ltd.", "sector": "Telecom", "domain": "airtel.in", "exchange": "NSE", "currency": "₹"},
    "AAPL": {"name": "Apple Inc.", "sector": "Consumer Tech", "domain": "apple.com", "exchange": "NASDAQ", "currency": "$"},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "AI & Semiconductors", "domain": "nvidia.com", "exchange": "NASDAQ", "currency": "$"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Cloud & AI", "domain": "microsoft.com", "exchange": "NASDAQ", "currency": "$"},
    "TSLA": {"name": "Tesla Inc.", "sector": "EV & Robotics", "domain": "tesla.com", "exchange": "NASDAQ", "currency": "$"},
    "GOOGL": {"name": "Alphabet Inc. (Google)", "sector": "Search & Cloud AI", "domain": "google.com", "exchange": "NASDAQ", "currency": "$"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "E-Commerce & Cloud", "domain": "amazon.com", "exchange": "NASDAQ", "currency": "$"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Social & AI", "domain": "meta.com", "exchange": "NASDAQ", "currency": "$"}
}

CHAT_STOCK_ALIASES = {
    "apple": "AAPL", "aapl": "AAPL", "iphone": "AAPL",
    "nvidia": "NVDA", "nvda": "NVDA",
    "tesla": "TSLA", "tsla": "TSLA",
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "facebook": "META",
    "reliance": "RELIANCE.NS", "ril": "RELIANCE.NS",
    "tcs": "TCS.NS", "tata consultancy": "TCS.NS",
    "hdfc": "HDFCBANK.NS", "hdfcbank": "HDFCBANK.NS",
    "infosys": "INFY.NS", "infy": "INFY.NS",
    "sbi": "SBIN.NS", "state bank": "SBIN.NS", "sbin": "SBIN.NS",
    "icici": "ICICIBANK.NS", "icicibank": "ICICIBANK.NS",
    "tata motors": "TATAMOTORS.NS", "tatamotors": "TATAMOTORS.NS",
    "wipro": "WIPRO.NS",
    "itc": "ITC.NS",
    "airtel": "BHARTIARTL.NS", "bharti": "BHARTIARTL.NS"
}

def detect_stock_from_text(user_text, default_ticker):
    cleaned = user_text.lower().strip()
    for keyword in sorted(CHAT_STOCK_ALIASES.keys(), key=len, reverse=True):
        if cleaned == keyword or f" {keyword} " in f" {cleaned} " or f" {keyword}?" in f" {cleaned}" or f" {keyword}." in f" {cleaned}":
            return CHAT_STOCK_ALIASES[keyword], True
    return default_ticker, False

def get_logo_url(ticker):
    dom = STOCK_CATALOG.get(ticker, {}).get("domain", "tradingview.com")
    return f"https://www.google.com/s2/favicons?domain={dom}&sz=128"

@st.cache_data(ttl=300)
def fetch_stock_history(symbol, period="1y"):
    stock = yf.Ticker(symbol)
    df = stock.history(period=period)
    if df.empty:
        return None
    df.index = df.index.tz_localize(None)
    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + (gain / loss)))
    return df

@st.cache_data(ttl=600)
def fetch_market_snapshots(tickers_list):
    snapshots = {}
    for sym in tickers_list:
        try:
            hist = yf.Ticker(sym).history(period="1mo")
            if len(hist) >= 2:
                last_c = float(hist["Close"].iloc[-1])
                prev_c = float(hist["Close"].iloc[-2])
                chg = last_c - prev_c
                pct = (chg / prev_c) * 100
                
                delta = hist["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50.0
                sma10 = float(hist["Close"].tail(10).mean())
                
                snapshots[sym] = {
                    "price": last_c,
                    "change": chg,
                    "pct": pct,
                    "rsi": rsi,
                    "above_sma": last_c >= sma10
                }
        except Exception:
            pass
    return snapshots

# ==========================================================
# 3. TRIPLE-LAYER CONVERSATIONAL & STOCK AI ENGINE
# ==========================================================
def ask_built_in_ai_advisor(ticker, company_name, currency, price, pct_change, rsi, sma20, ema50, high52, low52, user_question):
    q_clean = user_question.strip().lower()

    greetings_exact = {"hi", "hello", "hey", "hii", "hola", "namaste", "good morning", "good evening", "good afternoon", "help", "who are you", "what can you do"}
    if q_clean in greetings_exact or q_clean.startswith(("hello ", "hi ", "hey ")):
        greeting_reply = f"""
### 👋 Hello! I am StreakPulse AI — Your Zerodha × TradingView Financial Analyst

I can analyze **any Indian (NSE) or US (NASDAQ) stock** in real time, explain brokerage & trading rules, or build custom trade setups.

* **🏢 Ask About Any Company Simply by Typing Its Name:**
  * Type **`Apple`**, **`NVIDIA`**, **`Tesla`**, **`Microsoft`**, **`TCS`**, **`HDFC Bank`**, **`SBI`**, **`Infosys`**, or **`ITC`** — I will automatically switch to that company's live chart and price!
* **📈 Ask Specific Trading Questions:**
  * *"Give me an intraday setup for Apple"*
  * *"Is NVIDIA good for a 5-year investment?"*
  * *"What is the stop-loss and target for Tata Motors?"*
  * *"Explain what RSI and Moving Averages mean"*

*(Currently selected in your terminal: **{company_name} (`{ticker}`)** trading at **{currency}{price:,.2f}**)*
"""
        return greeting_reply, "🟢 Conversational AI Assistant Active"

    df_live = fetch_stock_history(ticker, "1y")
    volatility_pct = float(df_live["Close"].pct_change().std() * 100) if df_live is not None else 1.8
    atr_val = float((df_live["High"] - df_live["Low"]).tail(14).mean()) if df_live is not None else (price * 0.02)
    
    ml_pred_5d = price * (1.022 if price >= sma20 else 0.982)
    if df_live is not None and len(df_live) > 40:
        ml_sub = df_live[["Close", "SMA_20", "EMA_50", "RSI"]].dropna().copy()
        ml_sub["Target_5D"] = ml_sub["Close"].shift(-5)
        train_df = ml_sub.dropna()
        if len(train_df) > 20:
            rf_quick = RandomForestRegressor(n_estimators=60, random_state=42)
            rf_quick.fit(train_df[["Close", "SMA_20", "EMA_50", "RSI"]].values, train_df["Target_5D"].values)
            ml_pred_5d = float(rf_quick.predict([[price, sma20, ema50, rsi]])[0])
    ml_move_pct = ((ml_pred_5d - price) / price) * 100

    system_prompt = (
        "You are StreakPulse AI, an intelligent conversational stock market advisor integrated into a Zerodha Kite & TradingView platform. "
        "CRITICAL RULES:\n"
        "1. Always answer the user's exact question naturally and directly in sentence 1.\n"
        "2. If they ask a general finance question (like 'what is RSI' or 'how to trade'), explain that concept clearly.\n"
        "3. If they ask about a company or type a company name (like 'apple'), provide a rich, custom analysis of THAT company using the live market metrics provided.\n"
        "4. Never repeat a static template—vary your structure based on what the user actually asked."
    )
    user_prompt = f"""
    Active Stock Context: {company_name} ({ticker})
    Live Market Data:
    - Current Price: {currency}{price:,.2f} ({pct_change:+.2f}% today)
    - 14-Day RSI: {rsi:.1f} | Daily Volatility: {volatility_pct:.2f}% | 14-Day ATR: {currency}{atr_val:,.2f}
    - 20-Day SMA: {currency}{sma20:,.2f} | 50-Day EMA: {currency}{ema50:,.2f}
    - 52-Week Low/High: {currency}{low52:,.2f} to {currency}{high52:,.2f}
    - 5-Day Machine Learning Forecast: {currency}{ml_pred_5d:,.2f} ({ml_move_pct:+.2f}%)

    User Message: "{user_question}"
    """

    clean_key = GROQ_API_KEY.strip()
    if clean_key.startswith("gsk_"):
        for model_name in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                client = Groq(api_key=clean_key)
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.6,
                    max_tokens=750
                )
                return resp.choices[0].message.content, f"🟢 Powered by Live Groq LLaMA ({model_name})"
            except Exception:
                continue

    try:
        payload = json.dumps({
            "model": "openai",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.6
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://text.pollinations.ai/openai",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "StreakPulseAI/1.0"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            ai_text = res_json["choices"][0]["message"]["content"]
            if ai_text and len(ai_text) > 20:
                return ai_text, f"🟢 Powered by Live Cloud LLM + Real-Time {ticker} RAG Feed"
    except Exception:
        pass

    trend_up = price >= sma20
    verdict = "BULLISH ACCUMULATION 🟢 ▲" if (trend_up and rsi < 68) else ("OVERBOUGHT / BOOK PROFITS 🟡" if rsi >= 68 else "BEARISH / WAIT FOR SUPPORT 🔴 ▼")
    return f"""
### 📊 Live Stock Intelligence Report: {company_name} (`{ticker}`)
* **Live Market Snapshot:** **{company_name} (`{ticker}`)** is trading at **`{currency}{price:,.2f}`** (`{pct_change:+.2f}%` today), with a 52-week range of **`{currency}{low52:,.2f}` – `{currency}{high52:,.2f}`**.
* **AI Technical Verdict:** **{verdict}**
  * **Trend vs 20-SMA (`{currency}{sma20:,.2f}`):** Price is trading **`{((price - sma20)/sma20)*100:+.2f}%`** {'above ▲' if trend_up else 'below ▼'} its 20-day average.
  * **Momentum (RSI-14):** **`{rsi:.1f}`** | **5-Day ML Forecast:** **`{currency}{ml_pred_5d:,.2f}`** (`{ml_move_pct:+.2f}%`).
* **Key Action Levels for `{ticker}`:**
  * **Buy / Entry Zone:** `{currency}{price * 0.994:,.2f}` – `{currency}{price:,.2f}`
  * **Stop-Loss (1.5x ATR):** `{currency}{price - (1.5 * atr_val):,.2f}`
  * **Target 1:** `{currency}{price + (1.8 * atr_val):,.2f}` | **Target 2:** `{currency}{price + (3.2 * atr_val):,.2f}`
""", f"⚡ Powered by StreakPulse Live Quant Engine ({ticker})"

# ==========================================================
# 4. SQLITE DATABASE (USERS, HOLDINGS, POSITIONS, ORDERS, TICKETS)
# ==========================================================
def init_db():
    conn = sqlite3.connect("streakpulse_pro.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    full_name TEXT,
                    email TEXT,
                    password_hash TEXT,
                    balance REAL
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS portfolio (
                    username TEXT,
                    ticker TEXT,
                    shares INTEGER,
                    avg_price REAL,
                    PRIMARY KEY (username, ticker)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS positions (
                    username TEXT,
                    ticker TEXT,
                    product_type TEXT,
                    shares INTEGER,
                    avg_price REAL,
                    PRIMARY KEY (username, ticker, product_type)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    timestamp TEXT,
                    ticker TEXT,
                    action TEXT,
                    shares INTEGER,
                    price REAL,
                    total REAL
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS funding_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    timestamp TEXT,
                    type TEXT,
                    method TEXT,
                    reference TEXT,
                    amount REAL,
                    status TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT,
                    timestamp TEXT,
                    category TEXT,
                    subject TEXT,
                    email TEXT,
                    status TEXT
                )""")
    
    demo_hash = hashlib.sha256("demo123".encode()).hexdigest()
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'trader_pro'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                  ("trader_pro", "Final Year Demo Trader", "demo@streakpulse.ai", demo_hash, 100000.0))
        c.execute("INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("trader_pro", datetime.now().strftime("%Y-%m-%d %H:%M"), "DEPOSIT", "Initial Welcome Bonus", "BONUS-100K", 100000.0, "COMPLETED"))
    conn.commit()
    return conn

conn = init_db()

def get_user_balance(username):
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    return row[0] if row else 0.0

def update_funds(username, amount, tx_type, method, reference):
    c = conn.cursor()
    bal = get_user_balance(username)
    if tx_type == "WITHDRAW" and amount > bal:
        return False, "❌ Withdrawal amount exceeds your available wallet cash!"
    new_bal = bal + amount if tx_type == "DEPOSIT" else bal - amount
    c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, username))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
                 VALUES (?, ?, ?, ?, ?, ?, 'COMPLETED')""",
              (username, now, tx_type, method, reference, amount))
    conn.commit()
    return True, f"✅ ₹{amount:,.2f} {'deposited to' if tx_type == 'DEPOSIT' else 'withdrawn from'} your trading wallet!"

def execute_trade(username, ticker, action, shares, current_price, product_type="CNC (Delivery)"):
    c = conn.cursor()
    balance = get_user_balance(username)
    # MIS Intraday gives 5x leverage (20% margin required), CNC requires 100%
    is_mis = "MIS" in product_type
    total_value = shares * current_price
    required_margin = total_value * 0.20 if is_mis else total_value
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "BUY":
        if required_margin > balance:
            return False, f"❌ Insufficient margin! Required: ₹{required_margin:,.2f}. Click 'Funds' to deposit cash."
        new_balance = balance - required_margin
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))
        
        if not is_mis:
            c.execute("SELECT shares, avg_price FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
            row = c.fetchone()
            if row:
                old_shares, old_avg = row
                new_shares = old_shares + shares
                new_avg = ((old_shares * old_avg) + total_value) / new_shares
                c.execute("UPDATE portfolio SET shares = ?, avg_price = ? WHERE username = ? AND ticker = ?",
                          (new_shares, new_avg, username, ticker))
            else:
                c.execute("INSERT INTO portfolio VALUES (?, ?, ?, ?)", (username, ticker, shares, current_price))
        
        # Also log in active positions (Kite Positions tab)
        p_tag = "MIS" if is_mis else "CNC"
        c.execute("SELECT shares, avg_price FROM positions WHERE username = ? AND ticker = ? AND product_type = ?", (username, ticker, p_tag))
        prow = c.fetchone()
        if prow:
            ns = prow[0] + shares
            na = ((prow[0] * prow[1]) + total_value) / ns
            c.execute("UPDATE positions SET shares = ?, avg_price = ? WHERE username = ? AND ticker = ? AND product_type = ?",
                      (ns, na, username, ticker, p_tag))
        else:
            c.execute("INSERT INTO positions VALUES (?, ?, ?, ?, ?)", (username, ticker, p_tag, shares, current_price))

        c.execute("""INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", (username, now, ticker, f"BUY ({p_tag})", shares, current_price, total_value))
        conn.commit()
        return True, f"✅ Executed BUY ({p_tag}): {shares} qty of {ticker} @ ₹{current_price:,.2f}"

    elif action == "SELL":
        p_tag = "MIS" if is_mis else "CNC"
        if is_mis:
            c.execute("SELECT shares, avg_price FROM positions WHERE username = ? AND ticker = ? AND product_type = 'MIS'", (username, ticker))
            row = c.fetchone()
            if not row or row[0] < shares:
                return False, "❌ You do not have enough open MIS Intraday positions to sell!"
            new_shares = row[0] - shares
            pnl = (current_price - row[1]) * shares
            margin_released = (shares * row[1]) * 0.20
            c.execute("UPDATE users SET balance = ? WHERE username = ?", (balance + margin_released + pnl, username))
            if new_shares == 0:
                c.execute("DELETE FROM positions WHERE username = ? AND ticker = ? AND product_type = 'MIS'", (username, ticker))
            else:
                c.execute("UPDATE positions SET shares = ? WHERE username = ? AND ticker = ? AND product_type = 'MIS'", (new_shares, username, ticker))
        else:
            c.execute("SELECT shares FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
            row = c.fetchone()
            if not row or row[0] < shares:
                return False, "❌ You do not hold enough CNC shares in your Holdings to sell!"
            new_shares = row[0] - shares
            c.execute("UPDATE users SET balance = ? WHERE username = ?", (balance + total_value, username))
            if new_shares == 0:
                c.execute("DELETE FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
                c.execute("DELETE FROM positions WHERE username = ? AND ticker = ? AND product_type = 'CNC'", (username, ticker))
            else:
                c.execute("UPDATE portfolio SET shares = ? WHERE username = ? AND ticker = ?", (new_shares, username, ticker))
                c.execute("UPDATE positions SET shares = ? WHERE username = ? AND ticker = ? AND product_type = 'CNC'", (new_shares, username, ticker))

        c.execute("""INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", (username, now, ticker, f"SELL ({p_tag})", shares, current_price, total_value))
        conn.commit()
        return True, f"✅ Executed SELL ({p_tag}): {shares} qty of {ticker} @ ₹{current_price:,.2f}"

# ==========================================================
# 5. SESSION STATE ROUTING INITIALIZATION
# ==========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "RELIANCE.NS"
if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []
if "public_page" not in st.session_state:
    st.session_state.public_page = "Home"

def navigate_to(page_name, ticker=None):
    st.session_state.page = page_name
    if ticker:
        st.session_state.selected_ticker = ticker

# ==========================================================
# 6. REUSABLE ZERODHA CLONE PUBLIC COMPONENTS (OPEN ACCOUNT & FOOTER)
# ==========================================================
def render_zerodha_open_account(key_suffix="main"):
    """Reusable OpenAccount.js component from the Zerodha Clone playlist."""
    st.markdown("""
    <div class="z-section-card" style="text-align:center; background: radial-gradient(circle at center, #111c35 0%, #070b14 100%);">
        <h2 style="color:#ffffff; font-weight:800; font-size:1.95rem; margin-bottom:10px;">Open a Zerodha × StreakPulse Account</h2>
        <p style="color:#94a3b8; font-size:1.02rem; margin-bottom:20px;">
            Modern platforms and apps, ₹0 equity delivery investments, flat ₹20 intraday and F&O trades, plus ₹1,00,000 instant virtual margin.
        </p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.6, 1.2, 1.6])
    with c2:
        if st.button("🚀 Sign up Now (Claim ₹1,00,000 Free)", key=f"open_acc_btn_{key_suffix}", type="primary", use_container_width=True):
            st.session_state.public_page = "Signup"
            st.rerun()

def render_zerodha_footer():
    """Reusable 4-Column Footer.js component with SEBI/NSE/BSE disclaimers from the Zerodha Clone playlist."""
    st.markdown("""
    <div class="z-footer">
        <div style="display:grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; gap:28px; padding-bottom:28px; border-bottom:1px solid #1e293b;">
            <div>
                <div style="font-weight:800; font-size:1.35rem; color:#ffffff; margin-bottom:10px;">
                    ⚡ <span style="color:#387ed1;">ZERODHA</span> × StreakPulse
                </div>
                <p style="font-size:0.82rem; color:#94a3b8; line-height:1.6;">
                    © 2010 - 2026, Zerodha × StreakPulse Broking Ltd.<br>
                    All rights reserved.<br>
                    B.Tech Final Year Major Project • AI & FinTech Terminal
                </p>
                <div style="margin-top:12px; font-size:0.85rem; color:#38bdf8;">
                    🌐 Twitter • 💼 LinkedIn • 📸 Instagram • ▶️ YouTube • 💬 Telegram
                </div>
            </div>
            <div>
                <div style="color:#ffffff; font-weight:700; font-size:0.95rem; margin-bottom:12px;">Company</div>
                <div style="font-size:0.84rem; line-height:2.0; color:#94a3b8;">
                    About<br>Products<br>Pricing<br>Referral programme<br>Careers<br>Zerodha.tech<br>Press & media<br>Zerodha Cares (CSR)
                </div>
            </div>
            <div>
                <div style="color:#ffffff; font-weight:700; font-size:0.95rem; margin-bottom:12px;">Support</div>
                <div style="font-size:0.84rem; line-height:2.0; color:#94a3b8;">
                    Contact us<br>Support portal<br>Z-Connect blog<br>List of charges<br>Downloads & resources<br>Videos<br>Market overview<br>How to file a complaint?
                </div>
            </div>
            <div>
                <div style="color:#ffffff; font-weight:700; font-size:0.95rem; margin-bottom:12px;">Account</div>
                <div style="font-size:0.84rem; line-height:2.0; color:#94a3b8;">
                    Open an account<br>Fund transfer<br>60 day challenge<br>Margin calculator<br>Streak AI Algo Lab
                </div>
            </div>
        </div>
        <div style="margin-top:22px; font-size:0.75rem; color:#64748b; line-height:1.7;">
            <p>Zerodha × StreakPulse Broking Ltd.: Member of NSE, BSE & MCX – SEBI Registration no.: INZ000031633. CDSL/NSDL: Depository services through Zerodha Broking Ltd. – SEBI Registration no.: IN-DP-431-2019.</p>
            <p style="margin-top:8px;">Investments in securities market are subject to market risks; read all the related documents carefully before investing. Prevent Unauthorized Transactions in your account — update your mobile numbers/email IDs with your stock brokers. Receive information of your transactions directly from Exchange on your mobile/email at the end of the day.</p>
            <div style="margin-top:14px; text-align:center; font-weight:600; color:#94a3b8;">
                NSE &nbsp;•&nbsp; BSE &nbsp;•&nbsp; MCX &nbsp;•&nbsp; Terms & conditions &nbsp;•&nbsp; Policies & procedures &nbsp;•&nbsp; Privacy policy &nbsp;•&nbsp; Disclosure &nbsp;•&nbsp; For investor's attention &nbsp;•&nbsp; Investor charter
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================================
# 7. PART 1: PUBLIC ZERODHA CLONE PORTAL (HOME, SIGNUP, ABOUT, PRODUCTS, PRICING, SUPPORT)
# ==========================================================
if not st.session_state.logged_in:
    # ZERODHA CLONE PERSISTENT TOP NAVBAR (Navbar.js)
    nav_c1, nav_c2, nav_c3, nav_c4, nav_c5, nav_c6, nav_c7, nav_c8 = st.columns([1.6, 1.8, 0.85, 0.85, 0.85, 0.9, 0.85, 1.2])
    
    with nav_c1:
        st.markdown("""
        <div style="font-weight:800; font-size:1.35rem; color:#ffffff; padding-top:6px; letter-spacing:-0.02em;">
            ⚡ <span style="color:#387ed1;">ZERODHA</span> <span style="font-size:0.85rem; color:#38bdf8;">× StreakAI</span>
        </div>
        """, unsafe_allow_html=True)

    with nav_c2:
        search_options = ["🔍 Search stocks (Ctrl+K)..."] + [
            f"{sym} — {meta['name']} ({meta['exchange']})" for sym, meta in STOCK_CATALOG.items()
        ]
        picked_search = st.selectbox("Search", search_options, label_visibility="collapsed")
        if picked_search != "🔍 Search stocks (Ctrl+K)...":
            sym_jump = picked_search.split(" — ")[0]
            st.session_state.logged_in = True
            st.session_state.username = "trader_pro"
            st.session_state.full_name = "Final Year Demo Trader"
            st.session_state.selected_ticker = sym_jump
            st.session_state.page = "Terminal"
            st.rerun()

    pub_pages = [
        ("🏠 Home", "Home", nav_c3),
        ("🔐 Signup", "Signup", nav_c4),
        ("🏛️ About", "About", nav_c5),
        ("🚀 Products", "Products", nav_c6),
        ("🏷️ Pricing", "Pricing", nav_c7)
    ]
    for label, p_name, col_obj in pub_pages:
        if col_obj.button(label, use_container_width=True, type="primary" if st.session_state.public_page == p_name else "secondary"):
            st.session_state.public_page = p_name
            st.rerun()

    if nav_c8.button("🎧 Support", use_container_width=True, type="primary" if st.session_state.public_page == "Support" else "secondary"):
        st.session_state.public_page = "Support"
        st.rerun()

    st.markdown("<hr style='border:0; border-top:1px solid #1e293b; margin:6px 0 18px 0;'>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # PUBLIC PAGE A: HOME PAGE (Hero + Awards + Stats + Pricing + Education + OpenAccount)
    # ----------------------------------------------------------
    if st.session_state.public_page == "Home":
        hero_left, hero_right = st.columns([1.62, 1.0], gap="large")

        with hero_left:
            live_hero_html = """
            <!DOCTYPE html>
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600;700;800&display=swap" rel="stylesheet">
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body { background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; color: #f8fafc; overflow: hidden; }
                .hero-card {
                    background: radial-gradient(circle at 85% 35%, rgba(56, 126, 209, 0.30), rgba(6, 182, 212, 0.16) 45%, #070b14 85%);
                    border: 1px solid #1e293b;
                    border-radius: 22px;
                    padding: 22px 24px;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.65);
                }
                .top-bar { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; margin-bottom: 16px; border-bottom: 1px solid #1e293b; }
                .live-dot { height: 10px; width: 10px; background: #10b981; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #10b981; animation: blink 1.2s infinite; }
                @keyframes blink { 50% { opacity: 0.35; } }
                .grid-box { display: grid; grid-template-columns: 1.45fr 1.15fr; gap: 14px; }
                .panel { background: #090d16; border: 1px solid #1e293b; border-radius: 16px; padding: 16px; }
                .logo-sm { width: 24px; height: 24px; border-radius: 6px; background: #ffffff; padding: 2px; object-fit: contain; vertical-align: middle; }
                .bar-row { display: flex; align-items: center; gap: 10px; margin: 10px 0; }
                .bar-track { flex: 1; background: #111827; height: 11px; border-radius: 6px; overflow: hidden; }
                .bar-fill { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
                .watch-row { display: flex; justify-content: space-between; align-items: center; padding: 7px 8px; border-radius: 8px; margin-bottom: 5px; transition: background 0.35s ease; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
                .watch-left { display: flex; align-items: center; gap: 8px; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 0.82rem; }
                .up-text { color: #34d399; font-weight: 700; }
                .down-text { color: #fb7185; font-weight: 700; }
                .flash-up { background: rgba(16, 185, 129, 0.22) !important; }
                .flash-down { background: rgba(244, 63, 94, 0.22) !important; }
                .explore-btn { margin-top: 16px; background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 999px; padding: 10px 24px; display: inline-flex; align-items: center; gap: 12px; color: #f8fafc; cursor: pointer; transition: all 0.2s ease; }
            </style>
            </head>
            <body>
            <div class="hero-card">
                <div class="top-bar">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span class="live-dot"></span>
                        <img src="https://www.google.com/s2/favicons?domain=ril.com&sz=128" class="logo-sm">
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#cbd5e1;">
                            ZERODHA KITE • LIVE MARKETWATCH & SUPERCHART
                        </span>
                    </div>
                    <span style="background:rgba(56,126,209,0.22); color:#60a5fa; padding:4px 10px; border-radius:6px; font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:700;">
                        ⚡ INVEST IN EVERYTHING
                    </span>
                </div>

                <div class="grid-box">
                    <div class="panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <img src="https://www.google.com/s2/favicons?domain=apple.com&sz=128" class="logo-sm">
                                <img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=128" class="logo-sm">
                                <span style="font-weight:800; font-size:0.88rem;">Kite Orderflow & Depth</span>
                            </div>
                            <span class="up-text" style="font-family:'JetBrains Mono',monospace; font-size:0.85rem;">▲ +2.84%</span>
                        </div>

                        <div class="bar-row">
                            <div class="bar-track"><div id="bar1" class="bar-fill" style="width:68%; background:linear-gradient(90deg, #eab308 60%, #3b82f6 40%);"></div></div>
                            <span id="poc-val" style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#cbd5e1; width:85px;">POC 271.59</span>
                        </div>
                        <div class="bar-row">
                            <div class="bar-track"><div id="bar2" class="bar-fill" style="width:86%; background:linear-gradient(90deg, #eab308 55%, #06b6d4 45%);"></div></div>
                            <span style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#38bdf8; width:85px;">VAH 274.10</span>
                        </div>
                        <div class="bar-row">
                            <div class="bar-track"><div id="bar3" class="bar-fill" style="width:48%; background:linear-gradient(90deg, #ef4444 50%, #3b82f6 50%);"></div></div>
                            <span style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#fb7185; width:85px;">VAL 266.20</span>
                        </div>
                        <div class="bar-row">
                            <div class="bar-track"><div id="bar4" class="bar-fill" style="width:76%; background:linear-gradient(90deg, #10b981 65%, #3b82f6 35%);"></div></div>
                            <span style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#34d399; width:85px;">▲ AI TARGET</span>
                        </div>

                        <div style="margin-top:16px; padding-top:12px; border-top:1px solid #1e293b; display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:0.76rem;">
                            <span>BTC/USD: <b id="btc-price" class="up-text">▲ $89,420.50</b></span>
                            <span>NIFTY 50: <b style="color:#38bdf8;">▲ 24,852.40</b></span>
                        </div>
                    </div>

                    <div class="panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid #1e293b;">
                            <span style="font-size:0.76rem; font-weight:800; color:#94a3b8;">📋 KITE MARKETWATCH</span>
                            <span style="font-size:0.7rem; color:#38bdf8; font-family:'JetBrains Mono',monospace;">LIVE TICKS</span>
                        </div>

                        <div id="row-nvda" class="watch-row">
                            <div class="watch-left"><img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=128" class="logo-sm"><span>NVDA</span></div>
                            <span id="p-nvda">177.19</span><span id="c-nvda" class="up-text">▲ +4.16%</span>
                        </div>
                        <div id="row-aapl" class="watch-row">
                            <div class="watch-left"><img src="https://www.google.com/s2/favicons?domain=apple.com&sz=128" class="logo-sm"><span>AAPL</span></div>
                            <span id="p-aapl">264.18</span><span id="c-aapl" class="down-text">▼ -1.21%</span>
                        </div>
                        <div id="row-tcs" class="watch-row">
                            <div class="watch-left"><img src="https://www.google.com/s2/favicons?domain=tcs.com&sz=128" class="logo-sm"><span>TCS</span></div>
                            <span id="p-tcs">4,120.50</span><span id="c-tcs" class="up-text">▲ +1.85%</span>
                        </div>
                        <div id="row-rel" class="watch-row">
                            <div class="watch-left"><img src="https://www.google.com/s2/favicons?domain=ril.com&sz=128" class="logo-sm"><span>RELIANCE</span></div>
                            <span id="p-rel">2,985.00</span><span id="c-rel" class="up-text">▲ +2.10%</span>
                        </div>
                        <div id="row-tsla" class="watch-row">
                            <div class="watch-left"><img src="https://www.google.com/s2/favicons?domain=tesla.com&sz=128" class="logo-sm"><span>TSLA</span></div>
                            <span id="p-tsla">402.51</span><span id="c-tsla" class="down-text">▼ -1.49%</span>
                        </div>
                    </div>
                </div>

                <div style="text-align:center;">
                    <div class="explore-btn">
                        <span style="font-size:1.15rem;">⚡</span>
                        <div style="text-align:left;">
                            <div style="font-weight:800; font-size:0.88rem; color:#38bdf8;">Online platform to invest in stocks, derivatives, mutual funds & algos</div>
                            <div style="font-size:0.74rem; color:#94a3b8;">1.5+ Crore clients • 15%+ of all Indian retail trading volume</div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                const stocks = [
                    { id: 'nvda', price: 177.19, pct: 4.16 },
                    { id: 'aapl', price: 264.18, pct: -1.21 },
                    { id: 'tcs',  price: 4120.50, pct: 1.85 },
                    { id: 'rel',  price: 2985.00, pct: 2.10 },
                    { id: 'tsla', price: 402.51, pct: -1.49 }
                ];
                let btc = 89420.50;
                setInterval(() => {
                    stocks.forEach(s => {
                        const delta = (Math.random() - 0.48) * (s.price * 0.003);
                        s.price = Math.max(1, s.price + delta);
                        s.pct = s.pct + (delta >= 0 ? 0.03 : -0.03);
                        const pEl = document.getElementById('p-' + s.id);
                        const cEl = document.getElementById('c-' + s.id);
                        const rEl = document.getElementById('row-' + s.id);
                        pEl.innerText = s.price >= 1000 ? s.price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : s.price.toFixed(2);
                        cEl.innerText = (s.pct >= 0 ? '▲ +' : '▼ ') + s.pct.toFixed(2) + '%';
                        cEl.className = s.pct >= 0 ? 'up-text' : 'down-text';
                        rEl.classList.remove('flash-up', 'flash-down');
                        void rEl.offsetWidth;
                        rEl.classList.add(delta >= 0 ? 'flash-up' : 'flash-down');
                    });
                    btc += (Math.random() - 0.47) * 45;
                    document.getElementById('btc-price').innerText = (btc >= 89400 ? '▲ $' : '▼ $') + btc.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    document.getElementById('bar1').style.width = (60 + Math.random()*25) + '%';
                    document.getElementById('bar2').style.width = (70 + Math.random()*22) + '%';
                }, 1100);
            </script>
            </body>
            </html>
            """
            components.html(live_hero_html, height=420)

        with hero_right:
            st.markdown("""
            <div style="background:linear-gradient(145deg, #0f172a, #090d16); border:1px solid #1e293b; border-radius:20px; padding:20px 24px; margin-bottom:12px;">
                <span style="background:rgba(56,126,209,0.2); color:#60a5fa; padding:4px 12px; border-radius:999px; font-size:0.75rem; font-weight:700;">
                    ⚡ KITE WEB TERMINAL • ZERO-LATENCY ACCESS
                </span>
                <h3 style="margin:10px 0 4px 0; font-weight:800; color:#ffffff;">Sign In to Kite Dashboard</h3>
                <p style="color:#94a3b8; font-size:0.83rem; margin:0;">Includes Orders, Holdings, Positions, Funds, SuperCharts & LLaMA 3.3 AI</p>
            </div>
            """, unsafe_allow_html=True)

            auth_tab1, auth_tab2 = st.tabs(["🔐 Kite Login", "✨ Open Free Account"])

            with auth_tab1:
                login_user = st.text_input("Kite User ID", value="trader_pro")
                login_pass = st.text_input("Password", type="password", value="demo123")
                
                b1, b2 = st.columns(2)
                if b1.button("🚀 Login to Kite", use_container_width=True, type="primary"):
                    c = conn.cursor()
                    pw_hash = hashlib.sha256(login_pass.encode()).hexdigest()
                    c.execute("SELECT full_name FROM users WHERE username = ? AND password_hash = ?", (login_user, pw_hash))
                    res = c.fetchone()
                    if res:
                        st.session_state.logged_in = True
                        st.session_state.username = login_user
                        st.session_state.full_name = res[0]
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid username or password!")

                if b2.button("⚡ 1-Click Demo Login", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.username = "trader_pro"
                    st.session_state.full_name = "Final Year Demo Trader"
                    st.session_state.page = "Dashboard"
                    st.rerun()

            with auth_tab2:
                new_name = st.text_input("Full Name", placeholder="e.g., Vishal Babu")
                new_user = st.text_input("Choose Kite ID", placeholder="e.g., vishal_quant")
                new_email = st.text_input("Email ID", placeholder="vishal@college.edu")
                new_pass = st.text_input("Create Password", type="password")
                if st.button("✅ Open Account & Claim ₹1,00,000", use_container_width=True, type="primary"):
                    if new_user and new_pass and new_name:
                        c = conn.cursor()
                        c.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_user,))
                        if c.fetchone()[0] > 0:
                            st.warning("Username already exists!")
                        else:
                            pw_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                                      (new_user, new_name, new_email, pw_hash, 100000.0))
                            c.execute("""INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
                                         VALUES (?, ?, 'DEPOSIT', 'Signup Margin Credit', 'INIT-100K', 100000.0, 'COMPLETED')""",
                                      (new_user, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            conn.commit()
                            st.session_state.logged_in = True
                            st.session_state.username = new_user
                            st.session_state.full_name = new_name
                            st.session_state.page = "Dashboard"
                            st.rerun()

        # ZERODHA HOME COMPONENT 2: AWARDS.JS ("Largest stock broker in India")
        st.markdown("""
        <div class="z-section-card">
            <div style="display:grid; grid-template-columns: 1fr 1.3fr; gap:32px; align-items:center;">
                <div style="background:linear-gradient(135deg, #1e293b, #0f172a); border-radius:16px; padding:28px; text-align:center; border:1px solid #334155;">
                    <div style="font-size:3.2rem; margin-bottom:10px;">🏆</div>
                    <h3 style="color:#ffffff; font-weight:800; margin-bottom:6px;">India's #1 Retail & Algo Trading Ecosystem</h3>
                    <p style="color:#38bdf8; font-family:'JetBrains Mono',monospace; font-size:0.9rem;">15%+ of all Indian retail order volumes daily</p>
                </div>
                <div>
                    <h2 style="color:#ffffff; font-weight:800; font-size:1.75rem; margin-bottom:10px;">Largest stock broker in India</h2>
                    <p style="color:#cbd5e1; font-size:0.95rem; margin-bottom:16px;">
                        1.5+ Crore clients contribute to over 15% of all retail order volumes in India daily by trading and investing in:
                    </p>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#38bdf8; font-weight:600; font-size:0.92rem;">
                        <div>• Futures and Options</div>
                        <div>• Stocks & IPOs</div>
                        <div>• Commodity derivatives</div>
                        <div>• Direct mutual funds</div>
                        <div>• Currency derivatives</div>
                        <div>• Bonds and Govt. Securities</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ZERODHA HOME COMPONENT 3: STATS.JS ("Trust with confidence") & PRICING.JS ("Unbeatable pricing")
        st_col1, st_col2 = st.columns([1.3, 1.0], gap="large")
        with st_col1:
            st.markdown("""
            <div class="z-section-card" style="height:100%;">
                <h2 style="color:#ffffff; font-weight:800; font-size:1.65rem; margin-bottom:14px;">🛡️ Trust with confidence</h2>
                <div style="margin-bottom:14px;">
                    <h4 style="color:#38bdf8; margin:0 0 4px 0;">Customer-first always</h4>
                    <p style="color:#94a3b8; font-size:0.88rem; margin:0;">That's why 1.5+ crore customers trust Zerodha with ₹4.5+ lakh crores of equity investments.</p>
                </div>
                <div style="margin-bottom:14px;">
                    <h4 style="color:#38bdf8; margin:0 0 4px 0;">No spam or gimmicks</h4>
                    <p style="color:#94a3b8; font-size:0.88rem; margin:0;">No gimmicks, spam, "gamification", or annoying push notifications. High quality apps that you use at your pace.</p>
                </div>
                <div>
                    <h4 style="color:#38bdf8; margin:0 0 4px 0;">The Zerodha × StreakPulse universe</h4>
                    <p style="color:#94a3b8; font-size:0.88rem; margin:0;">Not just an app, but a whole ecosystem with Streak AI Backtesting, Random Forest ML Forecasting, and LLaMA 3.3 Advisor.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st_col2:
            st.markdown("""
            <div class="z-section-card" style="height:100%;">
                <h2 style="color:#ffffff; font-weight:800; font-size:1.65rem; margin-bottom:10px;">🏷️ Unbeatable pricing</h2>
                <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:18px;">
                    We pioneered the concept of discount broking and price transparency in India. Flat fees and no hidden charges.
                </p>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; text-align:center;">
                    <div style="background:#090d16; border:1px solid #10b981; border-radius:14px; padding:18px;">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:800; color:#34d399;">₹0</div>
                        <div style="font-size:0.8rem; color:#cbd5e1; margin-top:6px;">Free equity delivery & direct mutual funds</div>
                    </div>
                    <div style="background:#090d16; border:1px solid #38bdf8; border-radius:14px; padding:18px;">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:800; color:#38bdf8;">₹20</div>
                        <div style="font-size:0.8rem; color:#cbd5e1; margin-top:6px;">Flat Intraday, F&O & Algo trades</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ZERODHA HOME COMPONENT 4: EDUCATION.JS ("Free and open market education")
        st.markdown("""
        <div class="z-section-card">
            <div style="display:grid; grid-template-columns: 1fr 1.4fr; gap:28px; align-items:center;">
                <div style="background:#090d16; border:1px solid #1e293b; border-radius:16px; padding:26px; text-align:center;">
                    <div style="font-size:3rem;">📚</div>
                    <h3 style="color:#ffffff; font-weight:800; margin-top:8px;">Varsity × AI Quant Academy</h3>
                    <p style="color:#94a3b8; font-size:0.85rem;">Free stock market & algorithmic trading education</p>
                </div>
                <div>
                    <h2 style="color:#ffffff; font-weight:800; font-size:1.65rem; margin-bottom:10px;">Free and open market education</h2>
                    <p style="color:#cbd5e1; font-size:0.9rem; margin-bottom:12px;">
                        <b>Varsity</b>, the largest online stock market education book in the world covering everything from the basics to advanced technical analysis and quantitative modeling.
                    </p>
                    <p style="color:#cbd5e1; font-size:0.9rem; margin:0;">
                        <b>TradingQ&A + LLaMA 3.3 AI Advisor</b>, the most active trading and investment community where our built-in AI answers every market query instantly.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_zerodha_open_account("home")

    # ----------------------------------------------------------
    # PUBLIC PAGE B: SIGNUP PAGE (Signup.js)
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Signup":
        s_left, s_right = st.columns([1.2, 1.2], gap="large")
        with s_left:
            st.markdown("""
            <div class="z-section-card">
                <span style="background:rgba(56,126,209,0.2); color:#60a5fa; padding:5px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
                    JOIN 1.5+ CRORE INVESTORS
                </span>
                <h2 style="color:#ffffff; font-weight:800; margin:12px 0 10px 0;">Open a free demat and trading account online</h2>
                <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6;">
                    Start investing brokerage-free and join a community of 1.5+ crore investors and traders. Instant paper margin of <b>₹1,00,000</b> credited immediately upon registration.
                </p>
                <div style="margin-top:18px; padding:16px; background:#090d16; border-radius:12px; border:1px solid #1e293b; color:#cbd5e1; font-size:0.86rem;">
                    ✅ ₹0 Equity Delivery Brokerage<br>
                    ✅ Built-In Groq LLaMA 3.3 AI Financial Advisor<br>
                    ✅ 7-Day Random Forest ML Price Predictor<br>
                    ✅ Streak v4 No-Code Strategy Backtester
                </div>
            </div>
            """, unsafe_allow_html=True)
        with s_right:
            st.markdown("### ✨ Create Your Kite Account Now")
            su_name = st.text_input("Your Full Name", placeholder="e.g., Vishal Babu")
            su_user = st.text_input("Choose Kite User ID", placeholder="e.g., vishal_01")
            su_email = st.text_input("Email Address", placeholder="vishal@example.com")
            su_pass = st.text_input("Password", type="password")
            if st.button("🚀 Complete Signup & Open Kite Dashboard", type="primary", use_container_width=True):
                if su_name and su_user and su_pass:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM users WHERE username = ?", (su_user,))
                    if c.fetchone()[0] > 0:
                        st.warning("User ID already exists! Try another or log in.")
                    else:
                        pw_hash = hashlib.sha256(su_pass.encode()).hexdigest()
                        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (su_user, su_name, su_email, pw_hash, 100000.0))
                        c.execute("""INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
                                     VALUES (?, ?, 'DEPOSIT', 'Signup Margin Credit', 'INIT-100K', 100000.0, 'COMPLETED')""",
                                  (su_user, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.session_state.logged_in = True
                        st.session_state.username = su_user
                        st.session_state.full_name = su_name
                        st.session_state.page = "Dashboard"
                        st.rerun()
                else:
                    st.warning("Please fill in Name, User ID, and Password.")
            st.markdown("---")
            if st.button("⚡ Or Use 1-Click Examiner Demo Account", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "trader_pro"
                st.session_state.full_name = "Final Year Demo Trader"
                st.session_state.page = "Dashboard"
                st.rerun()

    # ----------------------------------------------------------
    # PUBLIC PAGE C: ABOUT PAGE (AboutPage.js -> Hero.js + Team.js)
    # ----------------------------------------------------------
    elif st.session_state.public_page == "About":
        st.markdown("""
        <div class="z-section-card" style="text-align:center;">
            <h2 style="color:#ffffff; font-weight:800; font-size:1.85rem; max-width:800px; margin:0 auto;">
                We pioneered the discount broking model in India.<br>
                <span style="color:#38bdf8;">Now, we are breaking ground with AI & Quantitative Technology.</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)

        ab_c1, ab_c2 = st.columns(2, gap="large")
        with ab_c1:
            st.markdown("""
            <div class="z-section-card" style="height:100%; color:#cbd5e1; font-size:0.94rem; line-height:1.75;">
                <p>We kick-started operations with the goal of breaking all barriers that traders and investors face in India in terms of cost, support, and institutional technology.</p>
                <p>Today, our disruptive pricing models and in-house quantitative AI tools — including <b>Random Forest price forecasting</b> and <b>LLaMA 3.3 RAG market intelligence</b> — make institutional-grade analysis accessible to every retail investor.</p>
            </div>
            """, unsafe_allow_html=True)
        with ab_c2:
            st.markdown("""
            <div class="z-section-card" style="height:100%; color:#cbd5e1; font-size:0.94rem; line-height:1.75;">
                <p>In addition, we run a number of open educational and community initiatives to empower retail traders and investors through <b>Varsity</b> and <b>Streak Algo Lab</b>.</p>
                <p>Through our FinTech incubator <b>Rainmatter</b>, we also support innovative startups and student engineering projects building the future of Indian capital markets.</p>
            </div>
            """, unsafe_allow_html=True)

        # Team.js Section from Playlist
        st.markdown("""
        <div class="z-section-card">
            <h2 style="text-align:center; color:#ffffff; font-weight:800; margin-bottom:24px;">👥 People & Engineering Team</h2>
            <div style="display:grid; grid-template-columns: 1fr 2fr; gap:28px; align-items:center;">
                <div style="text-align:center; background:#090d16; padding:24px; border-radius:16px; border:1px solid #38bdf8;">
                    <div style="font-size:3.6rem;">👨‍💻</div>
                    <h4 style="color:#ffffff; font-weight:800; margin:10px 0 4px 0;">Final Year Project Team</h4>
                    <div style="color:#38bdf8; font-size:0.84rem; font-weight:600;">Full-Stack Python, ML & FinTech Architecture</div>
                </div>
                <div style="color:#cbd5e1; font-size:0.95rem; line-height:1.75;">
                    <p>This full-stack platform integrates the complete <b>Zerodha Kite, Console, Streak, and TradingView</b> architecture into a unified Python & SQLite web application.</p>
                    <p>Engineered with live <b>Yahoo Finance market streams</b>, <b>Scikit-Learn Random Forest ensemble modeling</b>, <b>Groq LLaMA 3.3 conversational RAG</b>, and real-time <b>MIS/CNC order execution</b>.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ----------------------------------------------------------
    # PUBLIC PAGE D: PRODUCTS PAGE (ProductPage.js -> Hero + LeftSection + RightSection + Universe)
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Products":
        st.markdown("""
        <div class="z-section-card" style="text-align:center;">
            <h1 style="color:#ffffff; font-weight:800; font-size:2.2rem; margin-bottom:8px;">Zerodha × StreakPulse Products</h1>
            <h4 style="color:#94a3b8; font-weight:500; margin-bottom:10px;">Sleek, modern, and intuitive trading & AI platforms</h4>
            <div style="color:#38bdf8; font-weight:700; font-size:0.92rem;">Check out our investment offerings →</div>
        </div>
        """, unsafe_allow_html=True)

        products_showcase = [
            ("left", "📈 Kite SuperChart Terminal", "Our ultra-fast flagship trading platform with streaming market data, 3-layer TradingView charts (Candlesticks, Volume, RSI), an elegant UI, and instant CNC/MIS order execution.", "Terminal"),
            ("right", "💿 Console Portfolio & Ledger", "The central dashboard for your Zerodha account. Gain insights into your trades and investments with in-depth visualisations, asset allocation donut charts, and downloadable Excel/CSV reports.", "Holdings"),
            ("left", "🤖 StreakPulse LLaMA 3.3 AI Advisor", "Institutional conversational AI analyst pre-configured with live RAG market feeds. Type any stock name (Apple, NVIDIA, Reliance, TCS) for instant entry, stop-loss, and target levels.", "Advisor"),
            ("right", "⚡ Kite Connect API & 7-Day ML Predictor", "Build powerful trading experiences and run live 7-Day Random Forest Machine Learning price projections trained on rolling 252-day OHLCV and momentum lag features.", "Terminal"),
            ("left", "🧪 Streak No-Code Algo Backtester", "Create systematic trading strategies (Golden Crossover, RSI Reversal, Momentum Surge) without writing code, backtest on historical candles, and scan the live market.", "Apps")
        ]

        for align, p_title, p_desc, target_tab in products_showcase:
            c_a, c_b = st.columns([1, 1.2] if align == "left" else [1.2, 1], gap="large")
            visual_col = c_a if align == "left" else c_b
            text_col = c_b if align == "left" else c_a

            with visual_col:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #0f172a, #090d16); border:1px solid #334155; border-radius:18px; padding:32px; text-align:center;">
                    <div style="font-size:2.8rem; margin-bottom:8px;">{p_title.split()[0]}</div>
                    <div style="font-weight:800; color:#ffffff; font-size:1.15rem;">{p_title}</div>
                    <div style="color:#38bdf8; font-size:0.8rem; margin-top:6px;">📱 Available on Web • Google Play • App Store</div>
                </div>
                """, unsafe_allow_html=True)
            with text_col:
                st.markdown(f"### {p_title}")
                st.write(p_desc)
                b_try, b_learn = st.columns(2)
                if b_try.button(f"🚀 Try Demo →", key=f"prod_demo_{p_title}", type="primary", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.username = "trader_pro"
                    st.session_state.full_name = "Final Year Demo Trader"
                    st.session_state.page = target_tab
                    st.rerun()
                b_learn.button("📖 Learn More →", key=f"prod_learn_{p_title}", use_container_width=True)
            st.markdown("<hr style='border:0; border-top:1px solid #1e293b; margin:16px 0;'>", unsafe_allow_html=True)

        # Universe.js Component from Playlist (6 Partner Ecosystem Cards in 3x2 Grid)
        st.markdown("""
        <div style="text-align:center; margin:28px 0 18px 0;">
            <h2 style="color:#ffffff; font-weight:800;">🌌 The Zerodha Universe</h2>
            <p style="color:#94a3b8;">Extend your trading and investment experience even further with our partner platforms</p>
        </div>
        """, unsafe_allow_html=True)

        universe_items = [
            ("⚡ Streak", "Algo & strategy platform — systematic no-code backtesting and live market scanner."),
            ("🎯 Sensibull", "Options trading platform — build strategies, analyze Greeks, and track OI data."),
            ("🧺 smallcase", "Thematic investment platform — invest in diversified baskets of stocks on ETFs."),
            ("🏦 Zerodha Fund House", "Our asset management venture creating simple and transparent index funds."),
            ("📜 GoldenPi", "Bonds & fixed-income trading platform — invest in high-yield corporate bonds and G-Secs."),
            ("🛡️ Ditto", "Personalized advice on life and health insurance — no spam and no mis-selling.")
        ]
        for r_idx in range(0, 6, 3):
            u_cols = st.columns(3)
            for c_i in range(3):
                u_name, u_desc = universe_items[r_idx + c_i]
                with u_cols[c_i]:
                    st.markdown(f"""
                    <div class="z-universe-card">
                        <h4 style="color:#38bdf8; font-weight:800; margin-bottom:8px;">{u_name}</h4>
                        <p style="color:#94a3b8; font-size:0.84rem; margin:0;">{u_desc}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        render_zerodha_open_account("products")

    # ----------------------------------------------------------
    # PUBLIC PAGE E: PRICING & BROKERAGE CALCULATOR PAGE (PricingPage.js -> Hero + Brokerage.js)
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Pricing":
        st.markdown("""
        <div class="z-section-card" style="text-align:center;">
            <h1 style="color:#ffffff; font-weight:800; font-size:2.1rem;">Pricing — Free equity investments and flat ₹20 intraday trades</h1>
            <p style="color:#94a3b8; font-size:0.95rem;">All equity delivery investments (NSE, BSE), are absolutely free — ₹ 0 brokerage.</p>
        </div>
        """, unsafe_allow_html=True)

        pr1, pr2, pr3 = st.columns(3)
        with pr1:
            render_kpi("Free Equity Delivery", "₹0", "All equity delivery investments (NSE, BSE) are 100% brokerage-free.", "kpi-emerald", "#34d399")
        with pr2:
            render_kpi("Intraday & F&O Trades", "₹20", "Flat ₹20 or 0.03% (whichever is lower) per executed order on intraday.", "kpi-cyan", "#38bdf8")
        with pr3:
            render_kpi("Free Direct Mutual Funds", "₹0", "All direct mutual fund investments are completely commission-free.", "kpi-violet", "#c084fc")

        # Interactive Brokerage.js Calculator from Playlist
        st.markdown("### 🧮 Interactive Zerodha Brokerage & Statutory Charges Calculator")
        calc_c1, calc_c2, calc_c3, calc_c4 = st.columns(4)
        c_trade_type = calc_c1.selectbox("Segment", ["Equity Delivery (CNC)", "Equity Intraday (MIS)", "F&O Futures"])
        c_buy_p = calc_c2.number_input("Buy Price (₹)", min_value=1.0, value=1500.0, step=10.0)
        c_sell_p = calc_c3.number_input("Sell Price (₹)", min_value=1.0, value=1545.0, step=10.0)
        c_qty = calc_c4.number_input("Quantity (Shares)", min_value=1, value=100, step=10)

        turnover = (c_buy_p + c_sell_p) * c_qty
        gross_pnl = (c_sell_p - c_buy_p) * c_qty
        if "Delivery" in c_trade_type:
            brokerage = 0.0
            stt = turnover * 0.001
        else:
            brokerage = min(20.0, (c_buy_p * c_qty) * 0.0003) + min(20.0, (c_sell_p * c_qty) * 0.0003)
            stt = (c_sell_p * c_qty) * 0.00025
        exch_txn = turnover * 0.0000325
        sebi_fee = turnover * 0.000001
        gst = 0.18 * (brokerage + exch_txn + sebi_fee)
        stamp_duty = (c_buy_p * c_qty) * 0.00015
        total_charges = brokerage + stt + exch_txn + sebi_fee + gst + stamp_duty
        net_pnl = gross_pnl - total_charges

        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1:
            render_kpi("Total Turnover", f"₹{turnover:,.2f}", f"Brokerage: ₹{brokerage:.2f}", "kpi-cyan", "#38bdf8")
        with bc2:
            render_kpi("Total Taxes & Charges", f"₹{total_charges:,.2f}", f"STT: ₹{stt:.2f} | GST: ₹{gst:.2f}", "kpi-violet", "#c084fc")
        with bc3:
            render_kpi("Breakeven Per Share", f"₹{(total_charges/c_qty):.2f}", "Points needed to cover taxes", "kpi-white", "#2563eb")
        with bc4:
            render_kpi("Net Realized Profit / Loss", f"₹{net_pnl:,.2f}", f"Gross P&L: ₹{gross_pnl:+.2f}", "kpi-emerald" if net_pnl >= 0 else "kpi-violet", "#34d399" if net_pnl >= 0 else "#fb7185")

        render_zerodha_open_account("pricing")

    # ----------------------------------------------------------
    # PUBLIC PAGE F: SUPPORT PORTAL PAGE (SupportPage.js -> Hero.js + CreateTicket.js)
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Support":
        st.markdown("""
        <div class="z-support-hero">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <h3 style="margin:0; font-weight:800;">🎧 Support Portal</h3>
                <span style="background:rgba(255,255,255,0.2); padding:5px 14px; border-radius:999px; font-size:0.82rem; font-weight:700;">Track Tickets</span>
            </div>
            <div style="display:grid; grid-template-columns: 1.4fr 1fr; gap:28px;">
                <div>
                    <h2 style="font-weight:800; font-size:1.6rem; margin-bottom:12px;">Search for an answer or browse help topics to create a ticket</h2>
                    <div style="background:#ffffff; color:#0f172a; padding:12px 18px; border-radius:10px; font-size:0.9rem; margin-bottom:12px;">
                        🔍 Eg: how do I activate F&O, why is my order getting rejected...
                    </div>
                    <div style="font-size:0.82rem; color:#e2e8f0; text-decoration:underline;">
                        Track account opening &nbsp;•&nbsp; Track segment activation &nbsp;•&nbsp; Intraday margins &nbsp;•&nbsp; Kite user manual
                    </div>
                </div>
                <div>
                    <h4 style="font-weight:800; margin-bottom:10px;">📌 Featured Announcements</h4>
                    <ol style="font-size:0.88rem; line-height:1.8; color:#f1f5f9;">
                        <li>Current Takeovers and Delisting – Watchlist Advisory</li>
                        <li>Latest Intraday leverages – MIS & CO (5x Margin Active)</li>
                    </ol>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # CreateTicket.js 6-Category Grid from Playlist
        st.subheader("📋 To create a ticket, select a relevant topic")
        ticket_topics = [
            ("➕ Account Opening", ["Online Account Opening", "Offline Account Opening", "Company, Partnership and HUF Account", "NRI Account Opening", "Charges at Zerodha"]),
            ("👤 Your Zerodha Account", ["Login Credentials", "Account Modification and Segment Addition", "DP ID and bank details", "Your Profile", "Transfer and conversion of shares"]),
            ("📊 Trading and Markets", ["Trading FAQs", "Kite Web & Mobile", "Margins & Leverage", "Product and order types (CNC / MIS)", "Corporate actions"]),
            ("💳 Funds & Banking", ["Adding Funds (Zero Fee UPI)", "Fund Withdrawal", "eMandates", "Adding Bank Accounts", "Instant IMPS Settlement"]),
            ("💿 Console & Reports", ["Reports & Tax P&L", "Ledger Statement", "Portfolio Analytics", "60 Day Challenge", "IPO & Corporate Bonds"]),
            ("🪙 Coin & Mutual Funds", ["Understanding Mutual Funds", "About Coin Direct MF", "Buying and Selling through Coin", "Starting an SIP", "Managing your Portfolio"])
        ]
        for row_i in range(0, 6, 3):
            t_cols = st.columns(3)
            for col_i in range(3):
                t_head, t_links = ticket_topics[row_i + col_i]
                links_html = "".join([f"<div style='color:#38bdf8; font-size:0.84rem; margin:6px 0;'>• {lnk}</div>" for lnk in t_links])
                with t_cols[col_i]:
                    st.markdown(f"""
                    <div class="stock-card" style="height:100%;">
                        <h4 style="color:#ffffff; font-weight:800; margin-bottom:12px;">{t_head}</h4>
                        {links_html}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎫 Submit a Live Support Ticket")
        tk_c1, tk_c2, tk_c3 = st.columns(3)
        tk_cat = tk_c1.selectbox("Topic Category", [t[0] for t in ticket_topics])
        tk_email = tk_c2.text_input("Your Email", value="demo@streakpulse.ai")
        tk_subj = tk_c3.text_input("Issue Summary", placeholder="e.g., Need help activating F&O segment")
        if st.button("✅ Create Support Ticket", type="primary"):
            if tk_subj:
                c = conn.cursor()
                t_id = f"ZTK-{np.random.randint(10000, 99999)}"
                c.execute("INSERT INTO support_tickets (ticket_id, timestamp, category, subject, email, status) VALUES (?, ?, ?, ?, ?, 'OPEN')",
                          (t_id, datetime.now().strftime("%Y-%m-%d %H:%M"), tk_cat, tk_subj, tk_email))
                conn.commit()
                st.success(f"🎉 Ticket **{t_id}** created! Our support desk will respond shortly.")
        tk_df = pd.read_sql_query("SELECT ticket_id, timestamp, category, subject, email, status FROM support_tickets ORDER BY id DESC LIMIT 5", conn)
        if not tk_df.empty:
            st.dataframe(tk_df, use_container_width=True, hide_index=True)

    # Render Persistent 4-Column Zerodha Footer at the bottom of every public page
    render_zerodha_footer()
    st.stop()

# ==========================================================
# 8. PART 2: AUTHENTICATED ZERODHA KITE DASHBOARD (AFTER LOGIN)
# ==========================================================
core_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "AAPL", "NVDA", "TSLA"]
snapshots = fetch_market_snapshots(core_tickers)

ticker_items_html = ""
for sym, data in snapshots.items():
    cur = STOCK_CATALOG.get(sym, {}).get("currency", "₹")
    logo = get_logo_url(sym)
    arrow = "▲" if data["pct"] >= 0 else "▼"
    color = "#34d399" if data["pct"] >= 0 else "#fb7185"
    ticker_items_html += (
        f'<span class="ticker-item">'
        f'<img src="{logo}" class="ticker-logo">'
        f'<b>{sym.replace(".NS","")}</b> '
        f'<span style="color:#38bdf8;">{cur}{data["price"]:,.2f}</span> '
        f'<span style="color:{color}; font-weight:800;">{arrow} {data["pct"]:+.2f}%</span>'
        f'</span>'
    )

st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker-move">
        {ticker_items_html} {ticker_items_html}
    </div>
</div>
""", unsafe_allow_html=True)

# KITE DASHBOARD TOP NAVIGATION BAR (Matches Demo Video: Dashboard, Orders, Holdings, Positions, Funds, SuperChart, AI Advisor, Apps)
nav_cols = st.columns([1.15, 0.95, 1.05, 1.05, 0.95, 1.15, 1.15, 1.05, 0.85])
kite_pages = [
    ("📊 Dashboard", "Dashboard"),
    ("📜 Orders", "Orders"),
    ("💼 Holdings", "Holdings"),
    ("⚡ Positions", "Positions"),
    ("💳 Funds", "Funds"),
    ("📈 SuperChart", "Terminal"),
    ("🤖 AI Advisor", "Advisor"),
    ("🧩 Apps (Algo)", "Apps")
]
for idx, (label, p_key) in enumerate(kite_pages):
    btn_type = "primary" if st.session_state.page == p_key else "secondary"
    if nav_cols[idx].button(label, key=f"kite_nav_{p_key}", use_container_width=True, type=btn_type):
        navigate_to(p_key)
        st.rerun()

if nav_cols[8].button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.public_page = "Home"
    st.rerun()

# LEFT SIDEBAR: KITE MARKETWATCH + QUICK BUY / SELL / ANALYTICS
user_bal = get_user_balance(st.session_state.username)
st.sidebar.markdown(f"### 👤 {st.session_state.full_name}")
st.sidebar.caption(f"Kite ID: `@{st.session_state.username}` • **ZERODHA KITE**")

st.sidebar.markdown(f"""
<div style="background:linear-gradient(135deg, #091526, #0f2942); border:1px solid #06b6d4; border-radius:14px; padding:14px; margin-bottom:12px;">
    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase; font-weight:700;">💳 Available Kite Margin</div>
    <div style="font-family:'JetBrains Mono',monospace; font-size:1.4rem; font-weight:800; color:#38bdf8; margin-top:4px;">
        ₹{user_bal:,.2f}
    </div>
    <div style="font-size:0.72rem; color:#34d399; margin-top:3px;">● CNC Delivery (1x) & MIS Intraday (5x)</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.subheader("📋 Kite Marketwatch")
catalog_options = [f"{k} — {v['name']}" for k, v in STOCK_CATALOG.items()]
current_idx = list(STOCK_CATALOG.keys()).index(st.session_state.selected_ticker) if st.session_state.selected_ticker in STOCK_CATALOG else 0
chosen_option = st.sidebar.selectbox("Search / Select Stock", catalog_options, index=current_idx)
chosen_sym = chosen_option.split(" — ")[0]
if chosen_sym != st.session_state.selected_ticker:
    st.session_state.selected_ticker = chosen_sym
    st.rerun()

# Sidebar Instant Kite Buy/Sell Action Widget (Just like the Zerodha Clone Demo Video!)
mw_snap = snapshots.get(st.session_state.selected_ticker, {"price": 1000.0, "pct": 0.0})
mw_cur = STOCK_CATALOG.get(st.session_state.selected_ticker, {}).get("currency", "₹")
st.sidebar.markdown(f"**Selected:** `{st.session_state.selected_ticker}` ({mw_cur}{mw_snap['price']:,.2f})")
mw_prod = st.sidebar.radio("Product", ["CNC (Delivery)", "MIS (Intraday 5x)"], horizontal=True)
mw_qty = st.sidebar.number_input("Qty", min_value=1, max_value=10000, value=10, step=1)
sb_b1, sb_b2 = st.sidebar.columns(2)
if sb_b1.button("🟦 BUY (B)", use_container_width=True, type="primary"):
    ok, msg = execute_trade(st.session_state.username, st.session_state.selected_ticker, "BUY", mw_qty, mw_snap["price"], mw_prod)
    if ok:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)
if sb_b2.button("🟧 SELL (S)", use_container_width=True):
    ok, msg = execute_trade(st.session_state.username, st.session_state.selected_ticker, "SELL", mw_qty, mw_snap["price"], mw_prod)
    if ok:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)

st.sidebar.markdown("---")
st.sidebar.caption("📌 **Watchlist Live Feed**")
for w_sym in ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "AAPL", "NVDA"]:
    w_s = snapshots.get(w_sym, {"price": 0.0, "pct": 0.0})
    w_c = "#34d399" if w_s["pct"] >= 0 else "#fb7185"
    w_arr = "▲" if w_s["pct"] >= 0 else "▼"
    st.sidebar.markdown(
        f"<div style='display:flex; justify-content:space-between; font-family:JetBrains Mono,monospace; font-size:0.78rem; padding:3px 0; border-bottom:1px solid #1e293b;'>"
        f"<span>{w_sym.replace('.NS','')}</span>"
        f"<span style='color:{w_c};'>{w_s['price']:,.2f} ({w_arr}{w_s['pct']:+.2f}%)</span></div>",
        unsafe_allow_html=True
    )

# ==========================================================
# 9. KITE TAB 1: DASHBOARD (SUMMARY + INSTITUTIONAL STOCKS)
# ==========================================================
if st.session_state.page == "Dashboard":
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(st.session_state.username,))
    tot_inv = (port_df["shares"] * port_df["avg_price"]).sum() if not port_df.empty else 0.0
    tot_cur = sum(
        row["shares"] * snapshots.get(row["ticker"], {}).get("price", row["avg_price"])
        for _, row in port_df.iterrows()
    ) if not port_df.empty else 0.0
    tot_pnl = tot_cur - tot_inv

    h_c1, h_c2, h_c3, h_c4 = st.columns(4)
    with h_c1:
        render_kpi("Equity Margin Available", f"₹{user_bal:,.2f}", "Opening Balance: ₹1,00,000", "kpi-white", "#2563eb")
    with h_c2:
        render_kpi("Holdings Value", f"₹{tot_cur:,.2f}", f"Invested: ₹{tot_inv:,.2f} ({len(port_df)} stocks)", "kpi-cyan", "#38bdf8")
    with h_c3:
        render_kpi("Unrealized P&L", f"₹{tot_pnl:,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} Net Portfolio P&L", "kpi-emerald" if tot_pnl >= 0 else "kpi-violet", "#34d399")
    with h_c4:
        render_kpi("NIFTY 50 / SENSEX", "24,852.10", "▲ +0.84% • Market Open", "kpi-violet", "#c084fc")

    st.subheader("🏢 Kite Institutional Marketwatch Cards (Click to Launch Chart or AI)")
    grid_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "ICICIBANK.NS", "AAPL", "NVDA", "TSLA"]
    for row_start in range(0, len(grid_tickers), 3):
        cols = st.columns(3)
        for col_idx in range(3):
            if row_start + col_idx < len(grid_tickers):
                sym = grid_tickers[row_start + col_idx]
                meta = STOCK_CATALOG[sym]
                snap = snapshots.get(sym, {"price": 0.0, "pct": 0.0, "rsi": 50.0, "above_sma": True})
                logo_url = get_logo_url(sym)
                badge_cls = "badge-up" if snap["pct"] >= 0 else "badge-down"
                arrow = "▲" if snap["pct"] >= 0 else "▼"
                ai_tag = "🟢 ▲ BULLISH" if snap["above_sma"] and snap["rsi"] < 68 else ("🔴 ▼ BEARISH" if not snap["above_sma"] else "🟡 NEUTRAL")

                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="stock-card">
                        <div class="company-header">
                            <img src="{logo_url}" class="company-logo" alt="{meta['name']}">
                            <div>
                                <div style="font-weight:800; font-size:1.02rem; color:#ffffff;">{meta['name']}</div>
                                <div style="font-size:0.76rem; color:#38bdf8; font-weight:600;">{meta['exchange']}: {sym.replace('.NS','')} • {meta['sector']}</div>
                            </div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-top:8px;">
                            <div class="mono-price">{meta['currency']}{snap['price']:,.2f}</div>
                            <span class="{badge_cls}">{arrow} {snap['pct']:+.2f}%</span>
                        </div>
                        <div style="margin-top:12px; padding-top:10px; border-top:1px solid #1e293b; display:flex; justify-content:space-between; font-size:0.78rem; color:#94a3b8;">
                            <span>RSI (14): <b style="color:#e2e8f0;">{snap['rsi']:.1f}</b></span>
                            <span style="font-weight:700;">{ai_tag}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button(f"📈 SuperChart", key=f"dash_chart_{sym}", use_container_width=True):
                        navigate_to("Terminal", sym)
                        st.rerun()
                    if c_btn2.button(f"🤖 Ask AI Advisor", key=f"dash_ai_{sym}", use_container_width=True):
                        navigate_to("Advisor", sym)
                        st.rerun()

# ==========================================================
# 10. KITE TAB 2: ORDERS PAGE (Order Book + CSV Export)
# ==========================================================
elif st.session_state.page == "Orders":
    st.subheader("📜 Kite Executed Orders & Tradebook")
    tx_df = pd.read_sql_query(
        "SELECT timestamp, ticker, action, shares, price, total FROM transactions WHERE username = ? ORDER BY id DESC",
        conn, params=(st.session_state.username,)
    )
    if tx_df.empty:
        st.info("You haven't placed any orders yet. Use the left sidebar **BUY (B) / SELL (S)** panel or visit **SuperChart** to place an order!")
    else:
        st.dataframe(tx_df, use_container_width=True, hide_index=True)
        csv_tx = tx_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Order Book to Excel (CSV)",
            data=csv_tx,
            file_name="zerodha_kite_orders.csv",
            mime="text/csv"
        )

# ==========================================================
# 11. KITE TAB 3: HOLDINGS PAGE (CNC Delivery Holdings + Pie Chart)
# ==========================================================
elif st.session_state.page == "Holdings":
    st.subheader("💼 Kite CNC Equity Holdings (Long-Term Demat Portfolio)")
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(st.session_state.username,))
    
    if port_df.empty:
        st.info("Your Demat Holdings are currently empty. Place a **CNC (Delivery) BUY** order in the sidebar or SuperChart to build your portfolio!")
    else:
        port_df["LTP (Live Price)"] = port_df["ticker"].apply(lambda s: snapshots.get(s, {}).get("price", float(fetch_stock_history(s, "5d")["Close"].iloc[-1])))
        port_df["Invested (₹)"] = port_df["shares"] * port_df["avg_price"]
        port_df["Current Value (₹)"] = port_df["shares"] * port_df["LTP (Live Price)"]
        port_df["Net P&L (₹)"] = port_df["Current Value (₹)"] - port_df["Invested (₹)"]
        port_df["Net Change (%)"] = (port_df["Net P&L (₹)"] / port_df["Invested (₹)"]) * 100

        tot_inv = port_df["Invested (₹)"].sum()
        tot_cur = port_df["Current Value (₹)"].sum()
        tot_pnl = tot_cur - tot_inv

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            render_kpi("Total Account Net Worth", f"₹{(user_bal + tot_cur):,.2f}", "Cash + Demat Holdings", "kpi-white", "#2563eb")
        with pc2:
            render_kpi("Total Investment", f"₹{tot_inv:,.2f}", f"{len(port_df)} Active Stocks", "kpi-cyan", "#38bdf8")
        with pc3:
            render_kpi("Current Value", f"₹{tot_cur:,.2f}", "Live Mark-to-Market", "kpi-violet", "#c084fc")
        with pc4:
            render_kpi("Total P&L", f"₹{tot_pnl:,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} {(tot_pnl/tot_inv)*100:+.2f}% ROI", "kpi-emerald" if tot_pnl >= 0 else "kpi-violet", "#34d399")

        d_col1, d_col2 = st.columns([1.8, 1.2])
        with d_col1:
            st.markdown("##### 📂 Demat Holdings Breakdown")
            st.dataframe(port_df.round(2), use_container_width=True, hide_index=True)
            csv_hold = port_df.round(2).to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Holdings Statement (CSV)", data=csv_hold, file_name="kite_holdings.csv", mime="text/csv")
        with d_col2:
            pie_fig = go.Figure(data=[go.Pie(labels=port_df["ticker"], values=port_df["Current Value (₹)"], hole=0.52)])
            pie_fig.update_layout(title="Holdings Allocation (Zerodha Console)", template="plotly_dark", paper_bgcolor="#090d16", height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(pie_fig, use_container_width=True)

# ==========================================================
# 12. KITE TAB 4: POSITIONS PAGE (MIS Intraday & CNC Open Positions + Square-Off)
# ==========================================================
elif st.session_state.page == "Positions":
    st.subheader("⚡ Kite Open Positions (MIS Intraday 5x & CNC Delivery)")
    pos_df = pd.read_sql_query("SELECT ticker, product_type, shares, avg_price FROM positions WHERE username = ?", conn, params=(st.session_state.username,))
    
    if pos_df.empty:
        st.info("No open positions right now. Place an **MIS (Intraday 5x)** or **CNC** order from the sidebar to track live M2M Positions!")
    else:
        pos_df["LTP"] = pos_df["ticker"].apply(lambda s: snapshots.get(s, {}).get("price", float(fetch_stock_history(s, "5d")["Close"].iloc[-1])))
        pos_df["M2M P&L (₹)"] = (pos_df["LTP"] - pos_df["avg_price"]) * pos_df["shares"]
        pos_df["Return (%)"] = ((pos_df["LTP"] - pos_df["avg_price"]) / pos_df["avg_price"]) * 100

        tot_m2m = pos_df["M2M P&L (₹)"].sum()
        render_kpi("Total Open Positions M2M P&L", f"₹{tot_m2m:,.2f}", f"{len(pos_df)} Active Positions", "kpi-emerald" if tot_m2m >= 0 else "kpi-violet", "#34d399")
        st.dataframe(pos_df.round(2), use_container_width=True, hide_index=True)

        st.markdown("##### ⚡ 1-Click Position Square-Off (Exit at Market)")
        sq_cols = st.columns(min(4, len(pos_df)))
        for idx, row in pos_df.iterrows():
            col_target = sq_cols[idx % len(sq_cols)]
            if col_target.button(f"🔴 Square Off {row['ticker']} ({row['product_type']})", key=f"sq_{idx}", use_container_width=True):
                ok, msg = execute_trade(st.session_state.username, row["ticker"], "SELL", int(row["shares"]), float(row["LTP"]), row["product_type"])
                if ok:
                    st.success(msg)
                    st.rerun()

# ==========================================================
# 13. KITE TAB 5: FUNDS PAGE (Add Money UPI + Withdraw IMPS)
# ==========================================================
elif st.session_state.page == "Funds":
    st.subheader("💳 Kite Funds, Margin & Banking Gateway")
    f_tab1, f_tab2 = st.tabs(["➕ Add Funds (Zero-Fee UPI / NetBanking)", "🏦 Withdraw Funds (Instant IMPS)"])

    with f_tab1:
        dep_col1, dep_col2 = st.columns([1.4, 1.6])
        with dep_col1:
            render_kpi("Available Cash Margin", f"₹{user_bal:,.2f}", "Zero Gateway Charges • Instant Credit", "kpi-white", "#2563eb")
            preset = st.radio("Quick Top-Up Amount", ["₹10,000", "₹25,000", "₹50,000", "₹1,00,000"], horizontal=True)
            preset_map = {"₹10,000": 10000.0, "₹25,000": 25000.0, "₹50,000": 50000.0, "₹1,00,000": 100000.0}
            dep_amount = st.number_input("Enter Deposit Amount (₹)", min_value=500.0, max_value=10000000.0, value=preset_map.get(preset, 25000.0), step=1000.0)
            pay_method = st.selectbox("Payment Mode", ["📱 Instant UPI (GPay / PhonePe / Paytm)", "🏦 NetBanking (HDFC / SBI / ICICI)", "💳 RuPay / Visa Debit Card"])
            pay_ref = st.text_input("UPI ID / Reference", value=f"{st.session_state.username}@okaxis")
            if st.button("✅ Authorize & Add Funds Instantly", type="primary", use_container_width=True):
                ok, msg = update_funds(st.session_state.username, dep_amount, "DEPOSIT", pay_method, pay_ref)
                if ok:
                    st.success(msg)
                    st.rerun()
        with dep_col2:
            st.markdown("##### 🧾 Recent Funding & Banking Ledger")
            f_df = pd.read_sql_query("SELECT timestamp, type, method, reference, amount, status FROM funding_history WHERE username = ? ORDER BY id DESC", conn, params=(st.session_state.username,))
            st.dataframe(f_df, use_container_width=True, hide_index=True)

    with f_tab2:
        w_col1, w_col2 = st.columns([1.4, 1.6])
        with w_col1:
            render_kpi("Withdrawable Balance", f"₹{user_bal:,.2f}", "Instant IMPS Bank Settlement", "kpi-emerald", "#34d399")
            bank_name = st.selectbox("Linked Bank", ["State Bank of India (SBI)", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank"])
            acc_num = st.text_input("Account Number", value="XXXX-XXXX-8821")
            ifsc_code = st.text_input("IFSC Code", value="SBIN0004821")
            w_amount = st.number_input("Withdrawal Amount (₹)", min_value=100.0, max_value=max(100.0, float(user_bal)), value=min(5000.0, max(100.0, float(user_bal))), step=500.0)
            if st.button("🏦 Initiate Instant Bank Payout", type="primary", use_container_width=True):
                ok, msg = update_funds(st.session_state.username, w_amount, "WITHDRAW", bank_name, f"A/C {acc_num[-4:]} ({ifsc_code})")
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        with w_col2:
            st.markdown("##### 📜 Complete Payout History")
            f_df = pd.read_sql_query("SELECT timestamp, type, method, reference, amount, status FROM funding_history WHERE username = ? ORDER BY id DESC", conn, params=(st.session_state.username,))
            st.dataframe(f_df, use_container_width=True, hide_index=True)

# ==========================================================
# 14. KITE TAB 6: SUPERCHART & 7-DAY ML PREDICTOR
# ==========================================================
elif st.session_state.page == "Terminal":
    ticker = st.session_state.selected_ticker
    meta = STOCK_CATALOG.get(ticker, {"name": ticker, "sector": "Global Equity", "domain": "tradingview.com", "exchange": "MKT", "currency": "₹"})
    currency = meta["currency"]
    logo_url = get_logo_url(ticker)

    df = fetch_stock_history(ticker, "1y")
    if df is None or len(df) < 35:
        st.error("Unable to fetch historical data for this symbol.")
        st.stop()

    latest_c = float(df["Close"].iloc[-1])
    prev_c = float(df["Close"].iloc[-2])
    chg = latest_c - prev_c
    pct = (chg / prev_c) * 100
    rsi_val = float(df["RSI"].iloc[-1])
    sma20_val = float(df["SMA_20"].iloc[-1])
    ema50_val = float(df["EMA_50"].iloc[-1])
    high_52 = float(df["High"].max())
    low_52 = float(df["Low"].min())

    st.markdown(f"""
    <div class="stock-card" style="display:flex; justify-content:space-between; align-items:center; padding:22px 26px; background:linear-gradient(135deg, #091324, #0f172a);">
        <div style="display:flex; align-items:center; gap:18px;">
            <img src="{logo_url}" class="company-logo-lg">
            <div>
                <span style="background:rgba(6,182,212,0.2); color:#22d3ee; padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:700;">
                    {meta['exchange']} • {meta['sector']}
                </span>
                <h2 style="margin:6px 0 2px 0; font-weight:800; color:#ffffff;">{meta['name']} ({ticker.replace('.NS','')})</h2>
                <div style="color:#94a3b8; font-size:0.84rem; font-family:'JetBrains Mono',monospace;">
                    52W Low: {currency}{low_52:,.2f} • 52W High: {currency}{high_52:,.2f} • 20-SMA: {currency}{sma20_val:,.2f}
                </div>
            </div>
        </div>
        <div style="text-align:right;">
            <div class="mono-price" style="font-size:2.1rem; color:#38bdf8;">{currency}{latest_c:,.2f}</div>
            <span class="{'badge-up' if pct >= 0 else 'badge-down'}" style="font-size:0.95rem;">
                {'▲' if pct >= 0 else '▼'} {chg:+.2f} ({pct:+.2f}%)
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    main_col, trade_col = st.columns([2.7, 1.1])

    with main_col:
        sub_t1, sub_t2, sub_t3 = st.tabs(["📊 Kite × TradingView SuperChart", "🤖 7-Day AI Price Forecast", "🧠 Built-In AI Stock Analyst"])
        
        with sub_t1:
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                row_heights=[0.62, 0.18, 0.20]
            )
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                name="Price", increasing_line_color="#10b981", decreasing_line_color="#f43f5e"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], name="20 SMA", line=dict(color="#38bdf8", width=1.8)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["EMA_50"], name="50 EMA", line=dict(color="#f59e0b", width=1.8, dash="dot")), row=1, col=1)

            v_colors = ["#10b981" if c >= o else "#f43f5e" for c, o in zip(df["Close"], df["Open"])]
            fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=v_colors), row=2, col=1)

            fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)", line=dict(color="#a855f7", width=2)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#f43f5e", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)

            fig.update_layout(
                template="plotly_dark", height=620, xaxis_rangeslider_visible=False,
                paper_bgcolor="#090d16", plot_bgcolor="#090d16",
                margin=dict(l=15, r=15, t=20, b=15),
                legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        with sub_t2:
            ml_df = df[["Close", "SMA_20", "EMA_50", "RSI"]].dropna().copy()
            for l in range(1, 6):
                ml_df[f"Lag_{l}"] = ml_df["Close"].shift(l)
            ml_df.dropna(inplace=True)

            f_cols = ["SMA_20", "EMA_50", "RSI", "Lag_1", "Lag_2", "Lag_3", "Lag_4", "Lag_5"]
            rf = RandomForestRegressor(n_estimators=120, random_state=42)
            rf.fit(ml_df[f_cols].values, ml_df["Close"].values)

            f_dates, f_preds = [], []
            curr_d = ml_df.index[-1]
            lags = list(ml_df["Close"].values[-5:])
            c_sma, c_ema, c_rsi = sma20_val, ema50_val, rsi_val

            for _ in range(7):
                curr_d += timedelta(days=1)
                while curr_d.weekday() >= 5:
                    curr_d += timedelta(days=1)
                vec = np.array([[c_sma, c_ema, c_rsi, lags[-1], lags[-2], lags[-3], lags[-4], lags[-5]]])
                p_val = float(rf.predict(vec)[0])
                f_dates.append(curr_d)
                f_preds.append(p_val)
                lags.append(p_val)
                c_sma = (c_sma * 19 + p_val) / 20

            target_7d = f_preds[-1]
            diff_pct = ((target_7d - latest_c) / latest_c) * 100
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                render_kpi("Current Close Price", f"{currency}{latest_c:,.2f}", "Live Spot Price", "kpi-cyan", "#38bdf8")
            with mc2:
                render_kpi("7-Day AI Projected Price", f"{currency}{target_7d:,.2f}", f"{'▲' if diff_pct >= 0 else '▼'} {diff_pct:+.2f}% Expected Move", "kpi-white", "#2563eb")
            with mc3:
                verdict_txt = "STRONG BUY ▲" if diff_pct > 1.2 else ("ACCUMULATE ▲" if diff_pct > 0 else "HOLD / CAUTION ▼")
                render_kpi("AI Model Verdict", verdict_txt, "Random Forest Ensemble", "kpi-emerald" if diff_pct >= 0 else "kpi-violet", "#34d399")

            p_fig = go.Figure()
            hist_60 = df.tail(55)
            p_fig.add_trace(go.Scatter(x=hist_60.index, y=hist_60["Close"], name="Historical Close", line=dict(color="#38bdf8", width=2.5)))
            p_fig.add_trace(go.Scatter(
                x=[hist_60.index[-1]] + f_dates, y=[latest_c] + f_preds,
                name="7-Day ML Projection", mode="lines+markers",
                line=dict(color="#10b981" if diff_pct >= 0 else "#f43f5e", width=3, dash="dash")
            ))
            p_fig.update_layout(template="plotly_dark", paper_bgcolor="#090d16", plot_bgcolor="#090d16", height=400, margin=dict(l=15, r=15, t=20, b=15))
            st.plotly_chart(p_fig, use_container_width=True)

        with sub_t3:
            q_input = st.text_input("Ask AI Advisor about any stock or strategy:", value=f"Give me a complete swing trading entry, stop-loss, and target for {meta['name']}.")
            if st.button("🧠 Generate Instant AI Report", type="primary"):
                target_sym, switched = detect_stock_from_text(q_input, ticker)
                if switched and target_sym != ticker:
                    st.session_state.selected_ticker = target_sym
                    st.rerun()
                with st.spinner("Analyzing live market indicators..."):
                    ans, engine_label = ask_built_in_ai_advisor(
                        ticker, meta["name"], currency, latest_c, pct, rsi_val, sma20_val, ema50_val, high_52, low_52, q_input
                    )
                    st.caption(engine_label)
                    st.markdown(ans)

    with trade_col:
        st.markdown("""
        <div class="kpi-box kpi-white" style="margin-bottom:14px;">
            <div style="font-weight:800; font-size:1.05rem; color:#0f172a;">⚡ Kite Order Window</div>
            <div style="font-size:0.78rem; color:#475569;">CNC (1x) & MIS Intraday (5x Leverage)</div>
        </div>
        """, unsafe_allow_html=True)

        prod_mode = st.radio("Kite Product", ["CNC (Delivery)", "MIS (Intraday 5x)"], horizontal=True)
        order_type = st.radio("Order Type", ["MARKET", "LIMIT"], horizontal=True)
        qty = st.number_input("Quantity (Shares)", min_value=1, max_value=10000, value=10, step=1)
        exec_price = st.number_input("Limit Price", value=float(round(latest_c, 2))) if order_type == "LIMIT" else latest_c
        
        req_margin = (qty * exec_price) * (0.20 if "MIS" in prod_mode else 1.0)
        st.markdown(f"""
        <div style="background:#0f172a; padding:14px; border-radius:12px; border:1px solid #06b6d4; margin:10px 0; font-family:'JetBrains Mono',monospace; font-size:0.86rem;">
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>Req. Margin:</span><b style="color:#ffffff;">₹{req_margin:,.2f}</b></div>
            <div style="display:flex; justify-content:space-between; margin-top:6px; color:#cbd5e1;"><span>Avail. Cash:</span><b style="color:#34d399;">₹{user_bal:,.2f}</b></div>
        </div>
        """, unsafe_allow_html=True)

        ob1, ob2 = st.columns(2)
        if ob1.button("🟦 BUY", use_container_width=True, type="primary"):
            ok, msg = execute_trade(st.session_state.username, ticker, "BUY", qty, exec_price, prod_mode)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        if ob2.button("🟧 SELL", use_container_width=True):
            ok, msg = execute_trade(st.session_state.username, ticker, "SELL", qty, exec_price, prod_mode)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        st.markdown("---")
        bull_count = sum([latest_c > sma20_val, latest_c > ema50_val, 35 < rsi_val < 68])
        verdict = "STRONG BUY ▲" if bull_count == 3 else ("BUY / HOLD ▲" if bull_count == 2 else "SELL / AVOID ▼")
        render_kpi("Technical Rating", verdict, f"14-Day RSI: {rsi_val:.1f}", "kpi-cyan", "#38bdf8")

# ==========================================================
# 15. KITE TAB 7: AI STOCK ADVISOR (AUTO-SWITCHING)
# ==========================================================
elif st.session_state.page == "Advisor":
    custom_q = st.chat_input("Ask anything! Try typing 'Hello', 'Apple', 'NVIDIA', 'Tesla', 'TCS', or 'What is RSI?'...")
    
    if custom_q:
        detected_sym, was_switched = detect_stock_from_text(custom_q, st.session_state.selected_ticker)
        if was_switched:
            st.session_state.selected_ticker = detected_sym

    ticker = st.session_state.selected_ticker
    meta = STOCK_CATALOG.get(ticker, {"name": ticker, "sector": "Equity", "domain": "tradingview.com", "exchange": "NSE", "currency": "₹"})
    currency = meta["currency"]
    logo_url = get_logo_url(ticker)
    df = fetch_stock_history(ticker, "1y")
    latest_c = float(df["Close"].iloc[-1])
    prev_c = float(df["Close"].iloc[-2])
    pct = ((latest_c - prev_c) / prev_c) * 100
    rsi_val = float(df["RSI"].iloc[-1])
    sma20_val = float(df["SMA_20"].iloc[-1])
    ema50_val = float(df["EMA_50"].iloc[-1])
    high_52 = float(df["High"].max())
    low_52 = float(df["Low"].min())

    st.markdown(f"""
    <div style="background: radial-gradient(circle at top right, #064e3b, #090d16 70%); border:1px solid #10b981; border-radius:18px; padding:22px 28px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:18px;">
            <img src="{logo_url}" class="company-logo-lg">
            <div>
                <span style="background:rgba(16,185,129,0.2); color:#6ee7b7; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
                    🤖 CONVERSATIONAL MULTI-STOCK AI • AUTO-DETECTS ANY COMPANY IN CHAT
                </span>
                <h2 style="margin:8px 0 4px 0; color:#ffffff; font-weight:800;">🧠 StreakPulse AI Advisor — {meta['name']} ({ticker.replace('.NS','')})</h2>
                <p style="margin:0; color:#cbd5e1; font-size:0.9rem;">
                    Live Price: <b>{currency}{latest_c:,.2f} ({'▲' if pct >= 0 else '▼'} {pct:+.2f}%)</b> • 14-Day RSI: <b>{rsi_val:.1f}</b> • 20-DMA: <b>{currency}{sma20_val:,.2f}</b>
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### ⚡ 1-Click AI Prompts & Instant Stock Switcher")
    q_col1, q_col2, q_col3, q_col4, q_col5 = st.columns([1.2, 1.2, 1.2, 1.2, 0.9])
    selected_prompt = None
    if q_col1.button(f"⚡ Intraday Plan ({ticker.replace('.NS','')})", use_container_width=True):
        selected_prompt = f"Give me an intraday trading plan for {meta['name']} ({ticker}) with exact breakout entry, stop-loss, and targets."
    if q_col2.button(f"🏛️ 5-Year SIP ({ticker.replace('.NS','')})", use_container_width=True):
        selected_prompt = f"Is {meta['name']} ({ticker}) a good long-term investment for 3 to 5 years? Give a staggered buying strategy."
    if q_col3.button(f"🛡️ Risk & Safe Qty ({ticker.replace('.NS','')})", use_container_width=True):
        selected_prompt = f"What are the biggest downside risks, support levels, and safe share quantity for {meta['name']} ({ticker})?"
    if q_col4.button(f"🤖 5-Day ML Forecast", use_container_width=True):
        selected_prompt = f"What is the 5-day Machine Learning price prediction and expected volatility range for {meta['name']} ({ticker})?"
    if q_col5.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.ai_chat_history = []
        st.rerun()

    active_question = selected_prompt or custom_q

    if active_question:
        with st.spinner(f"🤖 Analyzing '{active_question}' with Live Market & AI Engine..."):
            reply, source_badge = ask_built_in_ai_advisor(
                ticker, meta["name"], currency, latest_c, pct, rsi_val, sma20_val, ema50_val, high_52, low_52, active_question
            )
            st.session_state.ai_chat_history.insert(0, {
                "question": active_question,
                "answer": reply,
                "badge": source_badge,
                "stock": f"{meta['name']} ({ticker})",
                "logo": logo_url
            })

    if not st.session_state.ai_chat_history:
        st.info("💬 **Try typing in the chat box below!** You can type **`Hello`**, **`Apple`**, **`NVIDIA`**, **`Tesla`**, **`TCS`**, **`What is RSI?`**, or click any button above.")
    else:
        for item in st.session_state.ai_chat_history:
            st.markdown(f"""
            <div class="stock-card" style="border-left:4px solid #10b981; display:flex; align-items:center; gap:14px;">
                <img src="{item.get('logo', logo_url)}" class="company-logo">
                <div>
                    <div style="font-size:0.78rem; color:#38bdf8; font-weight:700;">{item['stock']} • {item['badge']}</div>
                    <div style="font-weight:700; color:#ffffff; margin-top:3px; font-size:1.02rem;">🙋‍♂️ You asked: "{item['question']}"</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(item["answer"])
            st.markdown("---")

# ==========================================================
# 16. KITE TAB 8: APPS (STREAK ALGO BACKTESTER & SCANNER)
# ==========================================================
elif st.session_state.page == "Apps":
    st.markdown("""
    <div style="background: radial-gradient(circle at top right, #3b0764, #090d16 70%); border:1px solid #9333ea; border-radius:18px; padding:22px 28px; margin-bottom:20px;">
        <span style="background:rgba(168,85,247,0.25); color:#e9d5ff; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
            ZERODHA KITE APPS • STREAK v4 ALGO ENGINE
        </span>
        <h2 style="margin:8px 0 4px 0; color:#ffffff; font-weight:800;">🧩 Kite Integrated Apps — Streak Strategy Backtester & Scanner</h2>
        <p style="margin:0; color:#cbd5e1; font-size:0.9rem;">
            Build algorithmic trading rules without coding, backtest them on historical candles, and export CSV reports.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st_tab1, st_tab2 = st.tabs(["🧪 No-Code Strategy Backtester", "📡 Live Multi-Stock Market Scanner"])

    with st_tab1:
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        bt_symbol = b_col1.selectbox("1️⃣ Select Stock", list(STOCK_CATALOG.keys()), index=list(STOCK_CATALOG.keys()).index(st.session_state.selected_ticker))
        bt_strategy = b_col2.selectbox("2️⃣ Entry Condition (Algorithm)", [
            "SMA 20 Golden Crossover (Trend Follow)",
            "RSI < 35 Oversold Reversal (Mean Reversion)",
            "Price > 20 SMA + RSI > 50 (Momentum Surge)"
        ])
        stop_loss_pct = b_col3.slider("3️⃣ Stop-Loss (%)", 1.0, 10.0, 3.0, 0.5)
        target_pct = b_col4.slider("4️⃣ Target Profit (%)", 2.0, 20.0, 6.0, 0.5)

        bt_df = fetch_stock_history(bt_symbol, "1y").dropna().copy()
        capital = 100000.0
        equity_curve = [capital]
        trades_log = []
        in_position = False
        entry_price = 0.0
        entry_date = None

        for i in range(1, len(bt_df)):
            row = bt_df.iloc[i]
            prev = bt_df.iloc[i - 1]
            date_str = bt_df.index[i].strftime("%d %b %Y")

            if not in_position:
                cond1 = "Golden" in bt_strategy and (prev["Close"] <= prev["SMA_20"] and row["Close"] > row["SMA_20"])
                cond2 = "Oversold" in bt_strategy and (row["RSI"] < 35)
                cond3 = "Momentum" in bt_strategy and (row["Close"] > row["SMA_20"] and row["RSI"] > 50 and prev["RSI"] <= 50)
                if cond1 or cond2 or cond3:
                    in_position = True
                    entry_price = float(row["Close"])
                    entry_date = date_str
            else:
                change_pct = ((float(row["Close"]) - entry_price) / entry_price) * 100
                if change_pct >= target_pct or change_pct <= -stop_loss_pct or i == len(bt_df) - 1:
                    in_position = False
                    pnl_amt = capital * (change_pct / 100)
                    capital += pnl_amt
                    trades_log.append({
                        "Entry Date": entry_date,
                        "Exit Date": date_str,
                        "Entry Price": f"₹{entry_price:,.2f}",
                        "Exit Price": f"₹{float(row['Close']):,.2f}",
                        "Return (%)": f"{'▲' if change_pct >= 0 else '▼'} {change_pct:+.2f}%",
                        "Net P&L (₹)": round(pnl_amt, 2),
                        "Outcome": "WIN ✅" if change_pct > 0 else "LOSS ❌"
                    })
            equity_curve.append(capital)

        total_ret = ((capital - 100000.0) / 100000.0) * 100
        wins = sum(1 for t in trades_log if "WIN" in t["Outcome"])
        win_rate = (wins / len(trades_log) * 100) if trades_log else 0.0

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_kpi("Final Backtest Capital", f"₹{capital:,.2f}", f"{'▲' if total_ret >= 0 else '▼'} {total_ret:+.2f}% Net Return", "kpi-emerald" if total_ret >= 0 else "kpi-violet", "#34d399")
        with k2:
            render_kpi("Total Signals Triggered", f"{len(trades_log)} Trades", "1-Year Historical Sample", "kpi-cyan", "#38bdf8")
        with k3:
            render_kpi("Strategy Win Rate", f"{win_rate:.1f}%", f"{wins} Winning Trades", "kpi-white", "#2563eb")
        with k4:
            render_kpi("Risk-Reward Ratio", f"1 : {target_pct/stop_loss_pct:.1f}", f"SL: {stop_loss_pct}% | TP: {target_pct}%", "kpi-violet", "#c084fc")

        eq_fig = go.Figure()
        eq_fig.add_trace(go.Scatter(
            x=bt_df.index, y=equity_curve, mode="lines", fill="tozeroy",
            name="Strategy Equity", line=dict(color="#38bdf8", width=2.8),
            fillcolor="rgba(56, 189, 248, 0.14)"
        ))
        eq_fig.update_layout(
            title="📈 Streak Backtest Equity Curve (Initial Capital: ₹1,00,000)",
            template="plotly_dark", paper_bgcolor="#090d16", plot_bgcolor="#090d16", height=370
        )
        st.plotly_chart(eq_fig, use_container_width=True)

        if trades_log:
            st.markdown("##### 📜 Simulated Backtest Trade Ledger")
            st.dataframe(pd.DataFrame(trades_log), use_container_width=True, hide_index=True)
            csv_bt = pd.DataFrame(trades_log).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Backtest Trade Report (CSV/Excel)",
                data=csv_bt,
                file_name=f"{bt_symbol}_streak_backtest.csv",
                mime="text/csv"
            )

    with st_tab2:
        st.subheader("📡 Real-Time Streak Market Scanner")
        scan_rows = []
        for sym, snap in snapshots.items():
            meta = STOCK_CATALOG.get(sym, {"name": sym, "sector": "Equity"})
            status = "🟢 ▲ BULLISH BREAKOUT" if snap["above_sma"] and snap["rsi"] > 52 else ("🔵 ▲ OVERSOLD BOUNCE" if snap["rsi"] < 38 else "🔴 ▼ BEARISH / NEUTRAL")
            scan_rows.append({
                "Symbol": sym,
                "Company": meta["name"],
                "Sector": meta["sector"],
                "Live Price": f"{meta.get('currency','₹')}{snap['price']:,.2f}",
                "Day Change": f"{'▲' if snap['pct'] >= 0 else '▼'} {snap['pct']:+.2f}%",
                "RSI (14)": round(snap["rsi"], 1),
                "Scanner Signal": status
            })
        st.dataframe(pd.DataFrame(scan_rows), use_container_width=True, hide_index=True)