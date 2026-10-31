import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
import sqlite3
import hashlib
import json
import socket
import urllib.request
from datetime import datetime, timedelta
from groq import Groq

# ==========================================================
# 🔑 BUILT-IN GROQ API KEY + KEYLESS LIVE AI BACKUP
# ==========================================================
GROQ_API_KEY = "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"

# ==========================================================
# 1. PAGE CONFIG, FINANCESIGHT LOGO & SVG NAVIGATION ICONS
# ==========================================================
st.set_page_config(
    page_title="FinanceSight | Market Analytics, AI Forecasting & Paper Trading",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

FINANCESIGHT_LOGO_SVG = '<svg width="34" height="34" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle; flex-shrink:0;"><rect width="40" height="40" rx="10" fill="url(#fs_grad)"/><path d="M9 26L16 19L22 23L31 12" stroke="white" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 12H31V19" stroke="#38bdf8" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="16" cy="19" r="2.5" fill="#34d399"/><defs><linearGradient id="fs_grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse"><stop stop-color="#387ed1"/><stop offset="0.5" stop-color="#1e3a8a"/><stop offset="1" stop-color="#0f172a"/></linearGradient></defs></svg>'

# Crisp Vector SVG Logos for Navigation Buttons (Replaces Emojis)
NAV_SVGS = {
    "Home": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "Signup": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>',
    "About": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "Products": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "Pricing": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
    "Support": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
    "Dashboard": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    "Orders": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "Holdings": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "Positions": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "Funds": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
    "Terminal": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "Advisor": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/><path d="M16 14H8a4 4 0 0 0-4 4v2h16v-2a4 4 0 0 0-4-4z"/></svg>',
    "Apps": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "Logout": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
}

def render_html(raw_html: str):
    """Renders HTML safely by stripping leading line indentation so Markdown never prints raw code."""
    cleaned = "\n".join(line.lstrip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

def is_internet_connected() -> bool:
    """Checks real-time internet connectivity so prices never fake-update when offline."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
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

    .fs-title {
        color: var(--text-color) !important;
        font-weight: 800;
    }
    .fs-muted {
        color: var(--text-color) !important;
        opacity: 0.72;
    }
    .fs-panel {
        background: var(--background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 16px;
        padding: 16px;
        color: var(--text-color);
    }

    /* Clickable Brand Logo Hover */
    .fs-logo-link {
        text-decoration: none !important;
        display: inline-flex;
        align-items: center;
        gap: 9px;
        font-weight: 800;
        font-size: 1.3rem;
        color: var(--text-color) !important;
        letter-spacing: -0.02em;
        cursor: pointer;
        transition: opacity 0.2s ease;
    }
    .fs-logo-link:hover {
        opacity: 0.85;
    }

    /* Custom Top Navbar SVG Buttons (ALL CAPS + Vector Logo) */
    .fs-nav-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        width: 100%;
        padding: 8px 10px;
        border-radius: 9px;
        background: var(--background-color);
        border: 1px solid rgba(128, 128, 128, 0.28);
        color: var(--text-color) !important;
        text-decoration: none !important;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        transition: all 0.2s ease;
        box-sizing: border-box;
        white-space: nowrap;
    }
    .fs-nav-btn:hover {
        border-color: #387ed1;
        color: #387ed1 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(56, 126, 209, 0.14);
    }
    .fs-nav-btn.active {
        background: #ff4b4b !important;
        color: #ffffff !important;
        border-color: #ff4b4b !important;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.28);
    }
    .fs-nav-btn.active svg {
        stroke: #ffffff !important;
    }

    /* Footer & Social Media Clickable Links */
    .fs-footer-link {
        color: var(--text-color) !important;
        opacity: 0.75;
        text-decoration: none !important;
        font-size: 0.85rem;
        display: block;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    .fs-footer-link:hover {
        color: #387ed1 !important;
        opacity: 1.0;
        transform: translateX(3px);
    }
    .fs-social-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }
    .fs-social-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 11px;
        border-radius: 999px;
        background: var(--background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        color: var(--text-color) !important;
        text-decoration: none !important;
        font-size: 0.78rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .fs-social-link:hover {
        border-color: #387ed1;
        color: #387ed1 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(56, 126, 209, 0.15);
    }
    .social-logo {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        object-fit: contain;
        background: #ffffff;
        padding: 1px;
    }
    .fs-bottom-link {
        color: var(--text-color) !important;
        opacity: 0.75;
        text-decoration: none !important;
        margin: 0 6px;
        font-weight: 600;
        transition: color 0.2s ease;
    }
    .fs-bottom-link:hover {
        color: #387ed1 !important;
        opacity: 1.0;
        text-decoration: underline !important;
    }

    @keyframes tickerMove {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: var(--secondary-background-color);
        border: 1px solid rgba(56, 189, 248, 0.35);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        padding: 11px 0;
        margin-top: 6px;
        margin-bottom: 18px;
        white-space: nowrap;
        border-radius: 12px;
    }
    .ticker-move {
        display: inline-block;
        animation: tickerMove 26s linear infinite;
    }
    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin: 0 24px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        color: var(--text-color);
    }
    .ticker-logo {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #ffffff;
        padding: 2px;
        object-fit: contain;
        border: 1px solid rgba(128,128,128,0.25);
    }

    .kpi-box {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border-radius: 16px;
        padding: 18px 20px;
        border: 1px solid rgba(128, 128, 128, 0.22);
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .kpi-cyan { border-left: 5px solid #06b6d4; }
    .kpi-violet { border-left: 5px solid #8b5cf6; }
    .kpi-emerald { border-left: 5px solid #10b981; }
    .kpi-white { border-left: 5px solid #387ed1; }

    .kpi-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.75;
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
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 18px;
        padding: 18px;
        transition: all 0.25s ease;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .stock-card:hover {
        border-color: #387ed1;
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(56, 126, 209, 0.18);
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
        border: 1px solid rgba(128,128,128,0.3);
    }
    .company-logo-lg {
        width: 64px;
        height: 64px;
        border-radius: 16px;
        object-fit: contain;
        background: #ffffff;
        padding: 6px;
        border: 2px solid #06b6d4;
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.25);
    }
    .mono-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem;
        font-weight: 800;
        color: var(--text-color);
    }
    .badge-up {
        background: rgba(16, 185, 129, 0.16);
        color: #10b981;
        padding: 5px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 800;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .badge-down {
        background: rgba(244, 63, 94, 0.16);
        color: #f43f5e;
        padding: 5px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 800;
        border: 1px solid rgba(244, 63, 94, 0.35);
    }

    .z-section-card {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 20px;
        padding: 28px 32px;
        margin: 22px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }
    .z-support-hero {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 65%, #1e3a8a 100%);
        border: 1px solid #60a5fa;
        border-radius: 20px;
        padding: 32px 36px;
        color: #ffffff !important;
        margin-bottom: 24px;
    }
    .z-universe-card {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
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
        background: var(--secondary-background-color);
        color: var(--text-color);
        border-top: 1px solid rgba(128, 128, 128, 0.25);
        padding: 36px 28px 20px 28px;
        margin-top: 42px;
        border-radius: 18px;
    }
    .watch-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 10px;
        border-radius: 8px;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.15);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
    }
    .logo-sm {
        width: 24px;
        height: 24px;
        border-radius: 6px;
        background: #ffffff;
        padding: 2px;
        object-fit: contain;
        vertical-align: middle;
        border: 1px solid rgba(128,128,128,0.25);
    }
</style>
""", unsafe_allow_html=True)

def render_kpi(title, value, subtext="", theme="kpi-cyan", sub_color="#0284c7"):
    render_html(f"""
    <div class="kpi-box {theme}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-val">{value}</div>
        <div class="kpi-sub" style="color:{sub_color};">{subtext}</div>
    </div>
    """)

# ==========================================================
# 2. STOCK CATALOG & REAL-TIME MARKET DATA ENGINE
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
    dom = STOCK_CATALOG.get(ticker, {}).get("domain", "google.com")
    return f"https://www.google.com/s2/favicons?domain={dom}&sz=128"

@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
def fetch_market_snapshots(tickers_list):
    snapshots = {}
    if not is_internet_connected():
        return snapshots
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

if "last_valid_snapshots" not in st.session_state:
    st.session_state.last_valid_snapshots = {
        "NVDA": {"price": 177.19, "change": 7.08, "pct": 4.16, "rsi": 61.2, "above_sma": True},
        "AAPL": {"price": 264.18, "change": -3.23, "pct": -1.21, "rsi": 48.5, "above_sma": False},
        "TCS.NS": {"price": 4120.50, "change": 74.80, "pct": 1.85, "rsi": 57.4, "above_sma": True},
        "RELIANCE.NS": {"price": 2985.00, "change": 61.40, "pct": 2.10, "rsi": 59.1, "above_sma": True},
        "TSLA": {"price": 402.51, "change": -6.09, "pct": -1.49, "rsi": 44.8, "above_sma": False},
        "HDFCBANK.NS": {"price": 1742.30, "change": 15.40, "pct": 0.89, "rsi": 55.2, "above_sma": True},
        "INFY.NS": {"price": 1865.10, "change": 21.10, "pct": 1.14, "rsi": 58.0, "above_sma": True},
        "SBIN.NS": {"price": 842.60, "change": 9.80, "pct": 1.18, "rsi": 60.4, "above_sma": True},
        "ICICIBANK.NS": {"price": 1295.40, "change": 11.20, "pct": 0.87, "rsi": 56.3, "above_sma": True},
        "TATAMOTORS.NS": {"price": 918.75, "change": -4.50, "pct": -0.49, "rsi": 49.1, "above_sma": False}
    }

online_status = is_internet_connected()
core_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "AAPL", "NVDA", "TSLA"]
if online_status:
    fresh_snaps = fetch_market_snapshots(core_tickers)
    if fresh_snaps:
        st.session_state.last_valid_snapshots.update(fresh_snaps)
snapshots = st.session_state.last_valid_snapshots

