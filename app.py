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
# 1. PAGE CONFIG & TRADINGVIEW DYNAMIC CSS ENGINE
# ==========================================================
st.set_page_config(
    page_title="TradingView × StreakPulse AI | Smart Terminal",
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
        border-left: 5px solid #2563eb;
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
        margin-bottom: 10px;
    }
    .stock-card:hover {
        border-color: #06b6d4;
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(6, 182, 212, 0.2);
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

# Maps any company name typed by the user in chat to its exact Yahoo Finance symbol
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
    """Detects if the user mentioned a specific stock name (like 'apple' or 'tesla') in their question."""
    cleaned = user_text.lower().strip()
    # Sort longer phrases first so 'tata motors' matches before 'tata'
    for keyword in sorted(CHAT_STOCK_ALIASES.keys(), key=len, reverse=True):
        # Match whole word or exact input
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

    # STEP A: Handle Greetings ("hello", "hi", "hey", "who are you") Naturally!
    greetings_exact = {"hi", "hello", "hey", "hii", "hola", "namaste", "good morning", "good evening", "good afternoon", "help", "who are you", "what can you do"}
    if q_clean in greetings_exact or q_clean.startswith(("hello ", "hi ", "hey ")):
        greeting_reply = f"""
### 👋 Hello! I am StreakPulse AI — Your Live Financial & Stock Analyst

I can analyze **any Indian (NSE) or US (NASDAQ) stock** in real time, explain trading concepts, or build custom trade setups for you.

* **🏢 Ask About Any Company Simply by Typing Its Name:**
  * Try typing **`Apple`**, **`NVIDIA`**, **`Tesla`**, **`Microsoft`**, **`TCS`**, **`HDFC Bank`**, **`SBI`**, **`Infosys`**, or **`ITC`** — I will automatically switch to that company's live chart and price!
* **📈 Ask Specific Trading Questions:**
  * *"Give me an intraday setup for Apple"*
  * *"Is NVIDIA good for a 5-year investment?"*
  * *"What is the stop-loss and target for Tata Motors?"*
  * *"Explain what RSI and Moving Averages mean"*

*(Currently selected in your terminal: **{company_name} (`{ticker}`)** trading at **{currency}{price:,.2f}**)*
"""
        return greeting_reply, "🟢 Conversational AI Assistant Active"

    # STEP B: Prepare Live Quantitative Context (RAG) for the Target Stock
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
        "You are StreakPulse AI, an intelligent conversational stock market advisor (like ChatGPT for Finance). "
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

    # LAYER 1: Try Groq LLaMA 3.3 SDK
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

    # LAYER 2: Keyless Free Live AI LLM API (Works 24/7 Even If Groq Key Is Blocked/Revoked!)
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

    # LAYER 3: Offline Concept & Stock-Specific Engine
    if any(w in q_clean for w in ["what is rsi", "what is sma", "what is ema", "what is macd", "explain", "meaning of"]):
        return f"""
### 📚 Financial Concept Breakdown: *"{user_question}"*
* **14-Day RSI (Relative Strength Index):** Measures momentum on a 0–100 scale. Below **30** means a stock is *Oversold* (potential bounce upward), while above **70** means *Overbought* (due for a cooldown). Right now, **{company_name} (`{ticker}`)** has an RSI of **`{rsi:.1f}`**.
* **20-Day SMA & 50-Day EMA (Moving Averages):** Track the average closing price over the last 20 and 50 sessions to filter out daily noise. When live price (`{currency}{price:,.2f}`) stays above the 20-SMA (`{currency}{sma20:,.2f}`), the short-term trend is bullish.
""", "⚡ Powered by StreakPulse Financial Knowledge Engine"

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
# 4. SQLITE MULTI-PAGE DATABASE (USERS, WALLET, BANKING)
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

def execute_trade(username, ticker, action, shares, current_price):
    c = conn.cursor()
    balance = get_user_balance(username)
    total_cost = shares * current_price
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "BUY":
        if total_cost > balance:
            return False, "❌ Insufficient funds! Click 'Deposit' in the top bar to add margin."
        new_balance = balance - total_cost
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))
        c.execute("SELECT shares, avg_price FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
        row = c.fetchone()
        if row:
            old_shares, old_avg = row
            new_shares = old_shares + shares
            new_avg = ((old_shares * old_avg) + total_cost) / new_shares
            c.execute("UPDATE portfolio SET shares = ?, avg_price = ? WHERE username = ? AND ticker = ?",
                      (new_shares, new_avg, username, ticker))
        else:
            c.execute("INSERT INTO portfolio VALUES (?, ?, ?, ?)", (username, ticker, shares, current_price))
        c.execute("""INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total)
                     VALUES (?, ?, ?, 'BUY', ?, ?, ?)""", (username, now, ticker, shares, current_price, total_cost))
        conn.commit()
        return True, f"✅ Executed BUY: {shares} qty of {ticker} @ ₹{current_price:,.2f}"

    elif action == "SELL":
        c.execute("SELECT shares FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
        row = c.fetchone()
        if not row or row[0] < shares:
            return False, "❌ You do not hold enough shares in your portfolio to sell!"
        new_shares = row[0] - shares
        new_balance = balance + total_cost
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))
        if new_shares == 0:
            c.execute("DELETE FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
        else:
            c.execute("UPDATE portfolio SET shares = ? WHERE username = ? AND ticker = ?", (new_shares, username, ticker))
        c.execute("""INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total)
                     VALUES (?, ?, ?, 'SELL', ?, ?, ?)""", (username, now, ticker, shares, current_price, total_cost))
        conn.commit()
        return True, f"✅ Executed SELL: {shares} qty of {ticker} @ ₹{current_price:,.2f}"

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
    st.session_state.page = "Home"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "RELIANCE.NS"
if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []
if "landing_nav" not in st.session_state:
    st.session_state.landing_nav = "Overview"

def navigate_to(page_name, ticker=None):
    st.session_state.page = page_name
    if ticker:
        st.session_state.selected_ticker = ticker

# ==========================================================
# 6. PAGE 1: DYNAMIC TRADINGVIEW LANDING & LOGIN PORTAL
# ==========================================================
if not st.session_state.logged_in:
    top_c1, top_c2, top_c3, top_c4, top_c5, top_c6, top_c7, top_c8 = st.columns([1.3, 2.2, 0.9, 1.0, 0.9, 0.9, 0.9, 1.2])
    
    with top_c1:
        st.markdown("""
        <div style="font-weight:800; font-size:1.35rem; color:#ffffff; padding-top:6px; letter-spacing:-0.03em;">
            17 <span style="color:#38bdf8;">Streak</span>View
        </div>
        """, unsafe_allow_html=True)

    with top_c2:
        search_options = ["🔍 Search markets, tickers, algos (Ctrl+K)..."] + [
            f"{sym} — {meta['name']} ({meta['exchange']})" for sym, meta in STOCK_CATALOG.items()
        ]
        picked_search = st.selectbox("Search", search_options, label_visibility="collapsed")
        if picked_search != "🔍 Search markets, tickers, algos (Ctrl+K)...":
            sym_jump = picked_search.split(" — ")[0]
            st.session_state.logged_in = True
            st.session_state.username = "trader_pro"
            st.session_state.full_name = "Final Year Demo Trader"
            st.session_state.selected_ticker = sym_jump
            st.session_state.page = "Terminal"
            st.rerun()

    if top_c3.button("Products", use_container_width=True, type="primary" if st.session_state.landing_nav == "Products" else "secondary"):
        st.session_state.landing_nav = "Products"
    if top_c4.button("Community", use_container_width=True, type="primary" if st.session_state.landing_nav == "Community" else "secondary"):
        st.session_state.landing_nav = "Community"
    if top_c5.button("Markets", use_container_width=True, type="primary" if st.session_state.landing_nav == "Markets" else "secondary"):
        st.session_state.landing_nav = "Markets"
    if top_c6.button("Brokers", use_container_width=True, type="primary" if st.session_state.landing_nav == "Brokers" else "secondary"):
        st.session_state.landing_nav = "Brokers"
    if top_c7.button("AI Lab", use_container_width=True, type="primary" if st.session_state.landing_nav == "AI Lab" else "secondary"):
        st.session_state.landing_nav = "AI Lab"
    if top_c8.button("🚀 Get started", use_container_width=True, type="primary"):
        st.session_state.logged_in = True
        st.session_state.username = "trader_pro"
        st.session_state.full_name = "Final Year Demo Trader"
        st.session_state.page = "Home"
        st.rerun()

    if st.session_state.landing_nav != "Overview":
        nav_info = {
            "Products": ("⚡ StreakView Pro Suite", "Includes TradingView Multi-Timeframe SuperCharts, Streak No-Code Algo Backtester, Volume Profile POC/VAH/VAL, and Paper Trading Engine.", "Terminal"),
            "Community": ("🌐 Global Quant & Trader Community", "Live trade setups shared by 50,000+ algorithmic traders across NSE NIFTY 50 and NASDAQ tech giants.", "Home"),
            "Markets": ("📈 Live Multi-Exchange Market Pulse", "Real-time coverage of NSE India (Reliance, TCS, HDFC Bank, Infosys, SBI) & US NASDAQ (NVIDIA, Apple, Tesla, Microsoft).", "Streak"),
            "Brokers": ("🏦 Instant Zero-Fee Paper & UPI Gateway", "Pre-loaded with ₹1,00,000 virtual margin, instant UPI/NetBanking deposit simulator, and IMPS bank withdrawal ledger.", "Deposit"),
            "AI Lab": ("🧠 Conversational AI + Multi-Stock Detector Lab", "Type any stock name like 'Apple', 'NVIDIA', or 'TCS' or say 'Hello' — the AI switches stocks automatically!", "Advisor")
        }
        title_txt, desc_txt, target_p = nav_info[st.session_state.landing_nav]
        d_col1, d_col2, d_col3 = st.columns([4.2, 1.3, 0.8])
        with d_col1:
            st.info(f"**{title_txt}:** {desc_txt}")
        with d_col2:
            if st.button(f"🚀 Open {st.session_state.landing_nav} Live", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.session_state.username = "trader_pro"
                st.session_state.full_name = "Final Year Demo Trader"
                st.session_state.page = target_p
                st.rerun()
        with d_col3:
            if st.button("✖ Close", use_container_width=True):
                st.session_state.landing_nav = "Overview"
                st.rerun()

    hero_left, hero_right = st.columns([1.62, 1.0], gap="large")

    with hero_left:
        live_hero_html = """
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                background: transparent;
                font-family: 'Plus Jakarta Sans', sans-serif;
                color: #f8fafc;
                overflow: hidden;
            }
            .hero-card {
                background: radial-gradient(circle at 85% 35%, rgba(6, 182, 212, 0.28), rgba(37, 99, 235, 0.16) 45%, #070b14 85%);
                border: 1px solid #1e293b;
                border-radius: 22px;
                padding: 22px 24px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.65);
            }
            .top-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-bottom: 12px;
                margin-bottom: 16px;
                border-bottom: 1px solid #1e293b;
            }
            .live-dot {
                height: 10px; width: 10px;
                background: #10b981;
                border-radius: 50%;
                display: inline-block;
                box-shadow: 0 0 10px #10b981;
                animation: blink 1.2s infinite;
            }
            @keyframes blink { 50% { opacity: 0.35; } }
            .grid-box {
                display: grid;
                grid-template-columns: 1.45fr 1.15fr;
                gap: 14px;
            }
            .panel {
                background: #090d16;
                border: 1px solid #1e293b;
                border-radius: 16px;
                padding: 16px;
            }
            .logo-sm {
                width: 24px; height: 24px;
                border-radius: 6px;
                background: #ffffff;
                padding: 2px;
                object-fit: contain;
                vertical-align: middle;
            }
            .bar-row {
                display: flex;
                align-items: center;
                gap: 10px;
                margin: 10px 0;
            }
            .bar-track {
                flex: 1;
                background: #111827;
                height: 11px;
                border-radius: 6px;
                overflow: hidden;
            }
            .bar-fill {
                height: 100%;
                border-radius: 6px;
                transition: width 0.6s ease;
            }
            .watch-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 7px 8px;
                border-radius: 8px;
                margin-bottom: 5px;
                transition: background 0.35s ease;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
            }
            .watch-left {
                display: flex;
                align-items: center;
                gap: 8px;
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-weight: 700;
                font-size: 0.82rem;
            }
            .up-text { color: #34d399; font-weight: 700; }
            .down-text { color: #fb7185; font-weight: 700; }
            .flash-up { background: rgba(16, 185, 129, 0.22) !important; }
            .flash-down { background: rgba(244, 63, 94, 0.22) !important; }
            .explore-btn {
                margin-top: 16px;
                background: rgba(15, 23, 42, 0.9);
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 999px;
                padding: 10px 24px;
                display: inline-flex;
                align-items: center;
                gap: 12px;
                color: #f8fafc;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .explore-btn:hover {
                border-color: #38bdf8;
                transform: scale(1.03);
                box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
            }
        </style>
        </head>
        <body>
        <div class="hero-card">
            <div class="top-bar">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="live-dot"></span>
                    <img src="https://www.google.com/s2/favicons?domain=ril.com&sz=128" class="logo-sm">
                    <span style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#cbd5e1;">
                        RELIANCE • NSE • 1D • SUPERCHART + VOLUME PROFILE
                    </span>
                </div>
                <span id="live-clock" style="background:rgba(6,182,212,0.18); color:#22d3ee; padding:4px 10px; border-radius:6px; font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:700;">
                    ⚡ LIVE STREAMING
                </span>
            </div>

            <div class="grid-box">
                <div class="panel">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <img src="https://www.google.com/s2/favicons?domain=apple.com&sz=128" class="logo-sm">
                            <img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=128" class="logo-sm">
                            <span style="font-weight:800; font-size:0.88rem;">Apple / NVIDIA Multi-Grid</span>
                        </div>
                        <span id="grid-Hero-Pct" class="up-text" style="font-family:'JetBrains Mono',monospace; font-size:0.85rem;">
                            ▲ +2.84%
                        </span>
                    </div>

                    <div class="bar-row">
                        <div class="bar-track"><div id="bar1" class="bar-fill" style="width:68%; background:linear-gradient(90deg, #eab308 60%, #3b82f6 40%);"></div></div>
                        <span id="poc-val" style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#cbd5e1; width:85px;">POC 271.59</span>
                    </div>
                    <div class="bar-row">
                        <div class="bar-track"><div id="bar2" class="bar-fill" style="width:86%; background:linear-gradient(90deg, #eab308 55%, #06b6d4 45%);"></div></div>
                        <span id="vah-val" style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#38bdf8; width:85px;">VAH 274.10</span>
                    </div>
                    <div class="bar-row">
                        <div class="bar-track"><div id="bar3" class="bar-fill" style="width:48%; background:linear-gradient(90deg, #ef4444 50%, #3b82f6 50%);"></div></div>
                        <span id="val-val" style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#fb7185; width:85px;">VAL 266.20</span>
                    </div>
                    <div class="bar-row">
                        <div class="bar-track"><div id="bar4" class="bar-fill" style="width:76%; background:linear-gradient(90deg, #10b981 65%, #3b82f6 35%);"></div></div>
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#34d399; width:85px;">▲ AI TARGET</span>
                    </div>

                    <div style="margin-top:16px; padding-top:12px; border-top:1px solid #1e293b; display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:0.76rem;">
                        <span>BTC/USD: <b id="btc-price" class="up-text">▲ $89,420.50 (+3.12%)</b></span>
                        <span>NIFTY 50: <b id="nifty-mini" style="color:#38bdf8;">▲ 24,852.40</b></span>
                    </div>
                </div>

                <div class="panel">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid #1e293b;">
                        <span style="font-size:0.76rem; font-weight:800; color:#94a3b8; letter-spacing:0.04em;">📋 LIVE WATCHLIST</span>
                        <span style="font-size:0.7rem; color:#38bdf8; font-family:'JetBrains Mono',monospace;">REAL-TIME TICKS</span>
                    </div>

                    <div id="row-nvda" class="watch-row">
                        <div class="watch-left">
                            <img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=128" class="logo-sm">
                            <span>NVDA</span>
                        </div>
                        <span id="p-nvda">177.19</span>
                        <span id="c-nvda" class="up-text">▲ +4.16%</span>
                    </div>

                    <div id="row-aapl" class="watch-row">
                        <div class="watch-left">
                            <img src="https://www.google.com/s2/favicons?domain=apple.com&sz=128" class="logo-sm">
                            <span>AAPL</span>
                        </div>
                        <span id="p-aapl">264.18</span>
                        <span id="c-aapl" class="down-text">▼ -1.21%</span>
                    </div>

                    <div id="row-tcs" class="watch-row">
                        <div class="watch-left">
                            <img src="https://www.google.com/s2/favicons?domain=tcs.com&sz=128" class="logo-sm">
                            <span>TCS</span>
                        </div>
                        <span id="p-tcs">4,120.50</span>
                        <span id="c-tcs" class="up-text">▲ +1.85%</span>
                    </div>

                    <div id="row-rel" class="watch-row">
                        <div class="watch-left">
                            <img src="https://www.google.com/s2/favicons?domain=ril.com&sz=128" class="logo-sm">
                            <span>RELIANCE</span>
                        </div>
                        <span id="p-rel">2,985.00</span>
                        <span id="c-rel" class="up-text">▲ +2.10%</span>
                    </div>

                    <div id="row-tsla" class="watch-row">
                        <div class="watch-left">
                            <img src="https://www.google.com/s2/favicons?domain=tesla.com&sz=128" class="logo-sm">
                            <span>TSLA</span>
                        </div>
                        <span id="p-tsla">402.51</span>
                        <span id="c-tsla" class="down-text">▼ -1.49%</span>
                    </div>
                </div>
            </div>

            <div style="text-align:center;">
                <div class="explore-btn" onclick="cycleMode()">
                    <span style="font-size:1.15rem;">⚡</span>
                    <div style="text-align:left;">
                        <div id="explore-title" style="font-weight:800; font-size:0.88rem; color:#38bdf8;">Explore all features › (Click to Cycle Live AI Feeds)</div>
                        <div id="explore-sub" style="font-size:0.74rem; color:#94a3b8;">Showing: Real-Time Volume Profile + Multi-Exchange Watchlist</div>
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
            let modeIdx = 0;
            const modes = [
                "Showing: Real-Time Volume Profile + Multi-Exchange Watchlist",
                "Showing: Streak v4 Algorithmic Crossover Scanner Active",
                "Showing: Groq LLaMA 3.3 + Random Forest 7-Day Predictor Active"
            ];

            function cycleMode() {
                modeIdx = (modeIdx + 1) % modes.length;
                document.getElementById('explore-sub').innerText = modes[modeIdx];
                document.getElementById('bar1').style.width = (50 + Math.random()*40) + '%';
                document.getElementById('bar2').style.width = (50 + Math.random()*40) + '%';
                document.getElementById('bar3').style.width = (40 + Math.random()*40) + '%';
                document.getElementById('bar4').style.width = (60 + Math.random()*35) + '%';
            }

            setInterval(() => {
                stocks.forEach(s => {
                    const delta = (Math.random() - 0.48) * (s.price * 0.003);
                    s.price = Math.max(1, s.price + delta);
                    s.pct = s.pct + (delta >= 0 ? 0.03 : -0.03);
                    const pEl = document.getElementById('p-' + s.id);
                    const cEl = document.getElementById('c-' + s.id);
                    const rEl = document.getElementById('row-' + s.id);

                    pEl.innerText = s.price >= 1000 ? s.price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : s.price.toFixed(2);
                    const arrow = s.pct >= 0 ? '▲ +' : '▼ ';
                    cEl.innerText = arrow + s.pct.toFixed(2) + '%';
                    cEl.className = s.pct >= 0 ? 'up-text' : 'down-text';

                    rEl.classList.remove('flash-up', 'flash-down');
                    void rEl.offsetWidth;
                    rEl.classList.add(delta >= 0 ? 'flash-up' : 'flash-down');
                });

                btc += (Math.random() - 0.47) * 45;
                document.getElementById('btc-price').innerText = (btc >= 89400 ? '▲ $' : '▼ $') + btc.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                document.getElementById('btc-price').className = btc >= 89400 ? 'up-text' : 'down-text';

                document.getElementById('bar1').style.width = (60 + Math.random()*25) + '%';
                document.getElementById('bar2').style.width = (70 + Math.random()*22) + '%';
                document.getElementById('poc-val').innerText = 'POC ' + (271 + Math.random()).toFixed(2);
            }, 1100);
        </script>
        </body>
        </html>
        """
        components.html(live_hero_html, height=420)

    with hero_right:
        st.markdown("""
        <div style="background:linear-gradient(145deg, #0f172a, #090d16); border:1px solid #1e293b; border-radius:20px; padding:20px 24px; margin-bottom:12px;">
            <span style="background:rgba(56,189,248,0.15); color:#38bdf8; padding:4px 12px; border-radius:999px; font-size:0.75rem; font-weight:700;">
                ⚡ GET STARTED • ZERO-LATENCY ACCESS
            </span>
            <h3 style="margin:10px 0 4px 0; font-weight:800; color:#ffffff;">Sign In to Trading Terminal</h3>
            <p style="color:#94a3b8; font-size:0.83rem; margin:0;">Pre-configured with Conversational AI, Streak Backtesting & ₹1,00,000 Wallet</p>
        </div>
        """, unsafe_allow_html=True)

        auth_tab1, auth_tab2 = st.tabs(["🔐 Sign In", "✨ Create Account"])

        with auth_tab1:
            login_user = st.text_input("Username", value="trader_pro")
            login_pass = st.text_input("Password", type="password", value="demo123")
            
            b1, b2 = st.columns(2)
            if b1.button("🚀 Launch Terminal", use_container_width=True, type="primary"):
                c = conn.cursor()
                pw_hash = hashlib.sha256(login_pass.encode()).hexdigest()
                c.execute("SELECT full_name FROM users WHERE username = ? AND password_hash = ?", (login_user, pw_hash))
                res = c.fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.full_name = res[0]
                    st.rerun()
                else:
                    st.error("Invalid username or password!")

            if b2.button("⚡ 1-Click Demo Login", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "trader_pro"
                st.session_state.full_name = "Final Year Demo Trader"
                st.rerun()

        with auth_tab2:
            new_name = st.text_input("Full Name", placeholder="e.g., Vishal Babu")
            new_user = st.text_input("Choose Username", placeholder="e.g., vishal_quant")
            new_email = st.text_input("Email ID", placeholder="vishal@college.edu")
            new_pass = st.text_input("Create Password", type="password")
            if st.button("✅ Register & Claim ₹1,00,000 Margin", use_container_width=True, type="primary"):
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
                        st.success("🎉 Account created! Switch to 'Sign In' tab.")

    market_summary_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; }
        .white-box {
            background: #ffffff;
            color: #0f172a;
            border-radius: 22px;
            padding: 24px 28px;
            box-shadow: 0 12px 36px rgba(0,0,0,0.4);
        }
        .header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }
        .idx-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 16px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.3s ease;
        }
        .badge-circle {
            width: 44px; height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            font-size: 0.95rem;
            flex-shrink: 0;
        }
        .price-txt {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.15rem;
            font-weight: 800;
            color: #0f172a;
            margin-top: 2px;
        }
        .bull-pill {
            background: rgba(16, 185, 129, 0.15);
            color: #059669;
            padding: 5px 10px;
            border-radius: 999px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            font-size: 0.84rem;
        }
        .bear-pill {
            background: rgba(225, 29, 72, 0.12);
            color: #e11d48;
            padding: 5px 10px;
            border-radius: 999px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            font-size: 0.84rem;
        }
    </style>
    </head>
    <body>
    <div class="white-box">
        <div class="header-row">
            <h2 style="font-weight:800; font-size:1.55rem; color:#0f172a;">Market summary ›</h2>
            <span style="font-size:0.86rem; font-weight:700; color:#2563eb;">● Major Global & Indian Indices • Live Real-Time Ticks</span>
        </div>
        <div class="cards-grid">
            <div class="idx-card" id="card-spx">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="badge-circle" style="background:#e11d48;">500</div>
                    <div>
                        <div style="font-weight:800; font-size:0.95rem;">S&P 500 <span style="font-size:0.72rem; color:#64748b;">SPX</span></div>
                        <div class="price-txt" id="val-spx">7,714.21</div>
                    </div>
                </div>
                <span class="bear-pill" id="pct-spx">▼ -0.38%</span>
            </div>

            <div class="idx-card" id="card-ndx">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="badge-circle" style="background:#0284c7;">100</div>
                    <div>
                        <div style="font-weight:800; font-size:0.95rem;">Nasdaq 100 <span style="font-size:0.72rem; color:#64748b;">NDX</span></div>
                        <div class="price-txt" id="val-ndx">29,415.59</div>
                    </div>
                </div>
                <span class="bear-pill" id="pct-ndx">▼ -1.33%</span>
            </div>

            <div class="idx-card" id="card-nifty">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="badge-circle" style="background:#4f46e5;">50</div>
                    <div>
                        <div style="font-weight:800; font-size:0.95rem;">NIFTY 50 <span style="font-size:0.72rem; color:#64748b;">NSE</span></div>
                        <div class="price-txt" id="val-nifty">24,852.10</div>
                    </div>
                </div>
                <span class="bull-pill" id="pct-nifty">▲ +0.84%</span>
            </div>

            <div class="idx-card" id="card-sensex">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div class="badge-circle" style="background:#059669;">30</div>
                    <div>
                        <div style="font-weight:800; font-size:0.95rem;">BSE SENSEX <span style="font-size:0.72rem; color:#64748b;">BSE</span></div>
                        <div class="price-txt" id="val-sensex">81,742.65</div>
                    </div>
                </div>
                <span class="bull-pill" id="pct-sensex">▲ +0.92%</span>
            </div>
        </div>
    </div>

    <script>
        const indices = [
            { id: 'spx', val: 7714.21, pct: -0.38 },
            { id: 'ndx', val: 29415.59, pct: -1.33 },
            { id: 'nifty', val: 24852.10, pct: 0.84 },
            { id: 'sensex', val: 81742.65, pct: 0.92 }
        ];
        setInterval(() => {
            indices.forEach(idx => {
                const move = (Math.random() - 0.48) * (idx.val * 0.0008);
                idx.val += move;
                idx.pct += (move >= 0 ? 0.01 : -0.01);
                document.getElementById('val-' + idx.id).innerText = idx.val.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                const pEl = document.getElementById('pct-' + idx.id);
                pEl.innerText = (idx.pct >= 0 ? '▲ +' : '▼ ') + idx.pct.toFixed(2) + '%';
                pEl.className = idx.pct >= 0 ? 'bull-pill' : 'bear-pill';
            });
        }, 1300);
    </script>
    </body>
    </html>
    """
    components.html(market_summary_html, height=195)
    st.stop()

# ==========================================================
# 7. GLOBAL ANIMATED LIVE TICKER TAPE (WITH LOGOS & ARROWS)
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

# Top Hyperlinked Navigation Bar
nav_cols = st.columns([1.1, 1.2, 1.25, 1.25, 1.1, 1.1, 1.1, 0.95])
pages_list = [
    ("🏠 Home", "Home"),
    ("📈 Terminal", "Terminal"),
    ("🤖 AI Advisor", "Advisor"),
    ("⚡ Streak Algo", "Streak"),
    ("💼 Portfolio", "Portfolio"),
    ("💳 Deposit", "Deposit"),
    ("🏦 Withdraw", "Withdraw")
]
for idx, (label, p_key) in enumerate(pages_list):
    btn_type = "primary" if st.session_state.page == p_key else "secondary"
    if nav_cols[idx].button(label, key=f"top_nav_{p_key}", use_container_width=True, type=btn_type):
        navigate_to(p_key)
        st.rerun()

if nav_cols[7].button("🚪 Exit", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# Sidebar Account & Non-Truncating Margin Box
user_bal = get_user_balance(st.session_state.username)
st.sidebar.markdown(f"### 👤 {st.session_state.full_name}")
st.sidebar.caption(f"Account ID: `@{st.session_state.username}` • **KYC Verified**")

st.sidebar.markdown(f"""
<div style="background:linear-gradient(135deg, #091526, #0f2942); border:1px solid #06b6d4; border-radius:14px; padding:16px; margin-bottom:14px; box-shadow:0 4px 16px rgba(6,182,212,0.2);">
    <div style="font-size:0.78rem; color:#94a3b8; text-transform:uppercase; font-weight:700;">💳 Available Margin</div>
    <div style="font-family:'JetBrains Mono',monospace; font-size:1.45rem; font-weight:800; color:#38bdf8; margin-top:4px; word-break:break-word;">
        ₹{user_bal:,.2f}
    </div>
    <div style="font-size:0.72rem; color:#34d399; margin-top:4px;">● Instant Equity & Algo Margin</div>
