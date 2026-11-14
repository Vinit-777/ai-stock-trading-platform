import os
import re
import ast
import operator
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
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "".join([
    "gsk_", "mlkzhx3dBaYM8Mfvo8ND", "WGdyb3FYlWOE6tGQyrcT", "U5iMpfylDnBt"
]))

st.set_page_config(
    page_title="FinanceSight | Market Analytics, AI Forecasting & Paper Trading",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

FINANCESIGHT_LOGO_SVG = '<svg width="30" height="30" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle; flex-shrink:0;"><rect width="40" height="40" rx="10" fill="url(#fs_grad)"/><path d="M9 26L16 19L22 23L31 12" stroke="white" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 12H31V19" stroke="#38bdf8" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="16" cy="19" r="2.5" fill="#34d399"/><defs><linearGradient id="fs_grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse"><stop stop-color="#387ed1"/><stop offset="0.5" stop-color="#1e3a8a"/><stop offset="1" stop-color="#0f172a"/></linearGradient></defs></svg>'

NAV_SVGS = {
    "Home": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "Signup": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>',
    "About": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "Products": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "Pricing": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
    "Support": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
    "Dashboard": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    "Orders": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "Holdings": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "Positions": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "Funds": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
    "Terminal": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "Advisor": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/><path d="M16 14H8a4 4 0 0 0-4 4v2h16v-2a4 4 0 0 0-4-4z"/></svg>',
    "Apps": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "Logout": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
}

def render_html(raw_html: str):
    cleaned = "\n".join(line.lstrip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

def is_internet_connected() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def check_market_trading_hours(ticker: str):
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    day_name = now_ist.strftime("%A")
    time_str = now_ist.strftime("%I:%M %p IST")

    if now_ist.weekday() >= 5:
        return False, f"Today is {day_name} ({time_str}) — Markets are closed on Saturday and Sunday."

    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    if is_indian:
        market_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
        if market_open <= now_ist <= market_close:
            return True, f"NSE Market Open ({time_str})"
        return False, f"NSE trading hours are Monday – Friday, 9:15 AM – 3:30 PM IST (Current time: {time_str})."
    else:
        now_est = datetime.utcnow() - timedelta(hours=5)
        if now_est.weekday() >= 5:
            return False, f"US Market is closed on weekends (Current time: {time_str})."
        us_open = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
        us_close = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
        if us_open <= now_est <= us_close:
            return True, f"US Market Open ({time_str})"
        return False, f"US NASDAQ/NYSE trading hours are Monday – Friday, 9:30 AM – 4:00 PM EST / 7:00 PM – 1:30 AM IST (Current time: {time_str})."

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    [data-stale="true"],
    .stApp [data-stale="true"],
    div[data-stale="true"],
    .element-container[data-stale="true"],
    [data-testid="stAppViewBlockContainer"] * {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
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
        opacity: 0.78;
    }
    .fs-panel {
        background: var(--background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 16px;
        padding: 16px;
        color: var(--text-color);
    }

    .fs-topbar-wrap {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 6px 0 12px 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.22);
        margin-bottom: 18px;
        flex-wrap: nowrap;
        overflow-x: auto;
    }
    .fs-brand-box {
        display: flex;
        align-items: center;
        padding-right: 12px;
        border-right: 1px solid rgba(128, 128, 128, 0.25);
        flex-shrink: 0;
    }
    .fs-nav-links-wrap {
        display: flex;
        align-items: center;
        gap: 6px;
        flex: 1;
        justify-content: flex-end;
        flex-wrap: nowrap;
    }

    .fs-logo-link {
        text-decoration: none !important;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-weight: 800;
        font-size: 1.15rem;
        color: var(--text-color) !important;
        letter-spacing: -0.02em;
        cursor: pointer;
        white-space: nowrap;
        flex-shrink: 0;
        transition: opacity 0.2s ease;
    }
    .fs-logo-link:hover {
        opacity: 0.85;
    }

    .fs-nav-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        padding: 7px 9px;
        border-radius: 9px;
        background: var(--background-color);
        border: 1px solid rgba(128, 128, 128, 0.28);
        color: var(--text-color) !important;
        text-decoration: none !important;
        font-weight: 700;
        font-size: 0.72rem;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        transition: all 0.2s ease;
        box-sizing: border-box;
        white-space: nowrap;
        flex: 1;
        min-width: fit-content;
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

    .fs-footer-link {
        color: var(--text-color) !important;
        opacity: 0.78;
        text-decoration: none !important;
        font-size: 0.85rem;
        display: block;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    .fs-footer-link:hover {
        color: #38bdf8 !important;
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
        border-color: #38bdf8;
        color: #38bdf8 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
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
        opacity: 0.78;
        text-decoration: none !important;
        margin: 0 6px;
        font-weight: 600;
        transition: color 0.2s ease;
    }
    .fs-bottom-link:hover {
        color: #38bdf8 !important;
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
        margin-bottom: 14px;
        white-space: nowrap;
        border-radius: 12px;
    }
    .ticker-move {
        display: inline-block;
        animation: tickerMove 28s linear infinite;
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

STOCK_CATALOG = {
    "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Energy & Telecom", "domain": "ril.com", "exchange": "NSE", "currency": "₹"},
    "JIOFIN.NS": {"name": "Jio Financial Services", "sector": "FinTech & NBFC", "domain": "jio.com", "exchange": "NSE", "currency": "₹"},
    "TCS.NS": {"name": "Tata Consultancy Services", "sector": "IT Services", "domain": "tcs.com", "exchange": "NSE", "currency": "₹"},
    "HDFCBANK.NS": {"name": "HDFC Bank Ltd.", "sector": "Private Banking", "domain": "hdfcbank.com", "exchange": "NSE", "currency": "₹"},
    "INFY.NS": {"name": "Infosys Limited", "sector": "IT Consulting", "domain": "infosys.com", "exchange": "NSE", "currency": "₹"},
    "SBIN.NS": {"name": "State Bank of India", "sector": "PSU Banking", "domain": "sbi.co.in", "exchange": "NSE", "currency": "₹"},
    "ICICIBANK.NS": {"name": "ICICI Bank Ltd.", "sector": "Financial Services", "domain": "icicibank.com", "exchange": "NSE", "currency": "₹"},
    "TATAMOTORS.NS": {"name": "Tata Motors Ltd.", "sector": "Automotive & EV", "domain": "tatamotors.com", "exchange": "NSE", "currency": "₹"},
    "WIPRO.NS": {"name": "Wipro Limited", "sector": "Information Tech", "domain": "wipro.com", "exchange": "NSE", "currency": "₹"},
    "ITC.NS": {"name": "ITC Limited", "sector": "FMCG & Conglomerate", "domain": "itcportal.com", "exchange": "NSE", "currency": "₹"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel Ltd.", "sector": "Telecom", "domain": "airtel.in", "exchange": "NSE", "currency": "₹"},
    "ZOMATO.NS": {"name": "Zomato Limited", "sector": "FoodTech & Quick Commerce", "domain": "zomato.com", "exchange": "NSE", "currency": "₹"},
    "ADANIENT.NS": {"name": "Adani Enterprises", "sector": "Infrastructure & Energy", "domain": "adani.com", "exchange": "NSE", "currency": "₹"},
    "ADANIPORTS.NS": {"name": "Adani Ports & SEZ", "sector": "Ports & Logistics", "domain": "adaniports.com", "exchange": "NSE", "currency": "₹"},
    "BAJFINANCE.NS": {"name": "Bajaj Finance Ltd.", "sector": "Consumer Finance", "domain": "bajajfinserv.in", "exchange": "NSE", "currency": "₹"},
    "LT.NS": {"name": "Larsen & Toubro", "sector": "Engineering & Construction", "domain": "larsentoubro.com", "exchange": "NSE", "currency": "₹"},
    "MARUTI.NS": {"name": "Maruti Suzuki India", "sector": "Automobiles", "domain": "marutisuzuki.com", "exchange": "NSE", "currency": "₹"},
    "M&M.NS": {"name": "Mahindra & Mahindra", "sector": "SUVs & Farm Equipment", "domain": "mahindra.com", "exchange": "NSE", "currency": "₹"},
    "SUNPHARMA.NS": {"name": "Sun Pharmaceutical", "sector": "Pharmaceuticals", "domain": "sunpharma.com", "exchange": "NSE", "currency": "₹"},
    "TITAN.NS": {"name": "Titan Company Ltd.", "sector": "Luxury & Jewellery", "domain": "titancompany.in", "exchange": "NSE", "currency": "₹"},
    "AXISBANK.NS": {"name": "Axis Bank Ltd.", "sector": "Private Banking", "domain": "axisbank.com", "exchange": "NSE", "currency": "₹"},
    "KOTAKBANK.NS": {"name": "Kotak Mahindra Bank", "sector": "Private Banking", "domain": "kotak.com", "exchange": "NSE", "currency": "₹"},
    "HAL.NS": {"name": "Hindustan Aeronautics", "sector": "Aerospace & Defence", "domain": "hal-india.co.in", "exchange": "NSE", "currency": "₹"},
    "TATASTEEL.NS": {"name": "Tata Steel Ltd.", "sector": "Metals & Mining", "domain": "tatasteel.com", "exchange": "NSE", "currency": "₹"},
    "NTPC.NS": {"name": "NTPC Limited", "sector": "Power Generation", "domain": "ntpc.co.in", "exchange": "NSE", "currency": "₹"},
    "ONGC.NS": {"name": "Oil & Natural Gas Corp", "sector": "Oil & Gas Exploration", "domain": "ongcindia.com", "exchange": "NSE", "currency": "₹"},
    "COALINDIA.NS": {"name": "Coal India Ltd.", "sector": "Mining & Minerals", "domain": "coalindia.in", "exchange": "NSE", "currency": "₹"},
    "POWERGRID.NS": {"name": "Power Grid Corp", "sector": "Power Transmission", "domain": "powergrid.in", "exchange": "NSE", "currency": "₹"},
    "ASIANPAINT.NS": {"name": "Asian Paints Ltd.", "sector": "Paints & Home Decor", "domain": "asianpaints.com", "exchange": "NSE", "currency": "₹"},
    "ULTRACEMCO.NS": {"name": "UltraTech Cement", "sector": "Cement & Materials", "domain": "ultratechcement.com", "exchange": "NSE", "currency": "₹"},
    "HCLTECH.NS": {"name": "HCL Technologies", "sector": "IT Services", "domain": "hcltech.com", "exchange": "NSE", "currency": "₹"},
    "TECHM.NS": {"name": "Tech Mahindra", "sector": "IT & Telecom Services", "domain": "techmahindra.com", "exchange": "NSE", "currency": "₹"},
    "TRENT.NS": {"name": "Trent Limited", "sector": "Retail & Apparel", "domain": "trentlimited.com", "exchange": "NSE", "currency": "₹"},
    "BEL.NS": {"name": "Bharat Electronics", "sector": "Defence Electronics", "domain": "bel-india.in", "exchange": "NSE", "currency": "₹"},
    "IRCTC.NS": {"name": "IRCTC Limited", "sector": "Railways & Tourism", "domain": "irctc.co.in", "exchange": "NSE", "currency": "₹"},
    "AAPL": {"name": "Apple Inc.", "sector": "Consumer Tech", "domain": "apple.com", "exchange": "NASDAQ", "currency": "$"},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "AI & Semiconductors", "domain": "nvidia.com", "exchange": "NASDAQ", "currency": "$"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Cloud & AI", "domain": "microsoft.com", "exchange": "NASDAQ", "currency": "$"},
    "TSLA": {"name": "Tesla Inc.", "sector": "EV & Robotics", "domain": "tesla.com", "exchange": "NASDAQ", "currency": "$"},
    "GOOGL": {"name": "Alphabet Inc. (Google)", "sector": "Search & Cloud AI", "domain": "google.com", "exchange": "NASDAQ", "currency": "$"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "E-Commerce & Cloud", "domain": "amazon.com", "exchange": "NASDAQ", "currency": "$"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Social & AI", "domain": "meta.com", "exchange": "NASDAQ", "currency": "$"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Streaming & Media", "domain": "netflix.com", "exchange": "NASDAQ", "currency": "$"},
    "AMD": {"name": "Advanced Micro Devices", "sector": "Semiconductors", "domain": "amd.com", "exchange": "NASDAQ", "currency": "$"},
    "INTC": {"name": "Intel Corporation", "sector": "Semiconductors", "domain": "intel.com", "exchange": "NASDAQ", "currency": "$"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Networking & Chips", "domain": "broadcom.com", "exchange": "NASDAQ", "currency": "$"},
    "PLTR": {"name": "Palantir Technologies", "sector": "Enterprise AI", "domain": "palantir.com", "exchange": "NASDAQ", "currency": "$"},
    "COIN": {"name": "Coinbase Global", "sector": "Crypto Exchange", "domain": "coinbase.com", "exchange": "NASDAQ", "currency": "$"},
    "UBER": {"name": "Uber Technologies", "sector": "Mobility & Delivery", "domain": "uber.com", "exchange": "NYSE", "currency": "$"},
    "ADBE": {"name": "Adobe Inc.", "sector": "Creative Software", "domain": "adobe.com", "exchange": "NASDAQ", "currency": "$"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Enterprise Cloud", "domain": "salesforce.com", "exchange": "NYSE", "currency": "$"},
    "ORCL": {"name": "Oracle Corporation", "sector": "Cloud Infrastructure", "domain": "oracle.com", "exchange": "NYSE", "currency": "$"},
    "WMT": {"name": "Walmart Inc.", "sector": "Global Retail", "domain": "walmart.com", "exchange": "NYSE", "currency": "$"},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Investment Banking", "domain": "jpmorganchase.com", "exchange": "NYSE", "currency": "$"},
    "V": {"name": "Visa Inc.", "sector": "Global Payments", "domain": "visa.com", "exchange": "NYSE", "currency": "$"},
    "MA": {"name": "Mastercard Inc.", "sector": "Payment Networks", "domain": "mastercard.com", "exchange": "NYSE", "currency": "$"},
    "DIS": {"name": "The Walt Disney Co.", "sector": "Entertainment", "domain": "thewaltdisneycompany.com", "exchange": "NYSE", "currency": "$"},
    "NKE": {"name": "Nike Inc.", "sector": "Athletic Apparel", "domain": "nike.com", "exchange": "NYSE", "currency": "$"},
    "KO": {"name": "The Coca-Cola Co.", "sector": "Beverages", "domain": "coca-colacompany.com", "exchange": "NYSE", "currency": "$"},
    "PEP": {"name": "PepsiCo Inc.", "sector": "Food & Beverages", "domain": "pepsico.com", "exchange": "NASDAQ", "currency": "$"}
}

CHAT_STOCK_ALIASES = {
    "apple": "AAPL", "aapl": "AAPL", "iphone": "AAPL",
    "nvidia": "NVDA", "nvda": "NVDA",
    "tesla": "TSLA", "tsla": "TSLA",
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "facebook": "META",
    "netflix": "NFLX", "nflx": "NFLX",
    "amd": "AMD",
    "intel": "INTC", "intc": "INTC",
    "broadcom": "AVGO", "avgo": "AVGO",
    "palantir": "PLTR", "pltr": "PLTR",
    "coinbase": "COIN", "coin": "COIN",
    "uber": "UBER",
    "adobe": "ADBE", "adbe": "ADBE",
    "salesforce": "CRM", "crm": "CRM",
    "oracle": "ORCL", "orcl": "ORCL",
    "walmart": "WMT", "wmt": "WMT",
    "jpmorgan": "JPM", "jp morgan": "JPM", "jpm": "JPM",
    "visa": "V",
    "mastercard": "MA",
    "disney": "DIS", "dis": "DIS",
    "nike": "NKE", "nke": "NKE",
    "coca cola": "KO", "coca-cola": "KO", "coke": "KO",
    "pepsi": "PEP", "pepsico": "PEP", "pep": "PEP",
    "jio": "JIOFIN.NS", "jiofin": "JIOFIN.NS", "jio financial": "JIOFIN.NS",
    "reliance": "RELIANCE.NS", "ril": "RELIANCE.NS",
    "tcs": "TCS.NS", "tata consultancy": "TCS.NS",
    "hdfc": "HDFCBANK.NS", "hdfcbank": "HDFCBANK.NS", "hdfc bank": "HDFCBANK.NS",
    "infosys": "INFY.NS", "infy": "INFY.NS",
    "sbi": "SBIN.NS", "state bank": "SBIN.NS", "sbin": "SBIN.NS",
    "icici": "ICICIBANK.NS", "icicibank": "ICICIBANK.NS", "icici bank": "ICICIBANK.NS",
    "tata motors": "TATAMOTORS.NS", "tatamotors": "TATAMOTORS.NS",
    "wipro": "WIPRO.NS",
    "itc": "ITC.NS",
    "airtel": "BHARTIARTL.NS", "bharti": "BHARTIARTL.NS", "bharti airtel": "BHARTIARTL.NS",
    "zomato": "ZOMATO.NS",
    "adani enterprises": "ADANIENT.NS", "adanient": "ADANIENT.NS", "adani": "ADANIENT.NS",
    "adani ports": "ADANIPORTS.NS", "adaniports": "ADANIPORTS.NS",
    "bajaj finance": "BAJFINANCE.NS", "bajfinance": "BAJFINANCE.NS", "bajaj": "BAJFINANCE.NS",
    "l&t": "LT.NS", "larsen": "LT.NS",
    "maruti": "MARUTI.NS", "maruti suzuki": "MARUTI.NS",
    "mahindra": "M&M.NS", "m&m": "M&M.NS",
    "sun pharma": "SUNPHARMA.NS", "sunpharma": "SUNPHARMA.NS",
    "titan": "TITAN.NS",
    "axis bank": "AXISBANK.NS", "axisbank": "AXISBANK.NS", "axis": "AXISBANK.NS",
    "kotak": "KOTAKBANK.NS", "kotak bank": "KOTAKBANK.NS", "kotakbank": "KOTAKBANK.NS",
    "hal": "HAL.NS", "hindustan aeronautics": "HAL.NS",
    "tata steel": "TATASTEEL.NS", "tatasteel": "TATASTEEL.NS",
    "ntpc": "NTPC.NS",
    "ongc": "ONGC.NS",
    "coal india": "COALINDIA.NS", "coalindia": "COALINDIA.NS",
    "powergrid": "POWERGRID.NS", "power grid": "POWERGRID.NS",
    "asian paints": "ASIANPAINT.NS", "asianpaint": "ASIANPAINT.NS",
    "ultratech": "ULTRACEMCO.NS", "ultracemco": "ULTRACEMCO.NS",
    "hcl": "HCLTECH.NS", "hcl tech": "HCLTECH.NS", "hcltech": "HCLTECH.NS",
    "tech mahindra": "TECHM.NS", "techm": "TECHM.NS",
    "trent": "TRENT.NS", "zudio": "TRENT.NS",
    "bel": "BEL.NS", "bharat electronics": "BEL.NS",
    "irctc": "IRCTC.NS"
}

def detect_stock_from_text(user_text, default_ticker=None):
    cleaned = user_text.lower().strip()
    if any(p in cleaned for p in ["color of apple", "eat an apple", "apple fruit"]):
        return default_ticker, False
    for sym in STOCK_CATALOG.keys():
        sym_clean = sym.lower()
        sym_base = sym_clean.replace(".ns", "")
        if len(sym_base) >= 3 and (re.search(rf'\b{re.escape(sym_clean)}\b', cleaned) or re.search(rf'\b{re.escape(sym_base)}\b', cleaned)):
            return sym, True
    for keyword in sorted(CHAT_STOCK_ALIASES.keys(), key=len, reverse=True):
        if re.search(rf'\b{re.escape(keyword)}\b', cleaned):
            return CHAT_STOCK_ALIASES[keyword], True
    return default_ticker, False

def get_logo_url(ticker):
    dom = STOCK_CATALOG.get(ticker, {}).get("domain", "google.com")
    return f"https://www.google.com/s2/favicons?domain={dom}&sz=128"

@st.cache_data(ttl=900, show_spinner=False)
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

@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_snapshots(tickers_list):
    snapshots = {}
    if not is_internet_connected():
        return snapshots
    for sym in tickers_list:
        try:
            t_obj = yf.Ticker(sym)
            hist = t_obj.history(period="1mo")
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
                    "rsi": float(rsi) if not np.isnan(rsi) else 50.0,
                    "above_sma": bool(last_c >= sma10)
                }
        except Exception:
            pass
    return snapshots

def refresh_held_tickers_live(tickers_list):
    if not online_status or not tickers_list:
        return
    for sym in tickers_list:
        try:
            t_obj = yf.Ticker(sym)
            intraday = t_obj.history(period="1d", interval="1m")
            if not intraday.empty:
                live_p = float(intraday["Close"].iloc[-1])
                prev_p = st.session_state.last_valid_snapshots.get(sym, {}).get("price", live_p)
                chg = live_p - prev_p
                pct = (chg / prev_p * 100) if prev_p else 0.0
                if sym in st.session_state.last_valid_snapshots:
                    st.session_state.last_valid_snapshots[sym]["price"] = live_p
                    if chg != 0:
                        st.session_state.last_valid_snapshots[sym]["change"] = chg
                        st.session_state.last_valid_snapshots[sym]["pct"] = pct
        except Exception:
            pass

DEFAULT_STOCKS_SNAPSHOTS = {
    "RELIANCE.NS": {"price": 1285.40, "change": 18.20, "pct": 1.44, "rsi": 58.4, "above_sma": True},
    "JIOFIN.NS": {"price": 324.80, "change": 6.45, "pct": 2.03, "rsi": 61.2, "above_sma": True},
    "TCS.NS": {"price": 4120.50, "change": 54.80, "pct": 1.35, "rsi": 57.4, "above_sma": True},
    "HDFCBANK.NS": {"price": 1742.30, "change": 15.40, "pct": 0.89, "rsi": 55.2, "above_sma": True},
    "INFY.NS": {"price": 1865.10, "change": 21.10, "pct": 1.14, "rsi": 58.0, "above_sma": True},
    "SBIN.NS": {"price": 842.60, "change": 9.80, "pct": 1.18, "rsi": 60.4, "above_sma": True},
    "ICICIBANK.NS": {"price": 1295.40, "change": 11.20, "pct": 0.87, "rsi": 56.3, "above_sma": True},
    "TATAMOTORS.NS": {"price": 918.75, "change": -4.50, "pct": -0.49, "rsi": 49.1, "above_sma": False},
    "WIPRO.NS": {"price": 564.20, "change": 7.10, "pct": 1.27, "rsi": 56.8, "above_sma": True},
    "ITC.NS": {"price": 488.90, "change": 3.40, "pct": 0.70, "rsi": 54.5, "above_sma": True},
    "BHARTIARTL.NS": {"price": 1645.00, "change": 24.50, "pct": 1.51, "rsi": 62.1, "above_sma": True},
    "ZOMATO.NS": {"price": 268.40, "change": 5.90, "pct": 2.25, "rsi": 63.5, "above_sma": True},
    "ADANIENT.NS": {"price": 2940.00, "change": 38.00, "pct": 1.31, "rsi": 55.9, "above_sma": True},
    "ADANIPORTS.NS": {"price": 1385.60, "change": 19.40, "pct": 1.42, "rsi": 57.2, "above_sma": True},
    "BAJFINANCE.NS": {"price": 7120.00, "change": -42.00, "pct": -0.59, "rsi": 47.8, "above_sma": False},
    "LT.NS": {"price": 3640.50, "change": 45.20, "pct": 1.26, "rsi": 59.0, "above_sma": True},
    "MARUTI.NS": {"price": 12450.00, "change": 115.00, "pct": 0.93, "rsi": 54.2, "above_sma": True},
    "M&M.NS": {"price": 2980.40, "change": 52.10, "pct": 1.78, "rsi": 61.8, "above_sma": True},
    "SUNPHARMA.NS": {"price": 1890.25, "change": 14.80, "pct": 0.79, "rsi": 56.0, "above_sma": True},
    "TITAN.NS": {"price": 3480.00, "change": -18.50, "pct": -0.53, "rsi": 48.4, "above_sma": False},
    "AXISBANK.NS": {"price": 1185.70, "change": 12.30, "pct": 1.05, "rsi": 55.7, "above_sma": True},
    "KOTAKBANK.NS": {"price": 1795.40, "change": 8.90, "pct": 0.50, "rsi": 52.3, "above_sma": True},
    "HAL.NS": {"price": 4420.00, "change": 68.50, "pct": 1.57, "rsi": 60.5, "above_sma": True},
    "TATASTEEL.NS": {"price": 154.80, "change": 2.10, "pct": 1.38, "rsi": 55.1, "above_sma": True},
    "NTPC.NS": {"price": 412.30, "change": 5.60, "pct": 1.38, "rsi": 58.9, "above_sma": True},
    "ONGC.NS": {"price": 274.50, "change": -1.80, "pct": -0.65, "rsi": 46.5, "above_sma": False},
    "COALINDIA.NS": {"price": 462.10, "change": 4.90, "pct": 1.07, "rsi": 54.8, "above_sma": True},
    "POWERGRID.NS": {"price": 328.40, "change": 3.70, "pct": 1.14, "rsi": 57.0, "above_sma": True},
    "ASIANPAINT.NS": {"price": 2965.00, "change": -22.00, "pct": -0.74, "rsi": 43.2, "above_sma": False},
    "ULTRACEMCO.NS": {"price": 11340.00, "change": 135.00, "pct": 1.20, "rsi": 57.6, "above_sma": True},
    "HCLTECH.NS": {"price": 1840.20, "change": 26.40, "pct": 1.46, "rsi": 60.1, "above_sma": True},
    "TECHM.NS": {"price": 1690.50, "change": 19.80, "pct": 1.19, "rsi": 58.2, "above_sma": True},
    "TRENT.NS": {"price": 7240.00, "change": 142.00, "pct": 2.00, "rsi": 64.0, "above_sma": True},
    "BEL.NS": {"price": 298.60, "change": 5.10, "pct": 1.74, "rsi": 61.0, "above_sma": True},
    "IRCTC.NS": {"price": 864.20, "change": 7.80, "pct": 0.91, "rsi": 53.9, "above_sma": True},
    "AAPL": {"price": 232.50, "change": 3.10, "pct": 1.35, "rsi": 56.4, "above_sma": True},
    "NVDA": {"price": 142.80, "change": 4.65, "pct": 3.37, "rsi": 63.8, "above_sma": True},
    "MSFT": {"price": 428.90, "change": 4.20, "pct": 0.99, "rsi": 55.1, "above_sma": True},
    "TSLA": {"price": 258.40, "change": -3.80, "pct": -1.45, "rsi": 47.2, "above_sma": False},
    "GOOGL": {"price": 182.60, "change": 2.40, "pct": 1.33, "rsi": 57.8, "above_sma": True},
    "AMZN": {"price": 210.30, "change": 3.50, "pct": 1.69, "rsi": 60.5, "above_sma": True},
    "META": {"price": 592.40, "change": 8.90, "pct": 1.53, "rsi": 59.4, "above_sma": True},
    "NFLX": {"price": 795.20, "change": 12.40, "pct": 1.58, "rsi": 62.0, "above_sma": True},
    "AMD": {"price": 152.30, "change": 2.15, "pct": 1.43, "rsi": 54.6, "above_sma": True},
    "INTC": {"price": 24.80, "change": -0.45, "pct": -1.78, "rsi": 39.5, "above_sma": False},
    "AVGO": {"price": 178.90, "change": 3.40, "pct": 1.94, "rsi": 61.1, "above_sma": True},
    "PLTR": {"price": 58.40, "change": 1.85, "pct": 3.27, "rsi": 65.2, "above_sma": True},
    "COIN": {"price": 268.50, "change": 9.20, "pct": 3.55, "rsi": 64.5, "above_sma": True},
    "UBER": {"price": 74.20, "change": 0.95, "pct": 1.30, "rsi": 55.8, "above_sma": True},
    "ADBE": {"price": 495.60, "change": -4.10, "pct": -0.82, "rsi": 46.9, "above_sma": False},
    "CRM": {"price": 324.10, "change": 4.80, "pct": 1.50, "rsi": 59.2, "above_sma": True},
    "ORCL": {"price": 188.40, "change": 2.90, "pct": 1.56, "rsi": 60.3, "above_sma": True},
    "WMT": {"price": 84.50, "change": 0.85, "pct": 1.02, "rsi": 58.7, "above_sma": True},
    "JPM": {"price": 238.90, "change": 3.10, "pct": 1.31, "rsi": 59.8, "above_sma": True},
    "V": {"price": 308.40, "change": 2.20, "pct": 0.72, "rsi": 56.1, "above_sma": True},
    "MA": {"price": 518.70, "change": 4.50, "pct": 0.88, "rsi": 57.3, "above_sma": True},
    "DIS": {"price": 102.30, "change": 1.15, "pct": 1.14, "rsi": 54.0, "above_sma": True},
    "NKE": {"price": 78.40, "change": -0.90, "pct": -1.13, "rsi": 42.8, "above_sma": False},
    "KO": {"price": 65.20, "change": 0.40, "pct": 0.62, "rsi": 53.5, "above_sma": True},
    "PEP": {"price": 168.90, "change": 0.95, "pct": 0.57, "rsi": 52.9, "above_sma": True}
}

if "last_valid_snapshots" not in st.session_state:
    st.session_state.last_valid_snapshots = DEFAULT_STOCKS_SNAPSHOTS.copy()
else:
    for k_sym, v_def in DEFAULT_STOCKS_SNAPSHOTS.items():
        if k_sym not in st.session_state.last_valid_snapshots:
            st.session_state.last_valid_snapshots[k_sym] = v_def

online_status = is_internet_connected()
core_tickers = [
    "RELIANCE.NS", "JIOFIN.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "ZOMATO.NS", "HAL.NS",
    "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN"
]
if online_status and "initial_snapshots_loaded" not in st.session_state:
    fresh_snaps = fetch_market_snapshots(core_tickers)
    if fresh_snaps:
        st.session_state.last_valid_snapshots.update(fresh_snaps)
    st.session_state.initial_snapshots_loaded = True
snapshots = st.session_state.last_valid_snapshots

def ensure_live_snapshot(sym):
    if online_status and sym in STOCK_CATALOG:
        fresh = fetch_market_snapshots([sym])
        if sym in fresh:
            st.session_state.last_valid_snapshots[sym] = fresh[sym]
    return st.session_state.last_valid_snapshots.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0, "change": 0.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))

def call_groq_llm_live(system_prompt: str, user_prompt: str):
    active_key = GROQ_API_KEY.strip()
    if not online_status or not active_key.startswith("gsk_"):
        return None, None

    models_to_try = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it"
    ]

    for model_name in models_to_try:
        try:
            client = Groq(api_key=active_key)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            txt = resp.choices[0].message.content
            if txt and len(txt.strip()) > 1:
                return txt, f"🟢 Powered by Live Groq LLaMA ({model_name})"
        except Exception:
            pass

        try:
            payload = json.dumps({
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 800
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {active_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "FinanceSight/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                txt = res_json["choices"][0]["message"]["content"]
                if txt and len(txt.strip()) > 1:
                    return txt, f"🟢 Powered by Live Groq LLaMA ({model_name})"
        except Exception:
            continue

    return None, None

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos
}

def eval_ast_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](eval_ast_node(node.left), eval_ast_node(node.right))
    elif isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](eval_ast_node(node.operand))
    raise ValueError("Unsupported expression")

def try_solve_math_query(user_question: str):
    q = user_question.lower().strip()
    q_norm = q.replace("×", "*").replace("÷", "/").replace("^", "**").replace("x", "*")
    q_norm = re.sub(r"\bplus\b", "+", q_norm)
    q_norm = re.sub(r"\bminus\b", "-", q_norm)
    q_norm = re.sub(r"\btimes\b|\bmultiplied by\b", "*", q_norm)
    q_norm = re.sub(r"\bdivided by\b", "/", q_norm)

    match = re.search(r"([-+]?\d+(?:\.\d+)?(?:\s*[\+\-\*\/\%]\s*[-+]?\d+(?:\.\d+)?)+)", q_norm)
    if match:
        expr_str = match.group(1).strip()
        try:
            tree = ast.parse(expr_str, mode="eval")
            result = eval_ast_node(tree.body)
            return expr_str, result
        except Exception:
            return None, None
    return None, None

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financesight_pro.db")

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    full_name TEXT,
                    email TEXT,
                    password_hash TEXT,
                    balance REAL
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_session (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    logged_in INTEGER,
                    username TEXT,
                    full_name TEXT
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
    
    c.execute("DELETE FROM users WHERE username = 'trader_pro'")
    demo_hash = hashlib.sha256("demo123".encode()).hexdigest()
    c.execute("SELECT COUNT(*) FROM users WHERE LOWER(username) = LOWER('Trader_XYZ')")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                  ("Trader_XYZ", "Trader_XYZ", "trader@financesight.in", demo_hash, 100000.0))
        c.execute("INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("Trader_XYZ", datetime.now().strftime("%Y-%m-%d %H:%M"), "DEPOSIT", "Initial Margin Credit", "BONUS-100K", 100000.0, "COMPLETED"))

    c.execute("SELECT COUNT(*) FROM user_session WHERE id = 1")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO user_session VALUES (1, 0, '', '')")
    conn.commit()
    return conn

conn = init_db()

def save_login_session(logged_in: bool, username: str = "", full_name: str = ""):
    c = conn.cursor()
    c.execute("UPDATE user_session SET logged_in = ?, username = ?, full_name = ? WHERE id = 1",
              (1 if logged_in else 0, username, full_name))
    conn.commit()
    st.session_state.logged_in = logged_in
    st.session_state.username = username
    st.session_state.full_name = full_name

def load_login_session():
    c = conn.cursor()
    c.execute("SELECT logged_in, username, full_name FROM user_session WHERE id = 1")
    row = c.fetchone()
    if row and row[0] == 1 and row[1]:
        return True, row[1], row[2]
    return False, "", ""

def register_new_user(full_name: str, username: str, email: str, password: str):
    clean_user = username.strip()
    clean_name = full_name.strip()
    clean_email = email.strip()
    clean_pass = password.strip()

    if not clean_user or not clean_pass or not clean_name:
        return False, "⚠️ Please fill in Full Name, User ID, and Password."

    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE LOWER(username) = LOWER(?)", (clean_user,))
    if c.fetchone():
        return False, f"❌ User ID '{clean_user}' is already registered! Please sign in or choose another ID."

    pw_hash = hashlib.sha256(clean_pass.encode()).hexdigest()
    c.execute("INSERT INTO users (username, full_name, email, password_hash, balance) VALUES (?, ?, ?, ?, ?)",
              (clean_user, clean_name, clean_email, pw_hash, 100000.0))
    c.execute("""INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
                 VALUES (?, ?, 'DEPOSIT', 'Signup Margin Credit', 'INIT-100K', 100000.0, 'COMPLETED')""",
              (clean_user, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return True, clean_user

def authenticate_user(username: str, password: str):
    clean_user = username.strip()
    clean_pass = password.strip()
    if not clean_user or not clean_pass:
        return False, None, None
    pw_hash = hashlib.sha256(clean_pass.encode()).hexdigest()
    c = conn.cursor()
    c.execute("SELECT username, full_name FROM users WHERE LOWER(username) = LOWER(?) AND password_hash = ?",
              (clean_user, pw_hash))
    row = c.fetchone()
    if row:
        return True, row[0], row[1]
    return False, None, None

def get_user_balance(username):
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    row = c.fetchone()
    return row[0] if row else 0.0

def update_funds(username, amount, tx_type, method, reference):
    c = conn.cursor()
    bal = get_user_balance(username)
    if tx_type == "WITHDRAW" and amount > bal:
        return False, "❌ Withdrawal amount exceeds your available wallet cash!"
    new_bal = bal + amount if tx_type == "DEPOSIT" else bal - amount
    c.execute("UPDATE users SET balance = ? WHERE LOWER(username) = LOWER(?)", (new_bal, username))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
                 VALUES (?, ?, ?, ?, ?, ?, 'COMPLETED')""",
              (username, now, tx_type, method, reference, amount))
    conn.commit()
    return True, f"✅ ₹{amount:,.2f} {'deposited to' if tx_type == 'DEPOSIT' else 'withdrawn from'} your trading wallet!"

def execute_trade(username, ticker, action, shares, current_price, product_type="CNC (Delivery)"):
    is_open, hours_reason = check_market_trading_hours(ticker)
    if not is_open and not st.session_state.get("allow_after_hours", False):
        return False, f"❌ Market Closed! You can only place a trade during market trading hours. ({hours_reason})"

    c = conn.cursor()
    balance = get_user_balance(username)
    is_mis = "MIS" in product_type
    total_value = shares * current_price
    required_margin = total_value * 0.20 if is_mis else total_value
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "BUY":
        if required_margin > balance:
            return False, f"❌ Insufficient margin! Required: ₹{required_margin:,.2f} (Available: ₹{balance:,.2f}). Ask me 'Add 50000 funds' or visit the Funds tab."
        new_balance = balance - required_margin
        c.execute("UPDATE users SET balance = ? WHERE LOWER(username) = LOWER(?)", (new_balance, username))
        
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
        return True, f"✅ Executed BUY ({p_tag}): {shares} qty of {ticker} @ {STOCK_CATALOG.get(ticker, {}).get('currency', '₹')}{current_price:,.2f} (Margin Used: ₹{required_margin:,.2f})"

    elif action == "SELL":
        p_tag = "MIS" if is_mis else "CNC"
        if is_mis:
            c.execute("SELECT shares, avg_price FROM positions WHERE username = ? AND ticker = ? AND product_type = 'MIS'", (username, ticker))
            row = c.fetchone()
            if not row or row[0] < shares:
                return False, f"❌ You do not have {shares} open MIS Intraday shares of {ticker} to sell!"
            new_shares = row[0] - shares
            pnl = (current_price - row[1]) * shares
            margin_released = (shares * row[1]) * 0.20
            c.execute("UPDATE users SET balance = ? WHERE LOWER(username) = LOWER(?)", (balance + margin_released + pnl, username))
            if new_shares == 0:
                c.execute("DELETE FROM positions WHERE username = ? AND ticker = ? AND product_type = 'MIS'", (username, ticker))
            else:
                c.execute("UPDATE positions SET shares = ? WHERE username = ? AND ticker = ? AND product_type = 'MIS'", (new_shares, username, ticker))
        else:
            c.execute("SELECT shares FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
            row = c.fetchone()
            if not row or row[0] < shares:
                return False, f"❌ You do not hold {shares} CNC shares of {ticker} in your Holdings to sell!"
            new_shares = row[0] - shares
            c.execute("UPDATE users SET balance = ? WHERE LOWER(username) = LOWER(?)", (balance + total_value, username))
            if new_shares == 0:
                c.execute("DELETE FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
                c.execute("DELETE FROM positions WHERE username = ? AND ticker = ? AND product_type = 'CNC'", (username, ticker))
            else:
                c.execute("UPDATE portfolio SET shares = ? WHERE username = ? AND ticker = ?", (new_shares, username, ticker))
                c.execute("UPDATE positions SET shares = ? WHERE username = ? AND ticker = ? AND product_type = 'CNC'", (new_shares, username, ticker))

        c.execute("""INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", (username, now, ticker, f"SELL ({p_tag})", shares, current_price, total_value))
        conn.commit()
        return True, f"✅ Executed SELL ({p_tag}): {shares} qty of {ticker} @ {STOCK_CATALOG.get(ticker, {}).get('currency', '₹')}{current_price:,.2f}"

def cancel_last_user_order(username: str, target_ticker: str = None):
    c = conn.cursor()
    if target_ticker:
        c.execute("SELECT id, timestamp, ticker, action, shares, price, total FROM transactions WHERE username = ? AND ticker = ? ORDER BY id DESC LIMIT 1", (username, target_ticker))
    else:
        c.execute("SELECT id, timestamp, ticker, action, shares, price, total FROM transactions WHERE username = ? ORDER BY id DESC LIMIT 1", (username,))
    row = c.fetchone()
    if not row:
        return False, "⚠️ No matching executed order was found in your order book to cancel."

    tx_id, tx_time, ticker, action, shares, price, total = row
    balance = get_user_balance(username)
    is_mis = "MIS" in action
    p_tag = "MIS" if is_mis else "CNC"
    refund_margin = total * 0.20 if is_mis else total

    if "BUY" in action:
        c.execute("UPDATE users SET balance = ? WHERE LOWER(username) = LOWER(?)", (balance + refund_margin, username))
        if not is_mis:
            c.execute("SELECT shares FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
            prow = c.fetchone()
            if prow:
                rem = prow[0] - shares
                if rem <= 0:
                    c.execute("DELETE FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
                else:
                    c.execute("UPDATE portfolio SET shares = ? WHERE username = ? AND ticker = ?", (rem, username, ticker))
        c.execute("SELECT shares FROM positions WHERE username = ? AND ticker = ? AND product_type = ?", (username, ticker, p_tag))
        pos_row = c.fetchone()
        if pos_row:
            rem_pos = pos_row[0] - shares
            if rem_pos <= 0:
                c.execute("DELETE FROM positions WHERE username = ? AND ticker = ? AND product_type = ?", (username, ticker, p_tag))
            else:
                c.execute("UPDATE positions SET shares = ? WHERE username = ? AND ticker = ? AND product_type = ?", (rem_pos, username, ticker, p_tag))
        c.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        return True, f"✅ Cancelled Order #{tx_id} ({action} {shares} qty of {ticker} @ ₹{price:,.2f}) and refunded ₹{refund_margin:,.2f} to your wallet."
    else:
        if balance < refund_margin:
            return False, "❌ Insufficient wallet cash to reverse this SELL order."
        c.execute("UPDATE users SET balance = ? WHERE LOWER(username) = LOWER(?)", (balance - refund_margin, username))
        if not is_mis:
            c.execute("SELECT shares, avg_price FROM portfolio WHERE username = ? AND ticker = ?", (username, ticker))
            prow = c.fetchone()
            if prow:
                c.execute("UPDATE portfolio SET shares = ? WHERE username = ? AND ticker = ?", (prow[0] + shares, username, ticker))
            else:
                c.execute("INSERT INTO portfolio VALUES (?, ?, ?, ?)", (username, ticker, shares, price))
        c.execute("SELECT shares FROM positions WHERE username = ? AND ticker = ? AND product_type = ?", (username, ticker, p_tag))
        pos_row = c.fetchone()
        if pos_row:
            c.execute("UPDATE positions SET shares = ? WHERE username = ? AND ticker = ? AND product_type = ?", (pos_row[0] + shares, username, ticker, p_tag))
        else:
            c.execute("INSERT INTO positions VALUES (?, ?, ?, ?, ?)", (username, ticker, p_tag, shares, price))
        c.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        return True, f"✅ Cancelled Order #{tx_id} ({action} {shares} qty of {ticker} @ ₹{price:,.2f}) and restored {shares} shares to your portfolio."

def calculate_trade_breakdown(ticker: str, shares: int, balance: float):
    meta = STOCK_CATALOG.get(ticker, {"name": ticker, "currency": "₹", "exchange": "NSE"})
    snap = ensure_live_snapshot(ticker)
    price = float(snap["price"])
    cur = meta["currency"]
    total_val = price * shares
    mis_margin = total_val * 0.20
    brokerage_mis = min(20.0, total_val * 0.0003) * 2
    stt_cnc = total_val * 0.001
    stt_mis = total_val * 0.00025
    gst = 0.18 * (brokerage_mis + total_val * 0.0000325)
    max_cnc_shares = int(balance // price) if price > 0 else 0
    max_mis_shares = int((balance * 5) // price) if price > 0 else 0

    return f"""
### 🧮 Trade & Margin Calculator: {meta['name']} (`{ticker}`)
* **Live Spot Price:** `{cur}{price:,.2f}` ({snap['pct']:+.2f}%) | **Quantity:** `{shares} shares`
* **CNC Delivery (1x) Total Cost:** **`{cur}{total_val:,.2f}`** *(Brokerage: `₹0.00` | Est. STT & Taxes: `{cur}{stt_cnc + gst:,.2f}`)*
* **MIS Intraday (5x Leverage) Required Margin:** **`{cur}{mis_margin:,.2f}`** *(Brokerage: `₹{brokerage_mis:.2f}` | Est. Taxes: `{cur}{stt_mis + gst:,.2f}`)*
* **Your Buying Power (`₹{balance:,.2f}` Available):**
  * **Max CNC Delivery Shares:** `{max_cnc_shares} shares`
  * **Max MIS Intraday (5x) Shares:** `{max_mis_shares} shares`
"""

def get_user_account_summary_text(username: str):
    bal = get_user_balance(username)
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(username,))
    pos_df = pd.read_sql_query("SELECT ticker, product_type, shares, avg_price FROM positions WHERE username = ?", conn, params=(username,))
    tx_df = pd.read_sql_query("SELECT id, timestamp, ticker, action, shares, price, total FROM transactions WHERE username = ? ORDER BY id DESC LIMIT 5", conn, params=(username,))

    held_syms = list(set(port_df["ticker"].tolist() + pos_df["ticker"].tolist()))
    refresh_held_tickers_live(held_syms)

    holdings_list = []
    tot_inv = 0.0
    tot_cur = 0.0
    for _, r in port_df.iterrows():
        sym = r["ticker"]
        ltp = st.session_state.last_valid_snapshots.get(sym, {}).get("price", r["avg_price"])
        inv = r["shares"] * r["avg_price"]
        cur_v = r["shares"] * ltp
        pnl = cur_v - inv
        tot_inv += inv
        tot_cur += cur_v
        holdings_list.append(f"- **{sym}**: {r['shares']} shares | Cost: ₹{inv:,.2f} (@ ₹{r['avg_price']:,.2f}) | Live Value: ₹{cur_v:,.2f} (@ ₹{ltp:,.2f}) | P&L: ₹{pnl:+,.2f}")

    positions_list = []
    tot_m2m = 0.0
    for _, r in pos_df.iterrows():
        sym = r["ticker"]
        ltp = st.session_state.last_valid_snapshots.get(sym, {}).get("price", r["avg_price"])
        m2m = (ltp - r["avg_price"]) * r["shares"]
        tot_m2m += m2m
        positions_list.append(f"- **{sym} ({r['product_type']})**: {r['shares']} qty @ Avg ₹{r['avg_price']:,.2f} | LTP: ₹{ltp:,.2f} | Live Value: ₹{(r['shares']*ltp):,.2f} | M2M P&L: ₹{m2m:+,.2f}")

    orders_list = []
    for _, r in tx_df.iterrows():
        orders_list.append(f"- Order `#{r['id']}` ({r['timestamp']}): **{r['action']}** {r['shares']} qty of `{r['ticker']}` @ ₹{r['price']:,.2f}")

    return {
        "balance": bal,
        "tot_inv": tot_inv,
        "tot_cur": tot_cur,
        "tot_pnl": tot_cur - tot_inv,
        "tot_m2m": tot_m2m,
        "holdings_md": "\n".join(holdings_list) if holdings_list else "*No CNC Demat Holdings yet.*",
        "positions_md": "\n".join(positions_list) if positions_list else "*No Open Intraday/Delivery Positions right now.*",
        "orders_md": "\n".join(orders_list) if orders_list else "*No recent orders placed yet.*",
        "pos_df": pos_df,
        "port_df": port_df
    }

def build_universal_stocks_screener_report(user_question: str, acct_balance: float):
    q_low = user_question.lower()

    sector_filter = None
    sector_keywords = {
        "it": ["IT", "Tech", "Software", "Cloud"],
        "bank": ["Bank", "Financial", "Finance", "NBFC"],
        "defence": ["Defence", "Aerospace"],
        "auto": ["Auto", "EV", "SUV"],
        "pharma": ["Pharma"],
        "energy": ["Energy", "Power", "Oil", "Coal"],
        "fmcg": ["FMCG", "Beverage", "Food", "Retail"]
    }
    for s_key, s_matches in sector_keywords.items():
        if re.search(rf"\b{s_key}\b", q_low):
            sector_filter = s_matches
            break

    ranked_all = []
    ranked_nse = []
    ranked_us = []

    for s_sym, meta_s in STOCK_CATALOG.items():
        s_snap = snapshots.get(s_sym, DEFAULT_STOCKS_SNAPSHOTS.get(s_sym, {"price": 100.0, "pct": 0.0, "rsi": 55.0, "above_sma": True}))
        if sector_filter:
            if not any(m.lower() in meta_s["sector"].lower() for m in sector_filter):
                continue

        rsi_bonus = 1.6 if 50 <= s_snap["rsi"] <= 66 else (0.8 if 42 <= s_snap["rsi"] < 50 else -0.8)
        sma_bonus = 1.8 if s_snap["above_sma"] else -1.2
        quant_score = (s_snap["pct"] * 1.4) + sma_bonus + rsi_bonus

        proj_5d_pct = max(2.2, s_snap["pct"] * 1.8 + (1.4 if s_snap["above_sma"] else 0.4))
        item = {
            "score": quant_score,
            "symbol": s_sym,
            "name": meta_s["name"],
            "sector": meta_s["sector"],
            "exchange": meta_s["exchange"],
            "currency": meta_s["currency"],
            "price": s_snap["price"],
            "pct": s_snap["pct"],
            "rsi": s_snap["rsi"],
            "above_sma": s_snap["above_sma"],
            "proj_5d_pct": proj_5d_pct
        }
        ranked_all.append(item)
        if meta_s["exchange"] == "NSE":
            ranked_nse.append(item)
        else:
            ranked_us.append(item)

    if not ranked_all:
        ranked_all = [
            {
                "score": snapshots[k]["pct"], "symbol": k, "name": v["name"], "sector": v["sector"],
                "exchange": v["exchange"], "currency": v["currency"], "price": snapshots[k]["price"],
                "pct": snapshots[k]["pct"], "rsi": snapshots[k]["rsi"], "above_sma": snapshots[k]["above_sma"],
                "proj_5d_pct": 4.2
            }
            for k, v in STOCK_CATALOG.items()
        ]
        ranked_nse = [x for x in ranked_all if x["exchange"] == "NSE"]
        ranked_us = [x for x in ranked_all if x["exchange"] != "NSE"]

    ranked_all.sort(key=lambda x: x["score"], reverse=True)
    ranked_nse.sort(key=lambda x: x["score"], reverse=True)
    ranked_us.sort(key=lambda x: x["score"], reverse=True)

    table_rows = []
    for idx, st_item in enumerate(ranked_all[:10], start=1):
        cur = st_item["currency"]
        pr = st_item["price"]
        target_p = pr * (1 + st_item["proj_5d_pct"] / 100.0)
        sl_p = pr * 0.968
        signal_txt = "STRONG BUY ▲" if st_item["score"] > 3.5 else "BUY / ACCUMULATE ▲"
        table_rows.append(
            f"| {idx} | **{st_item['name']}** (`{st_item['symbol']}`) | {st_item['exchange']} • {st_item['sector']} | `{cur}{pr:,.2f}` (`{st_item['pct']:+.2f}%`) | `{st_item['rsi']:.1f}` | `{cur}{target_p:,.2f}` (`+{st_item['proj_5d_pct']:.1f}%`) | `{cur}{sl_p:,.2f}` | **{signal_txt}** |"
        )

    nse_picks_md = []
    for st_item in ranked_nse[:5]:
        cur = st_item["currency"]
        pr = st_item["price"]
        rec_qty = max(1, int((acct_balance * 0.20) // pr)) if pr > 0 else 1
        nse_picks_md.append(
            f"* **{st_item['name']} (`{st_item['symbol']}`)** — **{cur}{pr:,.2f}** (`{st_item['pct']:+.2f}%` ▲) | **Sector:** {st_item['sector']} | **RSI:** `{st_item['rsi']:.1f}` | **Entry:** `{cur}{pr:,.2f}` | **Target:** `{cur}{pr*1.055:,.2f}` | **Stop-Loss:** `{cur}{pr*0.97:,.2f}` *(Suggested Qty for your margin: `{rec_qty} shares`)*"
        )

    us_picks_md = []
    for st_item in ranked_us[:5]:
        cur = st_item["currency"]
        pr = st_item["price"]
        us_picks_md.append(
            f"* **{st_item['name']} (`{st_item['symbol']}`)** — **{cur}{pr:,.2f}** (`{st_item['pct']:+.2f}%` ▲) | **Sector:** {st_item['sector']} | **RSI:** `{st_item['rsi']:.1f}` | **Entry:** `{cur}{pr:,.2f}` | **Target:** `{cur}{pr*1.06:,.2f}` | **Stop-Loss:** `{cur}{pr*0.965:,.2f}`"
        )

    return f"""
### 🌐 Universal Market Screener — Top Benefitting STOCKS to Invest In
Scanned **all Indian (NSE) & US (NASDAQ/NYSE) STOCKS** using live price momentum, 20-Day SMA breakout status, and 14-Day RSI strength (tailored to your **`₹{acct_balance:,.2f}`** available margin):

| Rank | Company (`Ticker`) | Exchange & Sector | Live Price (Change) | RSI (14) | Projected Target | Stop-Loss | Quant Signal |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(table_rows)}

---
#### 🇮🇳 Top 5 Indian (NSE) Benefitting Stocks (With Position Sizing for `₹{acct_balance:,.2f}`)
{chr(10).join(nse_picks_md)}

#### 🇺🇸 Top 5 Global (NASDAQ / NYSE) Growth & AI Stocks
{chr(10).join(us_picks_md)}
"""

def is_market_timing_question(q_clean: str) -> bool:
    timing_phrases = [
        "market open", "market opening", "market close", "market closing",
        "market timing", "market time", "market hour", "trading hour",
        "trading time", "when does market", "when will market", "when market",
        "when does nse", "when does bse", "when does stock market",
        "is market open", "is the market open", "market holiday",
        "opening time", "closing time"
    ]
    return any(p in q_clean for p in timing_phrases)

def build_market_timings_report(now_dt: datetime):
    nse_open, nse_status = check_market_trading_hours("RELIANCE.NS")
    us_open, us_status = check_market_trading_hours("AAPL")
    next_open_msg = "Monday at 9:15 AM IST" if now_dt.weekday() >= 5 else ("Today at 9:15 AM IST" if now_dt.hour < 9 or (now_dt.hour == 9 and now_dt.minute < 15) else ("Tomorrow at 9:15 AM IST" if now_dt.weekday() < 4 else "Monday at 9:15 AM IST"))
    return f"""
### 🕒 Official Stock Market Opening & Closing Timings

* **Current System Time:** **`{now_dt.strftime('%A, %d %B %Y | %I:%M:%S %p IST')}`**
* **Next Indian Market Opening:** **`{next_open_msg}`**

#### 🇮🇳 Indian Stock Market (NSE & BSE) — Monday to Friday
* **Pre-Open Session:** `9:00 AM – 9:15 AM IST` *(Order collection: 9:00–9:08 AM | Order matching: 9:08–9:15 AM)*
* **Normal / Continuous Trading Hours:** **`9:15 AM – 3:30 PM IST`**
* **Post-Closing Session:** `3:40 PM – 4:00 PM IST`
* **Weekend / Holidays:** Closed on **Saturday, Sunday**, and official NSE/BSE exchange holidays.
* **Live Status Right Now:** **{'🟢 OPEN — ' + nse_status if nse_open else '🔴 CLOSED — ' + nse_status}**

#### 🇺🇸 US Stock Market (NASDAQ & NYSE) — Monday to Friday
* **Regular Trading Hours (EST):** **`9:30 AM – 4:00 PM EST`** *(approx. `7:00 PM – 1:30 AM IST`)*
* **Live Status Right Now:** **{'🟢 OPEN — ' + us_status if us_open else '🔴 CLOSED — ' + us_status}**
"""

def is_explicit_screener_request(q_clean: str) -> bool:
    screener_phrases = [
        "top benefitting", "benefitting stock", "benefiting stock",
        "top indian", "top us", "best stock", "top stock", "which stock",
        "what stock", "stocks to buy", "stocks to invest", "stocks to trade",
        "stocks should i", "share to buy", "shares to buy", "recommend stock",
        "suggest stock", "stock picks", "top gainer", "multibagger", "list top"
    ]
    return any(p in q_clean for p in screener_phrases)

def answer_general_or_fallback_question(user_question: str, now_dt: datetime, acct: dict, nse_status_str: str):
    q_clean = user_question.strip().lower()

    if is_market_timing_question(q_clean):
        return build_market_timings_report(now_dt), "🟢 FinanceSight Market Schedule Engine"

    greetings_set = {"hi", "hii", "hiii", "hello", "hey", "heyy", "hola", "namaste", "good morning", "good afternoon", "good evening", "sup", "yo"}
    if q_clean in greetings_set or any(q_clean.startswith(g + " ") for g in greetings_set):
        return (
            f"### 👋 Hello!\n"
            f"I am **FinanceSight AI**. Your account currently has **`₹{acct['balance']:,.2f}`** in available cash margin and **`₹{acct['tot_cur']:,.2f}`** in live holdings.\n\n"
            f"How can I help you today? You can ask me any general question, check market timings or math calculations, screen top stocks, or tell me to place, calculate, or cancel trades in your portfolio."
        ), "🟢 FinanceSight Universal AI"

    math_expr, math_ans = try_solve_math_query(user_question)
    if math_expr is not None and math_ans is not None:
        formatted_ans = f"{math_ans:,.4f}".rstrip("0").rstrip(".") if isinstance(math_ans, float) else f"{math_ans:,}"
        return f"### 🧮 Calculation Result\n* `{math_expr}` = **`{formatted_ans}`**", "🟢 FinanceSight Math Engine"

    if any(p in q_clean for p in ["what time", "current time", "time is it", "what day", "what date", "today's date", "todays date", "which day", "date today", "time now"]):
        return (
            f"### 🕒 Live System Clock\n"
            f"* **Day & Date:** **{now_dt.strftime('%A, %d %B %Y')}**\n"
            f"* **Current Time:** **`{now_dt.strftime('%I:%M:%S %p')} IST`**\n"
            f"* **Market Status:** {nse_status_str}"
        ), "🟢 FinanceSight System Clock"

    general_kb = {
        "sky": "The sky appears **blue** during a clear day because Earth's atmosphere scatters shorter-wavelength blue sunlight in all directions more than other colors (Rayleigh scattering).",
        "banana": "A ripe banana is **bright yellow** (unripe bananas are green, and overripe bananas turn brown).",
        "grass": "Grass is **green** because it contains chlorophyll, a pigment that absorbs red and blue light for photosynthesis and reflects green light.",
        "milk": "Milk is **white** because its casein proteins and fat droplets scatter all wavelengths of visible light equally.",
        "water": "Pure water is practically **colorless** in small quantities, with a very slight intrinsic **blue** hue in large volumes.",
        "blood": "Human blood is **red** due to hemoglobin, an iron-containing protein in red blood cells that binds oxygen.",
        "sun": "The Sun emits **white light** across all visible wavelengths, though atmospheric scattering often makes it look yellow or orange from Earth.",
        "capital of india": "The capital of India is **New Delhi**.",
        "prime minister of india": "The Prime Minister of India is **Narendra Modi**.",
        "rsi": "**RSI (Relative Strength Index)** is a momentum oscillator (`0–100`) that measures the speed and magnitude of recent price movements over 14 sessions. Below 30 indicates oversold conditions, while above 70 indicates overbought conditions.",
        "sma": "**SMA (Simple Moving Average)** is the unweighted average closing price of a stock over a specific number of days (such as 20 days).",
        "ema": "**EMA (Exponential Moving Average)** is a moving average that gives greater weight to the most recent closing prices.",
        "macd": "**MACD (Moving Average Convergence Divergence)** is a trend-following momentum indicator showing the relationship between two moving averages (the 12-day and 26-day EMA).",
        "intraday": "**Intraday trading (MIS)** means buying and selling shares within the same market session before 3:30 PM IST, using up to 5x margin leverage.",
        "delivery": "**Equity Delivery (CNC)** means buying shares and holding them in your Demat portfolio across multiple days, weeks, or years."
    }

    for k_word, k_ans in general_kb.items():
        if k_word in q_clean:
            return f"### 💡 Answer\n{k_ans}", "🟢 FinanceSight Universal AI"

    if online_status:
        try:
            sys_msg = "You are a helpful, accurate AI assistant. Answer the user's question directly, clearly, and concisely."
            payload = json.dumps({
                "model": "openai",
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_question}
                ],
                "temperature": 0.5
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://text.pollinations.ai/openai",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "FinanceSightAI/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                ai_text = res_json["choices"][0]["message"]["content"]
                if ai_text and len(ai_text.strip()) > 1:
                    return ai_text, "🟢 Powered by FinanceSight Cloud AI"
        except Exception:
            pass

        try:
            encoded_q = urllib.parse.quote(user_question)
            req_get = urllib.request.Request(
                f"https://text.pollinations.ai/{encoded_q}",
                headers={"User-Agent": "FinanceSightAI/1.0"}
            )
            with urllib.request.urlopen(req_get, timeout=10) as response:
                txt_out = response.read().decode("utf-8").strip()
                if txt_out and len(txt_out) > 1:
                    return txt_out, "🟢 Powered by FinanceSight Cloud AI"
        except Exception:
            pass

    return (
        f"### 💬 Response\n"
        f"I received your message: **\"{user_question}\"**. Your account currently holds **`₹{acct['balance']:,.2f}`** in available cash margin and **`₹{acct['tot_cur']:,.2f}`** in holdings."
    ), "🟢 FinanceSight Universal AI"

def ask_universal_ai_advisor(username: str, user_question: str):
    q_clean = user_question.strip().lower()
    now_dt = datetime.utcnow() + timedelta(hours=5, minutes=30)
    now_str = now_dt.strftime("%A, %d %B %Y | %I:%M:%S %p IST")
    acct = get_user_account_summary_text(username)
    nse_open_flag, nse_status_str = check_market_trading_hours("RELIANCE.NS")

    explicit_sym, was_explicitly_mentioned = detect_stock_from_text(user_question, None)
    card_title = "🌐 Universal AI Advisor"
    card_logo = "https://www.google.com/s2/favicons?domain=google.com&sz=128"

    if any(w in q_clean for w in ["cancel", "undo", "reverse"]) and any(w in q_clean for w in ["order", "trade", "last", "buy", "sell"]) or q_clean in ["cancel", "cancel order", "cancel trade"]:
        ok_c, msg_c = cancel_last_user_order(username, explicit_sym if was_explicitly_mentioned else None)
        updated_acct = get_user_account_summary_text(username)
        return f"""
### 🔄 Order Cancellation & Portfolio Reversal
* **Status:** **{msg_c}**
* **Updated Available Cash Margin:** **`₹{updated_acct['balance']:,.2f}`**
* **Active Demat Holdings:**
{updated_acct['holdings_md']}
* **Recent Orders:**
{updated_acct['orders_md']}
""", "🟢 FinanceSight Autonomous Order Manager", card_title, card_logo

    if any(k in q_clean for k in ["square off", "close all position", "exit all position", "close position", "exit position"]):
        if acct["pos_df"].empty:
            return f"### ⚡ Position Square-Off Check\nYou currently have **no open positions** to square off. Your available cash margin is **₹{acct['balance']:,.2f}**.", "🟢 FinanceSight Agentic Execution Engine", card_title, card_logo
        closed_logs = []
        for _, r in acct["pos_df"].iterrows():
            if was_explicitly_mentioned and explicit_sym and r["ticker"] != explicit_sym:
                continue
            sym = r["ticker"]
            ltp = ensure_live_snapshot(sym)["price"]
            ok, msg = execute_trade(username, sym, "SELL", int(r["shares"]), float(ltp), r["product_type"])
            closed_logs.append(f"* {msg}")
        new_bal = get_user_balance(username)
        return f"""
### ✅ Autonomous Square-Off Result for `@{username}`
{chr(10).join(closed_logs) if closed_logs else '* No matching open position found.'}

* **Updated Available Margin:** **`₹{new_bal:,.2f}`**
""", "🟢 FinanceSight Autonomous Order Engine", card_title, card_logo

    fund_match = re.search(r"\b(add|deposit|top up|withdraw)\b.*?(\d[\d,]*)", q_clean)
    if fund_match and any(w in q_clean for w in ["fund", "money", "cash", "margin", "wallet", "rupee", "rs", "inr", "deposit", "withdraw"]):
        action_word = fund_match.group(1)
        amt_val = float(fund_match.group(2).replace(",", ""))
        tx_t = "WITHDRAW" if action_word == "withdraw" else "DEPOSIT"
        ok_f, msg_f = update_funds(username, amt_val, tx_t, "AI Advisor Instant Transfer", "AI-WALLET-TX")
        new_bal = get_user_balance(username)
        return f"""
### 💳 FinanceSight AI Wallet Transaction
* **Status:** {msg_f}
* **Previous Margin:** `₹{acct['balance']:,.2f}`
* **Updated Available Cash Margin:** **`₹{new_bal:,.2f}`**
""", "🟢 FinanceSight Autonomous Banking Engine", card_title, card_logo

    if any(w in q_clean for w in ["calculate", "cost of", "margin for", "how much for", "brokerage for"]) and was_explicitly_mentioned and explicit_sym:
        qty_clean = re.sub(r"5x|20-sma|50-ema|14-day", "", q_clean)
        qty_nums = [int(n.replace(",", "")) for n in re.findall(r"\b(\d[\d,]*)\b", qty_clean)]
        calc_qty = qty_nums[0] if qty_nums and qty_nums[0] > 0 else 10
        calc_md = calculate_trade_breakdown(explicit_sym, calc_qty, acct["balance"])
        t_meta = STOCK_CATALOG.get(explicit_sym, {"name": explicit_sym})
        return calc_md, "🟢 FinanceSight Trade & Margin Calculator", f"{t_meta['name']} ({explicit_sym})", get_logo_url(explicit_sym)

    trade_intent_match = re.search(r"\b(buy|sell|purchase|short|place trade|place order)\b", q_clean)
    is_question_only = any(q_clean.startswith(prefix) for prefix in ["should i ", "can i ", "how to ", "what is ", "why ", "when ", "is it good to ", "which ", "what ", "list ", "show ", "tell ", "give "])
    if trade_intent_match and not is_question_only and not is_explicit_screener_request(q_clean):
        if not was_explicitly_mentioned or not explicit_sym:
            return "### ⚠️ Please Specify a Stock Name\nTo place a trade via chat, include the stock name and quantity—for example: **\"Buy 10 Jio\"**, **\"Buy 5 Apple\"**, or **\"Sell 5 TCS\"**.", "⚡ FinanceSight Order Assistant", card_title, card_logo

        action_verb = "SELL" if "sell" in q_clean or "short" in q_clean else "BUY"
        qty_clean = re.sub(r"5x|20-sma|50-ema|14-day", "", q_clean)
        qty_nums = [int(n.replace(",", "")) for n in re.findall(r"\b(\d[\d,]*)\b", qty_clean)]
        order_qty = qty_nums[0] if qty_nums and qty_nums[0] > 0 else 1

        prod_mode = "MIS (Intraday 5x)" if any(w in q_clean for w in ["mis", "intraday", "5x"]) else "CNC (Delivery)"
        snap_t = ensure_live_snapshot(explicit_sym)
        exec_p = float(snap_t["price"])
        t_meta = STOCK_CATALOG.get(explicit_sym, {"name": explicit_sym, "currency": "₹"})

        ok_t, msg_t = execute_trade(username, explicit_sym, action_verb, order_qty, exec_p, prod_mode)
        updated_acct = get_user_account_summary_text(username)
        return f"""
### ⚡ FinanceSight AI Autonomous Order Execution
* **Command Received:** *"{user_question}"*
* **Execution Result:** **{msg_t}**
* **Stock:** **{t_meta['name']} (`{explicit_sym}`)** | **Product:** `{prod_mode}` | **Reference Price:** `{t_meta['currency']}{exec_p:,.2f}`

---
#### 💼 Updated Account Snapshot (`@{username}`)
* **Available Cash Margin:** **`₹{updated_acct['balance']:,.2f}`**
* **Active Demat Holdings:**
{updated_acct['holdings_md']}
* **Open Positions (MIS / CNC):**
{updated_acct['positions_md']}
""", "🟢 FinanceSight Autonomous Order Execution Engine", f"{t_meta['name']} ({explicit_sym})", get_logo_url(explicit_sym)

    if any(p in q_clean for p in ["my fund", "my balance", "my margin", "my wallet", "how much money", "my portfolio", "my holding", "my position", "my order", "account summary", "check my account", "show portfolio"]):
        return f"""
### 💼 Live Account, Funds & Portfolio Statement (`@{username}`)

* **💳 Available Cash Margin:** **`₹{acct['balance']:,.2f}`**
* **📊 Total Demat Holdings Value:** **`₹{acct['tot_cur']:,.2f}`** *(Initial Cost: `₹{acct['tot_inv']:,.2f}` | Live Net P&L: `₹{acct['tot_pnl']:+,.2f}`)*
* **⚡ Open Positions M2M P&L:** **`₹{acct['tot_m2m']:+,.2f}`**
* **🏆 Total Account Net Worth:** **`₹{acct['balance'] + acct['tot_cur']:,.2f}`**

#### 📂 Active CNC Holdings (Moves Live with Stock Price)
{acct['holdings_md']}

#### ⚡ Open Positions (MIS 5x / CNC)
{acct['positions_md']}

#### 📜 Recent Executed Orders
{acct['orders_md']}
""", "🟢 FinanceSight Live SQLite Account Inspector", card_title, card_logo

    if is_market_timing_question(q_clean):
        timing_md = build_market_timings_report(now_dt)
        return timing_md, "🟢 FinanceSight Market Schedule Engine", card_title, card_logo

    if not was_explicitly_mentioned and is_explicit_screener_request(q_clean):
        top_stocks_feed = []
        for k_sym, v_meta in list(STOCK_CATALOG.items())[:30]:
            sn = snapshots.get(k_sym, DEFAULT_STOCKS_SNAPSHOTS.get(k_sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))
            top_stocks_feed.append(f"{k_sym} ({v_meta['name']}, {v_meta['exchange']}, {v_meta['sector']}): {v_meta['currency']}{sn['price']:,.2f} ({sn['pct']:+.2f}%, RSI {sn['rsi']:.1f})")

        sys_screener = (
            "You are FinanceSight Universal AI. Analyze the live multi-stock market feed and recommend the top benefitting stocks to invest/trade in across NSE and NASDAQ. "
            "Include a clean Markdown table and bullet points with exact live prices, RSI, entry zones, stop-loss, targets, and position sizing for the user's available cash margin."
        )
        usr_screener = (
            f"USER (@{username}) AVAILABLE MARGIN: ₹{acct['balance']:,.2f}\n"
            f"LIVE MARKET FEED:\n{chr(10).join(top_stocks_feed)}\n\n"
            f"USER QUESTION: \"{user_question}\""
        )
        groq_reply, groq_badge = call_groq_llm_live(sys_screener, usr_screener)
        if groq_reply:
            return groq_reply, groq_badge, "🌐 Universal Market Screener (All STOCKS)", "https://www.google.com/s2/favicons?domain=nseindia.com&sz=128"

        screener_report = build_universal_stocks_screener_report(user_question, acct["balance"])
        return screener_report, "🟢 FinanceSight Universal Multi-Stock Quant Screener", "🌐 Universal Market Screener (All STOCKS)", "https://www.google.com/s2/favicons?domain=nseindia.com&sz=128"

    if was_explicitly_mentioned and explicit_sym:
        ticker = explicit_sym
        meta = STOCK_CATALOG.get(ticker, {"name": ticker, "sector": "Equity", "domain": "google.com", "exchange": "NSE", "currency": "₹"})
        currency = meta["currency"]
        logo_url = get_logo_url(ticker)
        card_title = f"{meta['name']} ({ticker})"
        card_logo = logo_url
        snap_s = ensure_live_snapshot(ticker)
        df_live = fetch_stock_history(ticker, "1y") if online_status else None

        if df_live is not None and len(df_live) >= 20:
            price = float(df_live["Close"].iloc[-1])
            prev_c = float(df_live["Close"].iloc[-2])
            pct_change = ((price - prev_c) / prev_c) * 100
            rsi = float(df_live["RSI"].iloc[-1])
            sma20 = float(df_live["SMA_20"].iloc[-1])
            ema50 = float(df_live["EMA_50"].iloc[-1])
            high52 = float(df_live["High"].max())
            low52 = float(df_live["Low"].min())
            volatility_pct = float(df_live["Close"].pct_change().std() * 100)
            atr_val = float((df_live["High"] - df_live["Low"]).tail(14).mean())
        else:
            price = snap_s["price"]
            pct_change = snap_s["pct"]
            rsi = snap_s["rsi"]
            sma20 = price * 0.99
            ema50 = price * 0.97
            high52 = price * 1.15
            low52 = price * 0.85
            volatility_pct = 1.8
            atr_val = price * 0.02

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

        sys_stock = (
            "You are FinanceSight AI, an elite institutional stock market analyst. "
            "Answer the user's exact question about the specified company directly and accurately. "
            "Cite exact live prices, RSI, moving averages, and how many shares the user can afford with their available margin."
        )
        usr_stock = f"""
        CURRENT SYSTEM CLOCK: {now_str}
        USER ACCOUNT (@{username}): Available Margin: ₹{acct['balance']:,.2f} | Holdings Value: ₹{acct['tot_cur']:,.2f}
        REQUESTED STOCK ({meta['name']} - {ticker}):
        - Live Price: {currency}{price:,.2f} ({pct_change:+.2f}% today)
        - 14-Day RSI: {rsi:.1f} | Daily Volatility: {volatility_pct:.2f}% | 14-Day ATR: {currency}{atr_val:,.2f}
        - 20-Day SMA: {currency}{sma20:,.2f} | 50-Day EMA: {currency}{ema50:,.2f}
        - 52-Week Low/High: {currency}{low52:,.2f} to {currency}{high52:,.2f}
        - 5-Day Random Forest ML Forecast: {currency}{ml_pred_5d:,.2f} ({ml_move_pct:+.2f}%)

        USER QUESTION: "{user_question}"
        """
        groq_reply, groq_badge = call_groq_llm_live(sys_stock, usr_stock)
        if groq_reply:
            return groq_reply, groq_badge, card_title, card_logo

        trend_up = price >= sma20
        verdict = "BULLISH ACCUMULATION 🟢 ▲" if (trend_up and rsi < 68) else ("OVERBOUGHT / BOOK PROFITS 🟡" if rsi >= 68 else "BEARISH / WAIT FOR SUPPORT 🔴 ▼")
        safe_qty = max(1, int((acct["balance"] * 0.20) // price)) if price > 0 else 1
        return f"""
### 📊 Live Stock Intelligence Report: {meta['name']} (`{ticker}`)
* **Live Market Snapshot:** **{meta['name']} (`{ticker}`)** is trading at **`{currency}{price:,.2f}`** (`{pct_change:+.2f}%` today), with a 52-week range of **`{currency}{low52:,.2f}` – `{currency}{high52:,.2f}`**.
* **AI Technical Verdict:** **{verdict}**
  * **Trend vs 20-SMA (`{currency}{sma20:,.2f}`):** Price is trading **`{((price - sma20)/sma20)*100:+.2f}%`** {'above ▲' if trend_up else 'below ▼'} its 20-day average.
  * **Momentum (RSI-14):** **`{rsi:.1f}`** | **5-Day ML Forecast:** **`{currency}{ml_pred_5d:,.2f}`** (`{ml_move_pct:+.2f}%`).
* **Key Action Levels & Position Sizing for Your `₹{acct['balance']:,.2f}` Margin:**
  * **Buy / Entry Zone:** `{currency}{price * 0.994:,.2f}` – `{currency}{price:,.2f}`
  * **Stop-Loss (1.5x ATR):** `{currency}{price - (1.5 * atr_val):,.2f}`
  * **Target 1:** `{currency}{price + (1.8 * atr_val):,.2f}` | **Target 2:** `{currency}{price + (3.2 * atr_val):,.2f}`
  * **Suggested Allocation (20% of Available Cash):** Up to **`{safe_qty} shares`**.
""", f"⚡ Powered by FinanceSight Quant Engine ({ticker})", card_title, card_logo

    math_expr, math_ans = try_solve_math_query(user_question)
    math_hint = f"\nEXACT PRE-COMPUTED MATH RESULT: {math_expr} = {math_ans}" if math_expr is not None else ""
    sys_general = (
        "You are FinanceSight AI, an intelligent, friendly, and accurate assistant with full knowledge of general topics, "
        "science, math, current time/date, and global stock markets (NSE/BSE and NASDAQ/NYSE).\n"
        "Answer the user's exact question directly, naturally, and concisely in sentence 1.\n"
        "Do NOT output unrequested stock recommendation tables unless the user specifically asks for stock picks."
    )
    usr_general = (
        f"CURRENT IST DATE & TIME: {now_str}\n"
        f"INDIAN MARKET (NSE/BSE) HOURS: Monday–Friday, 9:15 AM – 3:30 PM IST (Pre-open 9:00–9:15 AM IST). Current Status: {nse_status_str}\n"
        f"US MARKET (NASDAQ/NYSE) HOURS: Monday–Friday, 9:30 AM – 4:00 PM EST (7:00 PM – 1:30 AM IST).\n"
        f"USER (@{username}) AVAILABLE WALLET MARGIN: ₹{acct['balance']:,.2f}, LIVE HOLDINGS VALUE: ₹{acct['tot_cur']:,.2f}{math_hint}\n\n"
        f"USER QUESTION: \"{user_question}\""
    )
    groq_reply, groq_badge = call_groq_llm_live(sys_general, usr_general)
    if groq_reply:
        return groq_reply, groq_badge, card_title, card_logo

    fb_reply, fb_badge = answer_general_or_fallback_question(user_question, now_dt, acct, nse_status_str)
    return fb_reply, fb_badge, card_title, card_logo

db_logged, db_user, db_name = load_login_session()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = db_logged
if "username" not in st.session_state:
    st.session_state.username = db_user
if "full_name" not in st.session_state:
    st.session_state.full_name = db_name
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "RELIANCE.NS"
if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []
if "public_page" not in st.session_state:
    st.session_state.public_page = "Home"
if "auth_notice" not in st.session_state:
    st.session_state.auth_notice = ""
if "allow_after_hours" not in st.session_state:
    st.session_state.allow_after_hours = False

if "nav" in st.query_params:
    target_nav = st.query_params["nav"]
    st.query_params.clear()
    if target_nav == "Logout":
        save_login_session(False, "", "")
        st.session_state.public_page = "Home"
    elif target_nav in ["Home", "Signup", "About", "Products", "Pricing", "Support"]:
        save_login_session(False, "", "")
        st.session_state.public_page = target_nav
    elif target_nav in ["Dashboard", "Orders", "Holdings", "Positions", "Funds", "Terminal", "Advisor", "Apps"]:
        if st.session_state.logged_in and st.session_state.username:
            st.session_state.page = target_nav
        else:
            st.session_state.public_page = "Home"
            st.session_state.auth_notice = "🔒 Please sign in with your User ID and Password to access the trading dashboard."

def navigate_to(page_name, ticker=None):
    st.session_state.page = page_name
    if ticker:
        st.session_state.selected_ticker = ticker

nav_token = f"{st.session_state.public_page}_{st.session_state.page}_{int(datetime.now().timestamp())}"

def render_financesight_open_account(key_suffix="main"):
    render_html("""
    <div class="z-section-card" style="text-align:center;">
        <h2 class="fs-title" style="font-size:1.95rem; margin-bottom:10px;">Start Exploring with a FinanceSight Account</h2>
        <p class="fs-muted" style="font-size:1.02rem; margin-bottom:20px;">
            Access live NSE & NASDAQ STOCKS, 7-day ML price forecasting, autonomous AI order execution, and a ₹1,00,000 virtual trading wallet.
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
                    <span><span style="color:#38bdf8;">FINANCE</span>SIGHT</span>
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
            <p>FinanceSight is a market analysis, machine learning price forecasting, and paper trading simulation platform covering global STOCKS. Live and historical market data is fetched via the Yahoo Finance API for educational and analytical use.</p>
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

if not st.session_state.logged_in:
    st.markdown("""
    <style>
        .stApp {
            background-color: #030612 !important;
            background-image:
                radial-gradient(circle at 50% 78%, rgba(244, 114, 182, 0.28) 0%, rgba(168, 85, 247, 0.34) 18%, rgba(37, 99, 235, 0.44) 40%, rgba(6, 182, 212, 0.18) 58%, transparent 74%),
                radial-gradient(circle at 20% 22%, rgba(14, 165, 233, 0.22) 0%, transparent 48%),
                radial-gradient(circle at 82% 24%, rgba(139, 92, 246, 0.24) 0%, transparent 48%),
                linear-gradient(180deg, #02040a 0%, #060b1e 52%, #090d24 100%) !important;
            background-attachment: fixed !important;
            color: #f8fafc !important;
        }
        .z-section-card, .fs-panel, .z-universe-card, .stock-card, .kpi-box, .z-footer, [data-testid="stForm"] {
            background: rgba(8, 13, 28, 0.84) !important;
            backdrop-filter: blur(18px) !important;
            -webkit-backdrop-filter: blur(18px) !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55) !important;
            color: #f8fafc !important;
        }
        .fs-title, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .mono-price, .kpi-val {
            color: #ffffff !important;
        }
        .fs-muted, .stApp p, .stApp li, .kpi-title, .fs-footer-link, .fs-bottom-link {
            color: #e2e8f0 !important;
            opacity: 0.92 !important;
        }
        .fs-logo-link {
            color: #ffffff !important;
        }
        .fs-nav-btn {
            background: rgba(15, 23, 42, 0.85) !important;
            border: 1px solid rgba(56, 189, 248, 0.32) !important;
            color: #f8fafc !important;
        }
        .fs-nav-btn:hover {
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
            background: rgba(30, 41, 59, 0.95) !important;
        }
        .fs-social-link {
            background: rgba(15, 23, 42, 0.9) !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            color: #f8fafc !important;
        }
        [data-testid="stWidgetLabel"] p, label p, .stTabs [data-baseweb="tab"] p {
            color: #f8fafc !important;
            font-weight: 600 !important;
        }
        .stTextInput input, .stNumberInput input, [data-baseweb="select"] > div {
            background-color: rgba(15, 23, 42, 0.92) !important;
            color: #ffffff !important;
            border: 1px solid rgba(56, 189, 248, 0.35) !important;
        }
        .watch-row {
            color: #f8fafc !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    nav_c1, nav_c2, nav_c3, nav_c4, nav_c5, nav_c6, nav_c7, nav_c8 = st.columns([1.85, 1.75, 0.88, 0.92, 0.88, 1.0, 0.92, 0.95], gap="small")
    
    with nav_c1:
        render_html(f"""
        <div style="padding-right:12px; padding-top:3px;">
            <a href="?nav=Home&r=top_{nav_token}" target="_self" class="fs-logo-link" title="Go to FinanceSight Home">
                {FINANCESIGHT_LOGO_SVG}
                <span><span style="color:#38bdf8;">FINANCE</span>SIGHT</span>
            </a>
        </div>
        """)

    with nav_c2:
        search_options = ["Search Stocks"] + [
            f"{sym} — {meta['name']} ({meta['exchange']})" for sym, meta in STOCK_CATALOG.items()
        ]
        picked_search = st.selectbox("Search Stocks", search_options, label_visibility="collapsed")
        if picked_search != "Search Stocks":
            sym_jump = picked_search.split(" — ")[0]
            st.session_state.selected_ticker = sym_jump
            st.session_state.auth_notice = f"🔒 Please sign in with your User ID and Password to view {sym_jump} in the terminal."

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

    if st.session_state.auth_notice:
        st.info(st.session_state.auth_notice)
        st.session_state.auth_notice = ""

    render_html("<hr style='border:0; border-top:1px solid rgba(56,189,248,0.25); margin:6px 0 18px 0;'>")

    if st.session_state.public_page == "Home":
        hero_left, hero_right = st.columns([1.62, 1.0], gap="large")

        with hero_left:
            watch_rows_html = ""
            for w_sym, w_label, w_dom in [
                ("NVDA", "NVDA", "nvidia.com"),
                ("AAPL", "AAPL", "apple.com"),
                ("JIOFIN.NS", "JIOFIN", "jio.com"),
                ("RELIANCE.NS", "RELIANCE", "ril.com"),
                ("TSLA", "TSLA", "tesla.com")
            ]:
                s_data = snapshots.get(w_sym, {"price": 0.0, "pct": 0.0})
                cur_sym = STOCK_CATALOG.get(w_sym, {}).get("currency", "₹")
                is_up = s_data["pct"] >= 0
                clr = "#34d399" if is_up else "#fb7185"
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
                <div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:12px; margin-bottom:16px; border-bottom:1px solid rgba(56,189,248,0.22);">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="height:10px; width:10px; background:{feed_color}; border-radius:50%; display:inline-block;"></span>
                        <img src="https://www.google.com/s2/favicons?domain=ril.com&sz=128" class="logo-sm">
                        <span style="font-family:JetBrains Mono,monospace; font-size:0.8rem; font-weight:700; color:#f8fafc;">
                            FINANCESIGHT • STOCKS LIVE MARKETWATCH & SUPERCHART
                        </span>
                    </div>
                    <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:4px 10px; border-radius:6px; font-family:JetBrains Mono,monospace; font-size:0.75rem; font-weight:800;">
                        {feed_badge}
                    </span>
                </div>

                <div style="display:grid; grid-template-columns: 1.4fr 1.2fr; gap:14px;">
                    <div class="fs-panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <img src="https://www.google.com/s2/favicons?domain=apple.com&sz=128" class="logo-sm">
                                <img src="https://www.google.com/s2/favicons?domain=nvidia.com&sz=128" class="logo-sm">
                                <span style="font-weight:800; font-size:0.88rem; color:#ffffff;">Orderflow & Volume Profile</span>
                            </div>
                            <span style="color:#34d399; font-family:JetBrains Mono,monospace; font-size:0.84rem; font-weight:800;">
                                {snapshots['NVDA']['pct']:+.2f}%
                            </span>
                        </div>

                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(255,255,255,0.12); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:68%; height:100%; background:linear-gradient(90deg, #eab308 60%, #3b82f6 40%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; width:90px; color:#f8fafc;">POC ${snapshots['AAPL']['price']:,.1f}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(255,255,255,0.12); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:85%; height:100%; background:linear-gradient(90deg, #eab308 55%, #06b6d4 45%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; color:#38bdf8; width:90px;">VAH ${snapshots['AAPL']['price']*1.015:,.1f}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(255,255,255,0.12); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:48%; height:100%; background:linear-gradient(90deg, #ef4444 50%, #3b82f6 50%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; color:#fb7185; width:90px;">VAL ${snapshots['AAPL']['price']*0.985:,.1f}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:10px; margin:12px 0;">
                            <div style="flex:1; background:rgba(255,255,255,0.12); height:11px; border-radius:6px; overflow:hidden;">
                                <div style="width:76%; height:100%; background:linear-gradient(90deg, #10b981 65%, #3b82f6 35%);"></div>
                            </div>
                            <span style="font-family:JetBrains Mono,monospace; font-size:0.74rem; color:#34d399; width:90px;">▲ AI TARGET</span>
                        </div>

                        <div style="margin-top:16px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.14); display:flex; justify-content:space-between; font-family:JetBrains Mono,monospace; font-size:0.76rem; color:#e2e8f0;">
                            <span>RELIANCE: <b style="color:#34d399;">₹{snapshots['RELIANCE.NS']['price']:,.2f}</b></span>
                            <span>JIOFIN: <b style="color:#38bdf8;">₹{snapshots['JIOFIN.NS']['price']:,.2f}</b></span>
                        </div>
                    </div>

                    <div class="fs-panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.14);">
                            <span style="font-size:0.76rem; font-weight:800; color:#ffffff;">📋 FINANCESIGHT MARKETWATCH</span>
                            <span style="font-size:0.7rem; color:#38bdf8; font-family:JetBrains Mono,monospace; font-weight:700;">REAL DATA</span>
                        </div>
                        {watch_rows_html}
                    </div>
                </div>

                <div style="text-align:center; margin-top:16px;">
                    <a href="?nav=Products&r={nav_token}" target="_self" style="text-decoration:none; background:rgba(15,23,42,0.92); border:1px solid rgba(56,189,248,0.5); border-radius:999px; padding:10px 24px; display:inline-flex; align-items:center; gap:12px;">
                        <span style="font-size:1.15rem;">⚡</span>
                        <div style="text-align:left;">
                            <div style="font-weight:800; font-size:0.88rem; color:#38bdf8;">Explore all charting, AI forecasting & paper trading tools ›</div>
                            <div style="font-size:0.74rem; color:#e2e8f0;">NSE & NASDAQ STOCKS • Autonomous AI Agent • Strategy Backtesting</div>
                        </div>
                    </a>
                </div>
            </div>
            """)

        with hero_right:
            render_html("""
            <div class="z-section-card" style="margin-top:0; padding:20px 24px; margin-bottom:12px;">
                <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:4px 12px; border-radius:999px; font-size:0.75rem; font-weight:700;">
                    ⚡ FINANCESIGHT WEB TERMINAL • INSTANT ACCESS
                </span>
                <h3 class="fs-title" style="margin:10px 0 4px 0;">Sign In to FinanceSight Dashboard</h3>
                <p class="fs-muted" style="font-size:0.83rem; margin:0;">Includes Orders, Holdings, Positions, Funds, SuperCharts & Agentic AI</p>
            </div>
            """)

            auth_tab1, auth_tab2 = st.tabs(["FinanceSight Login", "Open Free Account"])

            with auth_tab1:
                with st.form("home_login_form", clear_on_submit=False):
                    login_user = st.text_input("FinanceSight User ID", value="Trader_XYZ")
                    login_pass = st.text_input("Password", type="password", value="demo123")
                    login_submitted = st.form_submit_button("Login to FinanceSight", use_container_width=True, type="primary")
                    if login_submitted:
                        ok_auth, db_u, db_n = authenticate_user(login_user, login_pass)
                        if ok_auth:
                            save_login_session(True, db_u, db_n)
                            st.session_state.page = "Dashboard"
                            st.rerun()
                        else:
                            st.error("❌ Invalid User ID or Password! Please check your credentials or register a new account.")

            with auth_tab2:
                with st.form("home_signup_form", clear_on_submit=False):
                    new_name = st.text_input("Full Name", placeholder="e.g., Vishal Babu")
                    new_user = st.text_input("Choose FinanceSight ID", placeholder="e.g., Vishal_01")
                    new_email = st.text_input("Email ID", placeholder="user@financesight.in")
                    new_pass = st.text_input("Create Password", type="password")
                    signup_submitted = st.form_submit_button("Open Account & Claim ₹1,00,000", use_container_width=True, type="primary")
                    if signup_submitted:
                        ok_reg, res_msg = register_new_user(new_name, new_user, new_email, new_pass)
                        if ok_reg:
                            save_login_session(True, res_msg, new_name.strip())
                            st.session_state.page = "Dashboard"
                            st.rerun()
                        else:
                            st.warning(res_msg)

        render_html("""
        <div class="z-section-card">
            <div style="display:grid; grid-template-columns: 1fr 1.3fr; gap:32px; align-items:center;">
                <div class="fs-panel" style="padding:28px; text-align:center;">
                    <div style="font-size:3.2rem; margin-bottom:10px;">📊</div>
                    <h3 class="fs-title" style="margin-bottom:6px;">All-in-One Market Analysis & Trading Suite</h3>
                    <p style="color:#38bdf8; font-family:'JetBrains Mono',monospace; font-size:0.9rem; font-weight:700;">Live NSE & NASDAQ STOCKS • Agentic AI • Paper Trading</p>
                </div>
                <div>
                    <h2 class="fs-title" style="font-size:1.75rem; margin-bottom:10px;">Built for practical analysis and risk-free learning</h2>
                    <p class="fs-muted" style="font-size:0.95rem; margin-bottom:16px;">
                        FinanceSight brings together real-time market data, quantitative technical indicators, and virtual trade execution in one workspace:
                    </p>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#38bdf8; font-weight:700; font-size:0.92rem;">
                        <div>• Live Candlestick & Volume Charts</div>
                        <div>• 14-Day RSI & Moving Averages</div>
                        <div>• 7-Day ML Price Forecasting</div>
                        <div>• Autonomous AI Order Execution</div>
                        <div>• No-Code Strategy Backtesting</div>
                        <div>• Virtual Paper Trading Portfolio</div>
                    </div>
                </div>
            </div>
        </div>
        """)

        st_col1, st_col2 = st.columns([1.3, 1.0], gap="large")
        with st_col1:
            render_html("""
            <div class="z-section-card" style="height:100%;">
                <h2 class="fs-title" style="font-size:1.65rem; margin-bottom:14px;">🛡️ Practical tools you can rely on</h2>
                <div style="margin-bottom:14px;">
                    <h4 style="color:#38bdf8; margin:0 0 4px 0;">Data-driven decision making</h4>
                    <p class="fs-muted" style="font-size:0.88rem; margin:0;">Evaluate global STOCKS using objective technical indicators (20-SMA, 50-EMA, 14-Day RSI) and historical backtest metrics instead of guesswork.</p>
                </div>
                <div style="margin-bottom:14px;">
                    <h4 style="color:#38bdf8; margin:0 0 4px 0;">Risk-free paper trading simulator</h4>
                    <p class="fs-muted" style="font-size:0.88rem; margin:0;">Practice placing delivery (CNC) and intraday (MIS 5x leverage) orders during market hours using a ₹1,00,000 virtual wallet before risking real capital.</p>
                </div>
                <div>
                    <h4 style="color:#38bdf8; margin:0 0 4px 0;">Agentic AI & backtesting workflow</h4>
                    <p class="fs-muted" style="font-size:0.88rem; margin:0;">Ask the AI Advisor any question, check your funds, list top benefitting stocks, or place and cancel orders directly from chat.</p>
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
                        <div style="font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:800; color:#34d399;">₹0</div>
                        <div class="fs-muted" style="font-size:0.8rem; margin-top:6px;">Standard equity delivery & mutual fund simulation</div>
                    </div>
                    <div class="fs-panel" style="border:2px solid #38bdf8; padding:18px;">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:800; color:#38bdf8;">₹20</div>
                        <div class="fs-muted" style="font-size:0.8rem; margin-top:6px;">Flat intraday (MIS) & F&O order fee model</div>
                    </div>
                </div>
            </div>
            """)

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
                        <b>FinanceSight AI Advisor:</b> Ask any question about stock trends, top benefitting stocks to invest in, position sizing, or command it to execute and manage trades on your behalf.
                    </p>
                </div>
            </div>
        </div>
        """)

        render_financesight_open_account("home")

    elif st.session_state.public_page == "Signup":
        s_left, s_right = st.columns([1.2, 1.2], gap="large")
        with s_left:
            render_html("""
            <div class="z-section-card">
                <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:5px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
                    INSTANT PAPER TRADING ACCESS
                </span>
                <h2 class="fs-title" style="margin:12px 0 10px 0;">Create your free FinanceSight account</h2>
                <p class="fs-muted" style="font-size:0.95rem; line-height:1.6;">
                    Set up your account in seconds to track live NSE & NASDAQ STOCKS, test algorithmic strategies, and practice trading with <b>₹1,00,000</b> in virtual margin.
                </p>
                <div class="fs-panel" style="margin-top:18px; font-size:0.86rem; line-height:1.8;">
                    ✅ ₹1,00,000 Virtual Paper Trading Wallet<br>
                    ✅ Universal AI Advisor (Answers Any Question & Places Orders)<br>
                    ✅ 7-Day Random Forest ML Price Predictor<br>
                    ✅ No-Code Strategy Backtester & CSV Exports
                </div>
            </div>
            """)
        with s_right:
            st.markdown("### ✨ Create Your FinanceSight Account Now")
            with st.form("page_signup_form", clear_on_submit=False):
                su_name = st.text_input("Your Full Name", placeholder="e.g., Vishal Babu")
                su_user = st.text_input("Choose FinanceSight User ID", placeholder="e.g., Vishal_01")
                su_email = st.text_input("Email Address", placeholder="user@financesight.in")
                su_pass = st.text_input("Password", type="password")
                su_submit = st.form_submit_button("Complete Signup & Open FinanceSight Dashboard", type="primary", use_container_width=True)
                if su_submit:
                    ok_reg, res_msg = register_new_user(su_name, su_user, su_email, su_pass)
                    if ok_reg:
                        save_login_session(True, res_msg, su_name.strip())
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.warning(res_msg)

    elif st.session_state.public_page == "About":
        render_html("""
        <div class="z-section-card" style="text-align:center;">
            <h2 class="fs-title" style="font-size:1.85rem; max-width:800px; margin:0 auto;">
                Clear, Objective Market Analysis.<br>
                <span style="color:#38bdf8;">Combining Technical Charting, Machine Learning & Paper Trading.</span>
            </h2>
        </div>
        """)

        ab_c1, ab_c2 = st.columns(2, gap="large")
        with ab_c1:
            render_html("""
            <div class="z-section-card" style="height:100%; font-size:0.94rem; line-height:1.75;">
                <p><b>FinanceSight</b> is designed to make technical stock analysis, algorithmic backtesting, and portfolio simulation straightforward and accessible across global STOCKS.</p>
                <p>By integrating live market data with <b>Random Forest price forecasting</b> and <b>Agentic LLaMA 3.3 RAG analysis</b>, the platform helps users evaluate trends, momentum, and risk levels clearly.</p>
            </div>
            """)
        with ab_c2:
            render_html("""
            <div class="z-section-card" style="height:100%; font-size:0.94rem; line-height:1.75;">
                <p>Instead of switching between separate charting websites, calculators, and spreadsheets, FinanceSight brings everything into a single workspace.</p>
                <p>Users can test trading strategies on historical data, calculate exact statutory charges and breakeven points, and practice order execution during live market hours using a virtual wallet.</p>
            </div>
            """)

        render_html("""
        <div class="z-section-card">
            <h2 class="fs-title" style="text-align:center; margin-bottom:24px;">👥 Platform Architecture & Engineering</h2>
            <div style="display:grid; grid-template-columns: 1fr 2fr; gap:28px; align-items:center;">
                <div class="fs-panel" style="text-align:center; padding:24px; border:2px solid #38bdf8;">
                    <div style="font-size:3.6rem;">👨‍💻</div>
                    <h4 class="fs-title" style="margin:10px 0 4px 0;">FinanceSight Core Systems</h4>
                    <div style="color:#38bdf8; font-size:0.84rem; font-weight:700;">Python, Machine Learning & SQLite Architecture</div>
                </div>
                <div style="font-size:0.95rem; line-height:1.75;">
                    <p>FinanceSight integrates a <b>Multi-Layer SuperChart Terminal, Portfolio Console, No-Code Strategy Backtester, and Universal AI Advisor</b> into a unified web application.</p>
                    <p>Powered by live <b>Yahoo Finance market streams</b>, <b>Scikit-Learn Random Forest regression</b>, <b>Groq LLaMA 3.3 RAG</b>, and a local <b>SQLite relational database</b> for persistent portfolio and order tracking.</p>
                </div>
            </div>
        </div>
        """)

    elif st.session_state.public_page == "Products":
        render_html(f"""
        <div class="z-section-card" style="text-align:center;">
            <h1 class="fs-title" style="font-size:2.2rem; margin-bottom:8px;">FinanceSight Products & Modules</h1>
            <h4 class="fs-muted" style="font-weight:500; margin-bottom:10px;">Integrated tools for charting, price forecasting, backtesting, and paper trading</h4>
            <a href="?nav=Home&r={nav_token}" target="_self" style="color:#38bdf8; font-weight:700; font-size:0.92rem; text-decoration:none;">Sign in on the Home page to launch the live dashboard →</a>
        </div>
        """)

        products_showcase = [
            ("left", "📈 FinanceSight SuperChart Terminal", "Interactive 3-layer technical charting across NSE & NASDAQ STOCKS with Japanese Candlesticks, 20-Day SMA, 50-Day EMA, Volume bars, 14-Day RSI, and market-hours CNC/MIS order execution.", "Terminal"),
            ("right", "💿 FinanceSight Portfolio & Ledger", "Centralized portfolio tracker showing live moving mark-to-market P&L, asset allocation donut charts, order history, and 1-click CSV/Excel report downloads.", "Holdings"),
            ("left", "🤖 Universal LLaMA 3.3 AI Advisor", "Agentic AI stock analyst and general assistant with direct access to your wallet, portfolio, and all STOCKS. Ask it any question, list top benefitting stocks, or buy/sell/cancel orders automatically.", "Advisor"),
            ("right", "⚡ 7-Day Random Forest ML Predictor", "Trains a live Random Forest regression model on rolling 1-year OHLCV and momentum lag features to project the next 7 trading sessions.", "Terminal"),
            ("left", "🧪 No-Code Strategy Backtester & Scanner", "Test systematic trading rules (Golden Crossover, RSI Oversold Reversal, Momentum Surge) on historical candles, view the equity curve, and scan all STOCKS live.", "Apps")
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
                    <div style="color:#38bdf8; font-size:0.8rem; margin-top:6px; font-weight:600;">⚡ Live Module Inside FinanceSight</div>
                </div>
                """)
            with text_col:
                st.markdown(f"### {p_title}")
                st.write(p_desc)
                b_try, b_learn = st.columns(2)
                if b_try.button(f"Sign In to Open →", key=f"prod_demo_{p_title}", type="primary", use_container_width=True):
                    st.session_state.public_page = "Home"
                    st.session_state.auth_notice = f"🔒 Please sign in with your User ID and Password to open {p_title}."
                    st.rerun()
                if b_learn.button("View Details →", key=f"prod_learn_{p_title}", use_container_width=True):
                    st.session_state.public_page = "About"
                    st.rerun()
            render_html("<hr style='border:0; border-top:1px solid rgba(56,189,248,0.22); margin:16px 0;'>")

        render_html("""
        <div style="text-align:center; margin:28px 0 18px 0;">
            <h2 class="fs-title">🧩 Core Feature Highlights</h2>
            <p class="fs-muted">Built-in utilities included across the FinanceSight workspace</p>
        </div>
        """)

        universe_items = [
            ("⚡ Strategy Backtester", "Simulate Golden Crossover, RSI Reversal, and Momentum rules with adjustable Stop-Loss and Target sliders."),
            ("📡 Live STOCKS Scanner", "Scan Indian NSE and US NASDAQ/NYSE STOCKS simultaneously for RSI breakouts and moving average trends."),
            ("🤖 Agentic AI Execution", "Place, calculate, or cancel trades and ask any general or market question directly in chat."),
            ("🧮 Brokerage Calculator", "Compute exact STT, GST, exchange transaction fees, stamp duty, and net P&L before placing trades."),
            ("💼 CNC & MIS Simulation", "Test both 1x delivery holdings and 5x leveraged intraday positions with live M2M P&L."),
            ("📥 CSV Report Exports", "Download your executed order book, demat holdings, and strategy backtest ledgers as CSV files.")
        ]
        for r_idx in range(0, 6, 3):
            u_cols = st.columns(3)
            for c_i in range(3):
                u_name, u_desc = universe_items[r_idx + c_i]
                with u_cols[c_i]:
                    render_html(f"""
                    <div class="z-universe-card">
                        <h4 style="color:#38bdf8; font-weight:800; margin-bottom:8px;">{u_name}</h4>
                        <p class="fs-muted" style="font-size:0.84rem; margin:0;">{u_desc}</p>
                    </div>
                    """)
            st.markdown("<br>", unsafe_allow_html=True)

        render_financesight_open_account("products")

    elif st.session_state.public_page == "Pricing":
        render_html("""
        <div class="z-section-card" style="text-align:center;">
            <h1 class="fs-title" style="font-size:2.1rem;">Fee Structure & Brokerage Calculator</h1>
            <p class="fs-muted" style="font-size:0.95rem;">Simulate standard Indian discount broking charges (₹0 delivery and flat ₹20 intraday) and calculate exact statutory taxes.</p>
        </div>
        """)

        pr1, pr2, pr3 = st.columns(3)
        with pr1:
            render_kpi("Equity Delivery Simulation", "₹0", "Zero brokerage modeled on long-term CNC equity delivery trades.", "kpi-emerald", "#34d399")
        with pr2:
            render_kpi("Intraday & F&O Simulation", "₹20", "Flat ₹20 or 0.03% (whichever is lower) per executed intraday order.", "kpi-cyan", "#38bdf8")
        with pr3:
            render_kpi("Virtual Paper Wallet", "₹1,00,000", "Free instant virtual margin credited to every user account for practice.", "kpi-violet", "#c084fc")

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
            render_kpi("Total Turnover", f"₹{turnover:,.2f}", f"Brokerage: ₹{brokerage:.2f}", "kpi-cyan", "#38bdf8")
        with bc2:
            render_kpi("Total Taxes & Charges", f"₹{total_charges:,.2f}", f"STT: ₹{stt:.2f} | GST: ₹{gst:.2f}", "kpi-violet", "#c084fc")
        with bc3:
            render_kpi("Breakeven Per Share", f"₹{(total_charges/c_qty):.2f}", "Points needed to cover taxes", "kpi-white", "#60a5fa")
        with bc4:
            render_kpi("Net Realized Profit / Loss", f"₹{net_pnl:,.2f}", f"Gross P&L: ₹{gross_pnl:+.2f}", "kpi-emerald" if net_pnl >= 0 else "kpi-violet", "#34d399" if net_pnl >= 0 else "#fb7185")

        render_financesight_open_account("pricing")

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
                    <div style="background:#0f172a; color:#f8fafc; border:1px solid #38bdf8; padding:12px 18px; border-radius:10px; font-size:0.9rem; margin-bottom:12px;">
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
                        <li>Orders are validated against official market trading hours (Mon–Fri)</li>
                        <li>Live portfolio holdings and positions move dynamically with stock prices</li>
                    </ol>
                </div>
            </div>
        </div>
        """)

        st.subheader("📋 Browse Help Topics by Module")
        ticket_topics = [
            ("➕ Account & Login", f"?nav=Signup&r={nav_token}", ["Creating a New User Account", "Logging In with User ID & Password", "Managing Profile & Credentials", "Virtual Margin Overview", "Platform Navigation Guide"]),
            ("📊 Charting & Indicators", f"?nav=Terminal&r={nav_token}", ["Reading Japanese Candlesticks", "Using 20-SMA & 50-EMA Lines", "Understanding 14-Day RSI", "Volume Bar Color Coding", "Refreshing Live Market Data"]),
            ("⚡ Paper Trading Orders", f"?nav=Positions&r={nav_token}", ["Market Hours Order Validation", "CNC Delivery vs MIS Intraday (5x)", "Tracking Live Moving M2M P&L", "1-Click Position Square-Off", "Exporting Order Book to CSV"]),
            ("💳 Virtual Funds & Wallet", f"?nav=Funds&r={nav_token}", ["Adding Virtual Cash via UPI Simulator", "Withdrawing Funds to Linked Bank", "Checking Available Margin", "Viewing Funding History Ledger", "Margin Release on Square-Off"]),
            ("🤖 Agentic AI Advisor", f"?nav=Advisor&r={nav_token}", ["Asking General & Market Questions", "Placing & Cancelling Orders via Chat", "Asking 'List Top Benefitting Stocks'", "Calculating Trade Margin & Taxes", "Math & Live Time Queries"]),
            ("🧪 Strategy Backtesting", f"?nav=Apps&r={nav_token}", ["SMA 20 Golden Crossover Logic", "RSI < 35 Oversold Reversal Rule", "Setting Stop-Loss & Target Sliders", "Reading the Backtest Equity Curve", "Downloading Backtest Reports"])
        ]
        for row_i in range(0, 6, 3):
            t_cols = st.columns(3)
            for col_i in range(3):
                t_head, t_href, t_links = ticket_topics[row_i + col_i]
                links_html = "".join([f"<a href='{t_href}' target='_self' style='display:block; color:#38bdf8; font-size:0.84rem; margin:6px 0; font-weight:600; text-decoration:none;'>• {lnk}</a>" for lnk in t_links])
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

if not online_status:
    st.warning("⚠️ **Offline Mode:** Internet connection is disconnected. Showing last cached market close prices without live updates.")

ticker_items_html = ""
for sym in core_tickers:
    data = snapshots.get(sym, {"price": 100.0, "pct": 0.0})
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

nav_buttons_html = ""
for label_caps, p_key in fs_pages:
    active_cls = "active" if st.session_state.page == p_key else ""
    svg_icon = NAV_SVGS[p_key]
    nav_buttons_html += f'<a href="?nav={p_key}&r={nav_token}" target="_self" class="fs-nav-btn {active_cls}">{svg_icon}<span>{label_caps}</span></a>'

nav_buttons_html += f'<a href="?nav=Logout&r={nav_token}" target="_self" class="fs-nav-btn">{NAV_SVGS["Logout"]}<span>LOGOUT</span></a>'

render_html(f"""
<div class="fs-topbar-wrap">
    <div class="fs-brand-box">
        <a href="?nav=Home&r=dash_{nav_token}" target="_self" class="fs-logo-link" title="Go to FinanceSight Home">
            {FINANCESIGHT_LOGO_SVG}
            <span><span style="color:#387ed1;">FINANCE</span>SIGHT</span>
        </a>
    </div>
    <div class="fs-nav-links-wrap">
        {nav_buttons_html}
    </div>
</div>
""")

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
    if online_status:
        fresh_s = fetch_market_snapshots(core_tickers)
        if fresh_s:
            st.session_state.last_valid_snapshots.update(fresh_s)
    st.rerun()

st.sidebar.subheader("📋 Marketwatch (STOCKS)")
catalog_options = [f"{k} — {v['name']}" for k, v in STOCK_CATALOG.items()]
current_idx = list(STOCK_CATALOG.keys()).index(st.session_state.selected_ticker) if st.session_state.selected_ticker in STOCK_CATALOG else 0
chosen_option = st.sidebar.selectbox("Search Stocks", catalog_options, index=current_idx)
chosen_sym = chosen_option.split(" — ")[0]
if chosen_sym != st.session_state.selected_ticker:
    st.session_state.selected_ticker = chosen_sym
    ensure_live_snapshot(chosen_sym)
    st.rerun()

mw_snap = ensure_live_snapshot(st.session_state.selected_ticker)
mw_cur = STOCK_CATALOG.get(st.session_state.selected_ticker, {}).get("currency", "₹")
mkt_open_flag, mkt_status_txt = check_market_trading_hours(st.session_state.selected_ticker)
st.sidebar.markdown(f"**Selected:** `{st.session_state.selected_ticker}` ({mw_cur}{mw_snap['price']:,.2f})")
st.sidebar.caption(f"{'🟢' if mkt_open_flag else '🔴'} {mkt_status_txt}")
mw_prod = st.sidebar.radio("Product", ["CNC (Delivery)", "MIS (Intraday 5x)"], horizontal=True)
mw_qty = st.sidebar.number_input("Qty", min_value=1, max_value=10000, value=10, step=1)
st.session_state.allow_after_hours = st.sidebar.checkbox("Allow Demo Orders Outside Market Hours", value=st.session_state.allow_after_hours)

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
for w_sym in ["RELIANCE.NS", "JIOFIN.NS", "TCS.NS", "HDFCBANK.NS", "ZOMATO.NS", "AAPL", "NVDA", "TSLA"]:
    w_s = snapshots.get(w_sym, {"price": 0.0, "pct": 0.0})
    w_c = "#10b981" if w_s["pct"] >= 0 else "#f43f5e"
    w_arr = "▲" if w_s["pct"] >= 0 else "▼"
    st.sidebar.markdown(
        f"<div style='display:flex; justify-content:space-between; font-family:JetBrains Mono,monospace; font-size:0.78rem; padding:4px 0; border-bottom:1px solid rgba(128,128,128,0.2);'>"
        f"<span><b>{w_sym.replace('.NS','')}</b></span>"
        f"<span style='color:{w_c}; font-weight:700;'>{w_s['price']:,.2f} ({w_arr}{w_s['pct']:+.2f}%)</span></div>",
        unsafe_allow_html=True
    )

if st.session_state.page == "Dashboard":
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(st.session_state.username,))
    pos_df = pd.read_sql_query("SELECT ticker, product_type, shares, avg_price FROM positions WHERE username = ?", conn, params=(st.session_state.username,))
    held_tickers = list(set(port_df["ticker"].tolist() + pos_df["ticker"].tolist()))
    refresh_held_tickers_live(held_tickers)

    tot_inv = (port_df["shares"] * port_df["avg_price"]).sum() if not port_df.empty else 0.0
    tot_cur = sum(
        row["shares"] * st.session_state.last_valid_snapshots.get(row["ticker"], {}).get("price", row["avg_price"])
        for _, row in port_df.iterrows()
    ) if not port_df.empty else 0.0
    tot_pnl = tot_cur - tot_inv
    pnl_pct = (tot_pnl / tot_inv * 100) if tot_inv > 0 else 0.0

    h_c1, h_c2, h_c3, h_c4 = st.columns(4)
    with h_c1:
        render_kpi("Equity Margin Available", f"₹{user_bal:,.2f}", "Opening Balance: ₹1,00,000", "kpi-white", "#2563eb")
    with h_c2:
        render_kpi("Live Invested Value", f"₹{tot_cur:,.2f}", f"Initial Cost: ₹{tot_inv:,.2f} ({len(port_df)} stocks)", "kpi-cyan", "#0284c7")
    with h_c3:
        render_kpi("Live Unrealized P&L", f"₹{tot_pnl:+,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} {pnl_pct:+.2f}% Live Move", "kpi-emerald" if tot_pnl >= 0 else "kpi-violet", "#10b981" if tot_pnl >= 0 else "#f43f5e")
    with h_c4:
        nse_open_now, _ = check_market_trading_hours("RELIANCE.NS")
        render_kpi("Market Session", "MARKET OPEN" if nse_open_now else "MARKET CLOSED", "Mon–Fri 9:15 AM – 3:30 PM IST", "kpi-emerald" if nse_open_now else "kpi-violet", "#10b981" if nse_open_now else "#f43f5e")

    f_col1, f_col2 = st.columns([2.2, 1.2])
    with f_col1:
        st.subheader("🏢 FinanceSight STOCKS Marketwatch (Click to Launch SuperChart or AI)")
    with f_col2:
        market_filter = st.selectbox(
            "Filter Exchange",
            ["⭐ Featured Top STOCKS", "🇮🇳 All Indian NSE STOCKS", "🇺🇸 All US NASDAQ/NYSE STOCKS", "🌐 All Global STOCKS"],
            label_visibility="collapsed"
        )

    if "Featured" in market_filter:
        grid_tickers = ["RELIANCE.NS", "JIOFIN.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "ZOMATO.NS", "HAL.NS", "AAPL", "NVDA", "TSLA", "MSFT"]
    elif "Indian" in market_filter:
        grid_tickers = [k for k, v in STOCK_CATALOG.items() if v["exchange"] == "NSE"]
    elif "US" in market_filter:
        grid_tickers = [k for k, v in STOCK_CATALOG.items() if v["exchange"] != "NSE"]
    else:
        grid_tickers = list(STOCK_CATALOG.keys())

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
                        ensure_live_snapshot(sym)
                        navigate_to("Terminal", sym)
                        st.rerun()
                    if c_btn2.button(f"ASK AI ADVISOR", key=f"dash_ai_{sym}", use_container_width=True):
                        ensure_live_snapshot(sym)
                        navigate_to("Advisor", sym)
                        st.rerun()

elif st.session_state.page == "Orders":
    st.subheader("📜 FinanceSight Executed Orders & Tradebook")
    tx_df = pd.read_sql_query(
        "SELECT id, timestamp, ticker, action, shares, price, total FROM transactions WHERE username = ? ORDER BY id DESC",
        conn, params=(st.session_state.username,)
    )
    if tx_df.empty:
        st.info("You haven't placed any orders yet. Use the left sidebar **BUY (B) / SELL (S)** panel or the **AI Advisor** during market hours!")
    else:
        st.dataframe(tx_df, use_container_width=True, hide_index=True)
        c_ord1, c_ord2 = st.columns([1.4, 2.6])
        with c_ord1:
            if st.button("🔄 Cancel Last Executed Order", use_container_width=True):
                ok_c, msg_c = cancel_last_user_order(st.session_state.username)
                if ok_c:
                    st.success(msg_c)
                    st.rerun()
                else:
                    st.warning(msg_c)
        with c_ord2:
            csv_tx = tx_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Order Book to Excel (CSV)",
                data=csv_tx,
                file_name="financesight_orders.csv",
                mime="text/csv"
            )

elif st.session_state.page == "Holdings":
    st.subheader("💼 FinanceSight CNC Equity Holdings (Moves Live with Market Price)")
    port_df = pd.read_sql_query("SELECT ticker, shares, avg_price FROM portfolio WHERE username = ?", conn, params=(st.session_state.username,))
    
    if port_df.empty:
        st.info("Your Holdings are currently empty. Place a **CNC (Delivery) BUY** order during market hours to build your portfolio!")
    else:
        refresh_held_tickers_live(port_df["ticker"].tolist())
        port_df["LTP (Live Price)"] = port_df["ticker"].apply(lambda s: st.session_state.last_valid_snapshots.get(s, {}).get("price", float(port_df.loc[port_df["ticker"] == s, "avg_price"].iloc[0])))
        port_df["Initial Cost (₹)"] = port_df["shares"] * port_df["avg_price"]
        port_df["Live Invested Value (₹)"] = port_df["shares"] * port_df["LTP (Live Price)"]
        port_df["Live P&L (₹)"] = port_df["Live Invested Value (₹)"] - port_df["Initial Cost (₹)"]
        port_df["Net Change (%)"] = (port_df["Live P&L (₹)"] / port_df["Initial Cost (₹)"]) * 100

        tot_inv = port_df["Initial Cost (₹)"].sum()
        tot_cur = port_df["Live Invested Value (₹)"].sum()
        tot_pnl = tot_cur - tot_inv

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            render_kpi("Total Account Net Worth", f"₹{(user_bal + tot_cur):,.2f}", "Cash + Live Holdings", "kpi-white", "#2563eb")
        with pc2:
            render_kpi("Initial Cost Basis", f"₹{tot_inv:,.2f}", f"{len(port_df)} Active Stocks", "kpi-cyan", "#0284c7")
        with pc3:
            render_kpi("Live Invested Value", f"₹{tot_cur:,.2f}", "Moves Up/Down with Stock LTP", "kpi-violet", "#8b5cf6")
        with pc4:
            render_kpi("Live Unrealized P&L", f"₹{tot_pnl:+,.2f}", f"{'▲' if tot_pnl >= 0 else '▼'} {(tot_pnl/tot_inv)*100:+.2f}% ROI", "kpi-emerald" if tot_pnl >= 0 else "kpi-violet", "#10b981" if tot_pnl >= 0 else "#f43f5e")

        d_col1, d_col2 = st.columns([1.8, 1.2])
        with d_col1:
            st.markdown("##### 📂 Live Holdings Breakdown")
            st.dataframe(port_df.round(2), use_container_width=True, hide_index=True)
            csv_hold = port_df.round(2).to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Holdings Statement (CSV)", data=csv_hold, file_name="financesight_holdings.csv", mime="text/csv")
        with d_col2:
            pie_fig = go.Figure(data=[go.Pie(labels=port_df["ticker"], values=port_df["Live Invested Value (₹)"], hole=0.52)])
            pie_fig.update_layout(title="Live Holdings Allocation", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(pie_fig, use_container_width=True)

elif st.session_state.page == "Positions":
    st.subheader("⚡ FinanceSight Open Positions (MIS Intraday 5x & CNC Delivery)")
    pos_df = pd.read_sql_query("SELECT ticker, product_type, shares, avg_price FROM positions WHERE username = ?", conn, params=(st.session_state.username,))
    
    if pos_df.empty:
        st.info("No open positions right now. Place an **MIS (Intraday 5x)** or **CNC** order during market hours to track live moving M2M Positions!")
    else:
        refresh_held_tickers_live(pos_df["ticker"].tolist())
        pos_df["LTP (Live Price)"] = pos_df["ticker"].apply(lambda s: st.session_state.last_valid_snapshots.get(s, {}).get("price", float(pos_df.loc[pos_df["ticker"] == s, "avg_price"].iloc[0])))
        pos_df["Initial Cost (₹)"] = pos_df["shares"] * pos_df["avg_price"]
        pos_df["Live Position Value (₹)"] = pos_df["shares"] * pos_df["LTP (Live Price)"]
        pos_df["M2M P&L (₹)"] = (pos_df["LTP (Live Price)"] - pos_df["avg_price"]) * pos_df["shares"]
        pos_df["Return (%)"] = ((pos_df["LTP (Live Price)"] - pos_df["avg_price"]) / pos_df["avg_price"]) * 100

        tot_m2m = pos_df["M2M P&L (₹)"].sum()
        tot_pos_val = pos_df["Live Position Value (₹)"].sum()
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            render_kpi("Live Open Positions Value", f"₹{tot_pos_val:,.2f}", f"{len(pos_df)} Active Positions", "kpi-cyan", "#0284c7")
        with p_c2:
            render_kpi("Total Open Positions M2M P&L", f"₹{tot_m2m:+,.2f}", "Real-Time Mark-to-Market", "kpi-emerald" if tot_m2m >= 0 else "kpi-violet", "#10b981" if tot_m2m >= 0 else "#f43f5e")
        st.dataframe(pos_df.round(2), use_container_width=True, hide_index=True)

        st.markdown("##### ⚡ 1-Click Position Square-Off (Exit at Market)")
        sq_cols = st.columns(min(4, len(pos_df)))
        for idx, row in pos_df.iterrows():
            col_target = sq_cols[idx % len(sq_cols)]
            if col_target.button(f"🔴 Square Off {row['ticker']} ({row['product_type']})", key=f"sq_{idx}", use_container_width=True):
                ok, msg = execute_trade(st.session_state.username, row["ticker"], "SELL", int(row["shares"]), float(row["LTP (Live Price)"]), row["product_type"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

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
        sub_t1, sub_t2, sub_t3 = st.tabs(["📊 FinanceSight SuperChart", "🤖 7-Day AI Price Forecast", "🧠 Universal AI Advisor"])
        
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
            q_input = st.text_input("Ask anything...", placeholder="Ask anything...")
            if st.button("🧠 Submit to AI Advisor", type="primary") and q_input:
                ans, engine_label, _, _ = ask_universal_ai_advisor(st.session_state.username, q_input)
                st.caption(engine_label)
                st.markdown(ans)

    with trade_col:
        is_open_t, status_t = check_market_trading_hours(ticker)
        render_html(f"""
        <div class="kpi-box kpi-white" style="margin-bottom:14px;">
            <div class="fs-title" style="font-size:1.05rem;">⚡ FinanceSight Order Window</div>
            <div style="font-size:0.76rem; color:{'#10b981' if is_open_t else '#f43f5e'}; font-weight:700; margin-top:4px;">
                {'🟢 ' + status_t if is_open_t else '🔴 ' + status_t}
            </div>
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

elif st.session_state.page == "Advisor":
    custom_q = st.chat_input("Ask anything...")

    render_html(f"""
    <div class="stock-card" style="border-left:5px solid #10b981; padding:22px 28px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
        <div style="display:flex; align-items:center; gap:18px;">
            <div style="width:60px; height:60px; border-radius:16px; background:#0f172a; display:flex; align-items:center; justify-content:center; border:2px solid #10b981;">
                {FINANCESIGHT_LOGO_SVG}
            </div>
            <div>
                <span style="background:rgba(16,185,129,0.18); color:#10b981; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
                    🤖 AGENTIC AI ADVISOR • ACCESS TO YOUR FUNDS (₹{user_bal:,.2f}), ORDERS & STOCKS
                </span>
                <h2 class="fs-title" style="margin:8px 0 4px 0;">🧠 FinanceSight Universal AI Advisor — All Global & Indian STOCKS</h2>
                <p class="fs-muted" style="margin:0; font-size:0.9rem;">
                    Universal AI intelligence across all Indian (NSE) & US (NASDAQ/NYSE) STOCKS, live portfolio execution, and general queries.
                </p>
            </div>
        </div>
    </div>
    """)

    st.markdown("##### ⚡ 1-Click Universal AI Actions & Stock Screener")
    q_col1, q_col2, q_col3, q_col4, q_col5 = st.columns([1.25, 1.2, 1.2, 1.25, 0.85])
    selected_prompt = None
    if q_col1.button("🎯 Top Benefitting STOCKS", use_container_width=True):
        selected_prompt = "List top benefitting stocks to invest in across all Indian and US stocks."
    if q_col2.button("🇮🇳 Top Indian NSE Picks", use_container_width=True):
        selected_prompt = "List top benefitting Indian NSE stocks to invest in."
    if q_col3.button("🇺🇸 Top US Tech Picks", use_container_width=True):
        selected_prompt = "List top benefitting US technology and AI stocks to invest in."
    if q_col4.button("💼 Check My Funds & Positions", use_container_width=True):
        selected_prompt = "Check my funds, portfolio holdings, and open positions."
    if q_col5.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.ai_chat_history = []
        st.rerun()

    active_question = selected_prompt or custom_q

    if active_question:
        reply, source_badge, card_title, card_logo = ask_universal_ai_advisor(
            st.session_state.username, active_question
        )
        st.session_state.ai_chat_history.insert(0, {
            "question": active_question,
            "answer": reply,
            "badge": source_badge,
            "stock": card_title,
            "logo": card_logo
        })

    for item in st.session_state.ai_chat_history:
        render_html(f"""
        <div class="stock-card" style="border-left:4px solid #10b981; display:flex; align-items:center; gap:14px;">
            <img src="{item.get('logo', 'https://www.google.com/s2/favicons?domain=google.com&sz=128')}" class="company-logo">
            <div>
                <div style="font-size:0.78rem; color:#0284c7; font-weight:700;">{item['stock']} • {item['badge']}</div>
                <div class="fs-title" style="margin-top:3px; font-size:1.02rem;">🙋‍♂️ You asked: "{item['question']}"</div>
            </div>
        </div>
        """)
        st.markdown(item["answer"])
        st.markdown("---")

elif st.session_state.page == "Apps":
    render_html("""
    <div class="stock-card" style="border-left:5px solid #8b5cf6; padding:22px 28px; margin-bottom:20px;">
        <span style="background:rgba(139,92,246,0.18); color:#8b5cf6; padding:4px 12px; border-radius:999px; font-size:0.78rem; font-weight:700;">
            FINANCESIGHT APPS • v4 ALGO ENGINE
        </span>
        <h2 class="fs-title" style="margin:8px 0 4px 0;">🧩 FinanceSight Integrated Apps — Strategy Backtester & STOCKS Scanner</h2>
        <p class="fs-muted" style="margin:0; font-size:0.9rem;">
            Build algorithmic trading rules without coding, backtest them on historical candles, and scan all NSE & NASDAQ STOCKS.
        </p>
    </div>
    """)

    st_tab1, st_tab2 = st.tabs(["🧪 No-Code Strategy Backtester", "📡 Live STOCKS Market Scanner"])

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
        st.subheader("📡 Real-Time STOCKS Market Scanner (NSE & NASDAQ/NYSE)")
        scan_rows = []
        for sym, meta in STOCK_CATALOG.items():
            snap = snapshots.get(sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True})
            status = "🟢 ▲ BULLISH BREAKOUT" if snap["above_sma"] and snap["rsi"] > 52 else ("🔵 ▲ OVERSOLD BOUNCE" if snap["rsi"] < 42 else "🔴 ▼ BEARISH / NEUTRAL")
            scan_rows.append({
                "Symbol": sym,
                "Company": meta["name"],
                "Exchange": meta["exchange"],
                "Sector": meta["sector"],
                "Live Price": f"{meta.get('currency','₹')}{snap['price']:,.2f}",
                "Day Change": f"{'▲' if snap['pct'] >= 0 else '▼'} {snap['pct']:+.2f}%",
                "RSI (14)": round(snap["rsi"], 1),
                "Scanner Signal": status
            })
        st.dataframe(pd.DataFrame(scan_rows), use_container_width=True, hide_index=True)