# ==========================================================
# 3. TRIPLE-LAYER CONVERSATIONAL & STOCK AI ENGINE
# ==========================================================
def ask_built_in_ai_advisor(ticker, company_name, currency, price, pct_change, rsi, sma20, ema50, high52, low52, user_question):
    q_clean = user_question.strip().lower()

    greetings_exact = {"hi", "hello", "hey", "hii", "hola", "namaste", "good morning", "good evening", "good afternoon", "help", "who are you", "what can you do"}
    if q_clean in greetings_exact or q_clean.startswith(("hello ", "hi ", "hey ")):
        greeting_reply = f"""
### 👋 Hello! I am FinanceSight AI — Your Financial & Stock Analyst

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

    df_live = fetch_stock_history(ticker, "1y") if online_status else None
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
        "You are FinanceSight AI, an intelligent conversational stock market advisor integrated into the FinanceSight platform. "
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
    if online_status and clean_key.startswith("gsk_"):
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

    if online_status:
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
                headers={"Content-Type": "application/json", "User-Agent": "FinanceSightAI/1.0"}
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
""", f"⚡ Powered by FinanceSight Quant Engine ({'Online' if online_status else 'Offline Cached Data'})"

# ==========================================================
# 4. SQLITE DATABASE (USERS, HOLDINGS, POSITIONS, ORDERS, TICKETS)
# ==========================================================
def init_db():
    conn = sqlite3.connect("financesight_pro.db", check_same_thread=False)
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
    for demo_u in ["Trader_XYZ", "trader_pro"]:
        c.execute("SELECT COUNT(*) FROM users WHERE username = ?", (demo_u,))
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                      (demo_u, "Trader_XYZ", "trader@financesight.in", demo_hash, 100000.0))
            c.execute("INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (demo_u, datetime.now().strftime("%Y-%m-%d %H:%M"), "DEPOSIT", "Initial Margin Credit", "BONUS-100K", 100000.0, "COMPLETED"))
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
# 5. SESSION STATE & QUERY-PARAMETER ROUTING ENGINE
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

# Handle all clickable SVG Navbar, Logo & Footer links (?nav=...) reliably
if "nav" in st.query_params:
    target_nav = st.query_params["nav"]
    user_param = st.query_params.get("u", "")
    st.query_params.clear()
    if target_nav == "Logout":
        st.session_state.logged_in = False
        st.session_state.public_page = "Home"
    elif target_nav in ["Home", "Signup", "About", "Products", "Pricing", "Support"]:
        st.session_state.logged_in = False
        st.session_state.public_page = target_nav
    elif target_nav in ["Dashboard", "Orders", "Holdings", "Positions", "Funds", "Terminal", "Advisor", "Apps"]:
        st.session_state.logged_in = True
        if user_param:
            st.session_state.username = user_param
            c = conn.cursor()
            c.execute("SELECT full_name FROM users WHERE username = ?", (user_param,))
            r_u = c.fetchone()
            st.session_state.full_name = r_u[0] if r_u else user_param
        elif not st.session_state.username:
            st.session_state.username = "Trader_XYZ"
            st.session_state.full_name = "Trader_XYZ"
        st.session_state.page = target_nav

def navigate_to(page_name, ticker=None):
    st.session_state.page = page_name
    if ticker:
        st.session_state.selected_ticker = ticker

nav_token = f"{st.session_state.public_page}_{st.session_state.page}_{int(datetime.now().timestamp())}"

# ==========================================================
# 6. REUSABLE FINANCESIGHT PUBLIC COMPONENTS (OPEN ACCOUNT & WORKING FOOTER)
# ==========================================================
def render_financesight_open_account(key_suffix="main"):
    render_html("""
    <div class="z-section-card" style="text-align:center;">
        <h2 class="fs-title" style="font-size:1.95rem; margin-bottom:10px;">Start Exploring with a FinanceSight Account</h2>
        <p class="fs-muted" style="font-size:1.02rem; margin-bottom:20px;">
            Access live NSE & NASDAQ charts, 7-day ML price forecasting, strategy backtesting, and a ₹1,00,000 virtual paper trading wallet.
        </p>
    </div>
    """)
    c1, c2, c3 = st.columns([1.6, 1.2, 1.6])
    with c2:
        if st.button("🚀 SIGN UP NOW (CLAIM ₹1,00,000 VIRTUAL MARGIN)", key=f"open_acc_btn_{key_suffix}", type="primary", use_container_width=True):
            st.session_state.public_page = "Signup"
            st.rerun()

def render_financesight_footer():
    render_html(f"""
    <div class="z-footer">
        <div style="display:grid; grid-template-columns: 1.45fr 1fr 1fr 1fr; gap:28px; padding-bottom:28px; border-bottom:1px solid rgba(128,128,128,0.25);">
            <div>
                <a href="?nav=Home&r=ftr_{nav_token}" target="_self" class="fs-logo-link" title="Go to FinanceSight Home" style="margin-bottom:10px;">
                    {FINANCESIGHT_LOGO_SVG}
                    <span><span style="color:#387ed1;">FINANCE</span>SIGHT</span>
                </a>
                <p class="fs-muted" style="font-size:0.82rem; line-height:1.6;">
                    © 2026 FinanceSight.<br>
                    All rights reserved.<br>
                    Market Analytics, AI Forecasting & Paper Trading Platform
                </p>
                <div class="fs-social-wrap">
                    <a href="https://x.com" target="_blank" rel="noopener noreferrer" class="fs-social-link">
                        <img src="https://www.google.com/s2/favicons?domain=x.com&sz=64" class="social-logo" alt="X"> X
                    </a>
                    <a href="https://www.linkedin.com" target="_blank" rel="noopener noreferrer" class="fs-social-link">
                        <img src="https://www.google.com/s2/favicons?domain=linkedin.com&sz=64" class="social-logo" alt="LinkedIn"> LinkedIn
                    </a>
                    <a href="https://www.facebook.com" target="_blank" rel="noopener noreferrer" class="fs-social-link">
                        <img src="https://www.google.com/s2/favicons?domain=facebook.com&sz=64" class="social-logo" alt="Facebook"> Facebook
                    </a>
                    <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer" class="fs-social-link">
                        <img src="https://www.google.com/s2/favicons?domain=instagram.com&sz=64" class="social-logo" alt="Instagram"> Instagram
                    </a>
                    <a href="https://www.youtube.com" target="_blank" rel="noopener noreferrer" class="fs-social-link">
                        <img src="https://www.google.com/s2/favicons?domain=youtube.com&sz=64" class="social-logo" alt="YouTube"> YouTube
                    </a>
                    <a href="https://telegram.org" target="_blank" rel="noopener noreferrer" class="fs-social-link">
                        <img src="https://www.google.com/s2/favicons?domain=telegram.org&sz=64" class="social-logo" alt="Telegram"> Telegram
                    </a>
                </div>
            </div>
            <div>
                <div class="fs-title" style="font-size:0.95rem; margin-bottom:14px;">Platform</div>
                <a href="?nav=Home&r={nav_token}" target="_self" class="fs-footer-link">Home</a>
                <a href="?nav=About&r={nav_token}" target="_self" class="fs-footer-link">About</a>
                <a href="?nav=Products&r={nav_token}" target="_self" class="fs-footer-link">Products & Tools</a>
                <a href="?nav=Pricing&r={nav_token}" target="_self" class="fs-footer-link">Fee & Tax Calculator</a>
                <a href="?nav=Terminal&r={nav_token}" target="_self" class="fs-footer-link">SuperChart Terminal</a>
                <a href="?nav=Advisor&r={nav_token}" target="_self" class="fs-footer-link">AI Stock Advisor</a>
            </div>
            <div>
                <div class="fs-title" style="font-size:0.95rem; margin-bottom:14px;">Support & Resources</div>
                <a href="?nav=Support&r={nav_token}" target="_self" class="fs-footer-link">Contact us</a>
                <a href="?nav=Support&r={nav_token}" target="_self" class="fs-footer-link">Support portal</a>
                <a href="?nav=Pricing&r={nav_token}" target="_self" class="fs-footer-link">Brokerage & tax breakdown</a>
                <a href="?nav=Orders&r={nav_token}" target="_self" class="fs-footer-link">Order book CSV export</a>
                <a href="https://www.youtube.com" target="_blank" rel="noopener noreferrer" class="fs-footer-link">Video tutorials</a>
                <a href="?nav=Dashboard&r={nav_token}" target="_self" class="fs-footer-link">Live market overview</a>
            </div>
            <div>
                <div class="fs-title" style="font-size:0.95rem; margin-bottom:14px;">Account & Simulation</div>
                <a href="?nav=Signup&r={nav_token}" target="_self" class="fs-footer-link">Open an account</a>
                <a href="?nav=Funds&r={nav_token}" target="_self" class="fs-footer-link">Fund transfer (Virtual Wallet)</a>
                <a href="?nav=Holdings&r={nav_token}" target="_self" class="fs-footer-link">Portfolio holdings</a>
                <a href="?nav=Positions&r={nav_token}" target="_self" class="fs-footer-link">Intraday & delivery positions</a>
                <a href="?nav=Apps&r={nav_token}" target="_self" class="fs-footer-link">FinanceSight Algo Backtester</a>
            </div>
        </div>
        <div class="fs-muted" style="margin-top:22px; font-size:0.75rem; line-height:1.7;">
            <p>FinanceSight is a market analysis, machine learning price forecasting, and paper trading simulation platform. Live and historical market data is fetched via the Yahoo Finance API for educational and analytical use.</p>
            <p style="margin-top:8px;">Stock market investments and trading involve market risk. Past backtest performance and machine learning projections do not guarantee future returns. Always verify technical setups and risk parameters before making financial decisions.</p>
            <div style="margin-top:14px; text-align:center;">
                <a href="https://www.nseindia.com" target="_blank" rel="noopener noreferrer" class="fs-bottom-link">NSE</a> •
                <a href="https://www.bseindia.com" target="_blank" rel="noopener noreferrer" class="fs-bottom-link">BSE</a> •
                <a href="https://www.mcxindia.com" target="_blank" rel="noopener noreferrer" class="fs-bottom-link">MCX</a> •
                <a href="?nav=About&r={nav_token}" target="_self" class="fs-bottom-link">About Platform</a> •
                <a href="?nav=Pricing&r={nav_token}" target="_self" class="fs-bottom-link">Fee Calculator</a> •
                <a href="?nav=Support&r={nav_token}" target="_self" class="fs-bottom-link">Help & Support</a>
            </div>
        </div>
    </div>
    """)

# ==========================================================
# 7. PART 1: PUBLIC FINANCESIGHT PORTAL (HOME, SIGNUP, ABOUT, PRODUCTS, PRICING, SUPPORT)
# ==========================================================
if not st.session_state.logged_in:
    nav_c1, nav_c2, nav_c3, nav_c4, nav_c5, nav_c6, nav_c7, nav_c8 = st.columns([1.6, 1.75, 0.88, 0.92, 0.88, 1.0, 0.92, 0.95])
    
    with nav_c1:
        render_html(f"""
        <a href="?nav=Home&r=top_{nav_token}" target="_self" class="fs-logo-link" title="Go to FinanceSight Home" style="padding-top:3px;">
            {FINANCESIGHT_LOGO_SVG}
            <span><span style="color:#387ed1;">FINANCE</span>SIGHT</span>
        </a>
        """)

    with nav_c2:
        search_options = ["Search Stocks"] + [
            f"{sym} — {meta['name']} ({meta['exchange']})" for sym, meta in STOCK_CATALOG.items()
        ]
        picked_search = st.selectbox("Search Stocks", search_options, label_visibility="collapsed")
        if picked_search != "Search Stocks":
            sym_jump = picked_search.split(" — ")[0]
            st.session_state.logged_in = True
            st.session_state.username = "Trader_XYZ"
            st.session_state.full_name = "Trader_XYZ"
            st.session_state.selected_ticker = sym_jump
            st.session_state.page = "Terminal"
            st.rerun()

    # Render Capitalized Top Navigation Buttons with Vector SVG Logos
    pub_pages = [
        ("HOME", "Home", nav_c3),
        ("SIGNUP", "Signup", nav_c4),
        ("ABOUT", "About", nav_c5),
        ("PRODUCTS", "Products", nav_c6),
        ("PRICING", "Pricing", nav_c7),
        ("SUPPORT", "Support", nav_c8)
    ]
    for label_caps, p_name, col_obj in pub_pages:
        active_cls = "active" if st.session_state.public_page == p_name else ""
        svg_icon = NAV_SVGS[p_name]
        with col_obj:
            render_html(f"""
            <a href="?nav={p_name}&r={nav_token}" target="_self" class="fs-nav-btn {active_cls}">
                {svg_icon}
                <span>{label_caps}</span>
            </a>
            """)

    if not online_status:
        st.warning("⚠️ **Offline Mode Detected:** Your internet connection is currently disconnected. Market prices are frozen at their last recorded close and will not fluctuate until internet is restored.")

    render_html("<hr style='border:0; border-top:1px solid rgba(128,128,128,0.25); margin:6px 0 18px 0;'>")

    # ----------------------------------------------------------
    # PUBLIC PAGE A: HOME PAGE
    # ----------------------------------------------------------
    if st.session_state.public_page == "Home":
        hero_left, hero_right = st.columns([1.62, 1.0], gap="large")

        with hero_left:
            watch_rows_html = ""
            for w_sym, w_label, w_dom in [
                ("NVDA", "NVDA", "nvidia.com"),
                ("AAPL", "AAPL", "apple.com"),
                ("TCS.NS", "TCS", "tcs.com"),
                ("RELIANCE.NS", "RELIANCE", "ril.com"),
                ("TSLA", "TSLA", "tesla.com")
            ]:
                s_data = snapshots.get(w_sym, {"price": 0.0, "pct": 0.0})
                cur_sym = STOCK_CATALOG.get(w_sym, {}).get("currency", "₹")
                is_up = s_data["pct"] >= 0
                clr = "#10b981" if is_up else "#f43f5e"
                arr = "▲" if is_up else "▼"
                watch_rows_html += (
                    f'<div class="watch-row">'
                    f'<div style="display:flex; align-items:center; gap:8px; font-weight:700;">'
                    f'<img src="https://www.google.com/s2/favicons?domain={w_dom}&sz=128" class="logo-sm">'
                    f'<span>{w_label}</span></div>'
                    f'<span style="font-weight:700;">{cur_sym}{s_data["price"]:,.2f}</span>'
                    f'<span style="color:{clr}; font-weight:800;">{arr} {s_data["pct"]:+.2f}%</span>'
                    f'</div>'
                )

            feed_badge = "🟢 LIVE YAHOO FINANCE DATA" if online_status else "🔴 OFFLINE (FROZEN)"
            feed_color = "#10b981" if online_status else "#f43f5e"

            render_html(f"""
            <div class="z-section-card" style="margin-top:0; padding:22px 24px;">
                <div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:12px; margin-bottom:16px; border-bottom:1px solid rgba(128,128,128,0.22);">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="height:10px; width:10px; background:{feed_color}; border-radius:50%; display:inline-block;"></span>
                        <img src="https://www.google.com/s2/favicons?domain=ril.com&sz=128" class="logo-sm">
                        <span style="font-family:JetBrains Mono,monospace; font-size:0.8rem; font-weight:700;">
                            FINANCESIGHT • LIVE MARKETWATCH & SUPERCHART
                        </span>
                    </div>
                    <span style="background:rgba(56,126,209,0.18); color:#387ed1; padding:4px 10px; border-radius:6px; font-family:JetBrains Mono,monospace; font-size:0.75rem; font-weight:800;">
                        {feed_badge}
                    </span>
                </div>

                <div style="display:grid; grid-template-columns: 1.4fr 1.2fr; gap:14px;">
                    <div class="fs-panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <img src="https://www.google.com/s2/favicons?domain=apple.com&sz=128" class="logo-sm">
                                <img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=128" class="logo-sm">
                                <span style="font-weight:800; font-size:0.88rem;">Orderflow & Volume Profile</span>
                            </div>
                            <span style="color:#10b981; font-family:JetBrains Mono,monospace; font-size:0.84rem; font-weight:800;">
                                {snapshots['NVDA']['pct']:+.2f}%
                            </span>
                        </div>

                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(128,128,128,0.2); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:68%; height:100%; background:linear-gradient(90deg, #eab308 60%, #3b82f6 40%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; width:90px;">POC ${snapshots['AAPL']['price']:,.1f}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(128,128,128,0.2); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:85%; height:100%; background:linear-gradient(90deg, #eab308 55%, #06b6d4 45%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; color:#0284c7; width:90px;">VAH ${snapshots['AAPL']['price']*1.015:,.1f}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(128,128,128,0.2); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:48%; height:100%; background:linear-gradient(90deg, #ef4444 50%, #3b82f6 50%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; color:#f43f5e; width:90px;">VAL ${snapshots['AAPL']['price']*0.985:,.1f}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(128,128,128,0.2); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:76%; height:100%; background:linear-gradient(90deg, #10b981 65%, #3b82f6 35%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; color:#10b981; width:90px;">▲ AI TARGET</span>
                        </div>

                        <div style="margin-top:16px; padding-top:12px; border-top:1px solid rgba(128,128,128,0.22); display:flex; justify-content:space-between; font-family:JetBrains Mono,monospace; font-size:0.76rem;">
                            <span>RELIANCE: <b style="color:#10b981;">₹{snapshots['RELIANCE.NS']['price']:,.2f}</b></span>
                            <span>TCS: <b style="color:#0284c7;">₹{snapshots['TCS.NS']['price']:,.2f}</b></span>
                        </div>
                    </div>

                    <div class="fs-panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid rgba(128,128,128,0.22);">
                            <span style="font-size:0.76rem; font-weight:800;">📋 FINANCESIGHT MARKETWATCH</span>
                            <span style="font-size:0.7rem; color:#0284c7; font-family:JetBrains Mono,monospace; font-weight:700;">REAL DATA</span>
                        </div>
                        {watch_rows_html}
                    </div>
                </div>

                <div style="text-align:center; margin-top:16px;">
                    <a href="?nav=Products&r={nav_token}" target="_self" style="text-decoration:none; background:var(--background-color); border:1px solid rgba(56,189,248,0.45); border-radius:999px; padding:10px 24px; display:inline-flex; align-items:center; gap:12px;">
                        <span style="font-size:1.15rem;">⚡</span>
                        <div style="text-align:left;">
                            <div style="font-weight:800; font-size:0.88rem; color:#0284c7;">Explore all charting, AI forecasting & paper trading tools ›</div>
                            <div class="fs-muted" style="font-size:0.74rem;">NSE & NASDAQ Equities • Technical Indicators • Strategy Backtesting</div>
                        </div>
                    </a>
                </div>
            </div>
            """)

        with hero_right:
            render_html("""
            <div class="z-section-card" style="margin-top:0; padding:20px 24px; margin-bottom:12px;">
                <span style="background:rgba(56,126,209,0.2); color:#387ed1; padding:4px 12px; border-radius:999px; font-size:0.75rem; font-weight:700;">
                    ⚡ FINANCESIGHT WEB TERMINAL • INSTANT ACCESS
                </span>
                <h3 class="fs-title" style="margin:10px 0 4px 0;">Sign In to FinanceSight Dashboard</h3>
                <p class="fs-muted" style="font-size:0.83rem; margin:0;">Includes Orders, Holdings, Positions, Funds, SuperCharts & LLaMA 3.3 AI</p>
            </div>
            """)

            auth_tab1, auth_tab2 = st.tabs(["FinanceSight Login", "Open Free Account"])

            with auth_tab1:
                login_user = st.text_input("FinanceSight User ID", value="Trader_XYZ")
                login_pass = st.text_input("Password", type="password", value="demo123")
                
                b1, b2 = st.columns(2)
                if b1.button("Login to FinanceSight", use_container_width=True, type="primary"):
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

                if b2.button("1-Click Guest Demo", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.username = "Trader_XYZ"
                    st.session_state.full_name = "Trader_XYZ"
                    st.session_state.page = "Dashboard"
                    st.rerun()

            with auth_tab2:
                new_name = st.text_input("Full Name", placeholder="e.g., Vishal Babu")
                new_user = st.text_input("Choose FinanceSight ID", placeholder="e.g., Trader_XYZ")
                new_email = st.text_input("Email ID", placeholder="user@financesight.in")
                new_pass = st.text_input("Create Password", type="password")
                if st.button("Open Account & Claim ₹1,00,000", use_container_width=True, type="primary"):
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

        # HOME COMPONENT 2: PRACTICAL PLATFORM CAPABILITIES
        render_html("""
        <div class="z-section-card">
            <div style="display:grid; grid-template-columns: 1fr 1.3fr; gap:32px; align-items:center;">
                <div class="fs-panel" style="padding:28px; text-align:center;">
                    <div style="font-size:3.2rem; margin-bottom:10px;">📊</div>
                    <h3 class="fs-title" style="margin-bottom:6px;">All-in-One Market Analysis & Trading Suite</h3>
                    <p style="color:#0284c7; font-family:'JetBrains Mono',monospace; font-size:0.9rem; font-weight:700;">Live NSE & NASDAQ Data • AI Signals • Paper Trading</p>
                </div>
                <div>
                    <h2 class="fs-title" style="font-size:1.75rem; margin-bottom:10px;">Built for practical analysis and risk-free learning</h2>
                    <p class="fs-muted" style="font-size:0.95rem; margin-bottom:16px;">
                        FinanceSight brings together real-time market data, quantitative technical indicators, and virtual trade execution in one workspace:
                    </p>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#0284c7; font-weight:700; font-size:0.92rem;">
                        <div>• Live Candlestick & Volume Charts</div>
                        <div>• 14-Day RSI & Moving Averages</div>
                        <div>• 7-Day ML Price Forecasting</div>
                        <div>• Conversational AI Stock Analyst</div>
                        <div>• No-Code Strategy Backtesting</div>
                        <div>• Virtual Paper Trading Portfolio</div>
                    </div>
                </div>
            </div>
        </div>
        """)

        # HOME COMPONENT 3: PRACTICAL FEATURES & FEE SIMULATOR
        st_col1, st_col2 = st.columns([1.3, 1.0], gap="large")
        with st_col1:
            render_html("""
            <div class="z-section-card" style="height:100%;">
                <h2 class="fs-title" style="font-size:1.65rem; margin-bottom:14px;">🛡️ Practical tools you can rely on</h2>
                <div style="margin-bottom:14px;">
                    <h4 style="color:#0284c7; margin:0 0 4px 0;">Data-driven decision making</h4>
                    <p class="fs-muted" style="font-size:0.88rem; margin:0;">Evaluate stocks using objective technical indicators (20-SMA, 50-EMA, 14-Day RSI) and historical backtest metrics instead of guesswork.</p>
                </div>
                <div style="margin-bottom:14px;">
                    <h4 style="color:#0284c7; margin:0 0 4px 0;">Risk-free paper trading simulator</h4>
                    <p class="fs-muted" style="font-size:0.88rem; margin:0;">Practice placing delivery (CNC) and intraday (MIS 5x leverage) orders using a ₹1,00,000 virtual wallet before risking real capital.</p>
                </div>
                <div>
                    <h4 style="color:#0284c7; margin:0 0 4px 0;">Integrated AI & backtesting workflow</h4>
                    <p class="fs-muted" style="font-size:0.88rem; margin:0;">Combine 7-day Random Forest price projections, LLaMA 3.3 market insights, and rule-based strategy backtesting in a single interface.</p>
                </div>
            </div>
            """)

        with st_col2:
            render_html("""
            <div class="z-section-card" style="height:100%;">
                <h2 class="fs-title" style="font-size:1.65rem; margin-bottom:10px;">🏷️ Transparent fee simulation</h2>
                <p class="fs-muted" style="font-size:0.9rem; margin-bottom:18px;">
                    Estimate real-world trading costs accurately using standard discount brokerage rates and our built-in tax & breakeven calculator.
                </p>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; text-align:center;">
                    <div class="fs-panel" style="border:2px solid #10b981; padding:18px;">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:800; color:#10b981;">₹0</div>
                        <div class="fs-muted" style="font-size:0.8rem; margin-top:6px;">Standard equity delivery & mutual fund simulation</div>
                    </div>
                    <div class="fs-panel" style="border:2px solid #0284c7; padding:18px;">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:800; color:#0284c7;">₹20</div>
                        <div class="fs-muted" style="font-size:0.8rem; margin-top:6px;">Flat intraday (MIS) & F&O order fee model</div>
                    </div>
                </div>
            </div>
            """)

        # HOME COMPONENT 4: EDUCATION & AI LEARNING
        render_html("""
        <div class="z-section-card">
            <div style="display:grid; grid-template-columns: 1fr 1.4fr; gap:28px; align-items:center;">
                <div class="fs-panel" style="padding:26px; text-align:center;">
                    <div style="font-size:3rem;">📚</div>
                    <h3 class="fs-title" style="margin-top:8px;">FinanceSight Learning Hub</h3>
                    <p class="fs-muted" style="font-size:0.85rem;">Interactive technical analysis & AI-assisted learning</p>
                </div>
                <div>
                    <h2 class="fs-title" style="font-size:1.65rem; margin-bottom:10px;">Learn market indicators as you trade</h2>
                    <p class="fs-muted" style="font-size:0.9rem; margin-bottom:12px;">
                        <b>Interactive Indicator Guides:</b> Understand how candlestick patterns, Moving Averages, Volume bars, and RSI momentum work directly on live stock charts.
                    </p>
                    <p class="fs-muted" style="font-size:0.9rem; margin:0;">
                        <b>FinanceSight AI Advisor:</b> Ask any question about stock trends, support and resistance zones, position sizing, or trading terminology and get instant explanations.
                    </p>
                </div>
            </div>
        </div>
        """)

        render_financesight_open_account("home")

    # ----------------------------------------------------------
    # PUBLIC PAGE B: SIGNUP PAGE
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Signup":
        s_left, s_right = st.columns([1.2, 1.2], gap="large")
        with s_left:
            render_html("""
            <div class="z-section-card">
                <span style="background:rgba(56,126,209,0.2); color:#387ed1; padding:5px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
                    INSTANT PAPER TRADING ACCESS
                </span>
                <h2 class="fs-title" style="margin:12px 0 10px 0;">Create your free FinanceSight account</h2>
                <p class="fs-muted" style="font-size:0.95rem; line-height:1.6;">
                    Set up your account in seconds to track live NSE & NASDAQ stocks, test algorithmic strategies, and practice trading with <b>₹1,00,000</b> in virtual margin.
                </p>
                <div class="fs-panel" style="margin-top:18px; font-size:0.86rem; line-height:1.8;">
                    ✅ ₹1,00,000 Virtual Paper Trading Wallet<br>
                    ✅ Built-In Groq LLaMA 3.3 AI Financial Advisor<br>
                    ✅ 7-Day Random Forest ML Price Predictor<br>
                    ✅ No-Code Strategy Backtester & CSV Exports
                </div>
            </div>
            """)
        with s_right:
            st.markdown("### ✨ Create Your FinanceSight Account Now")
            su_name = st.text_input("Your Full Name", placeholder="e.g., Vishal Babu")
            su_user = st.text_input("Choose FinanceSight User ID", placeholder="e.g., Trader_XYZ")
            su_email = st.text_input("Email Address", placeholder="user@financesight.in")
            su_pass = st.text_input("Password", type="password")
            if st.button("Complete Signup & Open FinanceSight Dashboard", type="primary", use_container_width=True):
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
            if st.button("Or Use 1-Click Guest Demo Account (Trader_XYZ)", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "Trader_XYZ"
                st.session_state.full_name = "Trader_XYZ"
                st.session_state.page = "Dashboard"
                st.rerun()

    # ----------------------------------------------------------
    # PUBLIC PAGE C: ABOUT PAGE
    # ----------------------------------------------------------
    elif st.session_state.public_page == "About":
        render_html("""
        <div class="z-section-card" style="text-align:center;">
            <h2 class="fs-title" style="font-size:1.85rem; max-width:800px; margin:0 auto;">
                Clear, Objective Market Analysis.<br>
                <span style="color:#0284c7;">Combining Technical Charting, Machine Learning & Paper Trading.</span>
            </h2>
        </div>
        """)

        ab_c1, ab_c2 = st.columns(2, gap="large")
        with ab_c1:
            render_html("""
            <div class="z-section-card" style="height:100%; font-size:0.94rem; line-height:1.75;">
                <p><b>FinanceSight</b> is designed to make technical stock analysis, algorithmic backtesting, and portfolio simulation straightforward and accessible.</p>
                <p>By integrating live market data with <b>Random Forest price forecasting</b> and <b>LLaMA 3.3 RAG market analysis</b>, the platform helps users evaluate trends, momentum, and risk levels clearly.</p>
            </div>
            """)
        with ab_c2:
            render_html("""
            <div class="z-section-card" style="height:100%; font-size:0.94rem; line-height:1.75;">
                <p>Instead of switching between separate charting websites, calculators, and spreadsheets, FinanceSight brings everything into a single workspace.</p>
                <p>Users can test trading strategies on historical data, calculate exact statutory charges and breakeven points, and practice order execution risk-free using a virtual wallet.</p>
            </div>
            """)

        render_html("""
        <div class="z-section-card">
            <h2 class="fs-title" style="text-align:center; margin-bottom:24px;">👥 Platform Architecture & Engineering</h2>
            <div style="display:grid; grid-template-columns: 1fr 2fr; gap:28px; align-items:center;">
                <div class="fs-panel" style="text-align:center; padding:24px; border:2px solid #0284c7;">
                    <div style="font-size:3.6rem;">👨‍💻</div>
                    <h4 class="fs-title" style="margin:10px 0 4px 0;">FinanceSight Core Systems</h4>
                    <div style="color:#0284c7; font-size:0.84rem; font-weight:700;">Python, Machine Learning & SQLite Architecture</div>
                </div>
                <div style="font-size:0.95rem; line-height:1.75;">
                    <p>FinanceSight integrates a <b>Multi-Layer SuperChart Terminal, Portfolio Console, No-Code Strategy Backtester, and Conversational AI Advisor</b> into a unified web application.</p>
                    <p>Powered by live <b>Yahoo Finance market streams</b>, <b>Scikit-Learn Random Forest regression</b>, <b>Groq LLaMA 3.3 RAG</b>, and a local <b>SQLite relational database</b> for persistent portfolio and order tracking.</p>
                </div>
            </div>
        </div>
        """)

    # ----------------------------------------------------------
    # PUBLIC PAGE D: PRODUCTS PAGE
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Products":
        render_html(f"""
        <div class="z-section-card" style="text-align:center;">
            <h1 class="fs-title" style="font-size:2.2rem; margin-bottom:8px;">FinanceSight Products & Modules</h1>
            <h4 class="fs-muted" style="font-weight:500; margin-bottom:10px;">Integrated tools for charting, price forecasting, backtesting, and paper trading</h4>
            <a href="?nav=Dashboard&r={nav_token}" target="_self" style="color:#0284c7; font-weight:700; font-size:0.92rem; text-decoration:none;">Launch the live trading dashboard →</a>
        </div>
        """)

        products_showcase = [
            ("left", "📈 FinanceSight SuperChart Terminal", "Interactive 3-layer technical charting with Japanese Candlesticks, 20-Day SMA, 50-Day EMA, Volume bars, 14-Day RSI, and instant CNC/MIS paper order execution.", "Terminal"),
            ("right", "💿 FinanceSight Portfolio & Ledger", "Centralized portfolio tracker showing live mark-to-market P&L, asset allocation donut charts, order history, and 1-click CSV/Excel report downloads.", "Holdings"),
            ("left", "🤖 FinanceSight LLaMA 3.3 AI Advisor", "Conversational AI stock analyst connected to live technical indicators. Type any supported stock name (Apple, NVIDIA, Reliance, TCS) for custom entry, stop-loss, and target analysis.", "Advisor"),
            ("right", "⚡ 7-Day Random Forest ML Predictor", "Trains a live Random Forest regression model on rolling 1-year OHLCV and momentum lag features to project the next 7 trading sessions.", "Terminal"),
            ("left", "🧪 No-Code Strategy Backtester & Scanner", "Test systematic trading rules (Golden Crossover, RSI Oversold Reversal, Momentum Surge) on historical candles, view the equity curve, and scan multiple stocks live.", "Apps")
        ]

        for align, p_title, p_desc, target_tab in products_showcase:
            c_a, c_b = st.columns([1, 1.2] if align == "left" else [1.2, 1], gap="large")
            visual_col = c_a if align == "left" else c_b
            text_col = c_b if align == "left" else c_a

            with visual_col:
                render_html(f"""
                <div class="z-section-card" style="margin:0; padding:32px; text-align:center;">
                    <div style="font-size:2.8rem; margin-bottom:8px;">{p_title.split()[0]}</div>
                    <div class="fs-title" style="font-size:1.15rem;">{p_title}</div>
                    <div style="color:#0284c7; font-size:0.8rem; margin-top:6px; font-weight:600;">⚡ Live Module Inside FinanceSight</div>
                </div>
                """)
            with text_col:
                st.markdown(f"### {p_title}")
                st.write(p_desc)
                b_try, b_learn = st.columns(2)
                if b_try.button(f"Open Module →", key=f"prod_demo_{p_title}", type="primary", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.username = "Trader_XYZ"
                    st.session_state.full_name = "Trader_XYZ"
                    st.session_state.page = target_tab
                    st.rerun()
                if b_learn.button("View Details →", key=f"prod_learn_{p_title}", use_container_width=True):
                    st.session_state.public_page = "About"
                    st.rerun()
            render_html("<hr style='border:0; border-top:1px solid rgba(128,128,128,0.22); margin:16px 0;'>")

        render_html("""
        <div style="text-align:center; margin:28px 0 18px 0;">
            <h2 class="fs-title">🧩 Core Feature Highlights</h2>
            <p class="fs-muted">Built-in utilities included across the FinanceSight workspace</p>
        </div>
        """)

        universe_items = [
            ("⚡ Strategy Backtester", "Simulate Golden Crossover, RSI Reversal, and Momentum rules with adjustable Stop-Loss and Target sliders."),
            ("📡 Live Market Scanner", "Scan NSE and NASDAQ stocks simultaneously for RSI breakouts and moving average trends."),
            ("🤖 Multi-Stock AI Chat", "Automatically detects company names in your chat prompt and switches the active stock context."),
            ("🧮 Brokerage Calculator", "Compute exact STT, GST, exchange transaction fees, stamp duty, and net P&L before placing trades."),
            ("💼 CNC & MIS Simulation", "Test both 1x delivery holdings and 5x leveraged intraday positions with 1-click square-off."),
            ("📥 CSV Report Exports", "Download your executed order book, demat holdings, and strategy backtest ledgers as CSV files.")
        ]
        for r_idx in range(0, 6, 3):
            u_cols = st.columns(3)
            for c_i in range(3):
                u_name, u_desc = universe_items[r_idx + c_i]
                with u_cols[c_i]:
                    render_html(f"""
                    <div class="z-universe-card">
                        <h4 style="color:#0284c7; font-weight:800; margin-bottom:8px;">{u_name}</h4>
                        <p class="fs-muted" style="font-size:0.84rem; margin:0;">{u_desc}</p>
                    </div>
                    """)
            st.markdown("<br>", unsafe_allow_html=True)

        render_financesight_open_account("products")

    # ----------------------------------------------------------
    # PUBLIC PAGE E: PRICING & BROKERAGE CALCULATOR PAGE
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Pricing":
        render_html("""
        <div class="z-section-card" style="text-align:center;">
            <h1 class="fs-title" style="font-size:2.1rem;">Fee Structure & Brokerage Calculator</h1>
            <p class="fs-muted" style="font-size:0.95rem;">Simulate standard Indian discount broking charges (₹0 delivery and flat ₹20 intraday) and calculate exact statutory taxes.</p>
        </div>
        """)

        pr1, pr2, pr3 = st.columns(3)
        with pr1:
            render_kpi("Equity Delivery Simulation", "₹0", "Zero brokerage modeled on long-term CNC equity delivery trades.", "kpi-emerald", "#10b981")
        with pr2:
            render_kpi("Intraday & F&O Simulation", "₹20", "Flat ₹20 or 0.03% (whichever is lower) per executed intraday order.", "kpi-cyan", "#0284c7")
        with pr3:
            render_kpi("Virtual Paper Wallet", "₹1,00,000", "Free instant virtual margin credited to every user account for practice.", "kpi-violet", "#8b5cf6")

        st.markdown("### 🧮 Interactive FinanceSight Brokerage & Statutory Charges Calculator")
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
            render_kpi("Total Turnover", f"₹{turnover:,.2f}", f"Brokerage: ₹{brokerage:.2f}", "kpi-cyan", "#0284c7")
        with bc2:
            render_kpi("Total Taxes & Charges", f"₹{total_charges:,.2f}", f"STT: ₹{stt:.2f} | GST: ₹{gst:.2f}", "kpi-violet", "#8b5cf6")
        with bc3:
            render_kpi("Breakeven Per Share", f"₹{(total_charges/c_qty):.2f}", "Points needed to cover taxes", "kpi-white", "#2563eb")
        with bc4:
            render_kpi("Net Realized Profit / Loss", f"₹{net_pnl:,.2f}", f"Gross P&L: ₹{gross_pnl:+.2f}", "kpi-emerald" if net_pnl >= 0 else "kpi-violet", "#10b981" if net_pnl >= 0 else "#f43f5e")

        render_financesight_open_account("pricing")

    # ----------------------------------------------------------
    # PUBLIC PAGE F: SUPPORT PORTAL PAGE
    # ----------------------------------------------------------
    elif st.session_state.public_page == "Support":
        render_html(f"""
        <div class="z-support-hero">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <h3 style="margin:0; font-weight:800; color:#ffffff;">🎧 FinanceSight Help & Support Center</h3>
                <span style="background:rgba(255,255,255,0.2); padding:5px 14px; border-radius:999px; font-size:0.82rem; font-weight:700; color:#ffffff;">Support Desk</span>
            </div>
            <div style="display:grid; grid-template-columns: 1.4fr 1fr; gap:28px;">
                <div>
                    <h2 style="font-weight:800; font-size:1.6rem; margin-bottom:12px; color:#ffffff;">Browse platform guides or submit a support ticket below</h2>
                    <div style="background:#ffffff; color:#0f172a; padding:12px 18px; border-radius:10px; font-size:0.9rem; margin-bottom:12px;">
                        🔍 Quick links to platform modules and user guides:
                    </div>
                    <div style="font-size:0.82rem; color:#e2e8f0;">
                        <a href="?nav=Signup&r={nav_token}" target="_self" style="color:#ffffff; text-decoration:underline;">Create an account</a> &nbsp;•&nbsp;
                        <a href="?nav=Terminal&r={nav_token}" target="_self" style="color:#ffffff; text-decoration:underline;">Open SuperChart</a> &nbsp;•&nbsp;
                        <a href="?nav=Pricing&r={nav_token}" target="_self" style="color:#ffffff; text-decoration:underline;">Brokerage calculator</a> &nbsp;•&nbsp;
                        <a href="?nav=Advisor&r={nav_token}" target="_self" style="color:#ffffff; text-decoration:underline;">Ask AI Advisor</a>
                    </div>
                </div>
                <div>
                    <h4 style="font-weight:800; margin-bottom:10px; color:#ffffff;">📌 Platform Highlights</h4>
                    <ol style="font-size:0.88rem; line-height:1.8; color:#f1f5f9;">
                        <li>Type any stock name in AI Advisor to switch charts automatically</li>
                        <li>Intraday MIS orders use 5x margin leverage (20% margin required)</li>
                    </ol>
                </div>
            </div>
        </div>
        """)

        st.subheader("📋 Browse Help Topics by Module")
        ticket_topics = [
            ("➕ Account & Login", f"?nav=Signup&r={nav_token}", ["Creating a New User Account", "Using 1-Click Guest Demo Login", "Managing Profile & Credentials", "Virtual Margin Overview", "Platform Navigation Guide"]),
            ("📊 Charting & Indicators", f"?nav=Terminal&r={nav_token}", ["Reading Japanese Candlesticks", "Using 20-SMA & 50-EMA Lines", "Understanding 14-Day RSI", "Volume Bar Color Coding", "Refreshing Live Market Data"]),
            ("⚡ Paper Trading Orders", f"?nav=Positions&r={nav_token}", ["CNC Delivery vs MIS Intraday (5x)", "Placing Market & Limit Orders", "Tracking Open Positions M2M", "1-Click Position Square-Off", "Exporting Order Book to CSV"]),
            ("💳 Virtual Funds & Wallet", f"?nav=Funds&r={nav_token}", ["Adding Virtual Cash via UPI Simulator", "Withdrawing Funds to Linked Bank", "Checking Available Margin", "Viewing Funding History Ledger", "Margin Release on Square-Off"]),
            ("🤖 AI Advisor & ML Forecast", f"?nav=Advisor&r={nav_token}", ["How the 7-Day Random Forest Model Works", "Asking Custom Stock Questions", "Auto-Switching Stocks via Chat", "Understanding ATR Stop-Loss Levels", "Position Sizing Rules"]),
            ("🧪 Strategy Backtesting", f"?nav=Apps&r={nav_token}", ["SMA 20 Golden Crossover Logic", "RSI < 35 Oversold Reversal Rule", "Setting Stop-Loss & Target Sliders", "Reading the Backtest Equity Curve", "Downloading Backtest Reports"])
        ]
        for row_i in range(0, 6, 3):
            t_cols = st.columns(3)
            for col_i in range(3):
                t_head, t_href, t_links = ticket_topics[row_i + col_i]
                links_html = "".join([f"<a href='{t_href}' target='_self' style='display:block; color:#0284c7; font-size:0.84rem; margin:6px 0; font-weight:600; text-decoration:none;'>• {lnk}</a>" for lnk in t_links])
                with t_cols[col_i]:
                    render_html(f"""
                    <div class="stock-card" style="height:100%;">
                        <h4 class="fs-title" style="margin-bottom:12px;">{t_head}</h4>
                        {links_html}
                    </div>
                    """)

        st.markdown("---")
        st.markdown("#### 🎫 Submit a Support Ticket")
        tk_c1, tk_c2, tk_c3 = st.columns(3)
        tk_cat = tk_c1.selectbox("Topic Category", [t[0] for t in ticket_topics])
        tk_email = tk_c2.text_input("Your Email", value="user@financesight.in")
        tk_subj = tk_c3.text_input("Issue Summary", placeholder="e.g., Question about backtest CSV export")
        if st.button("✅ Create Support Ticket", type="primary"):
            if tk_subj:
                c = conn.cursor()
                t_id = f"FS-{np.random.randint(10000, 99999)}"
                c.execute("INSERT INTO support_tickets (ticket_id, timestamp, category, subject, email, status) VALUES (?, ?, ?, ?, ?, 'OPEN')",
                          (t_id, datetime.now().strftime("%Y-%m-%d %H:%M"), tk_cat, tk_subj, tk_email))
                conn.commit()
                st.success(f"🎉 Ticket **{t_id}** logged in the database!")
        tk_df = pd.read_sql_query("SELECT ticket_id, timestamp, category, subject, email, status FROM support_tickets ORDER BY id DESC LIMIT 5", conn)
        if not tk_df.empty:
            st.dataframe(tk_df, use_container_width=True, hide_index=True)

    render_financesight_footer()
    st.stop()

# ==========================================================
# 8. PART 2: AUTHENTICATED FINANCESIGHT DASHBOARD (AFTER LOGIN)
# ==========================================================
if not online_status:
    st.warning("⚠️ **Offline Mode:** Internet connection is disconnected. Showing last cached market close prices without live updates.")

ticker_items_html = ""
for sym, data in snapshots.items():
    cur = STOCK_CATALOG.get(sym, {}).get("currency", "₹")
    logo = get_logo_url(sym)
    arrow = "▲" if data["pct"] >= 0 else "▼"
    color = "#10b981" if data["pct"] >= 0 else "#f43f5e"
    ticker_items_html += (
        f'<span class="ticker-item">'
        f'<img src="{logo}" class="ticker-logo">'
        f'<b>{sym.replace(".NS","")}</b> '
        f'<span style="color:#0284c7; font-weight:700;">{cur}{data["price"]:,.2f}</span> '
        f'<span style="color:{color}; font-weight:800;">{arrow} {data["pct"]:+.2f}%</span>'
        f'</span>'
    )

render_html(f"""
<div class="ticker-wrap">
    <div class="ticker-move">
        {ticker_items_html} {ticker_items_html}
    </div>
</div>
""")

# FINANCESIGHT DASHBOARD TOP NAVIGATION BAR (ALL CAPS + VECTOR SVG LOGOS)
nav_cols = st.columns([1.45, 1.08, 0.92, 1.02, 1.05, 0.9, 1.15, 1.12, 0.92, 0.92])
with nav_cols[0]:
    render_html(f"""
    <a href="?nav=Home&r=dash_{nav_token}" target="_self" class="fs-logo-link" title="Go to FinanceSight Home" style="font-size:1.15rem; padding-top:4px;">
        {FINANCESIGHT_LOGO_SVG}
        <span><span style="color:#387ed1;">FINANCE</span>SIGHT</span>
    </a>
    """)

fs_pages = [
    ("DASHBOARD", "Dashboard"),
    ("ORDERS", "Orders"),
    ("HOLDINGS", "Holdings"),
    ("POSITIONS", "Positions"),
    ("FUNDS", "Funds"),
    ("SUPERCHART", "Terminal"),
    ("AI ADVISOR", "Advisor"),
    ("APPS", "Apps")
]
for idx, (label_caps, p_key) in enumerate(fs_pages):
    active_cls = "active" if st.session_state.page == p_key else ""
    svg_icon = NAV_SVGS[p_key]
    with nav_cols[idx + 1]:
        render_html(f"""
        <a href="?nav={p_key}&u={st.session_state.username}&r={nav_token}" target="_self" class="fs-nav-btn {active_cls}">
            {svg_icon}
            <span>{label_caps}</span>
        </a>
        """)

with nav_cols[9]:
    render_html(f"""
    <a href="?nav=Logout&r={nav_token}" target="_self" class="fs-nav-btn">
        {NAV_SVGS['Logout']}
        <span>LOGOUT</span>
    </a>
    """)

# LEFT SIDEBAR: FINANCESIGHT MARKETWATCH + QUICK BUY / SELL
user_bal = get_user_balance(st.session_state.username)
st.sidebar.markdown(
    f'<a href="?nav=Home&r=sb_{nav_token}" target="_self" style="text-decoration:none; display:flex; align-items:center; gap:10px; margin-bottom:8px;" title="Go to FinanceSight Home">'
    f'{FINANCESIGHT_LOGO_SVG}'
    f'<div><div class="fs-title" style="font-size:1.05rem;">{st.session_state.full_name}</div>'
    f'<div class="fs-muted" style="font-size:0.75rem;">ID: @{st.session_state.username} • <b>FINANCESIGHT</b></div></div></a>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    f'<div class="kpi-box kpi-cyan" style="padding:14px; margin-bottom:12px;">'
    f'<div class="kpi-title">💳 Available FinanceSight Margin</div>'
    f'<div class="kpi-val" style="color:#0284c7;">₹{user_bal:,.2f}</div>'
    f'<div style="font-size:0.72rem; color:#10b981; margin-top:3px; font-weight:700;">● CNC Delivery (1x) & MIS Intraday (5x)</div></div>',
    unsafe_allow_html=True
)

if st.sidebar.button("Refresh Live Market Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.subheader("📋 FinanceSight Marketwatch")
catalog_options = [f"{k} — {v['name']}" for k, v in STOCK_CATALOG.items()]
current_idx = list(STOCK_CATALOG.keys()).index(st.session_state.selected_ticker) if st.session_state.selected_ticker in STOCK_CATALOG else 0
chosen_option = st.sidebar.selectbox("Search Stocks", catalog_options, index=current_idx)
chosen_sym = chosen_option.split(" — ")[0]
if chosen_sym != st.session_state.selected_ticker:
    st.session_state.selected_ticker = chosen_sym
    st.rerun()

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
st.sidebar.caption(f"📌 **Watchlist Feed ({'🟢 Live' if online_status else '🔴 Offline'})**")
for w_sym in ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "AAPL", "NVDA"]:
    w_s = snapshots.get(w_sym, {"price": 0.0, "pct": 0.0})
    w_c = "#10b981" if w_s["pct"] >= 0 else "#f43f5e"
    w_arr = "▲" if w_s["pct"] >= 0 else "▼"
    st.sidebar.markdown(
        f"<div style='display:flex; justify-content:space-between; font-family:JetBrains Mono,monospace; font-size:0.78rem; padding:4px 0; border-bottom:1px solid rgba(128,128,128,0.2);'>"
        f"<span><b>{w_sym.replace('.NS','')}</b></span>"
        f"<span style='color:{w_c}; font-weight:700;'>{w_s['price']:,.2f} ({w_arr}{w_s['pct']:+.2f}%)</span></div>",
        unsafe_allow_html=True
    )

# ==========================================================
# 9. TAB 1: DASHBOARD (SUMMARY + STOCKS)
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
        render_kpi("Holdings Value", f"₹{tot_cur:,.2f}", f"Invested: ₹{tot_inv:,.2f} ({len(port_df)} stocks)", "kpi-cyan", "#0284c7")
    with h_c3:
        render_kpi("Unrealized P&L", f"₹{tot_pnl:,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} Net Portfolio P&L", "kpi-emerald" if tot_pnl >= 0 else "kpi-violet", "#10b981" if tot_pnl >= 0 else "#f43f5e")
    with h_c4:
        render_kpi("Feed Connectivity", "LIVE ONLINE" if online_status else "OFFLINE CACHED", "Real-Time Yahoo Finance API", "kpi-emerald" if online_status else "kpi-violet", "#10b981" if online_status else "#f43f5e")

    st.subheader("🏢 FinanceSight Marketwatch Cards (Click to Launch SuperChart or AI)")
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
                    render_html(f"""
                    <div class="stock-card">
                        <div class="company-header">
                            <img src="{logo_url}" class="company-logo" alt="{meta['name']}">
                            <div>
                                <div class="fs-title" style="font-size:1.02rem;">{meta['name']}</div>
                                <div style="font-size:0.76rem; color:#0284c7; font-weight:700;">{meta['exchange']}: {sym.replace('.NS','')} • {meta['sector']}</div>
                            </div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-top:8px;">
                            <div class="mono-price">{meta['currency']}{snap['price']:,.2f}</div>
                            <span class="{badge_cls}">{arrow} {snap['pct']:+.2f}%</span>
                        </div>
                        <div class="fs-muted" style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(128,128,128,0.2); display:flex; justify-content:space-between; font-size:0.78rem;">
                            <span>RSI (14): <b>{snap['rsi']:.1f}</b></span>
                            <span style="font-weight:700;">{ai_tag}</span>
                        </div>
                    </div>
                    """)
                    
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button(f"SUPERCHART", key=f"dash_chart_{sym}", use_container_width=True):
                        navigate_to("Terminal", sym)
                        st.rerun()
                    if c_btn2.button(f"ASK AI ADVISOR", key=f"dash_ai_{sym}", use_container_width=True):
                        navigate_to("Advisor", sym)
                        st.rerun()

# ==========================================================
# 10. TAB 2: ORDERS PAGE (Order Book + CSV Export)
# ==========================================================
elif st.session_state.page == "Orders":
    st.subheader("📜 FinanceSight Executed Orders & Tradebook")
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
            file_name="financesight_orders.csv",
            mime="text/csv"
        )

# ==========================================================
# 11. TAB 3: HOLDINGS PAGE (CNC Delivery Holdings + Pie Chart)
# ==========================================================
elif st.session_state.page == "Holdings":
    st.subheader("💼 FinanceSight CNC Equity Holdings (Long-Term Portfolio)")
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(st.session_state.username,))
    
    if port_df.empty:
        st.info("Your Holdings are currently empty. Place a **CNC (Delivery) BUY** order in the sidebar or SuperChart to build your portfolio!")
    else:
        port_df["LTP (Live Price)"] = port_df["ticker"].apply(lambda s: snapshots.get(s, {}).get("price", float(port_df.loc[port_df["ticker"] == s, "avg_price"].iloc[0])))
        port_df["Invested (₹)"] = port_df["shares"] * port_df["avg_price"]
        port_df["Current Value (₹)"] = port_df["shares"] * port_df["LTP (Live Price)"]
        port_df["Net P&L (₹)"] = port_df["Current Value (₹)"] - port_df["Invested (₹)"]
        port_df["Net Change (%)"] = (port_df["Net P&L (₹)"] / port_df["Invested (₹)"]) * 100

        tot_inv = port_df["Invested (₹)"].sum()
        tot_cur = port_df["Current Value (₹)"].sum()
        tot_pnl = tot_cur - tot_inv

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            render_kpi("Total Account Net Worth", f"₹{(user_bal + tot_cur):,.2f}", "Cash + Holdings", "kpi-white", "#2563eb")
        with pc2:
            render_kpi("Total Investment", f"₹{tot_inv:,.2f}", f"{len(port_df)} Active Stocks", "kpi-cyan", "#0284c7")
        with pc3:
            render_kpi("Current Value", f"₹{tot_cur:,.2f}", "Live Mark-to-Market", "kpi-violet", "#8b5cf6")
        with pc4:
            render_kpi("Total P&L", f"₹{tot_pnl:,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} {(tot_pnl/tot_inv)*100:+.2f}% ROI", "kpi-emerald" if tot_pnl >= 0 else "kpi-violet", "#10b981" if tot_pnl >= 0 else "#f43f5e")

        d_col1, d_col2 = st.columns([1.8, 1.2])
        with d_col1:
            st.markdown("##### 📂 Holdings Breakdown")
            st.dataframe(port_df.round(2), use_container_width=True, hide_index=True)
            csv_hold = port_df.round(2).to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Holdings Statement (CSV)", data=csv_hold, file_name="financesight_holdings.csv", mime="text/csv")
        with d_col2:
            pie_fig = go.Figure(data=[go.Pie(labels=port_df["ticker"], values=port_df["Current Value (₹)"], hole=0.52)])
            pie_fig.update_layout(title="Holdings Allocation", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(pie_fig, use_container_width=True)

# ==========================================================
# 12. TAB 4: POSITIONS PAGE (MIS Intraday & CNC Open Positions + Square-Off)
# ==========================================================
elif st.session_state.page == "Positions":
    st.subheader("⚡ FinanceSight Open Positions (MIS Intraday 5x & CNC Delivery)")
    pos_df = pd.read_sql_query("SELECT ticker, product_type, shares, avg_price FROM positions WHERE username = ?", conn, params=(st.session_state.username,))
    
    if pos_df.empty:
        st.info("No open positions right now. Place an **MIS (Intraday 5x)** or **CNC** order from the sidebar to track live M2M Positions!")
    else:
        pos_df["LTP"] = pos_df["ticker"].apply(lambda s: snapshots.get(s, {}).get("price", float(pos_df.loc[pos_df["ticker"] == s, "avg_price"].iloc[0])))
        pos_df["M2M P&L (₹)"] = (pos_df["LTP"] - pos_df["avg_price"]) * pos_df["shares"]
        pos_df["Return (%)"] = ((pos_df["LTP"] - pos_df["avg_price"]) / pos_df["avg_price"]) * 100

        tot_m2m = pos_df["M2M P&L (₹)"].sum()
        render_kpi("Total Open Positions M2M P&L", f"₹{tot_m2m:,.2f}", f"{len(pos_df)} Active Positions", "kpi-emerald" if tot_m2m >= 0 else "kpi-violet", "#10b981" if tot_m2m >= 0 else "#f43f5e")
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
# 13. TAB 5: FUNDS PAGE (Add Money UPI + Withdraw IMPS)
# ==========================================================
elif st.session_state.page == "Funds":
    st.subheader("💳 FinanceSight Virtual Funds & Margin Gateway")
    f_tab1, f_tab2 = st.tabs(["➕ Add Virtual Funds (UPI / NetBanking Simulator)", "🏦 Withdraw Funds (Bank Settlement Simulator)"])

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
            render_kpi("Withdrawable Balance", f"₹{user_bal:,.2f}", "Instant Bank Settlement", "kpi-emerald", "#10b981")
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
# 14. TAB 6: SUPERCHART & 7-DAY ML PREDICTOR
# ==========================================================
elif st.session_state.page == "Terminal":
    ticker = st.session_state.selected_ticker
    meta = STOCK_CATALOG.get(ticker, {"name": ticker, "sector": "Global Equity", "domain": "google.com", "exchange": "MKT", "currency": "₹"})
    currency = meta["currency"]
    logo_url = get_logo_url(ticker)

    df = fetch_stock_history(ticker, "1y") if online_status else None
    if df is None or len(df) < 35:
        st.error("⚠️ Live historical chart data requires an active internet connection. Please reconnect and click 'Refresh Live Market Data'.")
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

    render_html(f"""
    <div class="stock-card" style="display:flex; justify-content:space-between; align-items:center; padding:22px 26px;">
        <div style="display:flex; align-items:center; gap:18px;">
            <img src="{logo_url}" class="company-logo-lg">
            <div>
                <span style="background:rgba(6,182,212,0.18); color:#0284c7; padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:700;">
                    {meta['exchange']} • {meta['sector']}
                </span>
                <h2 class="fs-title" style="margin:6px 0 2px 0;">{meta['name']} ({ticker.replace('.NS','')})</h2>
                <div class="fs-muted" style="font-size:0.84rem; font-family:'JetBrains Mono',monospace;">
                    52W Low: {currency}{low_52:,.2f} • 52W High: {currency}{high_52:,.2f} • 20-SMA: {currency}{sma20_val:,.2f}
                </div>
            </div>
        </div>
        <div style="text-align:right;">
            <div class="mono-price" style="font-size:2.1rem; color:#0284c7;">{currency}{latest_c:,.2f}</div>
            <span class="{'badge-up' if pct >= 0 else 'badge-down'}" style="font-size:0.95rem;">
                {'▲' if pct >= 0 else '▼'} {chg:+.2f} ({pct:+.2f}%)
            </span>
        </div>
    </div>
    """)

    main_col, trade_col = st.columns([2.7, 1.1])

    with main_col:
        sub_t1, sub_t2, sub_t3 = st.tabs(["📊 FinanceSight SuperChart", "🤖 7-Day AI Price Forecast", "🧠 Built-In AI Stock Analyst"])
        
        with sub_t1:
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                row_heights=[0.62, 0.18, 0.20]
            )
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                name="Price", increasing_line_color="#10b981", decreasing_line_color="#f43f5e"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], name="20 SMA", line=dict(color="#0284c7", width=1.8)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["EMA_50"], name="50 EMA", line=dict(color="#f59e0b", width=1.8, dash="dot")), row=1, col=1)

            v_colors = ["#10b981" if c >= o else "#f43f5e" for c, o in zip(df["Close"], df["Open"])]
            fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=v_colors), row=2, col=1)

            fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)", line=dict(color="#8b5cf6", width=2)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#f43f5e", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)

            fig.update_layout(
                height=620, xaxis_rangeslider_visible=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
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
                render_kpi("Current Close Price", f"{currency}{latest_c:,.2f}", "Live Spot Price", "kpi-cyan", "#0284c7")
            with mc2:
                render_kpi("7-Day AI Projected Price", f"{currency}{target_7d:,.2f}", f"{'▲' if diff_pct >= 0 else '▼'} {diff_pct:+.2f}% Expected Move", "kpi-white", "#2563eb")
            with mc3:
                verdict_txt = "STRONG BUY ▲" if diff_pct > 1.2 else ("ACCUMULATE ▲" if diff_pct > 0 else "HOLD / CAUTION ▼")
                render_kpi("AI Model Verdict", verdict_txt, "Random Forest Ensemble", "kpi-emerald" if diff_pct >= 0 else "kpi-violet", "#10b981")

            p_fig = go.Figure()
            hist_60 = df.tail(55)
            p_fig.add_trace(go.Scatter(x=hist_60.index, y=hist_60["Close"], name="Historical Close", line=dict(color="#0284c7", width=2.5)))
            p_fig.add_trace(go.Scatter(
                x=[hist_60.index[-1]] + f_dates, y=[latest_c] + f_preds,
                name="7-Day ML Projection", mode="lines+markers",
                line=dict(color="#10b981" if diff_pct >= 0 else "#f43f5e", width=3, dash="dash")
            ))
            p_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400, margin=dict(l=15, r=15, t=20, b=15))
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
        render_html("""
        <div class="kpi-box kpi-white" style="margin-bottom:14px;">
            <div class="fs-title" style="font-size:1.05rem;">⚡ FinanceSight Order Window</div>
            <div class="fs-muted" style="font-size:0.78rem;">CNC (1x) & MIS Intraday (5x Leverage)</div>
        </div>
        """)

        prod_mode = st.radio("FinanceSight Product", ["CNC (Delivery)", "MIS (Intraday 5x)"], horizontal=True)
        order_type = st.radio("Order Type", ["MARKET", "LIMIT"], horizontal=True)
        qty = st.number_input("Quantity (Shares)", min_value=1, max_value=10000, value=10, step=1)
        exec_price = st.number_input("Limit Price", value=float(round(latest_c, 2))) if order_type == "LIMIT" else latest_c
        
        req_margin = (qty * exec_price) * (0.20 if "MIS" in prod_mode else 1.0)
        render_html(f"""
        <div class="fs-panel" style="padding:14px; border:1px solid #06b6d4; margin:10px 0; font-family:'JetBrains Mono',monospace; font-size:0.86rem;">
            <div style="display:flex; justify-content:space-between;"><span>Req. Margin:</span><b>₹{req_margin:,.2f}</b></div>
            <div style="display:flex; justify-content:space-between; margin-top:6px;"><span>Avail. Cash:</span><b style="color:#10b981;">₹{user_bal:,.2f}</b></div>
        </div>
        """)

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
        render_kpi("Technical Rating", verdict, f"14-Day RSI: {rsi_val:.1f}", "kpi-cyan", "#0284c7")