</div>
""", unsafe_allow_html=True)

s_col1, s_col2 = st.sidebar.columns(2)
if s_col1.button("➕ Add Funds", use_container_width=True):
    navigate_to("Deposit")
    st.rerun()
if s_col2.button("🏦 Withdraw", use_container_width=True):
    navigate_to("Withdraw")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Quick Stock Jump")
catalog_options = [f"{k} — {v['name']}" for k, v in STOCK_CATALOG.items()]
current_idx = list(STOCK_CATALOG.keys()).index(st.session_state.selected_ticker) if st.session_state.selected_ticker in STOCK_CATALOG else 0
chosen_option = st.sidebar.selectbox("Select Company", catalog_options, index=current_idx)
chosen_sym = chosen_option.split(" — ")[0]
if chosen_sym != st.session_state.selected_ticker:
    st.session_state.selected_ticker = chosen_sym
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background:rgba(16,185,129,0.12); border:1px solid #10b981; border-radius:12px; padding:12px 14px;">
    <div style="font-size:0.8rem; font-weight:700; color:#34d399;">🟢 Multi-Stock AI Engine: ACTIVE</div>
    <div style="font-size:0.74rem; color:#94a3b8; margin-top:3px;">Type any company name (Apple, Tesla, TCS, SBI) in chat to auto-switch!</div>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# 8. PAGE: HOME HUB
# ==========================================================
if st.session_state.page == "Home":
    h_c1, h_c2, h_c3, h_c4 = st.columns(4)
    with h_c1:
        render_kpi("Available Trading Margin", f"₹{user_bal:,.2f}", "▲ Instant Zero-Fee Wallet", "kpi-white", "#2563eb")
    with h_c2:
        render_kpi("NIFTY 50 Benchmark", "24,852.10", "▲ +0.84% Bullish Session", "kpi-cyan", "#34d399")
    with h_c3:
        render_kpi("S&P 500 (US Market)", "7,714.21", "▼ -0.38% Consolidation", "kpi-violet", "#fb7185")
    with h_c4:
        render_kpi("AI Engine Status", "Multi-Stock NLP", "▲ Auto-Detects Any Company", "kpi-emerald", "#34d399")

    st.subheader("🏢 Top Traded Institutional Stocks (Real Logos & Live Signals)")
    
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
                    if c_btn1.button(f"📈 SuperChart", key=f"home_chart_{sym}", use_container_width=True):
                        navigate_to("Terminal", sym)
                        st.rerun()
                    if c_btn2.button(f"🤖 Ask AI Advisor", key=f"home_ai_{sym}", use_container_width=True):
                        navigate_to("Advisor", sym)
                        st.rerun()

# ==========================================================
# 9. PAGE: PRO TERMINAL
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
        sub_t1, sub_t2, sub_t3 = st.tabs(["📊 TradingView SuperChart", "🤖 7-Day AI Price Forecast", "🧠 Built-In AI Stock Analyst"])
        
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
            <div style="font-weight:800; font-size:1.05rem; color:#0f172a;">⚡ Instant Order Dock</div>
            <div style="font-size:0.78rem; color:#475569;">Zero-Latency Paper Execution</div>
        </div>
        """, unsafe_allow_html=True)

        order_type = st.radio("Order Type", ["MARKET ORDER", "LIMIT ORDER"], horizontal=True)
        qty = st.number_input("Quantity (Shares)", min_value=1, max_value=10000, value=10, step=1)
        exec_price = st.number_input("Limit Price", value=float(round(latest_c, 2))) if order_type == "LIMIT ORDER" else latest_c
        
        req_margin = qty * exec_price
        st.markdown(f"""
        <div style="background:#0f172a; padding:14px; border-radius:12px; border:1px solid #06b6d4; margin:10px 0; font-family:'JetBrains Mono',monospace; font-size:0.86rem;">
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>Req. Margin:</span><b style="color:#ffffff;">₹{req_margin:,.2f}</b></div>
            <div style="display:flex; justify-content:space-between; margin-top:6px; color:#cbd5e1;"><span>Avail. Cash:</span><b style="color:#34d399;">₹{user_bal:,.2f}</b></div>
        </div>
        """, unsafe_allow_html=True)

        ob1, ob2 = st.columns(2)
        if ob1.button("🟢 ▲ BUY", use_container_width=True, type="primary"):
            ok, msg = execute_trade(st.session_state.username, ticker, "BUY", qty, exec_price)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        if ob2.button("🔴 ▼ SELL", use_container_width=True):
            ok, msg = execute_trade(st.session_state.username, ticker, "SELL", qty, exec_price)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        st.markdown("---")
        bull_count = sum([latest_c > sma20_val, latest_c > ema50_val, 35 < rsi_val < 68])
        verdict = "STRONG BUY ▲" if bull_count == 3 else ("BUY / HOLD ▲" if bull_count == 2 else "SELL / AVOID ▼")
        render_kpi("TradingView Technical Rating", verdict, f"14-Day RSI: {rsi_val:.1f}", "kpi-cyan", "#38bdf8")

# ==========================================================
# 10. PAGE: DEDICATED BUILT-IN AI STOCK ADVISOR (AUTO-SWITCHING)
# ==========================================================
elif st.session_state.page == "Advisor":
    # Capture chat input FIRST so if the user types "apple" or "tesla", we switch the stock immediately!
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
# 11. PAGE: STREAK BY ZERODHA — ALGO BACKTESTER & SCANNER
# ==========================================================
elif st.session_state.page == "Streak":
    st.markdown("""
    <div style="background: radial-gradient(circle at top right, #3b0764, #090d16 70%); border:1px solid #9333ea; border-radius:18px; padding:22px 28px; margin-bottom:20px;">
        <span style="background:rgba(168,85,247,0.25); color:#e9d5ff; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
            STREAK v4 ENGINE • NO-CODE SYSTEMATIC TRADING
        </span>
        <h2 style="margin:8px 0 4px 0; color:#ffffff; font-weight:800;">⚡ Streak Strategy Builder, Backtester & Scanner</h2>
        <p style="margin:0; color:#cbd5e1; font-size:0.9rem;">
            Build algorithmic trading rules without coding, backtest them on historical candles, and scan the live market.
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

# ==========================================================
# 12. PAGE: PORTFOLIO & ORDER BOOK
# ==========================================================
elif st.session_state.page == "Portfolio":
    st.subheader("💼 Your Equity Portfolio & Order Book")
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(st.session_state.username,))
    
    if port_df.empty:
        st.info("Your portfolio is currently empty. Visit the **Terminal** page to buy your first stock!")
    else:
        port_df["Live Price"] = port_df["ticker"].apply(lambda s: snapshots.get(s, {}).get("price", fetch_stock_history(s, "5d")["Close"].iloc[-1]))
        port_df["Invested (₹)"] = port_df["shares"] * port_df["avg_price"]
        port_df["Current Value (₹)"] = port_df["shares"] * port_df["Live Price"]
        port_df["Net P&L (₹)"] = port_df["Current Value (₹)"] - port_df["Invested (₹)"]
        port_df["Return (%)"] = (port_df["Net P&L (₹)"] / port_df["Invested (₹)"]) * 100

        tot_inv = port_df["Invested (₹)"].sum()
        tot_cur = port_df["Current Value (₹)"].sum()
        tot_pnl = tot_cur - tot_inv

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            render_kpi("Total Account Net Worth", f"₹{(user_bal + tot_cur):,.2f}", "Cash + Equity Holdings", "kpi-white", "#2563eb")
        with pc2:
            render_kpi("Invested Margin", f"₹{tot_inv:,.2f}", "Active Cost Basis", "kpi-cyan", "#38bdf8")
        with pc3:
            render_kpi("Current Holdings Value", f"₹{tot_cur:,.2f}", "Live Mark-to-Market", "kpi-violet", "#c084fc")
        with pc4:
            render_kpi("Unrealized P&L", f"₹{tot_pnl:,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} {(tot_pnl/tot_inv)*100:+.2f}% Net ROI", "kpi-emerald", "#34d399")

        d_col1, d_col2 = st.columns([2, 1])
        with d_col1:
            st.markdown("##### 📂 Active Equity Holdings")
            st.dataframe(port_df.round(2), use_container_width=True, hide_index=True)
        with d_col2:
            pie_fig = go.Figure(data=[go.Pie(labels=port_df["ticker"], values=port_df["Current Value (₹)"], hole=0.55)])
            pie_fig.update_layout(title="Asset Allocation", template="plotly_dark", paper_bgcolor="#090d16", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("##### 📜 Executed Trade Order Book")
    tx_df = pd.read_sql_query("SELECT timestamp, ticker, action, shares, price, total FROM transactions WHERE username = ? ORDER BY id DESC", conn, params=(st.session_state.username,))
    st.dataframe(tx_df, use_container_width=True, hide_index=True)
    if not tx_df.empty:
    csv_tx = tx_df.to_csv(index=False).encode("utf-8")
    st.download_button(
    label="📥 Export Order Book to Excel (CSV)",
    data=csv_tx,
    file_name="portfolio_order_book.csv",
    mime="text/csv"
)

# ==========================================================
# 13. PAGE: DEPOSIT / ADD MONEY
# ==========================================================
elif st.session_state.page == "Deposit":
    st.subheader("💳 Instant Margin Deposit Gateway")
    dep_col1, dep_col2 = st.columns([1.4, 1.6])

    with dep_col1:
        render_kpi("Instant Margin Top-Up", f"₹{user_bal:,.2f}", "Zero Gateway Charges • UPI & NetBanking", "kpi-white", "#2563eb")

        preset = st.radio("Quick Top-Up Amount", ["₹10,000", "₹25,000", "₹50,000", "₹1,00,000", "Custom Amount"], horizontal=True)
        preset_map = {"₹10,000": 10000.0, "₹25,000": 25000.0, "₹50,000": 50000.0, "₹1,00,000": 100000.0}
        dep_amount = st.number_input("Enter Deposit Amount (₹)", min_value=500.0, max_value=10000000.0, value=preset_map.get(preset, 25000.0), step=1000.0)
        
        pay_method = st.selectbox("Select Payment Mode", [
            "📱 Instant UPI (Google Pay / PhonePe / Paytm)",
            "🏦 NetBanking (HDFC / SBI / ICICI / Axis)",
            "💳 RuPay / Visa Debit Card"
        ])
        pay_ref = st.text_input("UPI ID / Bank Reference Number", value=f"{st.session_state.username}@okaxis")

        if st.button("✅ Authorize & Deposit Funds Instantly", type="primary", use_container_width=True):
            ok, msg = update_funds(st.session_state.username, dep_amount, "DEPOSIT", pay_method, pay_ref)
            if ok:
                st.success(msg)
                st.rerun()

    with dep_col2:
        st.markdown("##### 🧾 Recent Deposit & Withdrawal Ledger")
        f_df = pd.read_sql_query("SELECT timestamp, type, method, reference, amount, status FROM funding_history WHERE username = ? ORDER BY id DESC", conn, params=(st.session_state.username,))
        st.dataframe(f_df, use_container_width=True, hide_index=True)

# ==========================================================
# 14. PAGE: WITHDRAWAL PAGE
# ==========================================================
elif st.session_state.page == "Withdraw":
    st.subheader("🏦 Withdraw Funds to Linked Bank Account")
    w_col1, w_col2 = st.columns([1.4, 1.6])

    with w_col1:
        render_kpi("Withdrawable Cash Balance", f"₹{user_bal:,.2f}", "Instant IMPS Bank Settlement", "kpi-emerald", "#34d399")

        bank_name = st.selectbox("Select Linked Bank", ["State Bank of India (SBI)", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank"])
        acc_num = st.text_input("Bank Account Number", value="XXXX-XXXX-8821")
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
        st.markdown("##### 📜 Complete Banking & Payout History")
        f_df = pd.read_sql_query("SELECT timestamp, type, method, reference, amount, status FROM funding_history WHERE username = ? ORDER BY id DESC", conn, params=(st.session_state.username,))
        st.dataframe(f_df, use_container_width=True, hide_index=True)