# ==========================================================
# 15. TAB 7: AI STOCK ADVISOR (AUTO-SWITCHING)
# ==========================================================
elif st.session_state.page == "Advisor":
    custom_q = st.chat_input("Ask anything! Try typing 'Hello', 'Apple', 'NVIDIA', 'Tesla', 'TCS', or 'What is RSI?'...")
    
    if custom_q:
        detected_sym, was_switched = detect_stock_from_text(custom_q, st.session_state.selected_ticker)
        if was_switched:
            st.session_state.selected_ticker = detected_sym

    ticker = st.session_state.selected_ticker
    meta = STOCK_CATALOG.get(ticker, {"name": ticker, "sector": "Equity", "domain": "google.com", "exchange": "NSE", "currency": "₹"})
    currency = meta["currency"]
    logo_url = get_logo_url(ticker)
    df = fetch_stock_history(ticker, "1y") if online_status else None
    if df is not None and len(df) >= 20:
        latest_c = float(df["Close"].iloc[-1])
        prev_c = float(df["Close"].iloc[-2])
        pct = ((latest_c - prev_c) / prev_c) * 100
        rsi_val = float(df["RSI"].iloc[-1])
        sma20_val = float(df["SMA_20"].iloc[-1])
        ema50_val = float(df["EMA_50"].iloc[-1])
        high_52 = float(df["High"].max())
        low_52 = float(df["Low"].min())
    else:
        snap_fallback = snapshots.get(ticker, {"price": 1000.0, "pct": 0.0, "rsi": 50.0})
        latest_c = snap_fallback["price"]
        pct = snap_fallback["pct"]
        rsi_val = snap_fallback["rsi"]
        sma20_val = latest_c * 0.99
        ema50_val = latest_c * 0.97
        high_52 = latest_c * 1.15
        low_52 = latest_c * 0.85

    render_html(f"""
    <div class="stock-card" style="border-left:5px solid #10b981; padding:22px 28px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:18px;">
            <img src="{logo_url}" class="company-logo-lg">
            <div>
                <span style="background:rgba(16,185,129,0.18); color:#10b981; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
                    🤖 CONVERSATIONAL MULTI-STOCK AI • AUTO-DETECTS ANY COMPANY IN CHAT
                </span>
                <h2 class="fs-title" style="margin:8px 0 4px 0;">🧠 FinanceSight AI Advisor — {meta['name']} ({ticker.replace('.NS','')})</h2>
                <p class="fs-muted" style="margin:0; font-size:0.9rem;">
                    Live Price: <b>{currency}{latest_c:,.2f} ({'▲' if pct >= 0 else '▼'} {pct:+.2f}%)</b> • 14-Day RSI: <b>{rsi_val:.1f}</b> • 20-DMA: <b>{currency}{sma20_val:,.2f}</b>
                </p>
            </div>
        </div>
    </div>
    """)

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
            render_html(f"""
            <div class="stock-card" style="border-left:4px solid #10b981; display:flex; align-items:center; gap:14px;">
                <img src="{item.get('logo', logo_url)}" class="company-logo">
                <div>
                    <div style="font-size:0.78rem; color:#0284c7; font-weight:700;">{item['stock']} • {item['badge']}</div>
                    <div class="fs-title" style="margin-top:3px; font-size:1.02rem;">🙋‍♂️ You asked: "{item['question']}"</div>
                </div>
            </div>
            """)
            st.markdown(item["answer"])
            st.markdown("---")

# ==========================================================
# 16. TAB 8: APPS (FINANCESIGHT ALGO BACKTESTER & SCANNER)
# ==========================================================
elif st.session_state.page == "Apps":
    render_html("""
    <div class="stock-card" style="border-left:5px solid #8b5cf6; padding:22px 28px; margin-bottom:20px;">
        <span style="background:rgba(139,92,246,0.18); color:#8b5cf6; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
            FINANCESIGHT APPS • v4 ALGO ENGINE
        </span>
        <h2 class="fs-title" style="margin:8px 0 4px 0;">🧩 FinanceSight Integrated Apps — Strategy Backtester & Scanner</h2>
        <p class="fs-muted" style="margin:0; font-size:0.9rem;">
            Build algorithmic trading rules without coding, backtest them on historical candles, and export CSV reports.
        </p>
    </div>
    """)

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

        bt_raw = fetch_stock_history(bt_symbol, "1y") if online_status else None
        if bt_raw is None or bt_raw.empty:
            st.warning("⚠️ Historical backtesting requires an active internet connection to fetch 1-year OHLC candles.")
            st.stop()
        bt_df = bt_raw.dropna().copy()
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
            render_kpi("Final Backtest Capital", f"₹{capital:,.2f}", f"{'▲' if total_ret >= 0 else '▼'} {total_ret:+.2f}% Net Return", "kpi-emerald" if total_ret >= 0 else "kpi-violet", "#10b981")
        with k2:
            render_kpi("Total Signals Triggered", f"{len(trades_log)} Trades", "1-Year Historical Sample", "kpi-cyan", "#0284c7")
        with k3:
            render_kpi("Strategy Win Rate", f"{win_rate:.1f}%", f"{wins} Winning Trades", "kpi-white", "#2563eb")
        with k4:
            render_kpi("Risk-Reward Ratio", f"1 : {target_pct/stop_loss_pct:.1f}", f"SL: {stop_loss_pct}% | TP: {target_pct}%", "kpi-violet", "#8b5cf6")

        eq_fig = go.Figure()
        eq_fig.add_trace(go.Scatter(
            x=bt_df.index, y=equity_curve, mode="lines", fill="tozeroy",
            name="Strategy Equity", line=dict(color="#0284c7", width=2.8),
            fillcolor="rgba(2, 132, 199, 0.14)"
        ))
        eq_fig.update_layout(
            title="📈 FinanceSight Backtest Equity Curve (Initial Capital: ₹1,00,000)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=370
        )
        st.plotly_chart(eq_fig, use_container_width=True)

        if trades_log:
            st.markdown("##### 📜 Simulated Backtest Trade Ledger")
            st.dataframe(pd.DataFrame(trades_log), use_container_width=True, hide_index=True)
            csv_bt = pd.DataFrame(trades_log).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Backtest Trade Report (CSV/Excel)",
                data=csv_bt,
                file_name=f"{bt_symbol}_financesight_backtest.csv",
                mime="text/csv"
            )

    with st_tab2:
        st.subheader("📡 Real-Time FinanceSight Market Scanner")
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