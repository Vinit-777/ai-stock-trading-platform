from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import ast
import base64
import copy
import html
import hashlib
import hmac
import json
import operator
import os
from pathlib import Path
import re
import sqlite3
import urllib.parse
import urllib.request
import warnings
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

import altair as alt
import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
import yfinance as yf

MODELS_DIR = Path(__file__).resolve().parent / "models"

_pandas4_warn = getattr(pd.errors, "Pandas4Warning", None)
if _pandas4_warn is not None:
    warnings.filterwarnings("ignore", category=_pandas4_warn)

FINANCESIGHT_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="196" height="36" viewBox="0 0 212 40" fill="none">
  <rect width="38" height="38" x="1" y="1" rx="10" fill="url(#fs_grad)"/>
  <path d="M9 26L16 19L21.5 23L30 12" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M23.5 12H30V18.5" stroke="#38BDF8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="16" cy="19" r="2.4" fill="#34D399"/>
  <text x="48" y="26" font-family="Plus Jakarta Sans, Inter, sans-serif" font-size="18" font-weight="800" fill="#38BDF8">FINANCE</text>
  <text x="131" y="26" font-family="Plus Jakarta Sans, Inter, sans-serif" font-size="18" font-weight="800" fill="#64748B">SIGHT</text>
  <defs>
    <linearGradient id="fs_grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
      <stop stop-color="#2563EB"/>
      <stop offset="0.55" stop-color="#1E3A8A"/>
      <stop offset="1" stop-color="#0F172A"/>
    </linearGradient>
  </defs>
</svg>"""

FINANCESIGHT_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 40 40" fill="none">
  <rect width="40" height="40" rx="10" fill="url(#fs_i_grad)"/>
  <path d="M9 26L16 19L22 23L31 12" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M24 12H31V19" stroke="#38BDF8" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="16" cy="19" r="2.5" fill="#34D399"/>
  <defs>
    <linearGradient id="fs_i_grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
      <stop stop-color="#2563EB"/>
      <stop offset="0.55" stop-color="#1E3A8A"/>
      <stop offset="1" stop-color="#0F172A"/>
    </linearGradient>
  </defs>
</svg>"""

IST_TZ = ZoneInfo("Asia/Kolkata")
US_ET_TZ = ZoneInfo("America/New_York")
DEFAULT_USDINR_RATE = 92.98

MARKET_INDICES = {
    "^NSEI": {"name": "NIFTY 50", "exchange": "NSE", "currency": ""},
    "^BSESN": {"name": "SENSEX", "exchange": "BSE", "currency": ""},
    "^IXIC": {"name": "NASDAQ Composite", "exchange": "US", "currency": ""},
    "^GSPC": {"name": "S&P 500", "exchange": "US", "currency": ""},
}

DEFAULT_INDEX_SNAPSHOTS = {
    "^NSEI": {"price": 25607.20, "change": 112.40, "pct": 0.44, "sparkline": [25210, 25340, 25410, 25495, 25607]},
    "^BSESN": {"price": 83339.26, "change": 345.10, "pct": 0.42, "sparkline": [82150, 82540, 82880, 82994, 83339]},
    "^IXIC": {"price": 23585.80, "change": 168.90, "pct": 0.72, "sparkline": [23010, 23180, 23290, 23417, 23585]},
    "^GSPC": {"price": 7182.78, "change": 34.60, "pct": 0.48, "sparkline": [7040, 7085, 7112, 7148, 7182]},
    "USDINR=X": {"price": DEFAULT_USDINR_RATE, "change": 0.14, "pct": 0.15, "sparkline": [92.35, 92.48, 92.62, 92.84, 92.98]},
}

STOCK_CATALOG = {
    "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Energy & Telecom", "domain": "ril.com", "exchange": "NSE", "currency": "₹"},
    "TCS.NS": {"name": "Tata Consultancy Services", "sector": "IT Services", "domain": "tcs.com", "exchange": "NSE", "currency": "₹"},
    "HDFCBANK.NS": {"name": "HDFC Bank", "sector": "Private Banking", "domain": "hdfcbank.com", "exchange": "NSE", "currency": "₹"},
    "INFY.NS": {"name": "Infosys", "sector": "IT Consulting", "domain": "infosys.com", "exchange": "NSE", "currency": "₹"},
    "ICICIBANK.NS": {"name": "ICICI Bank", "sector": "Private Banking", "domain": "icicibank.com", "exchange": "NSE", "currency": "₹"},
    "SBIN.NS": {"name": "State Bank of India", "sector": "PSU Banking", "domain": "onlinesbi.sbi", "exchange": "NSE", "currency": "₹"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel", "sector": "Telecom", "domain": "airtel.in", "exchange": "NSE", "currency": "₹"},
    "ETERNAL.NS": {"name": "Eternal Ltd. (Zomato)", "sector": "FoodTech & Commerce", "domain": "zomato.com", "exchange": "NSE", "currency": "₹"},
    "JIOFIN.NS": {"name": "Jio Financial Services", "sector": "FinTech & NBFC", "domain": "jio.com", "exchange": "NSE", "currency": "₹"},
    "TMPV.NS": {"name": "Tata Motors (PV)", "sector": "Automotive & EV", "domain": "tatamotors.com", "exchange": "NSE", "currency": "₹"},
    "TMCV.NS": {"name": "Tata Motors (CV)", "sector": "Commercial Vehicles", "domain": "tatamotors.com", "exchange": "NSE", "currency": "₹"},
    "HAL.NS": {"name": "Hindustan Aeronautics", "sector": "Aerospace & Defence", "domain": "hal-india.co.in", "exchange": "NSE", "currency": "₹"},
    "ITC.NS": {"name": "ITC Limited", "sector": "FMCG & Conglomerate", "domain": "itcportal.com", "exchange": "NSE", "currency": "₹"},
    "LT.NS": {"name": "Larsen & Toubro", "sector": "Engineering & Infra", "domain": "larsentoubro.com", "exchange": "NSE", "currency": "₹"},
    "BAJFINANCE.NS": {"name": "Bajaj Finance", "sector": "Consumer Finance", "domain": "bajajfinserv.in", "exchange": "NSE", "currency": "₹"},
    "SUNPHARMA.NS": {"name": "Sun Pharma", "sector": "Pharmaceuticals", "domain": "sunpharma.com", "exchange": "NSE", "currency": "₹"},
    "MARUTI.NS": {"name": "Maruti Suzuki", "sector": "Automobiles", "domain": "marutisuzuki.com", "exchange": "NSE", "currency": "₹"},
    "M&M.NS": {"name": "Mahindra & Mahindra", "sector": "Automobiles & SUVs", "domain": "mahindra.com", "exchange": "NSE", "currency": "₹"},
    "TITAN.NS": {"name": "Titan Company", "sector": "Luxury & Jewellery", "domain": "titan.co.in", "exchange": "NSE", "currency": "₹"},
    "AXISBANK.NS": {"name": "Axis Bank", "sector": "Private Banking", "domain": "axisbank.com", "exchange": "NSE", "currency": "₹"},
    "KOTAKBANK.NS": {"name": "Kotak Mahindra Bank", "sector": "Private Banking", "domain": "kotak.com", "exchange": "NSE", "currency": "₹"},
    "ADANIENT.NS": {"name": "Adani Enterprises", "sector": "Conglomerate & Infra", "domain": "adani.com", "exchange": "NSE", "currency": "₹"},
    "TATASTEEL.NS": {"name": "Tata Steel", "sector": "Metals & Mining", "domain": "tatasteel.com", "exchange": "NSE", "currency": "₹"},
    "WIPRO.NS": {"name": "Wipro Limited", "sector": "IT Services", "domain": "wipro.com", "exchange": "NSE", "currency": "₹"},
    "AAPL": {"name": "Apple Inc.", "sector": "Consumer Tech", "domain": "apple.com", "exchange": "NASDAQ", "currency": "$"},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "AI & Semiconductors", "domain": "nvidia.com", "exchange": "NASDAQ", "currency": "$"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Cloud & AI", "domain": "microsoft.com", "exchange": "NASDAQ", "currency": "$"},
    "TSLA": {"name": "Tesla Inc.", "sector": "EV & Robotics", "domain": "tesla.com", "exchange": "NASDAQ", "currency": "$"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Search & Cloud AI", "domain": "google.com", "exchange": "NASDAQ", "currency": "$"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "E-Commerce & Cloud", "domain": "amazon.com", "exchange": "NASDAQ", "currency": "$"},
    "META": {"name": "Meta Platforms", "sector": "Social & AI", "domain": "meta.com", "exchange": "NASDAQ", "currency": "$"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Streaming & Media", "domain": "netflix.com", "exchange": "NASDAQ", "currency": "$"},
    "AMD": {"name": "AMD Inc.", "sector": "Semiconductors", "domain": "amd.com", "exchange": "NASDAQ", "currency": "$"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Semiconductors", "domain": "broadcom.com", "exchange": "NASDAQ", "currency": "$"},
    "PLTR": {"name": "Palantir Technologies", "sector": "Enterprise AI", "domain": "palantir.com", "exchange": "NASDAQ", "currency": "$"},
    "INTC": {"name": "Intel Corp.", "sector": "Semiconductors", "domain": "intel.com", "exchange": "NASDAQ", "currency": "$"},
    "COIN": {"name": "Coinbase Global", "sector": "Crypto Exchange", "domain": "coinbase.com", "exchange": "NASDAQ", "currency": "$"},
    "UBER": {"name": "Uber Technologies", "sector": "Mobility & Delivery", "domain": "uber.com", "exchange": "NYSE", "currency": "$"},
    "ADBE": {"name": "Adobe Inc.", "sector": "Creative Software", "domain": "adobe.com", "exchange": "NASDAQ", "currency": "$"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Enterprise Cloud", "domain": "salesforce.com", "exchange": "NYSE", "currency": "$"},
    "ORCL": {"name": "Oracle Corp.", "sector": "Cloud Infrastructure", "domain": "oracle.com", "exchange": "NYSE", "currency": "$"},
    "JPM": {"name": "JPMorgan Chase", "sector": "Investment Banking", "domain": "jpmorganchase.com", "exchange": "NYSE", "currency": "$"},
    "V": {"name": "Visa Inc.", "sector": "Global Payments", "domain": "visa.com", "exchange": "NYSE", "currency": "$"},
    "MA": {"name": "Mastercard Inc.", "sector": "Payment Networks", "domain": "mastercard.com", "exchange": "NYSE", "currency": "$"},
    "WMT": {"name": "Walmart Inc.", "sector": "Global Retail", "domain": "walmart.com", "exchange": "NYSE", "currency": "$"},
    "DIS": {"name": "Walt Disney Co.", "sector": "Entertainment", "domain": "thewaltdisneycompany.com", "exchange": "NYSE", "currency": "$"},
    "NKE": {"name": "Nike Inc.", "sector": "Athletic Apparel", "domain": "nike.com", "exchange": "NYSE", "currency": "$"},
    "KO": {"name": "Coca-Cola Co.", "sector": "Beverages", "domain": "coca-colacompany.com", "exchange": "NYSE", "currency": "$"},
    "HINDUNILVR.NS": {"name": "Hindustan Unilever", "sector": "FMCG", "domain": "hul.co.in", "exchange": "NSE", "currency": "₹"},
    "HCLTECH.NS": {"name": "HCL Technologies", "sector": "IT Services", "domain": "hcltech.com", "exchange": "NSE", "currency": "₹"},
    "ULTRACEMCO.NS": {"name": "UltraTech Cement", "sector": "Cement & Materials", "domain": "ultratechcement.com", "exchange": "NSE", "currency": "₹"},
    "NTPC.NS": {"name": "NTPC Limited", "sector": "Power Generation", "domain": "ntpc.co.in", "exchange": "NSE", "currency": "₹"},
    "ONGC.NS": {"name": "ONGC", "sector": "Oil & Gas", "domain": "ongcindia.com", "exchange": "NSE", "currency": "₹"},
    "ADANIPORTS.NS": {"name": "Adani Ports & SEZ", "sector": "Ports & Logistics", "domain": "adaniports.com", "exchange": "NSE", "currency": "₹"},
    "POWERGRID.NS": {"name": "Power Grid Corp", "sector": "Power Transmission", "domain": "powergrid.in", "exchange": "NSE", "currency": "₹"},
    "COALINDIA.NS": {"name": "Coal India", "sector": "Mining & Minerals", "domain": "coalindia.in", "exchange": "NSE", "currency": "₹"},
    "ASIANPAINT.NS": {"name": "Asian Paints", "sector": "Paints & Home Decor", "domain": "asianpaints.com", "exchange": "NSE", "currency": "₹"},
    "BAJAJFINSV.NS": {"name": "Bajaj Finserv", "sector": "Financial Services", "domain": "bajajfinserv.in", "exchange": "NSE", "currency": "₹"},
    "JSWSTEEL.NS": {"name": "JSW Steel", "sector": "Metals & Mining", "domain": "jsw.in", "exchange": "NSE", "currency": "₹"},
    "NESTLEIND.NS": {"name": "Nestle India", "sector": "FMCG & Foods", "domain": "nestle.in", "exchange": "NSE", "currency": "₹"},
    "TECHM.NS": {"name": "Tech Mahindra", "sector": "IT Services", "domain": "techmahindra.com", "exchange": "NSE", "currency": "₹"},
    "GRASIM.NS": {"name": "Grasim Industries", "sector": "Diversified Materials", "domain": "adityabirla.com", "exchange": "NSE", "currency": "₹"},
    "HINDALCO.NS": {"name": "Hindalco Industries", "sector": "Metals & Aluminium", "domain": "hindalco.com", "exchange": "NSE", "currency": "₹"},
    "CIPLA.NS": {"name": "Cipla Limited", "sector": "Pharmaceuticals", "domain": "cipla.com", "exchange": "NSE", "currency": "₹"},
    "DRREDDY.NS": {"name": "Dr. Reddy's Labs", "sector": "Pharmaceuticals", "domain": "drreddys.com", "exchange": "NSE", "currency": "₹"},
    "BRITANNIA.NS": {"name": "Britannia Industries", "sector": "FMCG & Foods", "domain": "britannia.co.in", "exchange": "NSE", "currency": "₹"},
    "APOLLOHOSP.NS": {"name": "Apollo Hospitals", "sector": "Healthcare", "domain": "apollohospitals.com", "exchange": "NSE", "currency": "₹"},
    "EICHERMOT.NS": {"name": "Eicher Motors", "sector": "Automobiles", "domain": "eichermotors.com", "exchange": "NSE", "currency": "₹"},
    "BAJAJ-AUTO.NS": {"name": "Bajaj Auto", "sector": "Two-Wheelers & EV", "domain": "bajajauto.com", "exchange": "NSE", "currency": "₹"},
    "HEROMOTOCO.NS": {"name": "Hero MotoCorp", "sector": "Two-Wheelers", "domain": "heromotocorp.com", "exchange": "NSE", "currency": "₹"},
    "INDUSINDBK.NS": {"name": "IndusInd Bank", "sector": "Private Banking", "domain": "indusind.com", "exchange": "NSE", "currency": "₹"},
    "DIVISLAB.NS": {"name": "Divi's Laboratories", "sector": "Pharmaceuticals", "domain": "divislabs.com", "exchange": "NSE", "currency": "₹"},
    "BPCL.NS": {"name": "Bharat Petroleum", "sector": "Oil & Refining", "domain": "bharatpetroleum.in", "exchange": "NSE", "currency": "₹"},
    "TATACONSUM.NS": {"name": "Tata Consumer Products", "sector": "FMCG & Beverages", "domain": "tataconsumer.com", "exchange": "NSE", "currency": "₹"},
    "HDFCLIFE.NS": {"name": "HDFC Life Insurance", "sector": "Insurance", "domain": "hdfclife.com", "exchange": "NSE", "currency": "₹"},
    "SBILIFE.NS": {"name": "SBI Life Insurance", "sector": "Insurance", "domain": "sbilife.co.in", "exchange": "NSE", "currency": "₹"},
    "SHRIRAMFIN.NS": {"name": "Shriram Finance", "sector": "NBFC & Lending", "domain": "shriramfinance.in", "exchange": "NSE", "currency": "₹"},
    "TRENT.NS": {"name": "Trent Limited", "sector": "Retail & Apparel", "domain": "westside.com", "exchange": "NSE", "currency": "₹"},
    "BEL.NS": {"name": "Bharat Electronics", "sector": "Defence Electronics", "domain": "bel-india.in", "exchange": "NSE", "currency": "₹"},
    "IRCTC.NS": {"name": "IRCTC Limited", "sector": "Railways & Tourism", "domain": "irctc.co.in", "exchange": "NSE", "currency": "₹"},
    "INDIGO.NS": {"name": "InterGlobe Aviation", "sector": "Aviation", "domain": "goindigo.in", "exchange": "NSE", "currency": "₹"},
    "DLF.NS": {"name": "DLF Limited", "sector": "Real Estate", "domain": "dlf.in", "exchange": "NSE", "currency": "₹"},
    "PIDILITIND.NS": {"name": "Pidilite Industries", "sector": "Specialty Chemicals", "domain": "pidilite.com", "exchange": "NSE", "currency": "₹"},
    "SIEMENS.NS": {"name": "Siemens India", "sector": "Industrial Automation", "domain": "siemens.com", "exchange": "NSE", "currency": "₹"},
    "ABB.NS": {"name": "ABB India", "sector": "Industrial Tech", "domain": "abb.com", "exchange": "NSE", "currency": "₹"},
    "AMBUJACEM.NS": {"name": "Ambuja Cements", "sector": "Cement & Materials", "domain": "ambujacement.com", "exchange": "NSE", "currency": "₹"},
    "VEDL.NS": {"name": "Vedanta Limited", "sector": "Metals & Mining", "domain": "vedantalimited.com", "exchange": "NSE", "currency": "₹"},
    "IOC.NS": {"name": "Indian Oil Corp", "sector": "Oil & Refining", "domain": "iocl.com", "exchange": "NSE", "currency": "₹"},
    "GAIL.NS": {"name": "GAIL India", "sector": "Gas Utilities", "domain": "gailonline.com", "exchange": "NSE", "currency": "₹"},
    "BANKBARODA.NS": {"name": "Bank of Baroda", "sector": "PSU Banking", "domain": "bankofbaroda.in", "exchange": "NSE", "currency": "₹"},
    "PNB.NS": {"name": "Punjab National Bank", "sector": "PSU Banking", "domain": "pnbindia.in", "exchange": "NSE", "currency": "₹"},
    "CANBK.NS": {"name": "Canara Bank", "sector": "PSU Banking", "domain": "canarabank.com", "exchange": "NSE", "currency": "₹"},
    "UNIONBANK.NS": {"name": "Union Bank of India", "sector": "PSU Banking", "domain": "unionbankofindia.co.in", "exchange": "NSE", "currency": "₹"},
    "PFC.NS": {"name": "Power Finance Corp", "sector": "Power Finance", "domain": "pfcindia.com", "exchange": "NSE", "currency": "₹"},
    "RECLTD.NS": {"name": "REC Limited", "sector": "Power Finance", "domain": "recindia.nic.in", "exchange": "NSE", "currency": "₹"},
    "IRFC.NS": {"name": "Indian Railway Finance", "sector": "Railways Finance", "domain": "irfc.co.in", "exchange": "NSE", "currency": "₹"},
    "RVNL.NS": {"name": "Rail Vikas Nigam", "sector": "Railways Infra", "domain": "rvnl.org", "exchange": "NSE", "currency": "₹"},
    "MAZDOCK.NS": {"name": "Mazagon Dock Shipbuilders", "sector": "Defence Shipbuilding", "domain": "mazagondock.in", "exchange": "NSE", "currency": "₹"},
    "COCHINSHIP.NS": {"name": "Cochin Shipyard", "sector": "Defence Shipbuilding", "domain": "cochinshipyard.in", "exchange": "NSE", "currency": "₹"},
    "BHEL.NS": {"name": "Bharat Heavy Electricals", "sector": "Heavy Engineering", "domain": "bhel.com", "exchange": "NSE", "currency": "₹"},
    "SUZLON.NS": {"name": "Suzlon Energy", "sector": "Renewable Energy", "domain": "suzlon.com", "exchange": "NSE", "currency": "₹"},
    "TATAPOWER.NS": {"name": "Tata Power", "sector": "Power & Renewables", "domain": "tatapower.com", "exchange": "NSE", "currency": "₹"},
    "ADANIPOWER.NS": {"name": "Adani Power", "sector": "Power Generation", "domain": "adanipower.com", "exchange": "NSE", "currency": "₹"},
    "ADANIGREEN.NS": {"name": "Adani Green Energy", "sector": "Renewable Energy", "domain": "adanigreenenergy.com", "exchange": "NSE", "currency": "₹"},
    "ADANIENSOL.NS": {"name": "Adani Energy Solutions", "sector": "Power Transmission", "domain": "adanienergysolutions.com", "exchange": "NSE", "currency": "₹"},
    "JSWENERGY.NS": {"name": "JSW Energy", "sector": "Power & Renewables", "domain": "jsw.in", "exchange": "NSE", "currency": "₹"},
    "NHPC.NS": {"name": "NHPC Limited", "sector": "Hydro Power", "domain": "nhpcindia.com", "exchange": "NSE", "currency": "₹"},
    "IREDA.NS": {"name": "IREDA", "sector": "Green Finance", "domain": "ireda.in", "exchange": "NSE", "currency": "₹"},
    "YESBANK.NS": {"name": "Yes Bank", "sector": "Private Banking", "domain": "yesbank.in", "exchange": "NSE", "currency": "₹"},
    "IDFCFIRSTB.NS": {"name": "IDFC First Bank", "sector": "Private Banking", "domain": "idfcfirstbank.com", "exchange": "NSE", "currency": "₹"},
    "FEDERALBNK.NS": {"name": "Federal Bank", "sector": "Private Banking", "domain": "federalbank.co.in", "exchange": "NSE", "currency": "₹"},
    "AUBANK.NS": {"name": "AU Small Finance Bank", "sector": "Banking", "domain": "aubank.in", "exchange": "NSE", "currency": "₹"},
    "BANDHANBNK.NS": {"name": "Bandhan Bank", "sector": "Banking", "domain": "bandhanbank.com", "exchange": "NSE", "currency": "₹"},
    "CHOLAFIN.NS": {"name": "Cholamandalam Inv.", "sector": "NBFC & Lending", "domain": "cholamandalam.com", "exchange": "NSE", "currency": "₹"},
    "MUTHOOTFIN.NS": {"name": "Muthoot Finance", "sector": "Gold Finance", "domain": "muthootfinance.com", "exchange": "NSE", "currency": "₹"},
    "SBICARD.NS": {"name": "SBI Cards", "sector": "Financial Services", "domain": "sbicard.com", "exchange": "NSE", "currency": "₹"},
    "ICICIGI.NS": {"name": "ICICI Lombard", "sector": "Insurance", "domain": "icicilombard.com", "exchange": "NSE", "currency": "₹"},
    "ICICIPRULI.NS": {"name": "ICICI Prudential Life", "sector": "Insurance", "domain": "iciciprulife.com", "exchange": "NSE", "currency": "₹"},
    "HDFCAMC.NS": {"name": "HDFC AMC", "sector": "Asset Management", "domain": "hdfcfund.com", "exchange": "NSE", "currency": "₹"},
    "BSE.NS": {"name": "BSE Limited", "sector": "Stock Exchange", "domain": "bseindia.com", "exchange": "NSE", "currency": "₹"},
    "CDSL.NS": {"name": "CDSL", "sector": "Market Infrastructure", "domain": "cdslindia.com", "exchange": "NSE", "currency": "₹"},
    "MCX.NS": {"name": "MCX India", "sector": "Commodity Exchange", "domain": "mcxindia.com", "exchange": "NSE", "currency": "₹"},
    "ANGELONE.NS": {"name": "Angel One", "sector": "FinTech & Broking", "domain": "angelone.in", "exchange": "NSE", "currency": "₹"},
    "PAYTM.NS": {"name": "One97 Comm. (Paytm)", "sector": "FinTech & Payments", "domain": "paytm.com", "exchange": "NSE", "currency": "₹"},
    "POLICYBZR.NS": {"name": "PB Fintech (Policybazaar)", "sector": "InsurTech", "domain": "policybazaar.com", "exchange": "NSE", "currency": "₹"},
    "NYKAA.NS": {"name": "FSN E-Commerce (Nykaa)", "sector": "Beauty & E-Commerce", "domain": "nykaa.com", "exchange": "NSE", "currency": "₹"},
    "DELHIVERY.NS": {"name": "Delhivery Limited", "sector": "Logistics", "domain": "delhivery.com", "exchange": "NSE", "currency": "₹"},
    "SWIGGY.NS": {"name": "Swiggy Limited", "sector": "FoodTech & Delivery", "domain": "swiggy.com", "exchange": "NSE", "currency": "₹"},
    "DMART.NS": {"name": "Avenue Supermarts (DMart)", "sector": "Retail", "domain": "dmartindia.com", "exchange": "NSE", "currency": "₹"},
    "DABUR.NS": {"name": "Dabur India", "sector": "FMCG", "domain": "dabur.com", "exchange": "NSE", "currency": "₹"},
    "MARICO.NS": {"name": "Marico Limited", "sector": "FMCG", "domain": "marico.com", "exchange": "NSE", "currency": "₹"},
    "GODREJCP.NS": {"name": "Godrej Consumer", "sector": "FMCG", "domain": "godrejcp.com", "exchange": "NSE", "currency": "₹"},
    "COLPAL.NS": {"name": "Colgate-Palmolive India", "sector": "FMCG", "domain": "colgatepalmolive.co.in", "exchange": "NSE", "currency": "₹"},
    "VBL.NS": {"name": "Varun Beverages", "sector": "Beverages", "domain": "varunbeverages.com", "exchange": "NSE", "currency": "₹"},
    "UNITDSPR.NS": {"name": "United Spirits", "sector": "Beverages", "domain": "diageoindia.com", "exchange": "NSE", "currency": "₹"},
    "UBL.NS": {"name": "United Breweries", "sector": "Beverages", "domain": "kingfisherworld.com", "exchange": "NSE", "currency": "₹"},
    "HAVELLS.NS": {"name": "Havells India", "sector": "Electricals", "domain": "havells.com", "exchange": "NSE", "currency": "₹"},
    "POLYCAB.NS": {"name": "Polycab India", "sector": "Cables & Wires", "domain": "polycab.com", "exchange": "NSE", "currency": "₹"},
    "VOLTAS.NS": {"name": "Voltas Limited", "sector": "Consumer Durables", "domain": "voltas.com", "exchange": "NSE", "currency": "₹"},
    "DIXON.NS": {"name": "Dixon Technologies", "sector": "Electronics Mfg.", "domain": "dixoninfo.com", "exchange": "NSE", "currency": "₹"},
    "CROMPTON.NS": {"name": "Crompton Greaves", "sector": "Consumer Durables", "domain": "crompton.co.in", "exchange": "NSE", "currency": "₹"},
    "PERSISTENT.NS": {"name": "Persistent Systems", "sector": "IT & Engineering", "domain": "persistent.com", "exchange": "NSE", "currency": "₹"},
    "COFORGE.NS": {"name": "Coforge Limited", "sector": "IT Services", "domain": "coforge.com", "exchange": "NSE", "currency": "₹"},
    "MPHASIS.NS": {"name": "Mphasis Limited", "sector": "IT Services", "domain": "mphasis.com", "exchange": "NSE", "currency": "₹"},
    "LTTS.NS": {"name": "L&T Technology Services", "sector": "ER&D Services", "domain": "ltts.com", "exchange": "NSE", "currency": "₹"},
    "TATAELXSI.NS": {"name": "Tata Elxsi", "sector": "Design & Tech", "domain": "tataelxsi.com", "exchange": "NSE", "currency": "₹"},
    "KPITTECH.NS": {"name": "KPIT Technologies", "sector": "Auto Software", "domain": "kpit.com", "exchange": "NSE", "currency": "₹"},
    "NAUKRI.NS": {"name": "Info Edge (Naukri)", "sector": "Internet & Tech", "domain": "naukri.com", "exchange": "NSE", "currency": "₹"},
    "OFSS.NS": {"name": "Oracle Financial Services", "sector": "FinTech Software", "domain": "oracle.com", "exchange": "NSE", "currency": "₹"},
    "LUPIN.NS": {"name": "Lupin Limited", "sector": "Pharmaceuticals", "domain": "lupin.com", "exchange": "NSE", "currency": "₹"},
    "AUROPHARMA.NS": {"name": "Aurobindo Pharma", "sector": "Pharmaceuticals", "domain": "aurobindo.com", "exchange": "NSE", "currency": "₹"},
    "TORNTPHARM.NS": {"name": "Torrent Pharmaceuticals", "sector": "Pharmaceuticals", "domain": "torrentpharma.com", "exchange": "NSE", "currency": "₹"},
    "ALKEM.NS": {"name": "Alkem Laboratories", "sector": "Pharmaceuticals", "domain": "alkemlabs.com", "exchange": "NSE", "currency": "₹"},
    "ZYDUSLIFE.NS": {"name": "Zydus Lifesciences", "sector": "Pharmaceuticals", "domain": "zyduslife.com", "exchange": "NSE", "currency": "₹"},
    "BIOCON.NS": {"name": "Biocon Limited", "sector": "Biotechnology", "domain": "biocon.com", "exchange": "NSE", "currency": "₹"},
    "MAXHEALTH.NS": {"name": "Max Healthcare", "sector": "Healthcare", "domain": "maxhealthcare.in", "exchange": "NSE", "currency": "₹"},
    "FORTIS.NS": {"name": "Fortis Healthcare", "sector": "Healthcare", "domain": "fortishealthcare.com", "exchange": "NSE", "currency": "₹"},
    "TVSMOTOR.NS": {"name": "TVS Motor Company", "sector": "Two-Wheelers & EV", "domain": "tvsmotor.com", "exchange": "NSE", "currency": "₹"},
    "ASHOKLEY.NS": {"name": "Ashok Leyland", "sector": "Commercial Vehicles", "domain": "ashokleyland.com", "exchange": "NSE", "currency": "₹"},
    "MOTHERSON.NS": {"name": "Samvardhana Motherson", "sector": "Auto Ancillaries", "domain": "motherson.com", "exchange": "NSE", "currency": "₹"},
    "BOSCHLTD.NS": {"name": "Bosch Limited", "sector": "Auto Components", "domain": "bosch.in", "exchange": "NSE", "currency": "₹"},
    "MRF.NS": {"name": "MRF Limited", "sector": "Tyres & Auto", "domain": "mrftyres.com", "exchange": "NSE", "currency": "₹"},
    "BHARATFORG.NS": {"name": "Bharat Forge", "sector": "Forging & Defence", "domain": "bharatforge.com", "exchange": "NSE", "currency": "₹"},
    "SONACOMS.NS": {"name": "Sona BLW Precision", "sector": "EV Components", "domain": "sonacomstar.com", "exchange": "NSE", "currency": "₹"},
    "CGPOWER.NS": {"name": "CG Power & Industrial", "sector": "Power Equipment", "domain": "cgglobal.com", "exchange": "NSE", "currency": "₹"},
    "CUMMINSIND.NS": {"name": "Cummins India", "sector": "Industrial Engines", "domain": "cummins.com", "exchange": "NSE", "currency": "₹"},
    "SAIL.NS": {"name": "Steel Authority of India", "sector": "Metals & Mining", "domain": "sail.co.in", "exchange": "NSE", "currency": "₹"},
    "NMDC.NS": {"name": "NMDC Limited", "sector": "Mining & Minerals", "domain": "nmdc.co.in", "exchange": "NSE", "currency": "₹"},
    "NATIONALUM.NS": {"name": "NALCO", "sector": "Metals & Aluminium", "domain": "nalcoindia.com", "exchange": "NSE", "currency": "₹"},
    "JINDALSTEL.NS": {"name": "Jindal Steel & Power", "sector": "Metals & Mining", "domain": "jindalsteelpower.com", "exchange": "NSE", "currency": "₹"},
    "SHREECEM.NS": {"name": "Shree Cement", "sector": "Cement & Materials", "domain": "shreecement.com", "exchange": "NSE", "currency": "₹"},
    "ACC.NS": {"name": "ACC Limited", "sector": "Cement & Materials", "domain": "acclimited.com", "exchange": "NSE", "currency": "₹"},
    "LODHA.NS": {"name": "Macrotech Developers (Lodha)", "sector": "Real Estate", "domain": "lodhagroup.com", "exchange": "NSE", "currency": "₹"},
    "GODREJPROP.NS": {"name": "Godrej Properties", "sector": "Real Estate", "domain": "godrejproperties.com", "exchange": "NSE", "currency": "₹"},
    "OBEROIRLTY.NS": {"name": "Oberoi Realty", "sector": "Real Estate", "domain": "oberoirealty.com", "exchange": "NSE", "currency": "₹"},
    "PRESTIGE.NS": {"name": "Prestige Estates", "sector": "Real Estate", "domain": "prestigeconstructions.com", "exchange": "NSE", "currency": "₹"},
    "PHOENIXLTD.NS": {"name": "Phoenix Mills", "sector": "Retail Real Estate", "domain": "thephoenixmills.com", "exchange": "NSE", "currency": "₹"},
    "INDHOTEL.NS": {"name": "Indian Hotels (Taj)", "sector": "Hospitality", "domain": "ihcltata.com", "exchange": "NSE", "currency": "₹"},
    "CONCOR.NS": {"name": "Container Corp", "sector": "Logistics", "domain": "concorindia.co.in", "exchange": "NSE", "currency": "₹"},
    "PIIND.NS": {"name": "PI Industries", "sector": "Agrochemicals", "domain": "piindustries.com", "exchange": "NSE", "currency": "₹"},
    "SRF.NS": {"name": "SRF Limited", "sector": "Specialty Chemicals", "domain": "srf.com", "exchange": "NSE", "currency": "₹"},
    "UPL.NS": {"name": "UPL Limited", "sector": "Agrochemicals", "domain": "upl-ltd.com", "exchange": "NSE", "currency": "₹"},
    "ASTRAL.NS": {"name": "Astral Limited", "sector": "Building Materials", "domain": "astralpipes.com", "exchange": "NSE", "currency": "₹"},
    "SUPREMEIND.NS": {"name": "Supreme Industries", "sector": "Plastics & Pipes", "domain": "supreme.co.in", "exchange": "NSE", "currency": "₹"},
    "PAGEIND.NS": {"name": "Page Industries (Jockey)", "sector": "Apparel", "domain": "pageindustries.com", "exchange": "NSE", "currency": "₹"},
    "JUBLFOOD.NS": {"name": "Jubilant FoodWorks", "sector": "QSR & Food", "domain": "dominos.co.in", "exchange": "NSE", "currency": "₹"},
    "TATACOMM.NS": {"name": "Tata Communications", "sector": "Telecom & Cloud", "domain": "tatacommunications.com", "exchange": "NSE", "currency": "₹"},
    "IDEA.NS": {"name": "Vodafone Idea", "sector": "Telecom", "domain": "myvi.in", "exchange": "NSE", "currency": "₹"},
    "INDUSTOWER.NS": {"name": "Indus Towers", "sector": "Telecom Infra", "domain": "industowers.com", "exchange": "NSE", "currency": "₹"},
    "GMRAIRPORT.NS": {"name": "GMR Airports", "sector": "Aviation Infra", "domain": "gmrgroup.in", "exchange": "NSE", "currency": "₹"},
    "TIINDIA.NS": {"name": "Tube Investments", "sector": "Engineering & EV", "domain": "tiindia.com", "exchange": "NSE", "currency": "₹"},
    "LICI.NS": {"name": "Life Insurance Corp", "sector": "Insurance", "domain": "licindia.in", "exchange": "NSE", "currency": "₹"},
    "OIL.NS": {"name": "Oil India", "sector": "Oil & Gas", "domain": "oil-india.com", "exchange": "NSE", "currency": "₹"},
    "HUDCO.NS": {"name": "HUDCO", "sector": "Housing Finance", "domain": "hudco.org.in", "exchange": "NSE", "currency": "₹"},
    "NBCC.NS": {"name": "NBCC India", "sector": "Construction", "domain": "nbccindia.in", "exchange": "NSE", "currency": "₹"},
    "SJVN.NS": {"name": "SJVN Limited", "sector": "Power & Hydro", "domain": "sjvn.nic.in", "exchange": "NSE", "currency": "₹"},
    "BRK-B": {"name": "Berkshire Hathaway", "sector": "Conglomerate", "domain": "berkshirehathaway.com", "exchange": "NYSE", "currency": "$"},
    "LLY": {"name": "Eli Lilly", "sector": "Pharmaceuticals", "domain": "lilly.com", "exchange": "NYSE", "currency": "$"},
    "XOM": {"name": "Exxon Mobil", "sector": "Oil & Gas", "domain": "exxonmobil.com", "exchange": "NYSE", "currency": "$"},
    "COST": {"name": "Costco Wholesale", "sector": "Retail", "domain": "costco.com", "exchange": "NASDAQ", "currency": "$"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "domain": "jnj.com", "exchange": "NYSE", "currency": "$"},
    "HD": {"name": "Home Depot", "sector": "Home Improvement", "domain": "homedepot.com", "exchange": "NYSE", "currency": "$"},
    "PG": {"name": "Procter & Gamble", "sector": "Consumer Goods", "domain": "pg.com", "exchange": "NYSE", "currency": "$"},
    "ABBV": {"name": "AbbVie Inc.", "sector": "Biopharma", "domain": "abbvie.com", "exchange": "NYSE", "currency": "$"},
    "BAC": {"name": "Bank of America", "sector": "Banking", "domain": "bankofamerica.com", "exchange": "NYSE", "currency": "$"},
    "UNH": {"name": "UnitedHealth Group", "sector": "Healthcare", "domain": "unitedhealthgroup.com", "exchange": "NYSE", "currency": "$"},
    "CVX": {"name": "Chevron Corp.", "sector": "Oil & Gas", "domain": "chevron.com", "exchange": "NYSE", "currency": "$"},
    "PEP": {"name": "PepsiCo Inc.", "sector": "Food & Beverages", "domain": "pepsico.com", "exchange": "NASDAQ", "currency": "$"},
    "MRK": {"name": "Merck & Co.", "sector": "Pharmaceuticals", "domain": "merck.com", "exchange": "NYSE", "currency": "$"},
    "CSCO": {"name": "Cisco Systems", "sector": "Networking", "domain": "cisco.com", "exchange": "NASDAQ", "currency": "$"},
    "TMUS": {"name": "T-Mobile US", "sector": "Telecom", "domain": "t-mobile.com", "exchange": "NASDAQ", "currency": "$"},
    "WFC": {"name": "Wells Fargo", "sector": "Banking", "domain": "wellsfargo.com", "exchange": "NYSE", "currency": "$"},
    "ACN": {"name": "Accenture plc", "sector": "IT Consulting", "domain": "accenture.com", "exchange": "NYSE", "currency": "$"},
    "MCD": {"name": "McDonald's Corp.", "sector": "Restaurants", "domain": "mcdonalds.com", "exchange": "NYSE", "currency": "$"},
    "ABT": {"name": "Abbott Laboratories", "sector": "Medical Devices", "domain": "abbott.com", "exchange": "NYSE", "currency": "$"},
    "PM": {"name": "Philip Morris Intl.", "sector": "Consumer Staples", "domain": "pmi.com", "exchange": "NYSE", "currency": "$"},
    "TMO": {"name": "Thermo Fisher", "sector": "Life Sciences", "domain": "thermofisher.com", "exchange": "NYSE", "currency": "$"},
    "IBM": {"name": "IBM Corp.", "sector": "Enterprise Tech & AI", "domain": "ibm.com", "exchange": "NYSE", "currency": "$"},
    "LIN": {"name": "Linde plc", "sector": "Industrial Gases", "domain": "linde.com", "exchange": "NASDAQ", "currency": "$"},
    "GE": {"name": "GE Aerospace", "sector": "Aerospace & Defence", "domain": "geaerospace.com", "exchange": "NYSE", "currency": "$"},
    "CAT": {"name": "Caterpillar Inc.", "sector": "Heavy Machinery", "domain": "caterpillar.com", "exchange": "NYSE", "currency": "$"},
    "GS": {"name": "Goldman Sachs", "sector": "Investment Banking", "domain": "goldmansachs.com", "exchange": "NYSE", "currency": "$"},
    "MS": {"name": "Morgan Stanley", "sector": "Investment Banking", "domain": "morganstanley.com", "exchange": "NYSE", "currency": "$"},
    "ISRG": {"name": "Intuitive Surgical", "sector": "Medical Robotics", "domain": "intuitive.com", "exchange": "NASDAQ", "currency": "$"},
    "QCOM": {"name": "Qualcomm Inc.", "sector": "Semiconductors", "domain": "qualcomm.com", "exchange": "NASDAQ", "currency": "$"},
    "TXN": {"name": "Texas Instruments", "sector": "Semiconductors", "domain": "ti.com", "exchange": "NASDAQ", "currency": "$"},
    "INTU": {"name": "Intuit Inc.", "sector": "FinTech Software", "domain": "intuit.com", "exchange": "NASDAQ", "currency": "$"},
    "NOW": {"name": "ServiceNow Inc.", "sector": "Enterprise SaaS", "domain": "servicenow.com", "exchange": "NYSE", "currency": "$"},
    "AXP": {"name": "American Express", "sector": "Payments & Credit", "domain": "americanexpress.com", "exchange": "NYSE", "currency": "$"},
    "AMGN": {"name": "Amgen Inc.", "sector": "Biotechnology", "domain": "amgen.com", "exchange": "NASDAQ", "currency": "$"},
    "VZ": {"name": "Verizon", "sector": "Telecom", "domain": "verizon.com", "exchange": "NYSE", "currency": "$"},
    "T": {"name": "AT&T Inc.", "sector": "Telecom", "domain": "att.com", "exchange": "NYSE", "currency": "$"},
    "RTX": {"name": "RTX Corp.", "sector": "Aerospace & Defence", "domain": "rtx.com", "exchange": "NYSE", "currency": "$"},
    "SPGI": {"name": "S&P Global", "sector": "Financial Data", "domain": "spglobal.com", "exchange": "NYSE", "currency": "$"},
    "BLK": {"name": "BlackRock Inc.", "sector": "Asset Management", "domain": "blackrock.com", "exchange": "NYSE", "currency": "$"},
    "PFE": {"name": "Pfizer Inc.", "sector": "Pharmaceuticals", "domain": "pfizer.com", "exchange": "NYSE", "currency": "$"},
    "BKNG": {"name": "Booking Holdings", "sector": "Travel Tech", "domain": "bookingholdings.com", "exchange": "NASDAQ", "currency": "$"},
    "LOW": {"name": "Lowe's Companies", "sector": "Retail", "domain": "lowes.com", "exchange": "NYSE", "currency": "$"},
    "UNP": {"name": "Union Pacific", "sector": "Railroads", "domain": "up.com", "exchange": "NYSE", "currency": "$"},
    "HON": {"name": "Honeywell Intl.", "sector": "Industrials", "domain": "honeywell.com", "exchange": "NASDAQ", "currency": "$"},
    "SYK": {"name": "Stryker Corp.", "sector": "Medical Tech", "domain": "stryker.com", "exchange": "NYSE", "currency": "$"},
    "C": {"name": "Citigroup Inc.", "sector": "Banking", "domain": "citigroup.com", "exchange": "NYSE", "currency": "$"},
    "SCHW": {"name": "Charles Schwab", "sector": "Brokerage & Wealth", "domain": "schwab.com", "exchange": "NYSE", "currency": "$"},
    "BA": {"name": "Boeing Co.", "sector": "Aerospace", "domain": "boeing.com", "exchange": "NYSE", "currency": "$"},
    "LMT": {"name": "Lockheed Martin", "sector": "Aerospace & Defence", "domain": "lockheedmartin.com", "exchange": "NYSE", "currency": "$"},
    "AMAT": {"name": "Applied Materials", "sector": "Chip Equipment", "domain": "appliedmaterials.com", "exchange": "NASDAQ", "currency": "$"},
    "LRCX": {"name": "Lam Research", "sector": "Chip Equipment", "domain": "lamresearch.com", "exchange": "NASDAQ", "currency": "$"},
    "KLAC": {"name": "KLA Corp.", "sector": "Chip Equipment", "domain": "kla.com", "exchange": "NASDAQ", "currency": "$"},
    "MU": {"name": "Micron Technology", "sector": "Memory Chips", "domain": "micron.com", "exchange": "NASDAQ", "currency": "$"},
    "ADI": {"name": "Analog Devices", "sector": "Semiconductors", "domain": "analog.com", "exchange": "NASDAQ", "currency": "$"},
    "PANW": {"name": "Palo Alto Networks", "sector": "Cybersecurity", "domain": "paloaltonetworks.com", "exchange": "NASDAQ", "currency": "$"},
    "CRWD": {"name": "CrowdStrike", "sector": "Cybersecurity", "domain": "crowdstrike.com", "exchange": "NASDAQ", "currency": "$"},
    "FTNT": {"name": "Fortinet Inc.", "sector": "Cybersecurity", "domain": "fortinet.com", "exchange": "NASDAQ", "currency": "$"},
    "ZS": {"name": "Zscaler Inc.", "sector": "Cloud Security", "domain": "zscaler.com", "exchange": "NASDAQ", "currency": "$"},
    "SNPS": {"name": "Synopsys Inc.", "sector": "Chip Design EDA", "domain": "synopsys.com", "exchange": "NASDAQ", "currency": "$"},
    "CDNS": {"name": "Cadence Design", "sector": "Chip Design EDA", "domain": "cadence.com", "exchange": "NASDAQ", "currency": "$"},
    "MRVL": {"name": "Marvell Technology", "sector": "Semiconductors", "domain": "marvell.com", "exchange": "NASDAQ", "currency": "$"},
    "ARM": {"name": "Arm Holdings", "sector": "CPU Architecture", "domain": "arm.com", "exchange": "NASDAQ", "currency": "$"},
    "ASML": {"name": "ASML Holding", "sector": "Lithography Systems", "domain": "asml.com", "exchange": "NASDAQ", "currency": "$"},
    "TSM": {"name": "TSMC", "sector": "Chip Foundry", "domain": "tsmc.com", "exchange": "NYSE", "currency": "$"},
    "SHOP": {"name": "Shopify Inc.", "sector": "E-Commerce SaaS", "domain": "shopify.com", "exchange": "NYSE", "currency": "$"},
    "PYPL": {"name": "PayPal Holdings", "sector": "Digital Payments", "domain": "paypal.com", "exchange": "NASDAQ", "currency": "$"},
    "HOOD": {"name": "Robinhood Markets", "sector": "FinTech & Trading", "domain": "robinhood.com", "exchange": "NASDAQ", "currency": "$"},
    "SOFI": {"name": "SoFi Technologies", "sector": "Digital Banking", "domain": "sofi.com", "exchange": "NASDAQ", "currency": "$"},
    "ABNB": {"name": "Airbnb Inc.", "sector": "Travel Marketplace", "domain": "airbnb.com", "exchange": "NASDAQ", "currency": "$"},
    "DASH": {"name": "DoorDash Inc.", "sector": "Delivery Platform", "domain": "doordash.com", "exchange": "NASDAQ", "currency": "$"},
    "SPOT": {"name": "Spotify Technology", "sector": "Audio Streaming", "domain": "spotify.com", "exchange": "NYSE", "currency": "$"},
    "SNOW": {"name": "Snowflake Inc.", "sector": "Data Cloud", "domain": "snowflake.com", "exchange": "NYSE", "currency": "$"},
    "DDOG": {"name": "Datadog Inc.", "sector": "Cloud Observability", "domain": "datadoghq.com", "exchange": "NASDAQ", "currency": "$"},
    "NET": {"name": "Cloudflare Inc.", "sector": "Edge & Security", "domain": "cloudflare.com", "exchange": "NYSE", "currency": "$"},
    "MDB": {"name": "MongoDB Inc.", "sector": "Database Cloud", "domain": "mongodb.com", "exchange": "NASDAQ", "currency": "$"},
    "WDAY": {"name": "Workday Inc.", "sector": "Enterprise SaaS", "domain": "workday.com", "exchange": "NASDAQ", "currency": "$"},
    "TEAM": {"name": "Atlassian Corp.", "sector": "Collaboration SaaS", "domain": "atlassian.com", "exchange": "NASDAQ", "currency": "$"},
    "ADSK": {"name": "Autodesk Inc.", "sector": "CAD Software", "domain": "autodesk.com", "exchange": "NASDAQ", "currency": "$"},
    "SBUX": {"name": "Starbucks Corp.", "sector": "Coffee & Retail", "domain": "starbucks.com", "exchange": "NASDAQ", "currency": "$"},
    "TGT": {"name": "Target Corp.", "sector": "Retail", "domain": "target.com", "exchange": "NYSE", "currency": "$"},
    "TJX": {"name": "TJX Companies", "sector": "Apparel Retail", "domain": "tjx.com", "exchange": "NYSE", "currency": "$"},
    "DE": {"name": "Deere & Company", "sector": "Agri Machinery", "domain": "deere.com", "exchange": "NYSE", "currency": "$"},
    "UPS": {"name": "United Parcel Service", "sector": "Logistics", "domain": "ups.com", "exchange": "NYSE", "currency": "$"},
    "FDX": {"name": "FedEx Corp.", "sector": "Logistics", "domain": "fedex.com", "exchange": "NYSE", "currency": "$"},
    "MMM": {"name": "3M Company", "sector": "Industrials", "domain": "3m.com", "exchange": "NYSE", "currency": "$"},
    "F": {"name": "Ford Motor Co.", "sector": "Automobiles & EV", "domain": "ford.com", "exchange": "NYSE", "currency": "$"},
    "GM": {"name": "General Motors", "sector": "Automobiles & EV", "domain": "gm.com", "exchange": "NYSE", "currency": "$"},
    "RIVN": {"name": "Rivian Automotive", "sector": "Electric Vehicles", "domain": "rivian.com", "exchange": "NASDAQ", "currency": "$"},
    "LCID": {"name": "Lucid Group", "sector": "Electric Vehicles", "domain": "lucidmotors.com", "exchange": "NASDAQ", "currency": "$"},
    "NIO": {"name": "NIO Inc.", "sector": "Electric Vehicles", "domain": "nio.com", "exchange": "NYSE", "currency": "$"},
    "BABA": {"name": "Alibaba Group", "sector": "E-Commerce & Cloud", "domain": "alibaba.com", "exchange": "NYSE", "currency": "$"},
    "JD": {"name": "JD.com Inc.", "sector": "E-Commerce", "domain": "jd.com", "exchange": "NASDAQ", "currency": "$"},
    "PDD": {"name": "PDD Holdings", "sector": "E-Commerce", "domain": "temu.com", "exchange": "NASDAQ", "currency": "$"},
    "BIDU": {"name": "Baidu Inc.", "sector": "Search & AI", "domain": "baidu.com", "exchange": "NASDAQ", "currency": "$"},
    "SONY": {"name": "Sony Group", "sector": "Electronics & Media", "domain": "sony.com", "exchange": "NYSE", "currency": "$"},
    "TM": {"name": "Toyota Motor", "sector": "Automobiles", "domain": "toyota.com", "exchange": "NYSE", "currency": "$"},
    "SAP": {"name": "SAP SE", "sector": "Enterprise Software", "domain": "sap.com", "exchange": "NYSE", "currency": "$"},
    "NVO": {"name": "Novo Nordisk", "sector": "Pharmaceuticals", "domain": "novonordisk.com", "exchange": "NYSE", "currency": "$"},
    "AZN": {"name": "AstraZeneca", "sector": "Pharmaceuticals", "domain": "astrazeneca.com", "exchange": "NASDAQ", "currency": "$"},
    "NVS": {"name": "Novartis AG", "sector": "Pharmaceuticals", "domain": "novartis.com", "exchange": "NYSE", "currency": "$"},
    "GILD": {"name": "Gilead Sciences", "sector": "Biopharma", "domain": "gilead.com", "exchange": "NASDAQ", "currency": "$"},
    "REGN": {"name": "Regeneron Pharma", "sector": "Biotech", "domain": "regeneron.com", "exchange": "NASDAQ", "currency": "$"},
    "VRTX": {"name": "Vertex Pharma", "sector": "Biotech", "domain": "vrtx.com", "exchange": "NASDAQ", "currency": "$"},
    "MRNA": {"name": "Moderna Inc.", "sector": "mRNA Biotech", "domain": "modernatx.com", "exchange": "NASDAQ", "currency": "$"},
    "BMY": {"name": "Bristol Myers Squibb", "sector": "Pharmaceuticals", "domain": "bms.com", "exchange": "NYSE", "currency": "$"},
    "MDT": {"name": "Medtronic plc", "sector": "Medical Devices", "domain": "medtronic.com", "exchange": "NYSE", "currency": "$"},
    "BSX": {"name": "Boston Scientific", "sector": "Medical Devices", "domain": "bostonscientific.com", "exchange": "NYSE", "currency": "$"},
    "ZTS": {"name": "Zoetis Inc.", "sector": "Animal Health", "domain": "zoetis.com", "exchange": "NYSE", "currency": "$"},
    "COP": {"name": "ConocoPhillips", "sector": "Oil & Gas", "domain": "conocophillips.com", "exchange": "NYSE", "currency": "$"},
    "SLB": {"name": "SLB (Schlumberger)", "sector": "Oilfield Services", "domain": "slb.com", "exchange": "NYSE", "currency": "$"},
    "EOG": {"name": "EOG Resources", "sector": "Oil & Gas", "domain": "eogresources.com", "exchange": "NYSE", "currency": "$"},
    "NEE": {"name": "NextEra Energy", "sector": "Clean Utilities", "domain": "nexteraenergy.com", "exchange": "NYSE", "currency": "$"},
    "DUK": {"name": "Duke Energy", "sector": "Utilities", "domain": "duke-energy.com", "exchange": "NYSE", "currency": "$"},
    "SO": {"name": "Southern Company", "sector": "Utilities", "domain": "southerncompany.com", "exchange": "NYSE", "currency": "$"},
    "D": {"name": "Dominion Energy", "sector": "Utilities", "domain": "dominionenergy.com", "exchange": "NYSE", "currency": "$"},
    "AMT": {"name": "American Tower", "sector": "Telecom REIT", "domain": "americantower.com", "exchange": "NYSE", "currency": "$"},
    "PLD": {"name": "Prologis Inc.", "sector": "Logistics REIT", "domain": "prologis.com", "exchange": "NYSE", "currency": "$"},
    "EQIX": {"name": "Equinix Inc.", "sector": "Data Center REIT", "domain": "equinix.com", "exchange": "NASDAQ", "currency": "$"},
    "CMCSA": {"name": "Comcast Corp.", "sector": "Media & Broadband", "domain": "comcastcorporation.com", "exchange": "NASDAQ", "currency": "$"},
    "CHTR": {"name": "Charter Comm.", "sector": "Broadband & Media", "domain": "corporate.charter.com", "exchange": "NASDAQ", "currency": "$"},
    "TTWO": {"name": "Take-Two Interactive", "sector": "Gaming", "domain": "take2games.com", "exchange": "NASDAQ", "currency": "$"},
    "RBLX": {"name": "Roblox Corp.", "sector": "Gaming Platform", "domain": "roblox.com", "exchange": "NYSE", "currency": "$"},
    "SNAP": {"name": "Snap Inc.", "sector": "Social Media", "domain": "snap.com", "exchange": "NYSE", "currency": "$"},
    "PINS": {"name": "Pinterest Inc.", "sector": "Visual Discovery", "domain": "pinterest.com", "exchange": "NYSE", "currency": "$"},
    "ZM": {"name": "Zoom Video Comm.", "sector": "Enterprise Video", "domain": "zoom.us", "exchange": "NASDAQ", "currency": "$"},
    "DOCU": {"name": "DocuSign Inc.", "sector": "eSignature SaaS", "domain": "docusign.com", "exchange": "NASDAQ", "currency": "$"},
    "DKNG": {"name": "DraftKings Inc.", "sector": "Sports Tech", "domain": "draftkings.com", "exchange": "NASDAQ", "currency": "$"},
    "MSTR": {"name": "Strategy (MicroStrategy)", "sector": "Enterprise & BTC", "domain": "strategy.com", "exchange": "NASDAQ", "currency": "$"},
    "SMCI": {"name": "Super Micro Computer", "sector": "AI Servers", "domain": "supermicro.com", "exchange": "NASDAQ", "currency": "$"},
    "DELL": {"name": "Dell Technologies", "sector": "IT Infrastructure", "domain": "dell.com", "exchange": "NYSE", "currency": "$"},
    "HPQ": {"name": "HP Inc.", "sector": "PC & Printing", "domain": "hp.com", "exchange": "NYSE", "currency": "$"},
    "HPE": {"name": "Hewlett Packard Ent.", "sector": "Enterprise Servers", "domain": "hpe.com", "exchange": "NYSE", "currency": "$"},
    "APP": {"name": "AppLovin Corp.", "sector": "AdTech & AI", "domain": "applovin.com", "exchange": "NASDAQ", "currency": "$"},
    "GME": {"name": "GameStop Corp.", "sector": "Specialty Retail", "domain": "gamestop.com", "exchange": "NYSE", "currency": "$"},
    "AMC": {"name": "AMC Entertainment", "sector": "Entertainment", "domain": "amctheatres.com", "exchange": "NYSE", "currency": "$"},
    "MAR": {"name": "Marriott Intl.", "sector": "Hospitality", "domain": "marriott.com", "exchange": "NASDAQ", "currency": "$"},
    "HLT": {"name": "Hilton Worldwide", "sector": "Hospitality", "domain": "hilton.com", "exchange": "NYSE", "currency": "$"},
    "DAL": {"name": "Delta Air Lines", "sector": "Aviation", "domain": "delta.com", "exchange": "NYSE", "currency": "$"},
    "UAL": {"name": "United Airlines", "sector": "Aviation", "domain": "united.com", "exchange": "NASDAQ", "currency": "$"},
    "LUV": {"name": "Southwest Airlines", "sector": "Aviation", "domain": "southwest.com", "exchange": "NYSE", "currency": "$"},
    "CCL": {"name": "Carnival Corp.", "sector": "Cruises & Travel", "domain": "carnivalcorp.com", "exchange": "NYSE", "currency": "$"},
    "RCL": {"name": "Royal Caribbean", "sector": "Cruises & Travel", "domain": "royalcaribbean.com", "exchange": "NYSE", "currency": "$"},
    "BRK-A": {"name": "Berkshire Hathaway A", "sector": "Conglomerate", "domain": "berkshirehathaway.com", "exchange": "NYSE", "currency": "$"},
    "NOC": {"name": "Northrop Grumman", "sector": "Aerospace & Defence", "domain": "northropgrumman.com", "exchange": "NYSE", "currency": "$"},
    "GD": {"name": "General Dynamics", "sector": "Aerospace & Defence", "domain": "gd.com", "exchange": "NYSE", "currency": "$"},
    "CI": {"name": "The Cigna Group", "sector": "Healthcare", "domain": "thecignagroup.com", "exchange": "NYSE", "currency": "$"},
    "ELV": {"name": "Elevance Health", "sector": "Healthcare", "domain": "elevancehealth.com", "exchange": "NYSE", "currency": "$"},
    "CVS": {"name": "CVS Health", "sector": "Healthcare & Pharmacy", "domain": "cvshealth.com", "exchange": "NYSE", "currency": "$"},
    "MCK": {"name": "McKesson Corp.", "sector": "Healthcare Supply", "domain": "mckesson.com", "exchange": "NYSE", "currency": "$"},
}

CHAT_STOCK_ALIASES = {
    "apple": "AAPL", "aapl": "AAPL", "iphone": "AAPL", "nvidia": "NVDA",
    "nvda": "NVDA", "tesla": "TSLA", "tsla": "TSLA", "microsoft": "MSFT",
    "msft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN", "meta": "META", "facebook": "META",
    "netflix": "NFLX", "nflx": "NFLX", "amd": "AMD", "intel": "INTC",
    "intc": "INTC", "broadcom": "AVGO", "avgo": "AVGO", "palantir": "PLTR",
    "pltr": "PLTR", "coinbase": "COIN", "coin": "COIN", "uber": "UBER",
    "adobe": "ADBE", "adbe": "ADBE", "salesforce": "CRM", "crm": "CRM",
    "oracle": "ORCL", "orcl": "ORCL", "walmart": "WMT", "wmt": "WMT",
    "jpmorgan": "JPM", "jp morgan": "JPM", "jpm": "JPM", "visa": "V",
    "mastercard": "MA", "disney": "DIS", "nike": "NKE", "nke": "NKE",
    "coca cola": "KO", "coke": "KO", "pepsi": "PEP", "pepsico": "PEP",
    "reliance": "RELIANCE.NS", "ril": "RELIANCE.NS", "jio": "JIOFIN.NS", "jio financial": "JIOFIN.NS",
    "jiofin": "JIOFIN.NS", "tcs": "TCS.NS", "tata consultancy": "TCS.NS", "hdfc": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS", "infosys": "INFY.NS", "infy": "INFY.NS", "sbi": "SBIN.NS",
    "state bank": "SBIN.NS", "state bank of india": "SBIN.NS", "icici": "ICICIBANK.NS", "icici bank": "ICICIBANK.NS",
    "tata motors": "TMPV.NS", "tmpv": "TMPV.NS", "tmcv": "TMCV.NS", "tatamotors": "TMPV.NS",
    "wipro": "WIPRO.NS", "itc": "ITC.NS", "airtel": "BHARTIARTL.NS", "bharti airtel": "BHARTIARTL.NS",
    "zomato": "ETERNAL.NS", "eternal": "ETERNAL.NS", "blinkit": "ETERNAL.NS", "adani enterprises": "ADANIENT.NS",
    "adani": "ADANIENT.NS", "adani ports": "ADANIPORTS.NS", "bajaj finance": "BAJFINANCE.NS", "bajfinance": "BAJFINANCE.NS",
    "l&t": "LT.NS", "larsen": "LT.NS", "larsen & toubro": "LT.NS", "maruti": "MARUTI.NS",
    "maruti suzuki": "MARUTI.NS", "mahindra": "M&M.NS", "m&m": "M&M.NS", "sun pharma": "SUNPHARMA.NS",
    "sunpharma": "SUNPHARMA.NS", "titan": "TITAN.NS", "axis bank": "AXISBANK.NS", "axisbank": "AXISBANK.NS",
    "kotak": "KOTAKBANK.NS", "kotak bank": "KOTAKBANK.NS", "hal": "HAL.NS", "hindustan aeronautics": "HAL.NS",
    "tata steel": "TATASTEEL.NS", "tatasteel": "TATASTEEL.NS", "ntpc": "NTPC.NS", "ongc": "ONGC.NS",
    "coal india": "COALINDIA.NS", "coalindia": "COALINDIA.NS", "powergrid": "POWERGRID.NS", "power grid": "POWERGRID.NS",
    "asian paints": "ASIANPAINT.NS", "asianpaint": "ASIANPAINT.NS", "ultratech": "ULTRACEMCO.NS", "ultracemco": "ULTRACEMCO.NS",
    "hcl": "HCLTECH.NS", "hcl tech": "HCLTECH.NS", "hcltech": "HCLTECH.NS", "tech mahindra": "TECHM.NS",
    "techm": "TECHM.NS", "trent": "TRENT.NS", "zudio": "TRENT.NS", "bel": "BEL.NS",
    "bharat electronics": "BEL.NS", "irctc": "IRCTC.NS", "swiggy": "SWIGGY.NS", "paytm": "PAYTM.NS",
    "nykaa": "NYKAA.NS", "dmart": "DMART.NS", "indigo": "INDIGO.NS", "suzlon": "SUZLON.NS",
    "mazagon": "MAZDOCK.NS", "cochin shipyard": "COCHINSHIP.NS", "varun beverages": "VBL.NS", "dixon": "DIXON.NS",
    "policybazaar": "POLICYBZR.NS", "bse": "BSE.NS", "cdsl": "CDSL.NS", "mcx": "MCX.NS",
    "angel one": "ANGELONE.NS", "costco": "COST", "starbucks": "SBUX", "boeing": "BA",
    "goldman sachs": "GS", "morgan stanley": "MS", "paypal": "PYPL", "shopify": "SHOP",
    "airbnb": "ABNB", "spotify": "SPOT", "snowflake": "SNOW", "crowdstrike": "CRWD",
    "palo alto": "PANW", "qualcomm": "QCOM", "micron": "MU", "arm": "ARM",
    "asml": "ASML", "tsmc": "TSM", "ford": "F", "general motors": "GM",
    "ibm": "IBM", "sony": "SONY", "toyota": "TM", "reliance industries": "RELIANCE.NS",
    "tata consultancy services": "TCS.NS", "eternal ltd. (zomato)": "ETERNAL.NS", "jio financial services": "JIOFIN.NS", "tata motors (pv)": "TMPV.NS",
    "tata motors (cv)": "TMCV.NS", "mahindra & mahindra": "M&M.NS", "titan company": "TITAN.NS", "kotak mahindra bank": "KOTAKBANK.NS",
    "amazon.com": "AMZN", "meta platforms": "META", "palantir technologies": "PLTR", "coinbase global": "COIN",
    "uber technologies": "UBER", "jpmorgan chase": "JPM", "walt disney": "DIS", "coca-cola": "KO",
    "hindustan unilever": "HINDUNILVR.NS", "hcl technologies": "HCLTECH.NS", "ultratech cement": "ULTRACEMCO.NS", "adani ports & sez": "ADANIPORTS.NS",
    "bajaj finserv": "BAJAJFINSV.NS", "jsw steel": "JSWSTEEL.NS", "nestle india": "NESTLEIND.NS", "grasim industries": "GRASIM.NS",
    "hindalco industries": "HINDALCO.NS", "cipla": "CIPLA.NS", "dr. reddy's labs": "DRREDDY.NS", "britannia industries": "BRITANNIA.NS",
    "apollo hospitals": "APOLLOHOSP.NS", "eicher motors": "EICHERMOT.NS", "bajaj auto": "BAJAJ-AUTO.NS", "hero motocorp": "HEROMOTOCO.NS",
    "indusind bank": "INDUSINDBK.NS", "divi's laboratories": "DIVISLAB.NS", "bharat petroleum": "BPCL.NS", "tata consumer products": "TATACONSUM.NS",
    "hdfc life insurance": "HDFCLIFE.NS", "sbi life insurance": "SBILIFE.NS", "shriram finance": "SHRIRAMFIN.NS", "interglobe aviation": "INDIGO.NS",
    "pidilite industries": "PIDILITIND.NS", "siemens india": "SIEMENS.NS", "abb india": "ABB.NS", "ambuja cements": "AMBUJACEM.NS",
    "vedanta": "VEDL.NS", "indian oil": "IOC.NS", "gail india": "GAIL.NS", "bank of baroda": "BANKBARODA.NS",
    "punjab national bank": "PNB.NS", "canara bank": "CANBK.NS", "union bank of india": "UNIONBANK.NS", "power finance": "PFC.NS",
    "indian railway finance": "IRFC.NS", "rail vikas nigam": "RVNL.NS", "mazagon dock shipbuilders": "MAZDOCK.NS", "bharat heavy electricals": "BHEL.NS",
    "suzlon energy": "SUZLON.NS", "tata power": "TATAPOWER.NS", "adani power": "ADANIPOWER.NS", "adani green energy": "ADANIGREEN.NS",
    "adani energy solutions": "ADANIENSOL.NS", "jsw energy": "JSWENERGY.NS", "nhpc": "NHPC.NS", "ireda": "IREDA.NS",
    "yes bank": "YESBANK.NS", "idfc first bank": "IDFCFIRSTB.NS", "federal bank": "FEDERALBNK.NS", "au small finance bank": "AUBANK.NS",
    "bandhan bank": "BANDHANBNK.NS", "cholamandalam inv.": "CHOLAFIN.NS", "muthoot finance": "MUTHOOTFIN.NS", "sbi cards": "SBICARD.NS",
    "icici lombard": "ICICIGI.NS", "icici prudential life": "ICICIPRULI.NS", "hdfc amc": "HDFCAMC.NS", "mcx india": "MCX.NS",
    "one97 comm. (paytm)": "PAYTM.NS", "pb fintech (policybazaar)": "POLICYBZR.NS", "fsn e-commerce (nykaa)": "NYKAA.NS", "delhivery": "DELHIVERY.NS",
    "avenue supermarts (dmart)": "DMART.NS", "dabur india": "DABUR.NS", "marico": "MARICO.NS", "godrej consumer": "GODREJCP.NS",
    "colgate-palmolive india": "COLPAL.NS", "united spirits": "UNITDSPR.NS", "united breweries": "UBL.NS", "havells india": "HAVELLS.NS",
    "polycab india": "POLYCAB.NS", "voltas": "VOLTAS.NS", "dixon technologies": "DIXON.NS", "crompton greaves": "CROMPTON.NS",
    "persistent systems": "PERSISTENT.NS", "coforge": "COFORGE.NS", "mphasis": "MPHASIS.NS", "l&t technology services": "LTTS.NS",
    "tata elxsi": "TATAELXSI.NS", "kpit technologies": "KPITTECH.NS", "info edge (naukri)": "NAUKRI.NS", "oracle financial services": "OFSS.NS",
    "lupin": "LUPIN.NS", "aurobindo pharma": "AUROPHARMA.NS", "torrent pharmaceuticals": "TORNTPHARM.NS", "alkem laboratories": "ALKEM.NS",
    "zydus lifesciences": "ZYDUSLIFE.NS", "biocon": "BIOCON.NS", "max healthcare": "MAXHEALTH.NS", "fortis healthcare": "FORTIS.NS",
    "tvs motor company": "TVSMOTOR.NS", "ashok leyland": "ASHOKLEY.NS", "samvardhana motherson": "MOTHERSON.NS", "bosch": "BOSCHLTD.NS",
    "bharat forge": "BHARATFORG.NS", "sona blw precision": "SONACOMS.NS", "cg power & industrial": "CGPOWER.NS", "cummins india": "CUMMINSIND.NS",
    "steel authority of india": "SAIL.NS", "nmdc": "NMDC.NS", "nalco": "NATIONALUM.NS", "jindal steel & power": "JINDALSTEL.NS",
    "shree cement": "SHREECEM.NS", "macrotech developers (lodha)": "LODHA.NS", "godrej properties": "GODREJPROP.NS", "oberoi realty": "OBEROIRLTY.NS",
    "prestige estates": "PRESTIGE.NS", "phoenix mills": "PHOENIXLTD.NS", "indian hotels (taj)": "INDHOTEL.NS", "concor": "CONCOR.NS",
    "pi industries": "PIIND.NS", "astral": "ASTRAL.NS", "supreme industries": "SUPREMEIND.NS", "page industries (jockey)": "PAGEIND.NS",
    "jubilant foodworks": "JUBLFOOD.NS", "tata communications": "TATACOMM.NS", "vodafone idea": "IDEA.NS", "indus towers": "INDUSTOWER.NS",
    "gmr airports": "GMRAIRPORT.NS", "tube investments": "TIINDIA.NS", "lic": "LICI.NS", "lic of india": "LICI.NS", "oil india": "OIL.NS",
    "hudco": "HUDCO.NS", "nbcc india": "NBCC.NS", "sjvn": "SJVN.NS", "berkshire hathaway": "BRK-B",
    "eli lilly": "LLY", "exxon mobil": "XOM", "costco wholesale": "COST", "johnson & johnson": "JNJ",
    "home depot": "HD", "procter & gamble": "PG", "abbvie": "ABBV", "bank of america": "BAC",
    "unitedhealth": "UNH", "chevron": "CVX", "merck": "MRK", "cisco systems": "CSCO",
    "t-mobile us": "TMUS", "wells fargo": "WFC", "accenture": "ACN", "mcdonald's": "MCD",
    "abbott laboratories": "ABT", "philip morris intl.": "PM", "thermo fisher": "TMO", "linde": "LIN",
    "ge aerospace": "GE", "caterpillar": "CAT", "intuitive surgical": "ISRG", "texas instruments": "TXN",
    "intuit": "INTU", "servicenow": "NOW", "american express": "AXP", "amgen": "AMGN",
    "verizon": "VZ", "at&t": "T", "s&p global": "SPGI", "blackrock": "BLK",
    "pfizer": "PFE", "booking holdings": "BKNG", "lowe's companies": "LOW", "union pacific": "UNP",
    "honeywell intl.": "HON", "stryker": "SYK", "citigroup": "C", "charles schwab": "SCHW",
    "lockheed martin": "LMT", "applied materials": "AMAT", "lam research": "LRCX", "micron technology": "MU",
    "analog devices": "ADI", "palo alto networks": "PANW", "fortinet": "FTNT", "zscaler": "ZS",
    "synopsys": "SNPS", "cadence design": "CDNS", "marvell technology": "MRVL", "arm holdings": "ARM",
    "asml holding": "ASML", "paypal holdings": "PYPL", "robinhood markets": "HOOD", "sofi technologies": "SOFI",
    "doordash": "DASH", "spotify technology": "SPOT", "datadog": "DDOG", "cloudflare": "NET",
    "mongodb": "MDB", "workday": "WDAY", "atlassian": "TEAM", "autodesk": "ADSK",
    "tjx companies": "TJX", "deere & company": "DE", "united parcel service": "UPS", "fedex": "FDX",
    "3m company": "MMM", "ford motor": "F", "rivian automotive": "RIVN", "lucid": "LCID",
    "alibaba": "BABA", "jd.com": "JD", "pdd holdings": "PDD", "baidu": "BIDU",
    "toyota motor": "TM", "novo nordisk": "NVO", "astrazeneca": "AZN", "novartis": "NVS",
    "gilead sciences": "GILD", "regeneron pharma": "REGN", "vertex pharma": "VRTX", "moderna": "MRNA",
    "bristol myers squibb": "BMY", "medtronic": "MDT", "boston scientific": "BSX", "zoetis": "ZTS",
    "conocophillips": "COP", "slb (schlumberger)": "SLB", "eog resources": "EOG", "nextera energy": "NEE",
    "duke energy": "DUK", "southern company": "SO", "dominion energy": "D", "american tower": "AMT",
    "prologis": "PLD", "equinix": "EQIX", "comcast": "CMCSA", "charter comm.": "CHTR",
    "take-two interactive": "TTWO", "roblox": "RBLX", "pinterest": "PINS", "zoom video comm.": "ZM",
    "docusign": "DOCU", "draftkings": "DKNG", "strategy (microstrategy)": "MSTR", "super micro computer": "SMCI",
    "dell technologies": "DELL", "hewlett packard ent.": "HPE", "applovin": "APP", "gamestop": "GME",
    "amc entertainment": "AMC", "marriott intl.": "MAR", "hilton worldwide": "HLT", "delta air lines": "DAL",
    "united airlines": "UAL", "southwest airlines": "LUV", "carnival": "CCL", "royal caribbean": "RCL",
    "berkshire hathaway a": "BRK-A", "northrop grumman": "NOC", "general dynamics": "GD", "cigna": "CI",
    "elevance health": "ELV", "cvs health": "CVS", "mckesson": "MCK",
}

DEFAULT_STOCKS_SNAPSHOTS = {
    "RELIANCE.NS": {"price": 1382.6, "change": -13.6, "pct": -0.97, "rsi": 50.0, "above_sma": False},
    "TCS.NS": {"price": 2572.5, "change": -67.8, "pct": -2.57, "rsi": 46.6, "above_sma": False},
    "HDFCBANK.NS": {"price": 857.25, "change": -4.75, "pct": -0.55, "rsi": 50.8, "above_sma": False},
    "INFY.NS": {"price": 1151.3, "change": -31.7, "pct": -2.68, "rsi": 46.4, "above_sma": False},
    "ICICIBANK.NS": {"price": 1593.4, "change": -17.6, "pct": -1.09, "rsi": 49.7, "above_sma": False},
    "SBIN.NS": {"price": 1123.9, "change": -12.75, "pct": -1.12, "rsi": 49.6, "above_sma": False},
    "BHARTIARTL.NS": {"price": 2067.9, "change": -34.6, "pct": -1.65, "rsi": 48.5, "above_sma": False},
    "ETERNAL.NS": {"price": 363.0, "change": -4.7, "pct": -1.28, "rsi": 49.3, "above_sma": False},
    "JIOFIN.NS": {"price": 222.6, "change": -4.4, "pct": -1.94, "rsi": 47.9, "above_sma": False},
    "TMPV.NS": {"price": 258.0, "change": -4.0, "pct": -1.53, "rsi": 48.8, "above_sma": False},
    "TMCV.NS": {"price": 424.95, "change": -6.05, "pct": -1.4, "rsi": 49.1, "above_sma": False},
    "HAL.NS": {"price": 5074.0, "change": 164.4, "pct": 3.35, "rsi": 59.0, "above_sma": True},
    "ITC.NS": {"price": 304.7, "change": -2.3, "pct": -0.75, "rsi": 50.4, "above_sma": False},
    "LT.NS": {"price": 4108.5, "change": -23.6, "pct": -0.57, "rsi": 50.8, "above_sma": False},
    "BAJFINANCE.NS": {"price": 1080.0, "change": -17.85, "pct": -1.63, "rsi": 48.6, "above_sma": False},
    "SUNPHARMA.NS": {"price": 1899.9, "change": -15.8, "pct": -0.82, "rsi": 50.3, "above_sma": False},
    "MARUTI.NS": {"price": 13765.0, "change": -250.0, "pct": -1.78, "rsi": 48.3, "above_sma": False},
    "M&M.NS": {"price": 3450.0, "change": -37.5, "pct": -1.08, "rsi": 49.7, "above_sma": False},
    "TITAN.NS": {"price": 4675.3, "change": 44.2, "pct": 0.95, "rsi": 54.0, "above_sma": True},
    "AXISBANK.NS": {"price": 1380.1, "change": -27.9, "pct": -1.98, "rsi": 47.8, "above_sma": False},
    "KOTAKBANK.NS": {"price": 500.0, "change": -9.95, "pct": -1.95, "rsi": 47.9, "above_sma": False},
    "ADANIENT.NS": {"price": 2640.4, "change": -19.6, "pct": -0.74, "rsi": 50.4, "above_sma": False},
    "TATASTEEL.NS": {"price": 163.94, "change": 0.4, "pct": 0.24, "rsi": 52.5, "above_sma": True},
    "WIPRO.NS": {"price": 192.1, "change": -4.44, "pct": -2.26, "rsi": 47.3, "above_sma": False},
    "AAPL": {"price": 358.62, "change": 3.04, "pct": 0.85, "rsi": 53.8, "above_sma": True},
    "NVDA": {"price": 147.88, "change": -1.42, "pct": -0.95, "rsi": 50.0, "above_sma": False},
    "MSFT": {"price": 492.11, "change": 2.18, "pct": 0.45, "rsi": 52.9, "above_sma": True},
    "TSLA": {"price": 400.21, "change": 20.07, "pct": 5.28, "rsi": 63.1, "above_sma": True},
    "GOOGL": {"price": 272.71, "change": -0.39, "pct": -0.14, "rsi": 51.7, "above_sma": True},
    "AMZN": {"price": 252.9, "change": 8.47, "pct": 3.47, "rsi": 59.3, "above_sma": True},
    "META": {"price": 633.02, "change": 23.13, "pct": 3.79, "rsi": 60.0, "above_sma": True},
    "NFLX": {"price": 60.67, "change": 1.26, "pct": 2.13, "rsi": 56.5, "above_sma": True},
    "AMD": {"price": 415.94, "change": 9.91, "pct": 2.44, "rsi": 57.1, "above_sma": True},
    "AVGO": {"price": 311.36, "change": 10.51, "pct": 3.49, "rsi": 59.3, "above_sma": True},
    "PLTR": {"price": 170.74, "change": 7.15, "pct": 4.37, "rsi": 61.2, "above_sma": True},
    "INTC": {"price": 56.46, "change": 1.99, "pct": 3.64, "rsi": 59.6, "above_sma": True},
    "COIN": {"price": 106.91, "change": 3.19, "pct": 3.08, "rsi": 58.5, "above_sma": True},
    "UBER": {"price": 67.28, "change": 0.93, "pct": 1.4, "rsi": 54.9, "above_sma": True},
    "ADBE": {"price": 233.5, "change": 0.67, "pct": 0.29, "rsi": 52.6, "above_sma": True},
    "CRM": {"price": 197.71, "change": 0.49, "pct": 0.25, "rsi": 52.5, "above_sma": True},
    "ORCL": {"price": 105.96, "change": 2.08, "pct": 2.0, "rsi": 56.2, "above_sma": True},
    "JPM": {"price": 323.58, "change": 6.84, "pct": 2.16, "rsi": 56.5, "above_sma": True},
    "V": {"price": 431.36, "change": 6.97, "pct": 1.64, "rsi": 55.4, "above_sma": True},
    "MA": {"price": 668.56, "change": 8.59, "pct": 1.3, "rsi": 54.7, "above_sma": True},
    "WMT": {"price": 132.19, "change": 0.25, "pct": 0.19, "rsi": 52.4, "above_sma": True},
    "DIS": {"price": 126.88, "change": 1.28, "pct": 1.02, "rsi": 54.1, "above_sma": True},
    "NKE": {"price": 37.17, "change": 0.51, "pct": 1.4, "rsi": 54.9, "above_sma": True},
    "KO": {"price": 97.4, "change": -0.19, "pct": -0.19, "rsi": 51.6, "above_sma": True},
    "HINDUNILVR.NS": {"price": 2117.2, "change": -13.6, "pct": -0.64, "rsi": 50.7, "above_sma": False},
    "HCLTECH.NS": {"price": 1424.1, "change": -44.5, "pct": -3.03, "rsi": 45.6, "above_sma": False},
    "ULTRACEMCO.NS": {"price": 12578.0, "change": -159.0, "pct": -1.25, "rsi": 49.4, "above_sma": False},
    "NTPC.NS": {"price": 319.75, "change": -0.5, "pct": -0.16, "rsi": 51.7, "above_sma": True},
    "ONGC.NS": {"price": 224.31, "change": 1.43, "pct": 0.64, "rsi": 53.3, "above_sma": True},
    "ADANIPORTS.NS": {"price": 1880.0, "change": -31.3, "pct": -1.64, "rsi": 48.6, "above_sma": False},
    "POWERGRID.NS": {"price": 268.2, "change": 1.25, "pct": 0.47, "rsi": 53.0, "above_sma": True},
    "COALINDIA.NS": {"price": 388.85, "change": -0.05, "pct": -0.01, "rsi": 52.0, "above_sma": True},
    "ASIANPAINT.NS": {"price": 2532.6, "change": -10.4, "pct": -0.41, "rsi": 51.1, "above_sma": False},
    "BAJAJFINSV.NS": {"price": 1849.0, "change": -36.9, "pct": -1.96, "rsi": 47.9, "above_sma": False},
    "JSWSTEEL.NS": {"price": 1321.2, "change": 18.2, "pct": 1.4, "rsi": 54.9, "above_sma": True},
    "NESTLEIND.NS": {"price": 1317.0, "change": -3.3, "pct": -0.25, "rsi": 51.5, "above_sma": True},
    "TECHM.NS": {"price": 1813.9, "change": -40.8, "pct": -2.2, "rsi": 47.4, "above_sma": False},
    "GRASIM.NS": {"price": 3124.2, "change": -54.8, "pct": -1.72, "rsi": 48.4, "above_sma": False},
    "HINDALCO.NS": {"price": 923.0, "change": 7.5, "pct": 0.82, "rsi": 53.7, "above_sma": True},
    "CIPLA.NS": {"price": 1439.9, "change": -10.1, "pct": -0.7, "rsi": 50.5, "above_sma": False},
    "DRREDDY.NS": {"price": 1381.7, "change": -10.3, "pct": -0.74, "rsi": 50.4, "above_sma": False},
    "BRITANNIA.NS": {"price": 5065.0, "change": -120.0, "pct": -2.31, "rsi": 47.1, "above_sma": False},
    "APOLLOHOSP.NS": {"price": 9128.0, "change": -94.5, "pct": -1.02, "rsi": 49.9, "above_sma": False},
    "EICHERMOT.NS": {"price": 8003.5, "change": -176.5, "pct": -2.16, "rsi": 47.5, "above_sma": False},
    "BAJAJ-AUTO.NS": {"price": 10485.0, "change": -365.0, "pct": -3.36, "rsi": 44.9, "above_sma": False},
    "HEROMOTOCO.NS": {"price": 5701.0, "change": -88.0, "pct": -1.52, "rsi": 48.8, "above_sma": False},
    "INDUSINDBK.NS": {"price": 958.4, "change": -7.7, "pct": -0.8, "rsi": 50.3, "above_sma": False},
    "DIVISLAB.NS": {"price": 11560.0, "change": -71.0, "pct": -0.61, "rsi": 50.7, "above_sma": False},
    "BPCL.NS": {"price": 308.55, "change": 0.9, "pct": 0.29, "rsi": 52.6, "above_sma": True},
    "TATACONSUM.NS": {"price": 1155.0, "change": -9.0, "pct": -0.77, "rsi": 50.4, "above_sma": False},
    "HDFCLIFE.NS": {"price": 588.45, "change": -5.95, "pct": -1.0, "rsi": 49.9, "above_sma": False},
    "SBILIFE.NS": {"price": 1856.0, "change": 13.7, "pct": 0.74, "rsi": 53.6, "above_sma": True},
    "SHRIRAMFIN.NS": {"price": 923.5, "change": -38.35, "pct": -3.99, "rsi": 43.6, "above_sma": False},
    "TRENT.NS": {"price": 3273.0, "change": 10.4, "pct": 0.32, "rsi": 52.7, "above_sma": True},
    "BEL.NS": {"price": 411.45, "change": 6.95, "pct": 1.72, "rsi": 55.6, "above_sma": True},
    "IRCTC.NS": {"price": 458.65, "change": 4.45, "pct": 0.98, "rsi": 54.1, "above_sma": True},
    "INDIGO.NS": {"price": 5659.6, "change": 34.6, "pct": 0.62, "rsi": 53.3, "above_sma": True},
    "DLF.NS": {"price": 805.45, "change": -2.35, "pct": -0.29, "rsi": 51.4, "above_sma": True},
    "PIDILITIND.NS": {"price": 1594.8, "change": -10.1, "pct": -0.63, "rsi": 50.7, "above_sma": False},
    "SIEMENS.NS": {"price": 3595.0, "change": 18.4, "pct": 0.51, "rsi": 53.1, "above_sma": True},
    "ABB.NS": {"price": 7060.0, "change": 99.5, "pct": 1.43, "rsi": 55.0, "above_sma": True},
    "AMBUJACEM.NS": {"price": 385.3, "change": -5.65, "pct": -1.45, "rsi": 49.0, "above_sma": False},
    "VEDL.NS": {"price": 245.31, "change": 7.31, "pct": 3.07, "rsi": 58.4, "above_sma": True},
    "IOC.NS": {"price": 144.21, "change": -0.21, "pct": -0.15, "rsi": 51.7, "above_sma": True},
    "GAIL.NS": {"price": 185.0, "change": -3.0, "pct": -1.6, "rsi": 48.6, "above_sma": False},
    "BANKBARODA.NS": {"price": 274.9, "change": 0.29, "pct": 0.11, "rsi": 52.2, "above_sma": True},
    "PNB.NS": {"price": 146.5, "change": -1.0, "pct": -0.68, "rsi": 50.6, "above_sma": False},
    "CANBK.NS": {"price": 131.11, "change": -1.29, "pct": -0.97, "rsi": 50.0, "above_sma": False},
    "UNIONBANK.NS": {"price": 211.1, "change": 0.9, "pct": 0.43, "rsi": 52.9, "above_sma": True},
    "PFC.NS": {"price": 327.8, "change": -3.3, "pct": -1.0, "rsi": 49.9, "above_sma": False},
    "RECLTD.NS": {"price": 295.05, "change": -2.25, "pct": -0.76, "rsi": 50.4, "above_sma": False},
    "IRFC.NS": {"price": 82.25, "change": -0.05, "pct": -0.06, "rsi": 51.9, "above_sma": True},
    "RVNL.NS": {"price": 190.7, "change": 3.56, "pct": 1.9, "rsi": 56.0, "above_sma": True},
    "MAZDOCK.NS": {"price": 1890.0, "change": 73.0, "pct": 4.02, "rsi": 60.4, "above_sma": True},
    "COCHINSHIP.NS": {"price": 1126.0, "change": 23.0, "pct": 2.09, "rsi": 56.4, "above_sma": True},
    "BHEL.NS": {"price": 421.95, "change": 3.0, "pct": 0.72, "rsi": 53.5, "above_sma": True},
    "SUZLON.NS": {"price": 36.38, "change": 0.09, "pct": 0.25, "rsi": 52.5, "above_sma": True},
    "TATAPOWER.NS": {"price": 320.05, "change": -3.45, "pct": -1.07, "rsi": 49.8, "above_sma": False},
    "ADANIPOWER.NS": {"price": 205.25, "change": -3.05, "pct": -1.46, "rsi": 48.9, "above_sma": False},
    "ADANIGREEN.NS": {"price": 1327.6, "change": -21.2, "pct": -1.57, "rsi": 48.7, "above_sma": False},
    "ADANIENSOL.NS": {"price": 1337.0, "change": -45.0, "pct": -3.26, "rsi": 45.2, "above_sma": False},
    "JSWENERGY.NS": {"price": 485.0, "change": -0.15, "pct": -0.03, "rsi": 51.9, "above_sma": True},
    "NHPC.NS": {"price": 75.65, "change": -0.25, "pct": -0.33, "rsi": 51.3, "above_sma": True},
    "IREDA.NS": {"price": 125.59, "change": -1.41, "pct": -1.11, "rsi": 49.7, "above_sma": False},
    "YESBANK.NS": {"price": 17.8, "change": 0.12, "pct": 0.68, "rsi": 53.4, "above_sma": True},
    "IDFCFIRSTB.NS": {"price": 86.8, "change": 0.09, "pct": 0.1, "rsi": 52.2, "above_sma": True},
    "FEDERALBNK.NS": {"price": 360.0, "change": 3.15, "pct": 0.88, "rsi": 53.8, "above_sma": True},
    "AUBANK.NS": {"price": 984.85, "change": 2.85, "pct": 0.29, "rsi": 52.6, "above_sma": True},
    "BANDHANBNK.NS": {"price": 166.66, "change": -2.83, "pct": -1.67, "rsi": 48.5, "above_sma": False},
    "CHOLAFIN.NS": {"price": 1802.0, "change": -40.9, "pct": -2.22, "rsi": 47.3, "above_sma": False},
    "MUTHOOTFIN.NS": {"price": 2609.5, "change": 51.5, "pct": 2.01, "rsi": 56.2, "above_sma": True},
    "SBICARD.NS": {"price": 565.8, "change": -20.3, "pct": -3.46, "rsi": 44.7, "above_sma": False},
    "ICICIGI.NS": {"price": 1738.5, "change": -1.5, "pct": -0.09, "rsi": 51.8, "above_sma": True},
    "ICICIPRULI.NS": {"price": 468.5, "change": -5.5, "pct": -1.16, "rsi": 49.6, "above_sma": False},
    "HDFCAMC.NS": {"price": 2706.0, "change": -19.1, "pct": -0.7, "rsi": 50.5, "above_sma": False},
    "BSE.NS": {"price": 3945.0, "change": -45.4, "pct": -1.14, "rsi": 49.6, "above_sma": False},
    "CDSL.NS": {"price": 1453.0, "change": 12.0, "pct": 0.83, "rsi": 53.7, "above_sma": True},
    "MCX.NS": {"price": 3900.0, "change": 65.0, "pct": 1.69, "rsi": 55.5, "above_sma": True},
    "ANGELONE.NS": {"price": 376.0, "change": 18.0, "pct": 5.03, "rsi": 62.6, "above_sma": True},
    "PAYTM.NS": {"price": 1741.9, "change": -27.0, "pct": -1.53, "rsi": 48.8, "above_sma": False},
    "POLICYBZR.NS": {"price": 1186.5, "change": 16.5, "pct": 1.41, "rsi": 55.0, "above_sma": True},
    "NYKAA.NS": {"price": 350.65, "change": -2.35, "pct": -0.67, "rsi": 50.6, "above_sma": False},
    "DELHIVERY.NS": {"price": 458.6, "change": -1.9, "pct": -0.41, "rsi": 51.1, "above_sma": False},
    "SWIGGY.NS": {"price": 180.0, "change": -2.93, "pct": -1.6, "rsi": 48.6, "above_sma": False},
    "DMART.NS": {"price": 3541.3, "change": 8.3, "pct": 0.23, "rsi": 52.5, "above_sma": True},
    "DABUR.NS": {"price": 412.75, "change": -5.75, "pct": -1.37, "rsi": 49.1, "above_sma": False},
    "MARICO.NS": {"price": 922.3, "change": -16.8, "pct": -1.79, "rsi": 48.2, "above_sma": False},
    "GODREJCP.NS": {"price": 918.9, "change": -28.6, "pct": -3.02, "rsi": 45.7, "above_sma": False},
    "COLPAL.NS": {"price": 1770.0, "change": -30.0, "pct": -1.67, "rsi": 48.5, "above_sma": False},
    "VBL.NS": {"price": 424.9, "change": -3.5, "pct": -0.82, "rsi": 50.3, "above_sma": False},
    "UNITDSPR.NS": {"price": 1476.2, "change": -12.3, "pct": -0.83, "rsi": 50.3, "above_sma": False},
    "UBL.NS": {"price": 1275.6, "change": 2.7, "pct": 0.21, "rsi": 52.4, "above_sma": True},
    "HAVELLS.NS": {"price": 1142.4, "change": -38.6, "pct": -3.27, "rsi": 45.1, "above_sma": False},
    "POLYCAB.NS": {"price": 7429.0, "change": 79.0, "pct": 1.07, "rsi": 54.2, "above_sma": True},
    "VOLTAS.NS": {"price": 1186.8, "change": -28.7, "pct": -2.36, "rsi": 47.0, "above_sma": False},
    "DIXON.NS": {"price": 13138.0, "change": 420.0, "pct": 3.3, "rsi": 58.9, "above_sma": True},
    "CROMPTON.NS": {"price": 211.0, "change": -4.6, "pct": -2.13, "rsi": 47.5, "above_sma": False},
    "PERSISTENT.NS": {"price": 6320.0, "change": 120.0, "pct": 1.94, "rsi": 56.1, "above_sma": True},
    "COFORGE.NS": {"price": 2071.0, "change": 71.0, "pct": 3.55, "rsi": 59.5, "above_sma": True},
    "MPHASIS.NS": {"price": 2441.2, "change": -68.8, "pct": -2.74, "rsi": 46.2, "above_sma": False},
    "LTTS.NS": {"price": 4227.2, "change": -18.0, "pct": -0.42, "rsi": 51.1, "above_sma": False},
    "TATAELXSI.NS": {"price": 3877.3, "change": 16.6, "pct": 0.43, "rsi": 52.9, "above_sma": True},
    "KPITTECH.NS": {"price": 520.0, "change": -2.2, "pct": -0.42, "rsi": 51.1, "above_sma": False},
    "NAUKRI.NS": {"price": 1203.8, "change": -25.2, "pct": -2.05, "rsi": 47.7, "above_sma": False},
    "OFSS.NS": {"price": 9250.0, "change": -41.0, "pct": -0.44, "rsi": 51.1, "above_sma": False},
    "LUPIN.NS": {"price": 2016.0, "change": 11.0, "pct": 0.55, "rsi": 53.2, "above_sma": True},
    "AUROPHARMA.NS": {"price": 1791.8, "change": -19.2, "pct": -1.06, "rsi": 49.8, "above_sma": False},
    "TORNTPHARM.NS": {"price": 5034.0, "change": 14.9, "pct": 0.3, "rsi": 52.6, "above_sma": True},
    "ALKEM.NS": {"price": 5130.0, "change": -26.5, "pct": -0.51, "rsi": 50.9, "above_sma": False},
    "ZYDUSLIFE.NS": {"price": 1156.9, "change": -37.3, "pct": -3.12, "rsi": 45.4, "above_sma": False},
    "BIOCON.NS": {"price": 362.0, "change": -3.0, "pct": -0.82, "rsi": 50.3, "above_sma": False},
    "MAXHEALTH.NS": {"price": 1071.3, "change": -9.95, "pct": -0.92, "rsi": 50.1, "above_sma": False},
    "FORTIS.NS": {"price": 832.0, "change": 6.1, "pct": 0.74, "rsi": 53.6, "above_sma": True},
    "TVSMOTOR.NS": {"price": 4526.5, "change": -23.6, "pct": -0.52, "rsi": 50.9, "above_sma": False},
    "ASHOKLEY.NS": {"price": 151.42, "change": -4.73, "pct": -3.03, "rsi": 45.6, "above_sma": False},
    "MOTHERSON.NS": {"price": 161.5, "change": -3.11, "pct": -1.89, "rsi": 48.0, "above_sma": False},
    "BOSCHLTD.NS": {"price": 49170.0, "change": 340.0, "pct": 0.7, "rsi": 53.5, "above_sma": True},
    "MRF.NS": {"price": 128000.0, "change": -465.0, "pct": -0.36, "rsi": 51.2, "above_sma": True},
    "BHARATFORG.NS": {"price": 1771.0, "change": 27.0, "pct": 1.55, "rsi": 55.3, "above_sma": True},
    "SONACOMS.NS": {"price": 879.0, "change": -2.5, "pct": -0.28, "rsi": 51.4, "above_sma": True},
    "CGPOWER.NS": {"price": 793.0, "change": 11.0, "pct": 1.41, "rsi": 55.0, "above_sma": True},
    "CUMMINSIND.NS": {"price": 4205.5, "change": 104.6, "pct": 2.55, "rsi": 57.4, "above_sma": True},
    "SAIL.NS": {"price": 163.95, "change": 2.99, "pct": 1.86, "rsi": 55.9, "above_sma": True},
    "NMDC.NS": {"price": 67.96, "change": 0.72, "pct": 1.07, "rsi": 54.2, "above_sma": True},
    "NATIONALUM.NS": {"price": 304.55, "change": 9.6, "pct": 3.25, "rsi": 58.8, "above_sma": True},
    "JINDALSTEL.NS": {"price": 1138.7, "change": 23.9, "pct": 2.14, "rsi": 56.5, "above_sma": True},
    "SHREECEM.NS": {"price": 25160.0, "change": -175.0, "pct": -0.69, "rsi": 50.6, "above_sma": False},
    "ACC.NS": {"price": 1250.6, "change": -13.0, "pct": -1.03, "rsi": 49.8, "above_sma": False},
    "LODHA.NS": {"price": 1251.8, "change": -9.4, "pct": -0.75, "rsi": 50.4, "above_sma": False},
    "GODREJPROP.NS": {"price": 1943.0, "change": -61.3, "pct": -3.06, "rsi": 45.6, "above_sma": False},
    "OBEROIRLTY.NS": {"price": 1889.2, "change": -16.0, "pct": -0.84, "rsi": 50.2, "above_sma": False},
    "PRESTIGE.NS": {"price": 1796.7, "change": -35.4, "pct": -1.93, "rsi": 47.9, "above_sma": False},
    "PHOENIXLTD.NS": {"price": 2229.7, "change": -61.3, "pct": -2.68, "rsi": 46.4, "above_sma": False},
    "INDHOTEL.NS": {"price": 884.8, "change": -1.9, "pct": -0.21, "rsi": 51.6, "above_sma": True},
    "CONCOR.NS": {"price": 420.7, "change": -0.3, "pct": -0.07, "rsi": 51.9, "above_sma": True},
    "PIIND.NS": {"price": 1606.0, "change": 14.8, "pct": 0.93, "rsi": 54.0, "above_sma": True},
    "SRF.NS": {"price": 2559.5, "change": 43.1, "pct": 1.71, "rsi": 55.6, "above_sma": True},
    "UPL.NS": {"price": 564.4, "change": -0.6, "pct": -0.11, "rsi": 51.8, "above_sma": True},
    "ASTRAL.NS": {"price": 1262.5, "change": 4.2, "pct": 0.33, "rsi": 52.7, "above_sma": True},
    "SUPREMEIND.NS": {"price": 3200.0, "change": 40.0, "pct": 1.27, "rsi": 54.7, "above_sma": True},
    "PAGEIND.NS": {"price": 30870.0, "change": 10.0, "pct": 0.03, "rsi": 52.1, "above_sma": True},
    "JUBLFOOD.NS": {"price": 422.8, "change": -2.3, "pct": -0.54, "rsi": 50.9, "above_sma": False},
    "TATACOMM.NS": {"price": 1707.3, "change": 10.1, "pct": 0.6, "rsi": 53.3, "above_sma": True},
    "IDEA.NS": {"price": 11.55, "change": -0.05, "pct": -0.43, "rsi": 51.1, "above_sma": False},
    "INDUSTOWER.NS": {"price": 377.65, "change": -1.35, "pct": -0.36, "rsi": 51.2, "above_sma": True},
    "GMRAIRPORT.NS": {"price": 99.26, "change": -1.94, "pct": -1.92, "rsi": 48.0, "above_sma": False},
    "TIINDIA.NS": {"price": 2243.2, "change": 31.0, "pct": 1.4, "rsi": 54.9, "above_sma": True},
    "LICI.NS": {"price": 405.4, "change": -4.6, "pct": -1.12, "rsi": 49.6, "above_sma": False},
    "OIL.NS": {"price": 433.45, "change": 6.35, "pct": 1.49, "rsi": 55.1, "above_sma": True},
    "HUDCO.NS": {"price": 155.64, "change": 0.83, "pct": 0.54, "rsi": 53.1, "above_sma": True},
    "NBCC.NS": {"price": 75.51, "change": 0.01, "pct": 0.01, "rsi": 52.0, "above_sma": True},
    "SJVN.NS": {"price": 55.05, "change": 0.01, "pct": 0.02, "rsi": 52.0, "above_sma": True},
    "BRK-B": {"price": 580.0, "change": 0.68, "pct": 0.12, "rsi": 52.3, "above_sma": True},
    "LLY": {"price": 1392.31, "change": 0.09, "pct": 0.01, "rsi": 52.0, "above_sma": True},
    "XOM": {"price": 161.06, "change": 2.98, "pct": 1.89, "rsi": 56.0, "above_sma": True},
    "COST": {"price": 1098.29, "change": 11.48, "pct": 1.06, "rsi": 54.2, "above_sma": True},
    "JNJ": {"price": 274.72, "change": 0.78, "pct": 0.28, "rsi": 52.6, "above_sma": True},
    "HD": {"price": 359.4, "change": -1.86, "pct": -0.51, "rsi": 50.9, "above_sma": False},
    "PG": {"price": 172.6, "change": -0.63, "pct": -0.36, "rsi": 51.2, "above_sma": True},
    "ABBV": {"price": 291.59, "change": -2.89, "pct": -0.98, "rsi": 49.9, "above_sma": False},
    "BAC": {"price": 49.17, "change": 0.63, "pct": 1.3, "rsi": 54.7, "above_sma": True},
    "UNH": {"price": 351.34, "change": 5.15, "pct": 1.49, "rsi": 55.1, "above_sma": True},
    "CVX": {"price": 214.56, "change": 3.61, "pct": 1.71, "rsi": 55.6, "above_sma": True},
    "PEP": {"price": 144.22, "change": 0.29, "pct": 0.2, "rsi": 52.4, "above_sma": True},
    "MRK": {"price": 141.15, "change": 0.87, "pct": 0.62, "rsi": 53.3, "above_sma": True},
    "CSCO": {"price": 96.46, "change": 2.26, "pct": 2.4, "rsi": 57.0, "above_sma": True},
    "TMUS": {"price": 167.88, "change": 1.63, "pct": 0.98, "rsi": 54.1, "above_sma": True},
    "WFC": {"price": 82.26, "change": 1.32, "pct": 1.63, "rsi": 55.4, "above_sma": True},
    "ACN": {"price": 241.77, "change": 1.28, "pct": 0.53, "rsi": 53.1, "above_sma": True},
    "MCD": {"price": 282.3, "change": -1.2, "pct": -0.42, "rsi": 51.1, "above_sma": False},
    "ABT": {"price": 107.81, "change": -0.19, "pct": -0.18, "rsi": 51.6, "above_sma": True},
    "PM": {"price": 187.14, "change": 2.82, "pct": 1.53, "rsi": 55.2, "above_sma": True},
    "TMO": {"price": 680.11, "change": -5.41, "pct": -0.79, "rsi": 50.3, "above_sma": False},
    "IBM": {"price": 246.47, "change": 3.0, "pct": 1.23, "rsi": 54.6, "above_sma": True},
    "LIN": {"price": 530.15, "change": 5.54, "pct": 1.06, "rsi": 54.2, "above_sma": True},
    "GE": {"price": 321.77, "change": 4.79, "pct": 1.51, "rsi": 55.2, "above_sma": True},
    "CAT": {"price": 559.72, "change": 16.03, "pct": 2.95, "rsi": 58.2, "above_sma": True},
    "GS": {"price": 811.94, "change": 10.91, "pct": 1.36, "rsi": 54.9, "above_sma": True},
    "MS": {"price": 171.29, "change": 3.74, "pct": 2.23, "rsi": 56.7, "above_sma": True},
    "ISRG": {"price": 428.4, "change": 1.22, "pct": 0.29, "rsi": 52.6, "above_sma": True},
    "QCOM": {"price": 176.87, "change": 8.21, "pct": 4.87, "rsi": 62.2, "above_sma": True},
    "TXN": {"price": 276.54, "change": 6.35, "pct": 2.35, "rsi": 56.9, "above_sma": True},
    "INTU": {"price": 274.14, "change": 2.42, "pct": 0.89, "rsi": 53.9, "above_sma": True},
    "NOW": {"price": 92.62, "change": 0.46, "pct": 0.5, "rsi": 53.0, "above_sma": True},
    "AXP": {"price": 316.23, "change": 3.84, "pct": 1.23, "rsi": 54.6, "above_sma": True},
    "AMGN": {"price": 471.56, "change": 2.32, "pct": 0.49, "rsi": 53.0, "above_sma": True},
    "VZ": {"price": 47.64, "change": 0.36, "pct": 0.76, "rsi": 53.6, "above_sma": True},
    "T": {"price": 23.14, "change": 0.17, "pct": 0.74, "rsi": 53.6, "above_sma": True},
    "RTX": {"price": 196.56, "change": 0.37, "pct": 0.19, "rsi": 52.4, "above_sma": True},
    "SPGI": {"price": 457.42, "change": -3.32, "pct": -0.72, "rsi": 50.5, "above_sma": False},
    "BLK": {"price": 1165.3, "change": 23.44, "pct": 2.05, "rsi": 56.3, "above_sma": True},
    "PFE": {"price": 28.44, "change": -0.02, "pct": -0.07, "rsi": 51.9, "above_sma": True},
    "BKNG": {"price": 149.48, "change": -0.02, "pct": -0.01, "rsi": 52.0, "above_sma": True},
    "LOW": {"price": 234.8, "change": -0.85, "pct": -0.36, "rsi": 51.2, "above_sma": True},
    "UNP": {"price": 298.51, "change": 0.12, "pct": 0.04, "rsi": 52.1, "above_sma": True},
    "HON": {"price": 227.84, "change": 2.74, "pct": 1.22, "rsi": 54.6, "above_sma": True},
    "SYK": {"price": 333.1, "change": 0.2, "pct": 0.06, "rsi": 52.1, "above_sma": True},
    "C": {"price": 115.45, "change": 2.12, "pct": 1.87, "rsi": 55.9, "above_sma": True},
    "SCHW": {"price": 94.0, "change": 0.55, "pct": 0.59, "rsi": 53.2, "above_sma": True},
    "BA": {"price": 166.63, "change": 2.1, "pct": 1.28, "rsi": 54.7, "above_sma": True},
    "LMT": {"price": 602.91, "change": 3.67, "pct": 0.61, "rsi": 53.3, "above_sma": True},
    "AMAT": {"price": 314.11, "change": 2.93, "pct": 0.94, "rsi": 54.0, "above_sma": True},
    "LRCX": {"price": 188.57, "change": 3.56, "pct": 1.92, "rsi": 56.0, "above_sma": True},
    "KLAC": {"price": 137.14, "change": 2.94, "pct": 2.19, "rsi": 56.6, "above_sma": True},
    "MU": {"price": 635.71, "change": 34.46, "pct": 5.73, "rsi": 64.0, "above_sma": True},
    "ADI": {"price": 339.67, "change": 6.56, "pct": 1.97, "rsi": 56.1, "above_sma": True},
    "PANW": {"price": 356.28, "change": 0.14, "pct": 0.04, "rsi": 52.1, "above_sma": True},
    "CRWD": {"price": 212.38, "change": 3.07, "pct": 1.47, "rsi": 55.1, "above_sma": True},
    "FTNT": {"price": 136.49, "change": 1.53, "pct": 1.13, "rsi": 54.4, "above_sma": True},
    "ZS": {"price": 234.5, "change": 3.64, "pct": 1.58, "rsi": 55.3, "above_sma": True},
    "SNPS": {"price": 417.59, "change": 12.5, "pct": 3.09, "rsi": 58.5, "above_sma": True},
    "CDNS": {"price": 298.6, "change": 3.71, "pct": 1.26, "rsi": 54.6, "above_sma": True},
    "MRVL": {"price": 138.3, "change": 7.37, "pct": 5.63, "rsi": 63.8, "above_sma": True},
    "ARM": {"price": 167.38, "change": 5.87, "pct": 3.63, "rsi": 59.6, "above_sma": True},
    "ASML": {"price": 1309.9, "change": 6.82, "pct": 0.52, "rsi": 53.1, "above_sma": True},
    "TSM": {"price": 350.71, "change": 8.37, "pct": 2.44, "rsi": 57.1, "above_sma": True},
    "SHOP": {"price": 142.09, "change": 8.69, "pct": 6.51, "rsi": 65.7, "above_sma": True},
    "PYPL": {"price": 59.25, "change": 1.44, "pct": 2.49, "rsi": 57.2, "above_sma": True},
    "HOOD": {"price": 67.41, "change": 1.63, "pct": 2.48, "rsi": 57.2, "above_sma": True},
    "SOFI": {"price": 13.4, "change": 0.33, "pct": 2.53, "rsi": 57.3, "above_sma": True},
    "ABNB": {"price": 177.7, "change": 5.55, "pct": 3.22, "rsi": 58.8, "above_sma": True},
    "DASH": {"price": 167.3, "change": 0.9, "pct": 0.54, "rsi": 53.1, "above_sma": True},
    "SPOT": {"price": 622.35, "change": 5.89, "pct": 0.96, "rsi": 54.0, "above_sma": True},
    "SNOW": {"price": 272.53, "change": 4.81, "pct": 1.8, "rsi": 55.8, "above_sma": True},
    "DDOG": {"price": 162.74, "change": 4.49, "pct": 2.84, "rsi": 58.0, "above_sma": True},
    "NET": {"price": 291.47, "change": 8.17, "pct": 2.88, "rsi": 58.0, "above_sma": True},
    "MDB": {"price": 318.01, "change": 4.48, "pct": 1.43, "rsi": 55.0, "above_sma": True},
    "WDAY": {"price": 179.94, "change": -0.5, "pct": -0.28, "rsi": 51.4, "above_sma": True},
    "TEAM": {"price": 147.98, "change": 3.59, "pct": 2.49, "rsi": 57.2, "above_sma": True},
    "ADSK": {"price": 252.39, "change": 5.6, "pct": 2.27, "rsi": 56.8, "above_sma": True},
    "SBUX": {"price": 109.11, "change": 1.37, "pct": 1.27, "rsi": 54.7, "above_sma": True},
    "TGT": {"price": 172.36, "change": 0.14, "pct": 0.08, "rsi": 52.2, "above_sma": True},
    "TJX": {"price": 142.75, "change": -3.34, "pct": -2.29, "rsi": 47.2, "above_sma": False},
    "DE": {"price": 654.18, "change": 13.16, "pct": 2.05, "rsi": 56.3, "above_sma": True},
    "UPS": {"price": 112.43, "change": 0.96, "pct": 0.86, "rsi": 53.8, "above_sma": True},
    "FDX": {"price": 311.64, "change": 2.77, "pct": 0.9, "rsi": 53.9, "above_sma": True},
    "MMM": {"price": 191.04, "change": 1.21, "pct": 0.64, "rsi": 53.3, "above_sma": True},
    "F": {"price": 12.37, "change": 0.2, "pct": 1.64, "rsi": 55.4, "above_sma": True},
    "GM": {"price": 85.89, "change": 1.9, "pct": 2.27, "rsi": 56.8, "above_sma": True},
    "RIVN": {"price": 12.12, "change": 0.41, "pct": 3.54, "rsi": 59.4, "above_sma": True},
    "LCID": {"price": 2.58, "change": 0.02, "pct": 0.59, "rsi": 53.2, "above_sma": True},
    "NIO": {"price": 2.85, "change": 0.16, "pct": 5.95, "rsi": 64.5, "above_sma": True},
    "BABA": {"price": 90.17, "change": 3.91, "pct": 4.53, "rsi": 61.5, "above_sma": True},
    "JD": {"price": 27.5, "change": 1.12, "pct": 4.26, "rsi": 60.9, "above_sma": True},
    "PDD": {"price": 89.39, "change": 1.97, "pct": 2.25, "rsi": 56.7, "above_sma": True},
    "BIDU": {"price": 63.78, "change": 0.29, "pct": 0.46, "rsi": 53.0, "above_sma": True},
    "SONY": {"price": 27.92, "change": -0.57, "pct": -2.02, "rsi": 47.8, "above_sma": False},
    "TM": {"price": 214.73, "change": -1.06, "pct": -0.49, "rsi": 51.0, "above_sma": False},
    "SAP": {"price": 213.46, "change": 4.09, "pct": 1.95, "rsi": 56.1, "above_sma": True},
    "NVO": {"price": 41.09, "change": 0.12, "pct": 0.29, "rsi": 52.6, "above_sma": True},
    "AZN": {"price": 183.38, "change": -0.83, "pct": -0.45, "rsi": 51.1, "above_sma": False},
    "NVS": {"price": 154.09, "change": -1.2, "pct": -0.78, "rsi": 50.4, "above_sma": False},
    "GILD": {"price": 175.82, "change": -0.92, "pct": -0.52, "rsi": 50.9, "above_sma": False},
    "REGN": {"price": 984.34, "change": 2.47, "pct": 0.25, "rsi": 52.5, "above_sma": True},
    "VRTX": {"price": 526.0, "change": -38.12, "pct": -6.76, "rsi": 37.8, "above_sma": False},
    "MRNA": {"price": 219.18, "change": -1.65, "pct": -0.75, "rsi": 50.4, "above_sma": False},
    "BMY": {"price": 61.2, "change": -0.36, "pct": -0.58, "rsi": 50.8, "above_sma": False},
    "MDT": {"price": 95.29, "change": -0.77, "pct": -0.8, "rsi": 50.3, "above_sma": False},
    "BSX": {"price": 45.08, "change": -0.04, "pct": -0.1, "rsi": 51.8, "above_sma": True},
    "ZTS": {"price": 82.18, "change": -0.42, "pct": -0.5, "rsi": 51.0, "above_sma": False},
    "COP": {"price": 138.03, "change": 3.01, "pct": 2.23, "rsi": 56.7, "above_sma": True},
    "SLB": {"price": 49.92, "change": 1.4, "pct": 2.89, "rsi": 58.1, "above_sma": True},
    "EOG": {"price": 150.93, "change": 2.62, "pct": 1.76, "rsi": 55.7, "above_sma": True},
    "NEE": {"price": 85.08, "change": -0.33, "pct": -0.39, "rsi": 51.2, "above_sma": True},
    "DUK": {"price": 132.04, "change": 0.14, "pct": 0.11, "rsi": 52.2, "above_sma": True},
    "SO": {"price": 95.06, "change": 0.06, "pct": 0.06, "rsi": 52.1, "above_sma": True},
    "D": {"price": 68.04, "change": 0.05, "pct": 0.07, "rsi": 52.1, "above_sma": True},
    "AMT": {"price": 184.49, "change": -0.1, "pct": -0.05, "rsi": 51.9, "above_sma": True},
    "PLD": {"price": 127.14, "change": 0.11, "pct": 0.09, "rsi": 52.2, "above_sma": True},
    "EQIX": {"price": 977.14, "change": -1.08, "pct": -0.11, "rsi": 51.8, "above_sma": True},
    "CMCSA": {"price": 26.13, "change": 0.4, "pct": 1.55, "rsi": 55.3, "above_sma": True},
    "CHTR": {"price": 155.52, "change": 8.25, "pct": 5.6, "rsi": 63.8, "above_sma": True},
    "TTWO": {"price": 230.79, "change": 3.46, "pct": 1.52, "rsi": 55.2, "above_sma": True},
    "RBLX": {"price": 58.77, "change": 3.14, "pct": 5.64, "rsi": 63.8, "above_sma": True},
    "SNAP": {"price": 5.29, "change": 0.25, "pct": 4.97, "rsi": 62.4, "above_sma": True},
    "PINS": {"price": 20.9, "change": 1.19, "pct": 6.04, "rsi": 64.7, "above_sma": True},
    "ZM": {"price": 91.54, "change": 2.98, "pct": 3.36, "rsi": 59.1, "above_sma": True},
    "DOCU": {"price": 80.99, "change": 0.24, "pct": 0.29, "rsi": 52.6, "above_sma": True},
    "DKNG": {"price": 18.0, "change": 0.35, "pct": 2.01, "rsi": 56.2, "above_sma": True},
    "MSTR": {"price": 82.12, "change": 2.16, "pct": 2.7, "rsi": 57.7, "above_sma": True},
    "SMCI": {"price": 23.47, "change": 0.16, "pct": 0.69, "rsi": 53.4, "above_sma": True},
    "DELL": {"price": 315.75, "change": 18.69, "pct": 6.29, "rsi": 65.2, "above_sma": True},
    "HPQ": {"price": 32.19, "change": 1.04, "pct": 3.34, "rsi": 59.0, "above_sma": True},
    "HPE": {"price": 42.92, "change": 2.1, "pct": 5.14, "rsi": 62.8, "above_sma": True},
    "APP": {"price": 396.22, "change": 17.27, "pct": 4.56, "rsi": 61.6, "above_sma": True},
    "GME": {"price": 26.47, "change": -0.5, "pct": -1.87, "rsi": 48.1, "above_sma": False},
    "AMC": {"price": 3.23, "change": 0.02, "pct": 0.62, "rsi": 53.3, "above_sma": True},
    "MAR": {"price": 417.79, "change": 2.02, "pct": 0.49, "rsi": 53.0, "above_sma": True},
    "HLT": {"price": 368.58, "change": 2.38, "pct": 0.65, "rsi": 53.4, "above_sma": True},
    "DAL": {"price": 84.52, "change": 1.57, "pct": 1.89, "rsi": 56.0, "above_sma": True},
    "UAL": {"price": 106.79, "change": 2.27, "pct": 2.17, "rsi": 56.6, "above_sma": True},
    "LUV": {"price": 46.61, "change": 0.66, "pct": 1.44, "rsi": 55.0, "above_sma": True},
    "CCL": {"price": 28.01, "change": 0.01, "pct": 0.05, "rsi": 52.1, "above_sma": True},
    "RCL": {"price": 314.3, "change": 0.19, "pct": 0.06, "rsi": 52.1, "above_sma": True},
    "BRK-A": {"price": 870289.56, "change": 139.56, "pct": 0.02, "rsi": 52.0, "above_sma": True},
    "NOC": {"price": 558.13, "change": 2.34, "pct": 0.42, "rsi": 52.9, "above_sma": True},
    "GD": {"price": 361.38, "change": 1.11, "pct": 0.31, "rsi": 52.7, "above_sma": True},
    "CI": {"price": 273.62, "change": 2.2, "pct": 0.81, "rsi": 53.7, "above_sma": True},
    "ELV": {"price": 393.28, "change": 3.58, "pct": 0.92, "rsi": 53.9, "above_sma": True},
    "CVS": {"price": 82.85, "change": 1.79, "pct": 2.21, "rsi": 56.6, "above_sma": True},
    "MCK": {"price": 1074.09, "change": -3.22, "pct": -0.3, "rsi": 51.4, "above_sma": True},
}

DDG_ICON_SET = {"BSE.NS", "COCHINSHIP.NS", "COP", "HCLTECH.NS", "ITC.NS", "JD", "LODHA.NS", "PANW", "SNPS", "T"}
FV2_ICON_SET = {"ALKEM.NS", "ANGELONE.NS", "BANDHANBNK.NS", "BEL.NS", "BHEL.NS", "BIOCON.NS", "CGPOWER.NS", "CHOLAFIN.NS", "FEDERALBNK.NS", "GODREJCP.NS", "GODREJPROP.NS", "HAL.NS", "HUDCO.NS", "MAZDOCK.NS", "NBCC.NS", "NMDC.NS", "NTPC.NS", "PNB.NS", "SAIL.NS", "SBILIFE.NS", "SRF.NS", "TCS.NS", "UNIONBANK.NS"}
SVG_MONOGRAM_SET = {"ACC.NS", "AMBUJACEM.NS", "BRK-A", "BRK-B", "CDSL.NS", "COALINDIA.NS", "FORTIS.NS", "GAIL.NS", "IRCTC.NS", "IREDA.NS", "IRFC.NS", "RVNL.NS", "SUZLON.NS", "UBL.NS"}

LEGACY_TICKER_REMAP = {
    "ZOMATO.NS": "ETERNAL.NS",
    "TATAMOTORS.NS": "TMPV.NS",
}

CORE_TICKERS = [
    "RELIANCE.NS", "JIOFIN.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "SBIN.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "TMPV.NS", "ETERNAL.NS", "HAL.NS",
    "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META",
]

SECTOR_PALETTE = [
    ("#2563EB", "#1D4ED8"),
    ("#059669", "#047857"),
    ("#7C3AED", "#5B21B6"),
    ("#D97706", "#B45309"),
    ("#DC2626", "#991B1B"),
    ("#0891B2", "#0E7490"),
]


def get_ist_now() -> datetime:
    return datetime.now(timezone.utc).astimezone(IST_TZ)


def get_us_et_now() -> datetime:
    return datetime.now(timezone.utc).astimezone(US_ET_TZ)


def check_market_trading_hours(ticker: str) -> tuple[bool, str]:
    now_ist = get_ist_now()
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")

    if is_indian:
        time_str = now_ist.strftime("%I:%M %p IST")
        if now_ist.weekday() >= 5:
            return False, f"Weekend ({now_ist.strftime('%A')}, {time_str}) — NSE closed."
        m_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
        m_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
        if m_open <= now_ist <= m_close:
            return True, f"NSE Market Open ({time_str})"
        return False, f"NSE Hours: Mon–Fri 9:15 AM – 3:30 PM IST (Now: {time_str})"

    now_et = get_us_et_now()
    tz_abbr = now_et.tzname() or "ET"
    et_str = now_et.strftime(f"%I:%M %p {tz_abbr}")
    ist_str = now_ist.strftime("%I:%M %p IST")
    if now_et.weekday() >= 5:
        return False, f"Weekend ({now_et.strftime('%A')}, {et_str}) — US market closed."
    us_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    us_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    if us_open <= now_et <= us_close:
        return True, f"US Market Open ({et_str} / {ist_str})"
    return False, f"US Hours: Mon–Fri 9:30 AM – 4:00 PM {tz_abbr} (Now: {et_str} / {ist_str})"


def is_indian_equity(ticker: str) -> bool:
    return ticker.endswith(".NS") or ticker.endswith(".BO")


def get_ticker_meta(ticker: str) -> dict:
    resolved = LEGACY_TICKER_REMAP.get(ticker, ticker)
    return STOCK_CATALOG.get(
        resolved,
        {
            "name": resolved,
            "sector": "Global Equity",
            "domain": "google.com",
            "exchange": "NSE" if is_indian_equity(resolved) else "US",
            "currency": "₹" if is_indian_equity(resolved) else "$",
        },
    )


def get_fx_rate_for_ticker(ticker: str, usdinr_rate: float) -> float:
    return 1.0 if is_indian_equity(ticker) else max(1.0, float(usdinr_rate or DEFAULT_USDINR_RATE))


def _make_monogram_svg_uri(ticker: str) -> str:
    clean = re.sub(r"[^A-Z0-9]", "", ticker.replace(".NS", "").upper()) or "EQ"
    initials = clean[:2] if len(clean) >= 2 else clean
    c1, c2 = SECTOR_PALETTE[sum(ord(ch) for ch in clean) % len(SECTOR_PALETTE)]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>'
        f'</linearGradient></defs>'
        f'<rect width="64" height="64" rx="16" fill="url(#g)"/>'
        f'<text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" '
        f'font-family="Inter,Arial,sans-serif" font-size="24" font-weight="800" fill="#ffffff">{initials}</text>'
        f'</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def get_logo_url(ticker: str) -> str:
    resolved = LEGACY_TICKER_REMAP.get(ticker, ticker)
    if resolved in SVG_MONOGRAM_SET:
        return _make_monogram_svg_uri(resolved)
    dom = get_ticker_meta(resolved).get("domain", "google.com")
    if resolved in DDG_ICON_SET:
        return f"https://icons.duckduckgo.com/ip3/{dom}.ico"
    if resolved in FV2_ICON_SET:
        return f"https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{dom}&size=128"
    return f"https://www.google.com/s2/favicons?domain={dom}&sz=128"


def stock_icon_html(ticker: str, size: int = 30, radius: int = 8) -> str:
    url = get_logo_url(ticker)
    fallback = _make_monogram_svg_uri(ticker)
    alt_txt = html.escape(get_ticker_meta(ticker)["name"])
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:{size}px;height:{size}px;min-width:{size}px;border-radius:{radius}px;'
        f'background:#ffffff;border:1px solid rgba(148,163,184,0.35);'
        f'box-shadow:0 2px 6px rgba(15,23,42,0.12);overflow:hidden;padding:3px;">'
        f'<img src="{url}" alt="{alt_txt}" loading="lazy" '
        f'onerror="this.onerror=null;this.src=\'{fallback}\';" '
        f'style="width:100%;height:100%;object-fit:contain;border-radius:{max(2, radius - 3)}px;"/>'
        f'</span>'
    )


def compute_brokerage_breakdown(segment: str, buy_price: float, sell_price: float, qty: int) -> dict:
    qty = max(1, int(qty))
    buy_val = float(buy_price) * qty
    sell_val = float(sell_price) * qty
    turnover = buy_val + sell_val
    gross_pnl = sell_val - buy_val

    if "Delivery" in segment or "CNC" in segment:
        brokerage = 0.0
        stt = turnover * 0.001
        stamp_duty = buy_val * 0.00015
    elif "Futures" in segment or "F&O" in segment:
        brokerage = min(20.0, buy_val * 0.0003) + min(20.0, sell_val * 0.0003)
        stt = sell_val * 0.0002
        stamp_duty = buy_val * 0.00002
    else:
        brokerage = min(20.0, buy_val * 0.0003) + min(20.0, sell_val * 0.0003)
        stt = sell_val * 0.00025
        stamp_duty = buy_val * 0.00003

    exch_txn = turnover * 0.0000307
    sebi_fee = turnover * 0.000001
    gst = 0.18 * (brokerage + exch_txn + sebi_fee)
    total_charges = brokerage + stt + exch_txn + sebi_fee + gst + stamp_duty
    net_pnl = gross_pnl - total_charges
    breakeven_pts = total_charges / qty

    return {
        "turnover": turnover,
        "gross_pnl": gross_pnl,
        "brokerage": brokerage,
        "stt": stt,
        "exch_txn": exch_txn,
        "sebi_fee": sebi_fee,
        "gst": gst,
        "stamp_duty": stamp_duty,
        "total_charges": total_charges,
        "net_pnl": net_pnl,
        "breakeven_pts": breakeven_pts,
    }


def compute_wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(avg_loss > 0, np.where(avg_gain > 0, 100.0, 50.0))
    return rsi.fillna(50.0)


def enrich_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    if getattr(out.index, "tz", None) is not None:
        out.index = out.index.tz_localize(None)

    close = out["Close"].astype(float)
    high = out["High"].astype(float)
    low = out["Low"].astype(float)

    out["SMA_20"] = close.rolling(20).mean()
    out["EMA_50"] = close.ewm(span=50, adjust=False).mean()

    bb_std = close.rolling(20).std()
    out["BB_Mid"] = out["SMA_20"]
    out["BB_Upper"] = out["BB_Mid"] + (2.0 * bb_std)
    out["BB_Lower"] = out["BB_Mid"] - (2.0 * bb_std)
    bb_range = (out["BB_Upper"] - out["BB_Lower"]).replace(0.0, np.nan)
    out["BB_PctB"] = ((close - out["BB_Lower"]) / bb_range).fillna(0.5)

    out["RSI"] = compute_wilder_rsi(close, 14)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_Signal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_Hist"] = out["MACD"] - out["MACD_Signal"]

    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    out["ATR_14"] = tr.rolling(14).mean()
    return out


def _build_default_snapshots() -> tuple[dict, dict, float, bool, str]:
    snaps = copy.deepcopy(DEFAULT_STOCKS_SNAPSHOTS)
    for v in snaps.values():
        p = v["price"]
        v.setdefault("prev_close", p - v["change"])
        v.setdefault("sma20", p * (0.985 if v["above_sma"] else 1.015))
        v.setdefault("ema50", p * (0.97 if v["above_sma"] else 1.03))
        v.setdefault("atr", p * 0.018)
        v.setdefault("sparkline", [round(p * (0.97 + 0.006 * i), 2) for i in range(6)])
        v.setdefault("volume", 0.0)
        v.setdefault("avg_volume", 1.0)
    idx_snaps = copy.deepcopy(DEFAULT_INDEX_SNAPSHOTS)
    return snaps, idx_snaps, DEFAULT_USDINR_RATE, False, "Cached Baseline"


def _extract_chunk_metrics(raw: pd.DataFrame, symbols: list[str], snaps: dict, idx_snaps: dict, usdinr: float) -> tuple[float, int]:
    if raw is None or raw.empty:
        return usdinr, 0

    top_cols = set(raw.columns.get_level_values(0)) if isinstance(raw.columns, pd.MultiIndex) else set()
    live_hits = 0

    if "USDINR=X" in top_cols:
        fx_close = raw["USDINR=X"]["Close"].dropna().astype(float)
        if not fx_close.empty:
            usdinr = float(fx_close.iloc[-1])
            fx_prev = float(fx_close.iloc[-2]) if len(fx_close) >= 2 else usdinr
            fx_chg = usdinr - fx_prev
            fx_pct = (fx_chg / fx_prev * 100.0) if fx_prev else 0.0
            idx_snaps["USDINR=X"] = {
                "price": usdinr,
                "change": fx_chg,
                "pct": fx_pct,
                "sparkline": [round(float(x), 2) for x in fx_close.tail(20).tolist()],
            }

    for sym in symbols:
        if sym == "USDINR=X" or sym not in top_cols:
            continue
        sub = raw[sym].dropna(subset=["Close"])
        if len(sub) < 2:
            continue

        close_s = sub["Close"].astype(float)
        last_c = float(close_s.iloc[-1])
        prev_c = float(close_s.iloc[-2])
        chg = last_c - prev_c
        pct = (chg / prev_c * 100.0) if prev_c else 0.0

        if sym in MARKET_INDICES:
            idx_snaps[sym] = {
                "price": last_c,
                "change": chg,
                "pct": pct,
                "sparkline": [round(float(x), 2) for x in close_s.tail(20).tolist()],
            }
            live_hits += 1
            continue

        rsi_val = float(compute_wilder_rsi(close_s, 14).iloc[-1])
        sma20 = float(close_s.tail(20).mean())
        ema50 = float(close_s.ewm(span=50, adjust=False).mean().iloc[-1])

        high_s = sub["High"].astype(float) if "High" in sub else close_s
        low_s = sub["Low"].astype(float) if "Low" in sub else close_s
        atr_val = float((high_s - low_s).tail(14).mean()) if len(sub) >= 2 else last_c * 0.02

        vol_s = sub["Volume"].astype(float) if "Volume" in sub else pd.Series([0.0])
        vol_last = float(vol_s.iloc[-1]) if not vol_s.empty else 0.0
        vol_avg = float(vol_s.tail(20).mean()) if not vol_s.empty and float(vol_s.tail(20).mean()) > 0 else 1.0

        snaps[sym] = {
            "price": last_c,
            "prev_close": prev_c,
            "change": chg,
            "pct": pct,
            "rsi": rsi_val,
            "sma20": sma20,
            "ema50": ema50,
            "above_sma": bool(last_c >= sma20),
            "atr": atr_val,
            "sparkline": [round(float(x), 2) for x in close_s.tail(20).tolist()],
            "volume": vol_last,
            "avg_volume": vol_avg,
        }
        live_hits += 1

    return usdinr, live_hits


@st.cache_data(ttl="5m", max_entries=8, refresh_mode="background", show_spinner=False)
def fetch_core_market_snapshots():
    snaps, idx_snaps, usdinr, _, _ = _build_default_snapshots()
    core_symbols = list(CORE_TICKERS) + list(MARKET_INDICES.keys()) + ["USDINR=X"]
    try:
        raw = yf.download(core_symbols, period="1mo", group_by="ticker", threads=True, progress=False)
        usdinr, hits = _extract_chunk_metrics(raw, core_symbols, snaps, idx_snaps, usdinr)
        is_live = hits >= 5
        stamp = get_ist_now().strftime("%d %b %Y, %I:%M %p IST") if is_live else "Cached Baseline"
        return snaps, idx_snaps, usdinr, is_live, stamp
    except Exception:
        return snaps, idx_snaps, usdinr, False, "Cached Baseline (Offline)"


@st.cache_data(ttl="5m", max_entries=48, refresh_mode="background", show_spinner=False)
def fetch_ticker_batch(tickers_tuple: tuple[str, ...]) -> dict:
    syms = [LEGACY_TICKER_REMAP.get(s, s) for s in tickers_tuple if LEGACY_TICKER_REMAP.get(s, s) not in CORE_TICKERS]
    if not syms:
        return {}
    snaps = {}
    dummy_idx = {}
    usdinr = DEFAULT_USDINR_RATE
    try:
        for start in range(0, len(syms), 20):
            chunk = syms[start : start + 20]
            raw = yf.download(chunk, period="1mo", group_by="ticker", threads=True, progress=False)
            usdinr, _ = _extract_chunk_metrics(raw, chunk, snaps, dummy_idx, usdinr)
    except Exception:
        pass
    return snaps


def ensure_symbols_live(tickers: list[str] | tuple[str, ...], base_snaps: dict) -> dict:
    missing = tuple(
        sorted({LEGACY_TICKER_REMAP.get(s, s) for s in tickers if LEGACY_TICKER_REMAP.get(s, s) in STOCK_CATALOG})
    )
    need = tuple(s for s in missing if s not in CORE_TICKERS)
    if not need:
        return base_snaps
    fetched = fetch_ticker_batch(need)
    if not fetched:
        return base_snaps
    merged = copy.deepcopy(base_snaps)
    merged.update(fetched)
    return merged


@st.cache_data(ttl="10m", max_entries=4, refresh_mode="background", show_spinner=False)
def fetch_extended_market_snapshots():
    top_ext = tuple(s for s in list(STOCK_CATALOG.keys())[:48] if s not in CORE_TICKERS)
    return fetch_ticker_batch(top_ext)


def fetch_all_market_snapshots(tickers_tuple: tuple[str, ...]):
    snaps, idx_snaps, usdinr, is_live, stamp = fetch_core_market_snapshots()
    merged = copy.deepcopy(snaps)
    need = tuple(s for s in tickers_tuple if s not in CORE_TICKERS)
    if need:
        ext = fetch_ticker_batch(need[:48])
        if ext:
            merged.update(ext)
    return merged, idx_snaps, usdinr, is_live, stamp


@st.cache_data(ttl="5m", max_entries=32, refresh_mode="background", show_spinner=False)
def fetch_stock_history(symbol: str, period: str = "1y") -> pd.DataFrame | None:
    resolved = LEGACY_TICKER_REMAP.get(symbol, symbol)
    try:
        df = yf.Ticker(resolved).history(period=period)
        if df is None or df.empty:
            return None
        return enrich_technical_indicators(df)
    except Exception:
        return None


@st.cache_data(ttl="30m", max_entries=32, show_spinner=False)
def fetch_stock_fundamentals(symbol: str) -> dict:
    resolved = LEGACY_TICKER_REMAP.get(symbol, symbol)
    try:
        info = yf.Ticker(resolved).info or {}
        return {
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "trailingEps": info.get("trailingEps"),
            "dividendYield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "recommendationKey": info.get("recommendationKey"),
            "summary": info.get("longBusinessSummary", ""),
        }
    except Exception:
        return {}


@st.cache_data(ttl="15m", max_entries=24, show_spinner=False)
def fetch_stock_news_headlines(symbol: str, company_name: str) -> list[dict]:
    query = urllib.parse.quote(f"{company_name} {symbol.replace('.NS', '')} stock")
    is_in = is_indian_equity(symbol)
    gl, ceid = ("IN", "IN:en") if is_in else ("US", "US:en")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-{gl}&gl={gl}&ceid={ceid}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        items = []
        for item in root.findall(".//item")[:4]:
            title = (item.findtext("title") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            link = (item.findtext("link") or "").strip()
            if title:
                items.append({"title": title, "pubDate": pub[:16], "link": link})
        return items
    except Exception:
        return []


@st.cache_data(ttl="15m", max_entries=16, show_spinner=False)
def fetch_peer_closes(tickers_tuple: tuple[str, ...], period: str = "6mo") -> pd.DataFrame | None:
    try:
        raw = yf.download(list(tickers_tuple), period=period, threads=True, progress=False)
        if raw is None or raw.empty:
            return None
        close_df = raw["Close"] if "Close" in raw else raw
        if isinstance(close_df, pd.Series):
            close_df = close_df.to_frame(name=tickers_tuple[0])
        if getattr(close_df.index, "tz", None) is not None:
            close_df.index = close_df.index.tz_localize(None)
        return close_df.dropna(how="all")
    except Exception:
        return None


def format_large_number(val: float | int | None, currency: str = "₹") -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    v = float(val)
    if v >= 1e12:
        return f"{currency}{v / 1e12:.2f}T"
    if v >= 1e9:
        return f"{currency}{v / 1e9:.2f}B"
    if v >= 1e7 and currency == "₹":
        return f"₹{v / 1e7:,.2f} Cr"
    if v >= 1e6:
        return f"{currency}{v / 1e6:.2f}M"
    return f"{currency}{v:,.2f}"


ML_FEATURE_COLS = [
    "ret_1d", "ret_3d", "ret_5d", "ret_10d",
    "sma20_ratio", "ema50_ratio", "rsi_norm",
    "macd_hist_norm", "bb_pctb", "vol_14d", "vol_ratio",
]


def build_stationary_ml_frame(df: pd.DataFrame) -> pd.DataFrame:
    feat = pd.DataFrame(index=df.index)
    close = df["Close"].astype(float)
    vol = df["Volume"].astype(float).replace(0.0, np.nan)
    vol_ma = vol.rolling(20).mean().replace(0.0, np.nan)

    feat["Close"] = close
    feat["ret_1d"] = close.pct_change(1)
    feat["ret_3d"] = close.pct_change(3)
    feat["ret_5d"] = close.pct_change(5)
    feat["ret_10d"] = close.pct_change(10)
    feat["sma20_ratio"] = (close / df["SMA_20"]) - 1.0
    feat["ema50_ratio"] = (close / df["EMA_50"]) - 1.0
    feat["rsi_norm"] = (df["RSI"] - 50.0) / 50.0
    feat["macd_hist_norm"] = df["MACD_Hist"] / close
    feat["bb_pctb"] = df["BB_PctB"]
    feat["vol_14d"] = feat["ret_1d"].rolling(14).std()
    feat["vol_ratio"] = (vol / vol_ma).fillna(1.0).clip(0.2, 5.0)
    feat["target_ret_1d"] = close.shift(-1) / close - 1.0

    return feat.replace([np.inf, -np.inf], np.nan).dropna()


HEALTH_FEATURE_COLS = [
    "ret_1d", "ret_5d", "ret_20d", "ret_60d",
    "sma20_dist", "ema50_dist", "trend_spread",
    "rsi_14", "macd_hist_norm", "bb_pctb",
    "atr_pct", "ann_vol_20", "ann_vol_60",
    "drawdown_60d", "trend_efficiency_20d", "win_ratio_20d", "vol_ratio",
]


def build_health_feature_frame(df: pd.DataFrame, include_targets: bool = False) -> pd.DataFrame:
    feat = pd.DataFrame(index=df.index)
    close = df["Close"].astype(float)
    high = df["High"].astype(float) if "High" in df else close
    vol = df["Volume"].astype(float).replace(0.0, np.nan)
    vol_ma = vol.rolling(20).mean().replace(0.0, np.nan)

    ret_1d = close.pct_change(1)
    abs_step = close.diff().abs().rolling(20).sum().replace(0.0, np.nan)
    net_step = (close - close.shift(20)).abs()
    roll_high_60 = high.rolling(60, min_periods=20).max()

    feat["ret_1d"] = ret_1d
    feat["ret_5d"] = close.pct_change(5)
    feat["ret_20d"] = close.pct_change(20)
    feat["ret_60d"] = close.pct_change(60).fillna(feat["ret_20d"])
    feat["sma20_dist"] = (close / df["SMA_20"]) - 1.0
    feat["ema50_dist"] = (close / df["EMA_50"]) - 1.0
    feat["trend_spread"] = (df["SMA_20"] / df["EMA_50"]) - 1.0
    feat["rsi_14"] = df["RSI"].astype(float)
    feat["macd_hist_norm"] = df["MACD_Hist"] / close
    feat["bb_pctb"] = df["BB_PctB"].astype(float)
    feat["atr_pct"] = (df["ATR_14"] / close).fillna(0.02)
    feat["ann_vol_20"] = ret_1d.rolling(20).std().fillna(ret_1d.rolling(10).std()) * np.sqrt(252.0)
    feat["ann_vol_60"] = ret_1d.rolling(60, min_periods=20).std().fillna(feat["ann_vol_20"]) * np.sqrt(252.0)
    feat["drawdown_60d"] = ((close / roll_high_60) - 1.0).fillna(0.0)
    feat["trend_efficiency_20d"] = (net_step / abs_step).fillna(0.25).clip(0.0, 1.0)
    feat["win_ratio_20d"] = (ret_1d > 0).astype(float).rolling(20, min_periods=10).mean().fillna(0.5)
    feat["vol_ratio"] = (vol / vol_ma).fillna(1.0).clip(0.2, 5.0)

    if include_targets:
        fwd_ret_20d = (close.shift(-20) / close) - 1.0
        fwd_vol_20d = ret_1d.rolling(20).std().shift(-20) * np.sqrt(252.0)
        fwd_low_20d = close.rolling(20).min().shift(-20)
        fwd_mdd_20d = (fwd_low_20d / close) - 1.0
        feat["fwd_ret_20d"] = fwd_ret_20d
        feat["fwd_vol_20d"] = fwd_vol_20d
        feat["fwd_mdd_20d"] = fwd_mdd_20d
        feat["fwd_suitability"] = np.clip(
            (fwd_ret_20d * 2.5) - (fwd_vol_20d * 1.4) + (0.6 * (1.0 + fwd_mdd_20d)),
            -2.0,
            2.0,
        )
        conditions = [
            (fwd_vol_20d >= 0.37) | (fwd_mdd_20d <= -0.095),
            (fwd_vol_20d <= 0.27) & (fwd_mdd_20d > -0.055) & (fwd_ret_20d >= -0.01),
        ]
        feat["health_class"] = np.select(conditions, [0, 2], default=1).astype(int)

    return feat.replace([np.inf, -np.inf], np.nan).dropna()


@st.cache_resource(show_spinner=False)
def load_trained_ml_artifacts() -> dict:
    res: dict = {"loaded": False, "health": None, "basket": None, "metrics": {}}
    try:
        m_path = MODELS_DIR / "training_metrics.json"
        if m_path.exists():
            res["metrics"] = json.loads(m_path.read_text(encoding="utf-8"))
        h_path = MODELS_DIR / "traffic_light_model.joblib"
        b_path = MODELS_DIR / "smart_basket_model.joblib"
        if h_path.exists() and b_path.exists():
            res["health"] = joblib.load(h_path)
            res["basket"] = joblib.load(b_path)
            res["loaded"] = True
    except Exception:
        res["loaded"] = False
    return res


@st.cache_data(ttl="15m", max_entries=16, refresh_mode="background", show_spinner=False)
def fetch_basket_candidate_histories(tickers_tuple: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    syms = [LEGACY_TICKER_REMAP.get(s, s) for s in tickers_tuple if LEGACY_TICKER_REMAP.get(s, s) in STOCK_CATALOG]
    out: dict[str, pd.DataFrame] = {}
    if not syms:
        return out
    try:
        raw = yf.download(syms, period="1y", group_by="ticker", threads=True, progress=False)
        if raw is None or raw.empty:
            return out
        top_cols = set(raw.columns.get_level_values(0)) if isinstance(raw.columns, pd.MultiIndex) else set()
        for sym in syms:
            sub = raw[sym].dropna(subset=["Close", "High", "Low"]).copy() if sym in top_cols else (raw.dropna(subset=["Close"]).copy() if len(syms) == 1 else None)
            if sub is not None and len(sub) >= 65:
                out[sym] = enrich_technical_indicators(sub)
    except Exception:
        pass
    return out


def compute_traffic_light_health(
    sym: str,
    df_hist: pd.DataFrame | None = None,
    snap: dict | None = None,
) -> dict:
    resolved = LEGACY_TICKER_REMAP.get(sym, sym)
    meta = get_ticker_meta(resolved)
    sn = snap or DEFAULT_STOCKS_SNAPSHOTS.get(resolved, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True})
    df = df_hist if df_hist is not None else fetch_stock_history(resolved, "1y")

    artifacts = load_trained_ml_artifacts()
    price = float(sn.get("price", 100.0))
    pct = float(sn.get("pct", 0.0))
    rsi_14 = float(sn.get("rsi", 50.0))
    ret_20d = 0.02 if sn.get("above_sma", True) else -0.02
    sma20_dist = 0.015 if sn.get("above_sma", True) else -0.015
    ann_vol = 0.26
    drawdown_60d = -0.04
    suitability = 0.25 if sn.get("above_sma", True) else -0.15
    probs = np.array([0.22, 0.34, 0.44])
    model_used = "Quant Baseline Fallback"

    if df is not None and len(df) >= 30:
        close = df["Close"].dropna().astype(float)
        if not close.empty and np.isfinite(close.iloc[-1]):
            price = float(close.iloc[-1])
            prev_c = float(close.iloc[-2]) if len(close) >= 2 and np.isfinite(close.iloc[-2]) else price
            pct = ((price - prev_c) / prev_c * 100.0) if prev_c else 0.0
        feat_df = build_health_feature_frame(df, include_targets=False)
        if not feat_df.empty:
            last_row = feat_df.iloc[-1]
            ret_20d = float(np.nan_to_num(last_row["ret_20d"], nan=ret_20d))
            sma20_dist = float(np.nan_to_num(last_row["sma20_dist"], nan=sma20_dist))
            rsi_14 = float(np.nan_to_num(last_row["rsi_14"], nan=rsi_14))
            ann_vol = float(np.clip(np.nan_to_num(last_row["ann_vol_20"], nan=ann_vol), 0.08, 1.2))
            drawdown_60d = float(np.nan_to_num(last_row["drawdown_60d"], nan=drawdown_60d))

            if artifacts.get("loaded") and artifacts["health"] and artifacts["basket"]:
                try:
                    h_bundle = artifacts["health"]
                    b_bundle = artifacts["basket"]
                    cols = h_bundle.get("feature_cols", HEALTH_FEATURE_COLS)
                    x_vec = np.nan_to_num(np.array([[float(last_row[c]) for c in cols]]), nan=0.0, posinf=0.0, neginf=0.0)
                    probs = np.asarray(h_bundle["model"].predict_proba(x_vec)[0], dtype=float)
                    suitability = float(b_bundle["model"].predict(x_vec)[0])
                    model_used = f"{h_bundle['model_name']} + {b_bundle['model_name']} (3Y Trained ML)"
                except Exception:
                    pass
            else:
                h_score_tmp = np.clip((0.02 if sma20_dist >= 0 else -0.02) + (0.30 - ann_vol), -0.4, 0.4)
                probs = np.array([max(0.1, 0.35 - h_score_tmp), 0.30, max(0.1, 0.35 + h_score_tmp)])
                probs = probs / probs.sum()
    else:
        base_p = 0.52 if (sn.get("above_sma", True) and 40 <= rsi_14 <= 66) else (0.20 if rsi_14 >= 70 or not sn.get("above_sma", True) else 0.36)
        probs = np.array([max(0.12, 0.65 - base_p), 0.35, base_p])
        probs = probs / probs.sum()

    score = int(round(np.clip(probs[2] * 100.0 + probs[1] * 55.0 + probs[0] * 12.0, 5.0, 99.0)))
    if score >= 66:
        label, color, badge_clr = "Healthy", "#10b981", "green"
        pill = "🟢 Healthy · Beginner Friendly"
    elif score >= 45:
        label, color, badge_clr = "Moderate", "#f59e0b", "orange"
        pill = "🟡 Moderate · Watch & Hold"
    else:
        label, color, badge_clr = "High Risk", "#ef4444", "red"
        pill = "🔴 High Risk · Volatile / Caution"

    if sma20_dist >= 0.0 and ret_20d >= 0.015:
        trend_plain = f"Steady Uptrend — Price has climbed {ret_20d*100:+.1f}% over the last month and sits above its trend line."
    elif sma20_dist >= -0.01:
        trend_plain = "Stable Support — Holding steady near its 1-month average price without sharp weakness."
    else:
        trend_plain = f"Cooling Trend — Trading {abs(sma20_dist)*100:.1f}% below its 1-month average; wait for stability."

    if rsi_14 >= 70.0:
        timing_plain = "Heated Entry — Jumped quickly in recent sessions; beginners may want to wait for a small dip."
    elif rsi_14 <= 34.0:
        timing_plain = "Discounted Zone — Pulled back noticeably below recent highs; look closely at risk before buying."
    else:
        timing_plain = "Fair Entry Zone — Price momentum is balanced and not overhyped right now."

    if ann_vol <= 0.25:
        risk_plain = f"Calm Price Swings — Smooth daily movement (~{ann_vol*100:.0f}% annualized volatility), well-suited for beginners."
    elif ann_vol <= 0.37:
        risk_plain = f"Moderate Price Swings — Normal market ups and downs (~{ann_vol*100:.0f}% annualized volatility)."
    else:
        risk_plain = f"Large Daily Swings — Elevated volatility (~{ann_vol*100:.0f}% annualized); expect sharper ups and downs."

    return {
        "sym": resolved,
        "meta": meta,
        "score": score,
        "label": label,
        "color": color,
        "badge_clr": badge_clr,
        "pill": pill,
        "probs": {
            "Healthy": round(float(probs[2]) * 100.0, 1),
            "Moderate": round(float(probs[1]) * 100.0, 1),
            "High Risk": round(float(probs[0]) * 100.0, 1),
        },
        "suitability": round(float(suitability), 3),
        "trend_plain": trend_plain,
        "timing_plain": timing_plain,
        "risk_plain": risk_plain,
        "model_used": model_used,
        "ann_vol_pct": round(ann_vol * 100.0, 1),
        "drawdown_pct": round(drawdown_60d * 100.0, 1),
        "ret_20d_pct": round(ret_20d * 100.0, 1),
        "price": price,
        "pct": pct,
    }


def score_quick_health_baseline(sym: str, snaps: dict) -> dict:
    resolved = LEGACY_TICKER_REMAP.get(sym, sym)
    meta = get_ticker_meta(resolved)
    sn = snaps.get(resolved, DEFAULT_STOCKS_SNAPSHOTS.get(resolved, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))
    pct = float(sn.get("pct", 0.0))
    rsi = float(sn.get("rsi", 50.0))
    above = bool(sn.get("above_sma", True))
    vol_est = min(55.0, max(14.0, 22.0 + abs(pct) * 3.8 + (4.0 if not above else 0.0)))

    s = 50.0
    s += 14.0 if above else -11.0
    s += 10.0 if 44.0 <= rsi <= 64.0 else (-10.0 if rsi >= 72.0 else (-4.0 if rsi <= 32.0 else 3.0))
    s += max(-10.0, min(12.0, pct * 2.5))
    s += max(-12.0, min(10.0, (28.0 - vol_est) * 0.5))
    score = int(round(max(12.0, min(95.0, s))))
    if score >= 66:
        label, pill, clr = "Healthy", "🟢 Healthy · Beginner Friendly", "#10b981"
    elif score >= 45:
        label, pill, clr = "Moderate", "🟡 Moderate · Watch & Hold", "#f59e0b"
    else:
        label, pill, clr = "High Risk", "🔴 High Risk · Volatile / Caution", "#ef4444"
    return {
        "sym": resolved,
        "meta": meta,
        "score": score,
        "label": label,
        "pill": pill,
        "color": clr,
        "price": float(sn.get("price", 100.0)),
        "pct": pct,
        "rsi": rsi,
        "vol_est": round(vol_est, 1),
    }


def build_beginner_smart_basket(
    budget_inr: float = 25000.0,
    risk_profile: str = "Balanced Mix",
    market_pref: str = "Global Mix (India + US)",
    snapshots: dict | None = None,
    usdinr_rate: float = DEFAULT_USDINR_RATE,
    basket_size: int = 5,
    weight_mode: str = "Risk-Parity (Inverse Volatility)",
    preferred_sectors: list[str] | None = None,
) -> dict:
    base_snaps = snapshots or {}
    budget = max(2000.0, float(budget_inr))
    pref_u = market_pref.upper()
    wants_nse = "INDIA" in pref_u or "NSE" in pref_u or "GLOBAL" in pref_u
    wants_us = "US" in pref_u or "NASDAQ" in pref_u or "GLOBAL" in pref_u
    sec_set = set(preferred_sectors or [])

    eligible: list[str] = []
    max_single_share_inr = budget * (0.42 if basket_size >= 5 else 0.48)
    for sym, meta in STOCK_CATALOG.items():
        is_in = meta["exchange"] == "NSE"
        if is_in and not wants_nse:
            continue
        if (not is_in) and not wants_us:
            continue
        if sec_set and meta["sector"] not in sec_set:
            continue
        sn = base_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 500.0}))
        px_inr = float(sn.get("price", 500.0)) * get_fx_rate_for_ticker(sym, usdinr_rate)
        if 5.0 <= px_inr <= max_single_share_inr:
            eligible.append(sym)

    if len(eligible) < basket_size:
        eligible = [
            s for s, m in STOCK_CATALOG.items()
            if ((m["exchange"] == "NSE" and wants_nse) or (m["exchange"] != "NSE" and wants_us))
        ][:30]

    seen_sectors: set[str] = set()
    nse_short, us_short = [], []
    for sym in eligible:
        sec = STOCK_CATALOG[sym]["sector"]
        if not sec_set and sec in seen_sectors and len(nse_short) + len(us_short) < 12:
            continue
        seen_sectors.add(sec)
        if STOCK_CATALOG[sym]["exchange"] == "NSE":
            if len(nse_short) < 8:
                nse_short.append(sym)
        else:
            if len(us_short) < 8:
                us_short.append(sym)
        if len(nse_short) + len(us_short) >= 16:
            break

    shortlist = (nse_short + us_short) if (wants_nse and wants_us) else (nse_short or us_short)
    if len(shortlist) < max(basket_size + 4, 12):
        for s in eligible:
            if s not in shortlist:
                shortlist.append(s)
            if len(shortlist) >= 16:
                break

    live_snaps = ensure_symbols_live(shortlist, base_snaps)
    hist_map = fetch_basket_candidate_histories(tuple(shortlist))

    scored: list[dict] = []
    for sym in shortlist:
        sn = live_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 500.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))
        h = compute_traffic_light_health(sym, hist_map.get(sym), sn)
        fx = get_fx_rate_for_ticker(sym, usdinr_rate)
        share_inr = float(h["price"]) * fx
        if not np.isfinite(share_inr) or share_inr <= 0 or share_inr > budget:
            continue

        p_healthy = h["probs"]["Healthy"] / 100.0
        p_risk = h["probs"]["High Risk"] / 100.0
        suit = float(h["suitability"])
        vol_ratio_pen = max(0.0, h["ann_vol_pct"] - 25.0) / 100.0

        if risk_profile == "Safe & Steady":
            rank_score = (p_healthy * 2.2) + (suit * 0.9) - (p_risk * 1.6) - (vol_ratio_pen * 1.4)
        elif risk_profile == "High Growth":
            rank_score = (suit * 1.8) + (p_healthy * 0.9) + (max(-5.0, h["ret_20d_pct"]) / 25.0) - (p_risk * 0.6)
        else:
            rank_score = (suit * 1.4) + (p_healthy * 1.5) - (p_risk * 1.0) - (vol_ratio_pen * 0.5)

        scored.append({**h, "fx": fx, "share_inr": share_inr, "rank_score": rank_score})

    scored.sort(key=lambda x: x["rank_score"], reverse=True)

    chosen: list[dict] = []
    used_sectors: set[str] = set()
    if wants_nse and wants_us and basket_size >= 4:
        for target_in in (True, True, False):
            ex_picks = [c for c in scored if (c["meta"]["exchange"] == "NSE") == target_in]
            for c in ex_picks:
                if c["sym"] not in {x["sym"] for x in chosen} and c["meta"]["sector"] not in used_sectors:
                    chosen.append(c)
                    used_sectors.add(c["meta"]["sector"])
                    break
            if len(chosen) >= basket_size:
                break

    for c in scored:
        if len(chosen) >= basket_size:
            break
        if c["sym"] not in {x["sym"] for x in chosen} and c["meta"]["sector"] not in used_sectors:
            chosen.append(c)
            used_sectors.add(c["meta"]["sector"])
    for c in scored:
        if len(chosen) >= basket_size:
            break
        if c["sym"] not in {x["sym"] for x in chosen}:
            chosen.append(c)

    if not chosen:
        return {"items": [], "total_cost_inr": 0.0, "leftover_inr": budget, "budget_inr": budget}

    chosen_syms = [c["sym"] for c in chosen]
    close_cols = {}
    for sym in chosen_syms:
        df_h = hist_map.get(sym)
        if df_h is not None and len(df_h) >= 40:
            close_cols[sym] = df_h["Close"].tail(126)

    corr_df = pd.DataFrame()
    avg_corr = 0.25
    if len(close_cols) >= 2:
        price_mat = pd.DataFrame(close_cols).dropna(how="all").ffill().dropna()
        ret_mat = price_mat.pct_change().dropna()
        if len(ret_mat) >= 20:
            corr_df = ret_mat.corr().round(2)
            vals = corr_df.values
            mask = ~np.eye(vals.shape[0], dtype=bool)
            avg_corr = float(vals[mask].mean()) if mask.any() else 0.25

    if "Equal" in weight_mode:
        raw_w = np.ones(len(chosen), dtype=float)
    elif "ML Score" in weight_mode:
        raw_w = np.array([
            max(0.10, (c["score"] / 100.0) + max(0.0, c["suitability"] * 0.25)) ** 1.5
            for c in chosen
        ])
    else:
        sens_pow = 1.35 if risk_profile == "Safe & Steady" else (0.65 if risk_profile == "High Growth" else 1.0)
        raw_w = np.array([
            max(0.08, (1.0 / max(12.0, c["ann_vol_pct"])) ** sens_pow) * (1.0 + max(0.0, c["score"] - 40.0) / 150.0)
            for c in chosen
        ])
    raw_w = np.nan_to_num(raw_w, nan=1.0, posinf=1.0, neginf=0.1)
    if raw_w.sum() <= 0 or not np.isfinite(raw_w.sum()):
        raw_w = np.ones(len(chosen), dtype=float)
    target_weights = raw_w / raw_w.sum()

    vols = np.nan_to_num(np.array([c["ann_vol_pct"] / 100.0 for c in chosen]), nan=0.25)
    avg_indiv_vol_pct = float(np.sum(target_weights * vols) * 100.0)
    if not corr_df.empty and set(chosen_syms).issubset(corr_df.columns):
        corr_sub = np.nan_to_num(corr_df.loc[chosen_syms, chosen_syms].values, nan=0.25)
        cov_mat = np.outer(vols, vols) * corr_sub
        port_var = float(target_weights @ cov_mat @ target_weights)
        port_vol_pct = float(np.sqrt(max(1e-6, port_var)) * 100.0)
    else:
        port_vol_pct = avg_indiv_vol_pct * float(np.sqrt(max(0.35, 1.0 / len(chosen) + avg_corr * (1.0 - 1.0 / len(chosen)))))
    div_reduction_pct = max(0.0, ((avg_indiv_vol_pct - port_vol_pct) / max(1e-6, avg_indiv_vol_pct)) * 100.0)

    qtys = [0] * len(chosen)
    remaining = budget
    order_by_weight = sorted(range(len(chosen)), key=lambda i: target_weights[i], reverse=True)
    for i in order_by_weight:
        cost1 = float(chosen[i]["share_inr"])
        if not np.isfinite(cost1) or cost1 <= 0:
            continue
        desired_inr = budget * float(target_weights[i])
        q_init = int(desired_inr // cost1) if np.isfinite(desired_inr) else 0
        if q_init == 0 and cost1 <= remaining:
            q_init = 1
        while q_init * cost1 > remaining and q_init > 0:
            q_init -= 1
        qtys[i] = q_init
        remaining -= q_init * cost1

    for _ in range(30):
        progressed = False
        total_now = max(1.0, budget - remaining)
        deficits = sorted(
            range(len(chosen)),
            key=lambda i: float(target_weights[i]) - ((qtys[i] * chosen[i]["share_inr"]) / total_now),
            reverse=True,
        )
        for i in deficits:
            c_px = chosen[i]["share_inr"]
            if c_px <= remaining:
                qtys[i] += 1
                remaining -= c_px
                progressed = True
                break
        if not progressed:
            break

    items = []
    tot_cost = sum(qtys[i] * chosen[i]["share_inr"] for i in range(len(chosen)))
    for i, c in enumerate(chosen):
        if qtys[i] <= 0:
            continue
        cost_i = qtys[i] * c["share_inr"]
        wt_actual = (cost_i / tot_cost * 100.0) if tot_cost > 0 else (float(target_weights[i]) * 100.0)
        reason = (
            f"ML Health {c['score']}/100 ({c['label']}) · Diversifies {c['meta']['sector']} "
            f"with ~{c['ann_vol_pct']:.0f}% annual volatility."
        )
        items.append(
            {
                **c,
                "qty": qtys[i],
                "cost_inr": round(cost_i, 2),
                "target_wt_pct": round(float(target_weights[i]) * 100.0, 1),
                "actual_wt_pct": round(wt_actual, 1),
                "why_picked": reason,
            }
        )

    avg_health = float(np.mean([it["score"] for it in items])) if items else 0.0
    exp_drift = 0.08 if risk_profile == "Safe & Steady" else (0.14 if risk_profile == "High Growth" else 0.11)
    p_vol_dec = port_vol_pct / 100.0
    proj_1y_expected = tot_cost * (1.0 + exp_drift)
    proj_1y_floor = max(0.0, tot_cost * (1.0 + exp_drift - 0.85 * p_vol_dec))
    proj_1y_upside = tot_cost * (1.0 + exp_drift + 1.15 * p_vol_dec)

    return {
        "items": items,
        "risk_profile": risk_profile,
        "market_pref": market_pref,
        "weight_mode": weight_mode,
        "budget_inr": round(budget, 2),
        "total_cost_inr": round(tot_cost, 2),
        "leftover_inr": round(max(0.0, budget - tot_cost), 2),
        "avg_health": round(avg_health, 1),
        "avg_indiv_vol_pct": round(avg_indiv_vol_pct, 1),
        "portfolio_vol_pct": round(port_vol_pct, 1),
        "diversification_reduction_pct": round(div_reduction_pct, 1),
        "avg_corr": round(avg_corr, 2),
        "corr_df": corr_df,
        "proj_1y_floor": round(proj_1y_floor, 0),
        "proj_1y_expected": round(proj_1y_expected, 0),
        "proj_1y_upside": round(proj_1y_upside, 0),
    }


def execute_smart_basket(
    username: str,
    basket_res: dict,
    usdinr_rate: float,
    allow_after_hours: bool = False,
    db_path: str | None = None,
) -> tuple[bool, list[str], float]:
    receipts: list[str] = []
    filled_cnt = 0
    spent_inr = 0.0
    target_db = db_path or DB_PATH
    for it in basket_res.get("items", []):
        ok, msg = execute_trade(
            username,
            it["sym"],
            "BUY",
            int(it["qty"]),
            float(it["price"]),
            "CNC (Delivery)",
            order_type="MARKET",
            usdinr_rate=usdinr_rate,
            allow_after_hours=allow_after_hours,
            db_path=target_db,
        )
        receipts.append(f"- **{it['meta']['name']} (`{it['sym']}` × {it['qty']}):** {msg}")
        if ok:
            filled_cnt += 1
            spent_inr += float(it["cost_inr"])
    return filled_cnt > 0, receipts, round(spent_inr, 2)


def _run_ml_forecast_core(df: pd.DataFrame, horizon: int = 7) -> dict | None:
    if df is None or len(df) < 80:
        return None

    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    ml_frame = build_stationary_ml_frame(df)
    if len(ml_frame) < 60:
        return None

    split_idx = max(40, int(len(ml_frame) * 0.80))
    train_df = ml_frame.iloc[:split_idx]
    test_df = ml_frame.iloc[split_idx:]
    if len(test_df) < 8:
        return None

    X_train = train_df[ML_FEATURE_COLS].values
    y_train = train_df["target_ret_1d"].values
    X_test = test_df[ML_FEATURE_COLS].values
    y_test_ret = test_df["target_ret_1d"].values

    base_test_prices = test_df["Close"].values
    actual_next_prices = base_test_prices * (1.0 + y_test_ret)

    candidates = {
        "Random Forest": RandomForestRegressor(n_estimators=150, max_depth=6, min_samples_leaf=4, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=120, max_depth=3, learning_rate=0.05, random_state=42),
        "Ridge Regression": make_pipeline(StandardScaler(), Ridge(alpha=2.0)),
    }

    eval_rows = []
    model_preds = {}
    residuals_map = {}

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        pred_ret = np.clip(model.predict(X_test), -0.08, 0.08)
        pred_prices = base_test_prices * (1.0 + pred_ret)

        rmse = float(np.sqrt(mean_squared_error(actual_next_prices, pred_prices)))
        mae = float(mean_absolute_error(actual_next_prices, pred_prices))
        mape = float(np.mean(np.abs((actual_next_prices - pred_prices) / np.maximum(actual_next_prices, 1e-6))) * 100.0)
        r2 = float(r2_score(actual_next_prices, pred_prices))
        dir_acc = float(np.mean(np.sign(pred_ret) == np.sign(y_test_ret)) * 100.0)

        eval_rows.append(
            {
                "Model": name,
                "RMSE": round(rmse, 3),
                "MAE": round(mae, 3),
                "MAPE (%)": round(mape, 2),
                "R² Score": round(r2, 4),
                "Directional Accuracy (%)": round(dir_acc, 1),
            }
        )
        model_preds[name] = pred_prices
        residuals_map[name] = float(np.std(y_test_ret - pred_ret))

    eval_df = pd.DataFrame(eval_rows).sort_values("RMSE", ascending=True).reset_index(drop=True)
    best_model_name = str(eval_df.iloc[0]["Model"])
    best_model = candidates[best_model_name]

    X_all = ml_frame[ML_FEATURE_COLS].values
    y_all = ml_frame["target_ret_1d"].values
    best_model.fit(X_all, y_all)

    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
    else:
        coef = best_model.named_steps["ridge"].coef_
        importances = np.abs(coef) / max(np.sum(np.abs(coef)), 1e-9)

    feat_imp_df = pd.DataFrame(
        {"Feature": ML_FEATURE_COLS, "Importance": [round(float(x) * 100, 2) for x in importances]}
    ).sort_values("Importance", ascending=False)

    rolling_closes = list(df["Close"].dropna().astype(float).tail(60).values)
    last_ema50 = float(df["EMA_50"].dropna().iloc[-1]) if not df["EMA_50"].dropna().empty else rolling_closes[-1]
    last_macd_norm = float(ml_frame["macd_hist_norm"].iloc[-1])
    last_vol_ratio = float(ml_frame["vol_ratio"].iloc[-1])
    step_sigma = max(residuals_map[best_model_name], float(ml_frame["vol_14d"].iloc[-1]), 0.006)

    curr_d = df.index[-1]
    f_dates, f_prices, f_upper, f_lower = [], [], [], []
    last_actual = rolling_closes[-1]

    for step_i in range(1, horizon + 1):
        curr_d = curr_d + timedelta(days=1)
        while curr_d.weekday() >= 5:
            curr_d = curr_d + timedelta(days=1)

        s_close = pd.Series(rolling_closes)
        p_now = float(s_close.iloc[-1])
        ret_1d = (p_now / float(s_close.iloc[-2])) - 1.0
        ret_3d = (p_now / float(s_close.iloc[-4])) - 1.0
        ret_5d = (p_now / float(s_close.iloc[-6])) - 1.0
        ret_10d = (p_now / float(s_close.iloc[-11])) - 1.0

        sma20_cur = float(s_close.tail(20).mean())
        bb_std_cur = float(s_close.tail(20).std())
        bb_up = sma20_cur + 2.0 * bb_std_cur
        bb_lo = sma20_cur - 2.0 * bb_std_cur
        bb_pctb_cur = (p_now - bb_lo) / max(bb_up - bb_lo, 1e-6)

        last_ema50 = (p_now * (2.0 / 51.0)) + (last_ema50 * (1.0 - 2.0 / 51.0))
        rsi_cur = float(compute_wilder_rsi(s_close, 14).iloc[-1])
        vol_14_cur = float(s_close.pct_change().tail(14).std())

        x_vec = np.nan_to_num(np.array([[
            ret_1d, ret_3d, ret_5d, ret_10d,
            (p_now / sma20_cur) - 1.0, (p_now / last_ema50) - 1.0,
            (rsi_cur - 50.0) / 50.0, last_macd_norm * (0.9 ** step_i),
            float(np.clip(bb_pctb_cur, 0.0, 1.0)), vol_14_cur, last_vol_ratio,
        ]]), nan=0.0, posinf=0.0, neginf=0.0)

        pred_r = float(np.clip(best_model.predict(x_vec)[0], -0.04, 0.04))
        next_p = p_now * (1.0 + pred_r)
        band = next_p * step_sigma * np.sqrt(step_i)

        f_dates.append(curr_d)
        f_prices.append(next_p)
        f_upper.append(next_p + band)
        f_lower.append(max(0.01, next_p - band))
        rolling_closes.append(next_p)

    test_dates = test_df.index + pd.Timedelta(days=1)
    return {
        "best_model": best_model_name,
        "eval_df": eval_df,
        "feature_importance": feat_imp_df,
        "test_dates": test_dates,
        "test_actual": actual_next_prices,
        "test_pred": model_preds[best_model_name],
        "forecast_dates": f_dates,
        "forecast_prices": f_prices,
        "forecast_upper": f_upper,
        "forecast_lower": f_lower,
        "last_close": last_actual,
        "target_7d": f_prices[-1],
    }


@st.cache_data(ttl="15m", max_entries=16, show_spinner=False)
def run_ml_forecast_suite(symbol: str, last_bar_iso: str, bar_count: int, _df: pd.DataFrame) -> dict | None:
    return _run_ml_forecast_core(_df, horizon=7)


BACKTEST_STRATEGIES = [
    "SMA 20/50 Golden Crossover (Trend Follow)",
    "RSI < 35 Oversold Reversal (Mean Reversion)",
    "Bollinger Band Mean Reversion (Lower Band)",
    "MACD Bullish Crossover (Momentum)",
]


@st.cache_data(ttl="15m", max_entries=24, show_spinner=False)
def run_backtest_cached(
    symbol: str,
    last_bar_iso: str,
    _df: pd.DataFrame,
    strategy_name: str,
    initial_capital: float,
    stop_loss_pct: float,
    target_pct: float,
    currency: str,
) -> dict:
    return run_backtest(_df, strategy_name, initial_capital, stop_loss_pct, target_pct, currency)


def run_backtest(
    df: pd.DataFrame,
    strategy_name: str,
    initial_capital: float = 100000.0,
    stop_loss_pct: float = 3.0,
    target_pct: float = 6.0,
    currency: str = "₹",
) -> dict:
    bt_df = df.dropna(subset=["Close", "SMA_20", "EMA_50", "RSI", "BB_Lower", "MACD", "MACD_Signal"]).copy()
    if len(bt_df) < 10:
        return {"empty": True}

    capital = float(initial_capital)
    shares_held = 0.0
    in_position = False
    entry_price = 0.0
    entry_date = None

    strategy_equity = [capital]
    trades_log = []
    signal_points = []

    first_close = float(bt_df["Close"].iloc[0])
    bh_shares = initial_capital / first_close if first_close > 0 else 0.0
    bh_equity = [initial_capital]

    for i in range(1, len(bt_df)):
        row = bt_df.iloc[i]
        prev = bt_df.iloc[i - 1]
        dt = bt_df.index[i]
        date_str = dt.strftime("%d %b %Y")

        close_p = float(row["Close"])
        high_p = float(row["High"])
        low_p = float(row["Low"])
        bh_equity.append(bh_shares * close_p)

        if not in_position:
            if "SMA" in strategy_name:
                enter = float(prev["SMA_20"]) <= float(prev["EMA_50"]) and float(row["SMA_20"]) > float(row["EMA_50"])
            elif "RSI" in strategy_name:
                enter = float(prev["RSI"]) < 35.0 and float(row["RSI"]) >= float(prev["RSI"])
            elif "Bollinger" in strategy_name:
                enter = float(row["Close"]) <= float(row["BB_Lower"])
            else:
                enter = float(prev["MACD"]) <= float(prev["MACD_Signal"]) and float(row["MACD"]) > float(row["MACD_Signal"])

            if enter and close_p > 0:
                in_position = True
                entry_price = close_p
                entry_date = date_str
                shares_held = capital / entry_price
                signal_points.append({"date": dt, "price": entry_price, "type": "BUY"})
            strategy_equity.append(capital)
        else:
            sl_price = entry_price * (1.0 - stop_loss_pct / 100.0)
            tp_price = entry_price * (1.0 + target_pct / 100.0)
            exit_reason = None
            exit_price = close_p

            if low_p <= sl_price:
                exit_price = sl_price
                exit_reason = "Stop-Loss"
            elif high_p >= tp_price:
                exit_price = tp_price
                exit_reason = "Target Hit"
            elif i == len(bt_df) - 1:
                exit_price = close_p
                exit_reason = "End of Period"

            if exit_reason:
                exit_val = shares_held * exit_price
                pnl_amt = exit_val - capital
                ret_pct = ((exit_price - entry_price) / entry_price) * 100.0
                capital = exit_val
                in_position = False
                shares_held = 0.0

                trades_log.append(
                    {
                        "Entry Date": entry_date,
                        "Exit Date": date_str,
                        "Exit Reason": exit_reason,
                        f"Entry ({currency})": round(entry_price, 2),
                        f"Exit ({currency})": round(exit_price, 2),
                        "Return (%)": round(ret_pct, 2),
                        f"Net P&L ({currency})": round(pnl_amt, 2),
                        "Outcome": "WIN" if ret_pct > 0 else "LOSS",
                    }
                )
                signal_points.append({"date": dt, "price": exit_price, "type": "SELL"})
                strategy_equity.append(capital)
            else:
                strategy_equity.append(shares_held * close_p)

    eq_series = pd.Series(strategy_equity, index=bt_df.index)
    bh_series = pd.Series(bh_equity, index=bt_df.index)

    daily_rets = eq_series.pct_change().dropna()
    sharpe = (
        float((daily_rets.mean() / daily_rets.std()) * np.sqrt(252))
        if len(daily_rets) > 2 and float(daily_rets.std()) > 0
        else 0.0
    )

    rolling_peak = eq_series.cummax()
    drawdown = ((eq_series - rolling_peak) / rolling_peak) * 100.0
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    final_cap = float(eq_series.iloc[-1])
    total_ret = ((final_cap - initial_capital) / initial_capital) * 100.0
    bh_ret = ((float(bh_series.iloc[-1]) - initial_capital) / initial_capital) * 100.0
    alpha = total_ret - bh_ret

    wins = [t for t in trades_log if t["Outcome"] == "WIN"]
    losses = [t for t in trades_log if t["Outcome"] == "LOSS"]
    win_rate = (len(wins) / len(trades_log) * 100.0) if trades_log else 0.0

    gross_win = sum(t[f"Net P&L ({currency})"] for t in wins)
    gross_loss = abs(sum(t[f"Net P&L ({currency})"] for t in losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (99.9 if gross_win > 0 else 0.0)

    return {
        "empty": False,
        "bt_df": bt_df,
        "eq_series": eq_series,
        "bh_series": bh_series,
        "trades_log": trades_log,
        "signal_points": signal_points,
        "final_capital": final_cap,
        "total_ret": total_ret,
        "bh_ret": bh_ret,
        "alpha": alpha,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "wins_count": len(wins),
        "profit_factor": profit_factor,
    }


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financesight_pro.db")


@contextmanager
def db_conn(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000).hex()
    return f"pbkdf2$100000${salt}${dk}"


def _verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    if stored_hash.startswith("pbkdf2$"):
        parts = stored_hash.split("$")
        if len(parts) != 4:
            return False, False
        _, iters_s, salt_hex, expected_hex = parts
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters_s)
        ).hex()
        return hmac.compare_digest(dk, expected_hex), False

    legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_hash), True


def _ensure_column(c: sqlite3.Cursor, table: str, col: str, col_def: str) -> None:
    existing = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
    if col not in existing:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")


def init_db(db_path: str = DB_PATH) -> None:
    with db_conn(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                full_name TEXT,
                email TEXT,
                password_hash TEXT,
                balance REAL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS portfolio (
                username TEXT,
                ticker TEXT,
                shares INTEGER,
                avg_price REAL,
                cost_inr REAL,
                currency TEXT DEFAULT '₹',
                PRIMARY KEY (username, ticker)
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS positions (
                username TEXT,
                ticker TEXT,
                product_type TEXT,
                shares INTEGER,
                avg_price REAL,
                cost_inr REAL,
                currency TEXT DEFAULT '₹',
                fx_rate REAL DEFAULT 1.0,
                PRIMARY KEY (username, ticker, product_type)
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                timestamp TEXT,
                ticker TEXT,
                action TEXT,
                shares INTEGER,
                price REAL,
                total REAL,
                currency TEXT DEFAULT '₹',
                fx_rate REAL DEFAULT 1.0,
                order_type TEXT DEFAULT 'MARKET',
                inr_total REAL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS pending_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                created_at TEXT,
                ticker TEXT,
                action TEXT,
                product_type TEXT,
                shares INTEGER,
                limit_price REAL,
                fx_rate REAL,
                reserved_margin_inr REAL,
                status TEXT DEFAULT 'PENDING'
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS funding_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                timestamp TEXT,
                type TEXT,
                method TEXT,
                reference TEXT,
                amount REAL,
                status TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT,
                timestamp TEXT,
                category TEXT,
                subject TEXT,
                email TEXT,
                status TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS watchlist (
                username TEXT,
                ticker TEXT,
                added_at TEXT,
                PRIMARY KEY (username, ticker)
            )"""
        )

        _ensure_column(c, "portfolio", "cost_inr", "REAL")
        _ensure_column(c, "portfolio", "currency", "TEXT DEFAULT '₹'")
        c.execute("UPDATE portfolio SET cost_inr = shares * avg_price WHERE cost_inr IS NULL")

        _ensure_column(c, "positions", "cost_inr", "REAL")
        _ensure_column(c, "positions", "currency", "TEXT DEFAULT '₹'")
        _ensure_column(c, "positions", "fx_rate", "REAL DEFAULT 1.0")
        c.execute("UPDATE positions SET cost_inr = shares * avg_price WHERE cost_inr IS NULL")

        _ensure_column(c, "transactions", "currency", "TEXT DEFAULT '₹'")
        _ensure_column(c, "transactions", "fx_rate", "REAL DEFAULT 1.0")
        _ensure_column(c, "transactions", "order_type", "TEXT DEFAULT 'MARKET'")
        _ensure_column(c, "transactions", "inr_total", "REAL")
        c.execute("UPDATE transactions SET inr_total = total WHERE inr_total IS NULL")

        c.execute("SELECT COUNT(*) FROM users WHERE LOWER(username) = LOWER('Trader_XYZ')")
        if c.fetchone()[0] == 0:
            demo_pw = _hash_password("demo123")
            c.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                ("Trader_XYZ", "Trader_XYZ", "trader@financesight.in", demo_pw, 100000.0),
            )
            c.execute(
                """INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
                   VALUES (?, ?, 'DEPOSIT', 'Initial Margin Credit', 'BONUS-100K', 100000.0, 'COMPLETED')""",
                ("Trader_XYZ", get_ist_now().strftime("%Y-%m-%d %H:%M")),
            )


@st.cache_resource
def ensure_db_initialized() -> bool:
    init_db(DB_PATH)
    return True


def register_new_user(
    full_name: str, username: str, email: str, password: str, db_path: str = DB_PATH
) -> tuple[bool, str]:
    clean_user = username.strip()
    clean_name = full_name.strip()
    clean_email = email.strip()
    clean_pass = password.strip()

    if not clean_user or not clean_pass or not clean_name:
        return False, "Please fill in Full Name, User ID, and Password."
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", clean_user):
        return False, "User ID must be 3–30 characters using letters, numbers, '_', '.', or '-'."
    if len(clean_pass) < 6:
        return False, "Password must be at least 6 characters long."
    if clean_email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", clean_email):
        return False, "Please enter a valid email address."

    with db_conn(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE LOWER(username) = LOWER(?)", (clean_user,))
        if c.fetchone():
            return False, f"User ID '{clean_user}' is already registered. Please sign in or pick another ID."

        pw_hash = _hash_password(clean_pass)
        c.execute(
            "INSERT INTO users (username, full_name, email, password_hash, balance) VALUES (?, ?, ?, ?, ?)",
            (clean_user, clean_name, clean_email, pw_hash, 100000.0),
        )
        c.execute(
            """INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
               VALUES (?, ?, 'DEPOSIT', 'Signup Margin Credit', 'INIT-100K', 100000.0, 'COMPLETED')""",
            (clean_user, get_ist_now().strftime("%Y-%m-%d %H:%M")),
        )
    return True, clean_user


def authenticate_user(
    username: str, password: str, db_path: str = DB_PATH
) -> tuple[bool, str | None, str | None]:
    clean_user = username.strip()
    clean_pass = password.strip()
    if not clean_user or not clean_pass:
        return False, None, None

    with db_conn(db_path) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT username, full_name, password_hash FROM users WHERE LOWER(username) = LOWER(?)",
            (clean_user,),
        )
        row = c.fetchone()
        if not row:
            return False, None, None

        db_user, db_name, stored_hash = row
        valid, needs_upgrade = _verify_password(clean_pass, stored_hash)
        if not valid:
            return False, None, None

        if needs_upgrade:
            c.execute(
                "UPDATE users SET password_hash = ? WHERE LOWER(username) = LOWER(?)",
                (_hash_password(clean_pass), db_user),
            )
        return True, db_user, db_name


def get_user_balance(username: str, db_path: str = DB_PATH) -> float:
    with db_conn(db_path) as conn:
        row = conn.execute(
            "SELECT balance FROM users WHERE LOWER(username) = LOWER(?)", (username,)
        ).fetchone()
        return float(row[0]) if row else 0.0


def update_funds(
    username: str,
    amount: float,
    tx_type: str,
    method: str,
    reference: str,
    db_path: str = DB_PATH,
) -> tuple[bool, str]:
    if amount <= 0 or amount > 1e8:
        return False, "Amount must be between ₹1 and ₹10,00,00,000."
    if tx_type not in {"DEPOSIT", "WITHDRAW"}:
        return False, "Invalid transaction type."

    with db_conn(db_path) as conn:
        c = conn.cursor()
        row = c.execute(
            "SELECT username, balance FROM users WHERE LOWER(username) = LOWER(?)", (username,)
        ).fetchone()
        if not row:
            return False, "User account not found."
        canon_user, bal = row[0], float(row[1])
        if tx_type == "WITHDRAW" and amount > bal:
            return False, "Withdrawal amount exceeds available cash margin."
        new_bal = bal + amount if tx_type == "DEPOSIT" else bal - amount
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, canon_user))
        now = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            """INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
               VALUES (?, ?, ?, ?, ?, ?, 'COMPLETED')""",
            (canon_user, now, tx_type, method, reference, amount),
        )
    verb = "deposited to" if tx_type == "DEPOSIT" else "withdrawn from"
    return True, f"₹{amount:,.2f} {verb} your trading wallet."


def reset_user_wallet(username: str, db_path: str = DB_PATH) -> tuple[bool, str]:
    with db_conn(db_path) as conn:
        c = conn.cursor()
        row = c.execute(
            "SELECT username FROM users WHERE LOWER(username) = LOWER(?)", (username,)
        ).fetchone()
        if not row:
            return False, "User not found."
        canon_user = row[0]
        c.execute("DELETE FROM portfolio WHERE LOWER(username) = LOWER(?)", (canon_user,))
        c.execute("DELETE FROM positions WHERE LOWER(username) = LOWER(?)", (canon_user,))
        c.execute("DELETE FROM pending_orders WHERE LOWER(username) = LOWER(?)", (canon_user,))
        c.execute("DELETE FROM transactions WHERE LOWER(username) = LOWER(?)", (canon_user,))
        c.execute("UPDATE users SET balance = 100000.0 WHERE username = ?", (canon_user,))
        c.execute(
            """INSERT INTO funding_history (username, timestamp, type, method, reference, amount, status)
               VALUES (?, ?, 'DEPOSIT', 'Wallet Reset', 'RESET-100K', 100000.0, 'COMPLETED')""",
            (canon_user, get_ist_now().strftime("%Y-%m-%d %H:%M:%S")),
        )
    return True, "Paper trading account reset to ₹1,00,000.00 cleanly."


def _get_locked_sell_shares(
    c: sqlite3.Cursor, username: str, ticker: str, p_tag: str, exclude_order_id: int | None = None
) -> int:
    prod_filter = "%MIS%" if p_tag == "MIS" else "%CNC%"
    if exclude_order_id is not None:
        row = c.execute(
            """SELECT COALESCE(SUM(shares), 0) FROM pending_orders
               WHERE LOWER(username) = LOWER(?) AND ticker = ? AND action = 'SELL'
                 AND product_type LIKE ? AND status = 'PENDING' AND id != ?""",
            (username, ticker, prod_filter, exclude_order_id),
        ).fetchone()
    else:
        row = c.execute(
            """SELECT COALESCE(SUM(shares), 0) FROM pending_orders
               WHERE LOWER(username) = LOWER(?) AND ticker = ? AND action = 'SELL'
                 AND product_type LIKE ? AND status = 'PENDING'""",
            (username, ticker, prod_filter),
        ).fetchone()
    return int(row[0]) if row and row[0] else 0


def _apply_filled_trade(
    c: sqlite3.Cursor,
    canon_user: str,
    ticker: str,
    action: str,
    shares: int,
    native_price: float,
    product_type: str,
    fx_rate: float,
    order_type: str,
    now_str: str,
    exclude_order_id: int | None = None,
) -> tuple[bool, str]:
    meta = get_ticker_meta(ticker)
    currency = meta["currency"]
    is_mis = "MIS" in product_type
    p_tag = "MIS" if is_mis else "CNC"

    native_total = shares * native_price
    inr_total = native_total * fx_rate
    required_margin_inr = inr_total * (0.20 if is_mis else 1.0)

    bal = float(c.execute("SELECT balance FROM users WHERE username = ?", (canon_user,)).fetchone()[0])

    if action == "BUY":
        if required_margin_inr > bal + 1e-6:
            return False, (
                f"Insufficient margin! Required: ₹{required_margin_inr:,.2f} "
                f"(Available: ₹{bal:,.2f}). Visit Funds or ask AI to add funds."
            )
        new_bal = max(0.0, bal - required_margin_inr)
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, canon_user))

        if not is_mis:
            prow = c.execute(
                "SELECT shares, avg_price, cost_inr FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                (canon_user, ticker),
            ).fetchone()
            if prow:
                old_s, old_avg, old_cost_inr = int(prow[0]), float(prow[1]), float(prow[2] or (prow[0] * prow[1]))
                new_s = old_s + shares
                new_avg = ((old_s * old_avg) + native_total) / new_s
                new_cost_inr = old_cost_inr + inr_total
                c.execute(
                    "UPDATE portfolio SET shares = ?, avg_price = ?, cost_inr = ?, currency = ? WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                    (new_s, new_avg, new_cost_inr, currency, canon_user, ticker),
                )
            else:
                c.execute(
                    "INSERT INTO portfolio (username, ticker, shares, avg_price, cost_inr, currency) VALUES (?, ?, ?, ?, ?, ?)",
                    (canon_user, ticker, shares, native_price, inr_total, currency),
                )

        pos_row = c.execute(
            "SELECT shares, avg_price, cost_inr FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = ?",
            (canon_user, ticker, p_tag),
        ).fetchone()
        if pos_row:
            ps, pa, pcost = int(pos_row[0]), float(pos_row[1]), float(pos_row[2] or (pos_row[0] * pos_row[1]))
            ns = ps + shares
            na = ((ps * pa) + native_total) / ns
            ncost = pcost + inr_total
            c.execute(
                "UPDATE positions SET shares = ?, avg_price = ?, cost_inr = ?, currency = ?, fx_rate = ? WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = ?",
                (ns, na, ncost, currency, fx_rate, canon_user, ticker, p_tag),
            )
        else:
            c.execute(
                "INSERT INTO positions (username, ticker, product_type, shares, avg_price, cost_inr, currency, fx_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (canon_user, ticker, p_tag, shares, native_price, inr_total, currency, fx_rate),
            )

        c.execute(
            """INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total, currency, fx_rate, order_type, inr_total)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (canon_user, now_str, ticker, f"BUY ({p_tag})", shares, native_price, native_total, currency, fx_rate, order_type, inr_total),
        )
        fx_note = f" (₹{required_margin_inr:,.2f} @ ₹{fx_rate:.2f}/$)" if currency == "$" else f" (Margin: ₹{required_margin_inr:,.2f})"
        return True, f"Executed BUY ({p_tag}): {shares} {ticker} @ {currency}{native_price:,.2f}{fx_note}"

    locked_sell = _get_locked_sell_shares(c, canon_user, ticker, p_tag, exclude_order_id=exclude_order_id)
    if is_mis:
        row = c.execute(
            "SELECT shares, avg_price, cost_inr FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'MIS'",
            (canon_user, ticker),
        ).fetchone()
        held_s = int(row[0]) if row else 0
        if held_s - locked_sell < shares:
            return False, f"Insufficient available MIS shares of {ticker} to sell (Available: {max(0, held_s - locked_sell)})."
        avg_p = float(row[1])
        row_cost_inr = float(row[2] or (held_s * avg_p))
        sold_cost_inr = row_cost_inr * (shares / held_s)
        margin_released_inr = sold_cost_inr * 0.20
        pnl_inr = inr_total - sold_cost_inr
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (max(0.0, bal + margin_released_inr + pnl_inr), canon_user))
        rem = held_s - shares
        if rem == 0:
            c.execute("DELETE FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'MIS'", (canon_user, ticker))
        else:
            c.execute(
                "UPDATE positions SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'MIS'",
                (rem, row_cost_inr - sold_cost_inr, canon_user, ticker),
            )
    else:
        row = c.execute(
            "SELECT shares, avg_price, cost_inr FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?",
            (canon_user, ticker),
        ).fetchone()
        held_s = int(row[0]) if row else 0
        if held_s - locked_sell < shares:
            return False, f"Insufficient available CNC holdings of {ticker} to sell (Available: {max(0, held_s - locked_sell)})."
        avg_p = float(row[1])
        row_cost_inr = float(row[2] or (held_s * avg_p))
        sold_cost_inr = row_cost_inr * (shares / held_s)
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (bal + inr_total, canon_user))
        rem = held_s - shares
        if rem == 0:
            c.execute("DELETE FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?", (canon_user, ticker))
            c.execute("DELETE FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'CNC'", (canon_user, ticker))
        else:
            c.execute(
                "UPDATE portfolio SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                (rem, row_cost_inr - sold_cost_inr, canon_user, ticker),
            )
            c.execute(
                "UPDATE positions SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'CNC'",
                (rem, row_cost_inr - sold_cost_inr, canon_user, ticker),
            )

    c.execute(
        """INSERT INTO transactions (username, timestamp, ticker, action, shares, price, total, currency, fx_rate, order_type, inr_total)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (canon_user, now_str, ticker, f"SELL ({p_tag})", shares, native_price, native_total, currency, fx_rate, order_type, inr_total),
    )
    return True, f"Executed SELL ({p_tag}): {shares} {ticker} @ {currency}{native_price:,.2f} (Credited: ₹{inr_total:,.2f})"


def execute_trade(
    username: str,
    ticker: str,
    action: str,
    shares: int,
    market_price: float,
    product_type: str = "CNC (Delivery)",
    order_type: str = "MARKET",
    limit_price: float | None = None,
    usdinr_rate: float = DEFAULT_USDINR_RATE,
    allow_after_hours: bool = False,
    db_path: str = DB_PATH,
) -> tuple[bool, str]:
    ticker = LEGACY_TICKER_REMAP.get(ticker, ticker)
    if ticker not in STOCK_CATALOG:
        return False, f"Unknown stock ticker '{ticker}'."
    if action not in {"BUY", "SELL"}:
        return False, "Action must be BUY or SELL."
    try:
        shares = int(shares)
    except (TypeError, ValueError):
        return False, "Quantity must be a positive integer."
    if shares <= 0 or shares > 100_000:
        return False, "Order quantity must be between 1 and 100,000 shares."
    if market_price <= 0:
        return False, "Invalid live market price."

    is_open, hours_reason = check_market_trading_hours(ticker)
    if not is_open and not allow_after_hours:
        return False, f"Market Closed! Enable 'Allow Demo Orders Outside Market Hours' or trade during market hours. ({hours_reason})"

    fx_rate = get_fx_rate_for_ticker(ticker, usdinr_rate)
    now_str = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
    is_mis = "MIS" in product_type
    p_tag = "MIS" if is_mis else "CNC"
    meta = get_ticker_meta(ticker)

    with db_conn(db_path) as conn:
        c = conn.cursor()
        urow = c.execute(
            "SELECT username, balance FROM users WHERE LOWER(username) = LOWER(?)", (username,)
        ).fetchone()
        if not urow:
            return False, "Account not found."
        canon_user, bal = urow[0], float(urow[1])

        if order_type == "LIMIT":
            if limit_price is None or limit_price <= 0:
                return False, "Limit price must be greater than zero."
            limit_price = float(limit_price)

            is_marketable = (action == "BUY" and limit_price >= market_price) or (
                action == "SELL" and limit_price <= market_price
            )
            if is_marketable:
                return _apply_filled_trade(
                    c, canon_user, ticker, action, shares, market_price, product_type, fx_rate, "LIMIT (Filled)", now_str
                )

            if action == "BUY":
                reserved_inr = shares * limit_price * fx_rate * (0.20 if is_mis else 1.0)
                if reserved_inr > bal:
                    return False, f"Insufficient margin for Limit Order! Required: ₹{reserved_inr:,.2f} (Available: ₹{bal:,.2f})."
                c.execute("UPDATE users SET balance = ? WHERE username = ?", (bal - reserved_inr, canon_user))
            else:
                reserved_inr = 0.0
                locked_sell = _get_locked_sell_shares(c, canon_user, ticker, p_tag)
                if is_mis:
                    prow = c.execute(
                        "SELECT shares FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'MIS'",
                        (canon_user, ticker),
                    ).fetchone()
                else:
                    prow = c.execute(
                        "SELECT shares FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                        (canon_user, ticker),
                    ).fetchone()
                held_s = int(prow[0]) if prow else 0
                if held_s - locked_sell < shares:
                    return False, f"Insufficient available {p_tag} shares of {ticker} for Limit Sell (Available: {max(0, held_s - locked_sell)})."

            c.execute(
                """INSERT INTO pending_orders (username, created_at, ticker, action, product_type, shares, limit_price, fx_rate, reserved_margin_inr, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')""",
                (canon_user, now_str, ticker, action, product_type, shares, limit_price, fx_rate, reserved_inr),
            )
            return (
                True,
                f"Placed PENDING {action} LIMIT order: {shares} {ticker} @ {meta['currency']}{limit_price:,.2f} "
                f"(Live: {meta['currency']}{market_price:,.2f}). Reserved ₹{reserved_inr:,.2f}.",
            )

        return _apply_filled_trade(
            c, canon_user, ticker, action, shares, market_price, product_type, fx_rate, "MARKET", now_str
        )


def sync_pending_orders(
    username: str,
    snapshots: dict,
    usdinr_rate: float = DEFAULT_USDINR_RATE,
    allow_after_hours: bool = False,
    db_path: str = DB_PATH,
) -> list[str]:
    filled_msgs = []
    now_str = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
    with db_conn(db_path) as conn:
        c = conn.cursor()
        rows = c.execute(
            """SELECT id, username, ticker, action, product_type, shares, limit_price, reserved_margin_inr
               FROM pending_orders WHERE LOWER(username) = LOWER(?) AND status = 'PENDING' ORDER BY id ASC""",
            (username,),
        ).fetchall()
        if not rows:
            return filled_msgs

        for oid, canon_user, ticker, action, prod_type, shares, lim_p, reserved_inr in rows:
            live_p = float(snapshots.get(ticker, {}).get("price", 0.0))
            if live_p <= 0:
                continue
            is_open, _ = check_market_trading_hours(ticker)
            if not is_open and not allow_after_hours:
                continue
            triggered = (action == "BUY" and live_p <= float(lim_p)) or (
                action == "SELL" and live_p >= float(lim_p)
            )
            if not triggered:
                continue

            if action == "BUY" and reserved_inr > 0:
                bal = float(c.execute("SELECT balance FROM users WHERE username = ?", (canon_user,)).fetchone()[0])
                c.execute("UPDATE users SET balance = ? WHERE username = ?", (bal + float(reserved_inr), canon_user))

            fx_rate = get_fx_rate_for_ticker(ticker, usdinr_rate)
            ok, msg = _apply_filled_trade(
                c, canon_user, ticker, action, int(shares), live_p, prod_type, fx_rate,
                "LIMIT (Triggered)", now_str, exclude_order_id=oid,
            )
            if ok:
                c.execute("UPDATE pending_orders SET status = 'FILLED' WHERE id = ?", (oid,))
                filled_msgs.append(f"Order #{oid}: {msg}")
            elif action == "BUY" and reserved_inr > 0:
                bal = float(c.execute("SELECT balance FROM users WHERE username = ?", (canon_user,)).fetchone()[0])
                c.execute("UPDATE users SET balance = ? WHERE username = ?", (max(0.0, bal - float(reserved_inr)), canon_user))
    return filled_msgs


def cancel_pending_order(username: str, order_id: int, db_path: str = DB_PATH) -> tuple[bool, str]:
    with db_conn(db_path) as conn:
        c = conn.cursor()
        row = c.execute(
            """SELECT id, username, ticker, action, shares, limit_price, reserved_margin_inr
               FROM pending_orders WHERE id = ? AND LOWER(username) = LOWER(?) AND status = 'PENDING'""",
            (order_id, username),
        ).fetchone()
        if not row:
            return False, f"Pending order #{order_id} was not found."
        oid, canon_user, ticker, action, shares, lim_p, reserved_inr = row
        if action == "BUY" and reserved_inr > 0:
            bal = float(c.execute("SELECT balance FROM users WHERE username = ?", (canon_user,)).fetchone()[0])
            c.execute("UPDATE users SET balance = ? WHERE username = ?", (bal + float(reserved_inr), canon_user))
        c.execute("UPDATE pending_orders SET status = 'CANCELLED' WHERE id = ?", (oid,))
        return True, f"Cancelled pending {action} limit order #{oid} ({shares} {ticker} @ {lim_p:,.2f}) and released ₹{float(reserved_inr):,.2f}."


def reverse_last_executed_order(
    username: str, target_ticker: str | None = None, db_path: str = DB_PATH
) -> tuple[bool, str]:
    with db_conn(db_path) as conn:
        c = conn.cursor()
        if target_ticker:
            row = c.execute(
                """SELECT id, username, ticker, action, shares, price, total, inr_total
                   FROM transactions WHERE LOWER(username) = LOWER(?) AND ticker = ? ORDER BY id DESC LIMIT 1""",
                (username, target_ticker),
            ).fetchone()
        else:
            row = c.execute(
                """SELECT id, username, ticker, action, shares, price, total, inr_total
                   FROM transactions WHERE LOWER(username) = LOWER(?) ORDER BY id DESC LIMIT 1""",
                (username,),
            ).fetchone()
        if not row:
            return False, "No executed order was found to reverse."

        tx_id, canon_user, ticker, action, shares, price, total, inr_total = row
        shares = int(shares)
        inr_val = float(inr_total if inr_total is not None else total)
        is_mis = "MIS" in action
        p_tag = "MIS" if is_mis else "CNC"
        bal = float(c.execute("SELECT balance FROM users WHERE username = ?", (canon_user,)).fetchone()[0])
        currency = get_ticker_meta(ticker)["currency"]

        if "BUY" in action:
            refund_inr = inr_val * (0.20 if is_mis else 1.0)
            pos_row = c.execute(
                "SELECT shares, cost_inr FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = ?",
                (canon_user, ticker, p_tag),
            ).fetchone()
            if not pos_row or int(pos_row[0]) < shares:
                return False, f"Cannot reverse BUY #{tx_id}: shares of {ticker} were already sold."

            rem_pos = int(pos_row[0]) - shares
            if rem_pos <= 0:
                c.execute(
                    "DELETE FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = ?",
                    (canon_user, ticker, p_tag),
                )
            else:
                new_cost = max(0.0, float(pos_row[1] or 0.0) - inr_val)
                c.execute(
                    "UPDATE positions SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = ?",
                    (rem_pos, new_cost, canon_user, ticker, p_tag),
                )

            if not is_mis:
                prow = c.execute(
                    "SELECT shares, cost_inr FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                    (canon_user, ticker),
                ).fetchone()
                if prow:
                    rem_p = int(prow[0]) - shares
                    if rem_p <= 0:
                        c.execute("DELETE FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?", (canon_user, ticker))
                    else:
                        c.execute(
                            "UPDATE portfolio SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                            (rem_p, max(0.0, float(prow[1] or 0.0) - inr_val), canon_user, ticker),
                        )

            c.execute("UPDATE users SET balance = ? WHERE username = ?", (bal + refund_inr, canon_user))
            c.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            return True, f"Reversed Order #{tx_id} ({action} {shares} {ticker} @ {currency}{price:,.2f}) and refunded ₹{refund_inr:,.2f}."

        if is_mis:
            return False, "MIS sell reversals are blocked after P&L settlement; place a fresh trade instead."
        if bal < inr_val:
            return False, f"Insufficient wallet cash (₹{bal:,.2f}) to reverse SELL #{tx_id} (₹{inr_val:,.2f})."
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (bal - inr_val, canon_user))

        prow = c.execute(
            "SELECT shares, avg_price, cost_inr FROM portfolio WHERE LOWER(username) = LOWER(?) AND ticker = ?",
            (canon_user, ticker),
        ).fetchone()
        if prow:
            c.execute(
                "UPDATE portfolio SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ?",
                (int(prow[0]) + shares, float(prow[2] or 0.0) + inr_val, canon_user, ticker),
            )
        else:
            c.execute(
                "INSERT INTO portfolio (username, ticker, shares, avg_price, cost_inr, currency) VALUES (?, ?, ?, ?, ?, ?)",
                (canon_user, ticker, shares, price, inr_val, currency),
            )

        pos_row = c.execute(
            "SELECT shares, cost_inr FROM positions WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'CNC'",
            (canon_user, ticker),
        ).fetchone()
        if pos_row:
            c.execute(
                "UPDATE positions SET shares = ?, cost_inr = ? WHERE LOWER(username) = LOWER(?) AND ticker = ? AND product_type = 'CNC'",
                (int(pos_row[0]) + shares, float(pos_row[1] or 0.0) + inr_val, canon_user, ticker),
            )
        else:
            fx = inr_val / max(shares * price, 1e-6)
            c.execute(
                "INSERT INTO positions (username, ticker, product_type, shares, avg_price, cost_inr, currency, fx_rate) VALUES (?, ?, 'CNC', ?, ?, ?, ?, ?)",
                (canon_user, ticker, shares, price, inr_val, currency, fx),
            )
        c.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        return True, f"Reversed Order #{tx_id} ({action} {shares} {ticker}) and restored {shares} shares."


def toggle_watchlist(username: str, ticker: str, db_path: str = DB_PATH) -> bool:
    with db_conn(db_path) as conn:
        c = conn.cursor()
        exists = c.execute(
            "SELECT 1 FROM watchlist WHERE LOWER(username) = LOWER(?) AND ticker = ?", (username, ticker)
        ).fetchone()
        if exists:
            c.execute("DELETE FROM watchlist WHERE LOWER(username) = LOWER(?) AND ticker = ?", (username, ticker))
            return False
        c.execute(
            "INSERT INTO watchlist (username, ticker, added_at) VALUES (?, ?, ?)",
            (username, ticker, get_ist_now().strftime("%Y-%m-%d %H:%M")),
        )
        return True


def get_user_watchlist(username: str, db_path: str = DB_PATH) -> list[str]:
    with db_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE LOWER(username) = LOWER(?) ORDER BY added_at DESC", (username,)
        ).fetchall()
        return [r[0] for r in rows]


def get_user_account_summary(
    username: str, snapshots: dict, usdinr_rate: float = DEFAULT_USDINR_RATE, db_path: str = DB_PATH
) -> dict:
    with db_conn(db_path) as conn:
        bal_row = conn.execute(
            "SELECT balance FROM users WHERE LOWER(username) = LOWER(?)", (username,)
        ).fetchone()
        bal = float(bal_row[0]) if bal_row else 0.0
        port_df = pd.read_sql_query(
            "SELECT ticker, shares, avg_price, cost_inr, currency FROM portfolio WHERE LOWER(username) = LOWER(?)",
            conn, params=(username,),
        )
        pos_df = pd.read_sql_query(
            "SELECT ticker, product_type, shares, avg_price, cost_inr, currency, fx_rate FROM positions WHERE LOWER(username) = LOWER(?)",
            conn, params=(username,),
        )
        tx_df = pd.read_sql_query(
            "SELECT id, timestamp, ticker, action, shares, price, total, currency, order_type, inr_total FROM transactions WHERE LOWER(username) = LOWER(?) ORDER BY id DESC",
            conn, params=(username,),
        )
        pend_df = pd.read_sql_query(
            "SELECT id, created_at, ticker, action, product_type, shares, limit_price, reserved_margin_inr, status FROM pending_orders WHERE LOWER(username) = LOWER(?) AND status = 'PENDING' ORDER BY id DESC",
            conn, params=(username,),
        )

    tot_inv_inr = 0.0
    tot_cur_inr = 0.0
    holdings_md_lines = []

    if not port_df.empty:
        ltps, fx_rates, cur_vals_inr, inv_vals_inr, pnls_inr, pnl_pcts, sectors = [], [], [], [], [], [], []
        for _, r in port_df.iterrows():
            sym = LEGACY_TICKER_REMAP.get(r["ticker"], r["ticker"])
            meta = get_ticker_meta(sym)
            cur = meta["currency"]
            fx = get_fx_rate_for_ticker(sym, usdinr_rate)
            ltp = float(snapshots.get(sym, {}).get("price", r["avg_price"]))
            inv_inr = float(r["cost_inr"]) if pd.notna(r["cost_inr"]) else float(r["shares"] * r["avg_price"] * fx)
            cur_inr = float(r["shares"]) * ltp * fx
            pnl_inr = cur_inr - inv_inr
            pct = (pnl_inr / inv_inr * 100.0) if inv_inr > 0 else 0.0

            tot_inv_inr += inv_inr
            tot_cur_inr += cur_inr
            ltps.append(round(ltp, 2))
            fx_rates.append(round(fx, 2))
            inv_vals_inr.append(round(inv_inr, 2))
            cur_vals_inr.append(round(cur_inr, 2))
            pnls_inr.append(round(pnl_inr, 2))
            pnl_pcts.append(round(pct, 2))
            sectors.append(meta["sector"])
            holdings_md_lines.append(
                f"- **{sym}**: {int(r['shares'])} qty @ {cur}{float(r['avg_price']):,.2f} | "
                f"LTP: {cur}{ltp:,.2f} | Value: ₹{cur_inr:,.2f} | P&L: ₹{pnl_inr:+,.2f} ({pct:+.2f}%)"
            )
        port_df["Sector"] = sectors
        port_df["LTP"] = ltps
        port_df["FX (₹)"] = fx_rates
        port_df["Cost (₹)"] = inv_vals_inr
        port_df["Live Value (₹)"] = cur_vals_inr
        port_df["Live P&L (₹)"] = pnls_inr
        port_df["Return (%)"] = pnl_pcts

    tot_m2m_inr = 0.0
    tot_pos_val_inr = 0.0
    positions_md_lines = []
    if not pos_df.empty:
        p_ltps, p_cur_inr, p_m2m, p_ret = [], [], [], []
        for _, r in pos_df.iterrows():
            sym = LEGACY_TICKER_REMAP.get(r["ticker"], r["ticker"])
            cur = get_ticker_meta(sym)["currency"]
            fx = get_fx_rate_for_ticker(sym, usdinr_rate)
            ltp = float(snapshots.get(sym, {}).get("price", r["avg_price"]))
            inv_inr = float(r["cost_inr"]) if pd.notna(r["cost_inr"]) else float(r["shares"] * r["avg_price"] * fx)
            cur_inr = float(r["shares"]) * ltp * fx
            m2m_inr = cur_inr - inv_inr
            pct = (m2m_inr / inv_inr * 100.0) if inv_inr > 0 else 0.0

            tot_pos_val_inr += cur_inr
            tot_m2m_inr += m2m_inr
            p_ltps.append(round(ltp, 2))
            p_cur_inr.append(round(cur_inr, 2))
            p_m2m.append(round(m2m_inr, 2))
            p_ret.append(round(pct, 2))
            positions_md_lines.append(
                f"- **{sym} ({r['product_type']})**: {int(r['shares'])} qty @ {cur}{float(r['avg_price']):,.2f} | "
                f"LTP: {cur}{ltp:,.2f} | M2M P&L: ₹{m2m_inr:+,.2f}"
            )
        pos_df["LTP"] = p_ltps
        pos_df["Live Value (₹)"] = p_cur_inr
        pos_df["M2M P&L (₹)"] = p_m2m
        pos_df["Return (%)"] = p_ret

    orders_md_lines = []
    for _, r in tx_df.head(5).iterrows():
        c_sym = r["currency"] if pd.notna(r["currency"]) else "₹"
        orders_md_lines.append(
            f"- Order `#{int(r['id'])}` ({r['timestamp']}): **{r['action']}** {int(r['shares'])} `{r['ticker']}` @ {c_sym}{float(r['price']):,.2f}"
        )

    return {
        "balance": bal,
        "tot_inv": tot_inv_inr,
        "tot_cur": tot_cur_inr,
        "tot_pnl": tot_cur_inr - tot_inv_inr,
        "tot_pos_val": tot_pos_val_inr,
        "tot_m2m": tot_m2m_inr,
        "port_df": port_df,
        "pos_df": pos_df,
        "tx_df": tx_df,
        "pend_df": pend_df,
        "holdings_md": "\n".join(holdings_md_lines) if holdings_md_lines else "*No CNC holdings yet.*",
        "positions_md": "\n".join(positions_md_lines) if positions_md_lines else "*No open positions right now.*",
        "orders_md": "\n".join(orders_md_lines) if orders_md_lines else "*No executed orders yet.*",
    }


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_ast_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        right = _eval_ast_node(node.right)
        if isinstance(node.op, (ast.Div, ast.Mod)) and right == 0:
            raise ValueError("Division by zero")
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent too large")
        return SAFE_OPERATORS[type(node.op)](_eval_ast_node(node.left), right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](_eval_ast_node(node.operand))
    raise ValueError("Unsupported expression")


def try_solve_math_query(user_question: str) -> tuple[str | None, float | int | None]:
    q = user_question.strip().lower()
    if re.search(r"\b(19|20)\d{2}\s*-\s*((19|20)\d{2}|\d{1,2})\b", q):
        return None, None

    q_norm = q.replace("×", "*").replace("÷", "/").replace("^", "**")
    q_norm = re.sub(r"(\d)\s*x\s*(\d)", r"\1 * \2", q_norm)
    q_norm = re.sub(r"\bplus\b", "+", q_norm)
    q_norm = re.sub(r"\bminus\b", "-", q_norm)
    q_norm = re.sub(r"\btimes\b|\bmultiplied by\b", "*", q_norm)
    q_norm = re.sub(r"\bdivided by\b", "/", q_norm)

    stripped = re.sub(r"^(what is|calculate|compute|solve|eval|evaluate)\s+", "", q_norm).rstrip("? =").strip()
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:\s*(?:\*\*|[\+\-\*\/\%])\s*[-+]?\d+(?:\.\d+)?)+", stripped):
        try:
            tree = ast.parse(stripped, mode="eval")
            return stripped, _eval_ast_node(tree.body)
        except Exception:
            return None, None
    return None, None


def detect_all_stocks_from_text(user_text: str, max_stocks: int = 4) -> list[str]:
    cleaned = user_text.lower().strip()
    if any(p in cleaned for p in ["color of apple", "eat an apple", "apple fruit"]):
        return []

    found = []
    for sym in STOCK_CATALOG:
        sym_clean = sym.lower()
        sym_base = sym_clean.replace(".ns", "")
        if len(sym_base) >= 3 and (
            re.search(rf"\b{re.escape(sym_clean)}\b", cleaned)
            or re.search(rf"\b{re.escape(sym_base)}\b", cleaned)
        ):
            if sym not in found:
                found.append(sym)

    for keyword in sorted(CHAT_STOCK_ALIASES.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(keyword)}\b", cleaned):
            sym = CHAT_STOCK_ALIASES[keyword]
            if sym not in found:
                found.append(sym)
        if len(found) >= max_stocks:
            break
    return found[:max_stocks]


def detect_stock_from_text(user_text: str, default_ticker: str | None = None) -> tuple[str | None, bool]:
    matches = detect_all_stocks_from_text(user_text, max_stocks=1)
    if matches:
        return matches[0], True
    return default_ticker, False


def parse_trade_command(user_text: str) -> dict | None:
    q = user_text.strip().lower()
    if "?" in q:
        return None
    non_imperative_markers = [
        "should i", "can i", "could i", "would you", "do you", "is it good",
        "why ", "when ", "what ", "which ", "how to", "don't ", "do not ",
        "never ", "avoid ", "if i ", "suggest", "recommend", "list ", "show ",
        "compare ", "vs ", "versus ",
    ]
    if any(m in q for m in non_imperative_markers):
        return None

    m = re.match(
        r"^(?:please\s+)?(?:place\s+(?:a\s+)?)?(buy|sell)\s+(?:(\d[\d,]*)\s+(?:shares?\s+of\s+)?)?(.+)$",
        q,
    )
    if not m:
        return None

    action = m.group(1).upper()
    qty_s = m.group(2)
    rest = m.group(3)
    ticker, found = detect_stock_from_text(rest, None)
    if not found or not ticker:
        return {"action": action, "ticker": None, "qty": 0, "product": "CNC (Delivery)", "limit_price": None}

    if not qty_s:
        extra_qty = re.search(r"\b(\d[\d,]*)\s*(?:shares?|qty|units?)\b", rest)
        qty = int(extra_qty.group(1).replace(",", "")) if extra_qty else 1
    else:
        qty = max(1, int(qty_s.replace(",", "")))

    prod = "MIS (Intraday 5x)" if any(w in q for w in ["mis", "intraday", "5x"]) else "CNC (Delivery)"
    lim_match = re.search(r"(?:at|@|limit)\s*[₹$]?\s*(\d+(?:\.\d+)?)", rest)
    lim_price = float(lim_match.group(1)) if lim_match else None
    return {
        "action": action,
        "ticker": ticker,
        "qty": qty,
        "product": prod,
        "limit_price": lim_price,
    }


def parse_auto_invest_command(user_text: str) -> dict | None:
    q = user_text.strip().lower()
    if "?" in q:
        return None
    advisory_blocks = [
        "should i", "can i", "could i", "would you", "do you", "is it good",
        "which stock", "what stock", "which is best", "which is the best",
        "suggest", "recommend", "list ", "compare ", "tell me", "analyze ",
    ]
    if any(m in q for m in advisory_blocks):
        return None

    has_auto_verb = any(
        k in q
        for k in [
            "auto buy", "auto-buy", "auto trade", "auto-trade", "auto invest", "auto-invest",
            "automatically buy", "automatically trade", "automatically invest", "automatically place",
            "find the best", "find best", "pick the best", "pick best", "top profitable",
            "best stock and buy", "best stock and invest", "invest in best", "invest in top",
            "buy the best", "buy top ",
        ]
    )
    if not has_auto_verb or not any(w in q for w in ["buy", "invest", "trade", "place"]):
        return None

    market = "ALL"
    if any(w in q for w in ["nse", "indian", "india", "nifty"]):
        market = "NSE"
    elif any(w in q for w in ["us ", "nasdaq", "nyse", "american", "usa"]):
        market = "US"

    sector_hint = ""
    for sk in ["it", "tech", "bank", "finance", "defence", "defense", "auto", "pharma", "energy", "fmcg", "ai", "semiconductor", "chip", "cloud", "ev"]:
        if re.search(rf"\b{re.escape(sk)}\b", q):
            sector_hint = sk
            break

    budget_match = re.search(r"(?:₹|rs\.?|inr|budget|with|worth|for|invest)\s*[₹]?\s*(\d[\d,]*)", q)
    budget_inr = float(budget_match.group(1).replace(",", "")) if budget_match else 0.0

    qty_match = re.search(r"\b(\d[\d,]*)\s*(?:shares?|units?|qty)\b", q)
    explicit_qty = int(qty_match.group(1).replace(",", "")) if qty_match else None
    prod = "MIS (Intraday 5x)" if any(w in q for w in ["mis", "intraday", "5x"]) else "CNC (Delivery)"

    return {
        "market": market,
        "sector_hint": sector_hint,
        "budget_inr": budget_inr,
        "qty": explicit_qty,
        "product": prod,
    }


def resolve_secret(key_name: str, session_override: str = "") -> str:
    if session_override and session_override.strip():
        return session_override.strip()
    try:
        secret_val = st.secrets.get(key_name, "")
        if secret_val and str(secret_val).strip() and "your_" not in str(secret_val):
            return str(secret_val).strip()
    except Exception:
        pass
    return os.environ.get(key_name, "").strip()


def resolve_groq_api_key(session_key: str = "") -> str:
    return resolve_secret("GROQ_API_KEY", session_key)


def _build_llm_messages(system_prompt: str, user_prompt: str, chat_history: list[dict] | None) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        for turn in chat_history[-4:]:
            q_prev = turn.get("question", "")
            a_prev = turn.get("answer", "")
            if q_prev and a_prev:
                messages.append({"role": "user", "content": q_prev[:500]})
                messages.append({"role": "assistant", "content": a_prev[:700]})
    messages.append({"role": "user", "content": user_prompt})
    return messages


GROQ_CHAT_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
]

GEMINI_CHAT_MODELS = [
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-2.5-flash",
]


def _select_groq_models(client) -> list[str]:
    candidates = list(GROQ_CHAT_MODELS)
    try:
        live_ids = [m.id for m in client.models.list().data]
        live_set = set(live_ids)
        prioritized = [m for m in candidates if m in live_set]
        extras = [
            mid for mid in live_ids
            if mid not in prioritized
            and not any(bad in mid.lower() for bad in ["whisper", "guard", "orpheus", "safeguard", "tts", "vision"])
        ]
        return (prioritized + extras) or candidates
    except Exception:
        return candidates


def call_groq_llm_live(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    chat_history: list[dict] | None = None,
) -> tuple[str | None, str | None, str | None]:
    active_key = (api_key or "").strip()
    if not active_key.startswith("gsk_"):
        return None, None, "missing_key"

    try:
        from groq import Groq
    except ImportError:
        return None, None, "missing_sdk"

    messages = _build_llm_messages(system_prompt, user_prompt, chat_history)
    client = Groq(api_key=active_key, timeout=18.0)

    for model_name in _select_groq_models(client)[:4]:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.35,
                max_tokens=2048,
            )
            txt = resp.choices[0].message.content
            if txt and len(txt.strip()) > 1:
                return txt.strip(), f"Live Groq AI ({model_name})", None
        except Exception as exc:
            err_s = str(exc).lower()
            if "401" in err_s or "invalid_api_key" in err_s or "authentication" in err_s:
                return None, None, "invalid_key"
            continue

    return None, None, "unavailable"


def call_gemini_llm_live(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    chat_history: list[dict] | None = None,
) -> tuple[str | None, str | None]:
    active_key = (api_key or "").strip()
    if not active_key:
        return None, None

    history_ctx = ""
    if chat_history:
        snippets = [f"User: {t['question'][:300]}\nAssistant: {t['answer'][:400]}" for t in chat_history[-3:]]
        history_ctx = "\n\nRecent conversation:\n" + "\n---\n".join(snippets)

    payload = json.dumps({
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt + history_ctx}]}],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 2048},
    }).encode("utf-8")

    for g_model in GEMINI_CHAT_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={urllib.parse.quote(active_key)}"
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=14) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cands = data.get("candidates", [])
            if cands:
                txt = cands[0]["content"]["parts"][0]["text"]
                if txt and txt.strip():
                    return txt.strip(), f"Live Gemini ({g_model})"
        except Exception:
            continue
    return None, None


def is_market_timing_question(q_clean: str) -> bool:
    timing_phrases = [
        "market open", "market opening", "market close", "market closing",
        "market timing", "market time", "market hour", "trading hour",
        "trading time", "when does market", "when will market", "is market open",
        "is the market open", "opening time", "closing time",
    ]
    return any(p in q_clean for p in timing_phrases)


def is_explicit_screener_request(q_clean: str) -> bool:
    screener_phrases = [
        "top benefitting", "benefitting stock", "benefiting stock",
        "top indian", "top us", "best stock", "top stock", "which stock",
        "what stock", "stocks to buy", "stocks to invest", "stocks to trade",
        "recommend stock", "suggest stock", "stock picks", "top gainer", "list top",
    ]
    return any(p in q_clean for p in screener_phrases)


def build_market_timings_report() -> str:
    now_ist = get_ist_now()
    nse_open, nse_status = check_market_trading_hours("RELIANCE.NS")
    us_open, us_status = check_market_trading_hours("AAPL")
    return f"""
### Official Stock Market Trading Hours
* **Current Clock:** `{now_ist.strftime('%A, %d %B %Y | %I:%M %p IST')}`

#### Indian Markets (NSE & BSE) — Mon to Fri
* **Pre-Open:** `9:00 AM – 9:15 AM IST` | **Continuous:** `9:15 AM – 3:30 PM IST`
* **Live Status:** **{'OPEN — ' + nse_status if nse_open else 'CLOSED — ' + nse_status}**

#### US Markets (NASDAQ & NYSE) — Mon to Fri
* **Regular Hours:** `9:30 AM – 4:00 PM ET` *(handles EST/EDT daylight saving automatically)*
* **Live Status:** **{'OPEN — ' + us_status if us_open else 'CLOSED — ' + us_status}**
"""


def _resolve_sector_keywords(query_text: str) -> list[str] | None:
    q_low = (query_text or "").lower()
    sector_keywords = {
        "it": ["IT", "Tech", "Software", "Cloud", "SaaS", "Semiconductor", "AI"],
        "tech": ["IT", "Tech", "Software", "Cloud", "AI", "Semiconductor", "Consumer Tech"],
        "ai": ["AI", "Cloud", "Semiconductor", "Enterprise AI"],
        "semiconductor": ["Semiconductor", "Chip", "AI & Semiconductors"],
        "semiconductors": ["Semiconductor", "Chip", "AI & Semiconductors"],
        "chip": ["Semiconductor", "Chip", "Foundry"],
        "bank": ["Bank", "Financial", "Finance", "NBFC"],
        "banking": ["Bank", "Financial", "Finance", "NBFC"],
        "finance": ["Bank", "Financial", "Finance", "NBFC", "Payments"],
        "defence": ["Defence", "Aerospace"],
        "defense": ["Defence", "Aerospace"],
        "auto": ["Auto", "EV", "SUV", "Vehicle"],
        "automotive": ["Auto", "EV", "SUV", "Vehicle"],
        "ev": ["EV", "Electric Vehicle", "Auto"],
        "pharma": ["Pharma", "Biotech", "Health"],
        "healthcare": ["Pharma", "Biotech", "Health"],
        "energy": ["Energy", "Power", "Oil", "Coal", "Gas"],
        "fmcg": ["FMCG", "Beverage", "Food", "Retail"],
    }
    for s_key, s_matches in sector_keywords.items():
        if re.search(rf"\b{re.escape(s_key)}\b", q_low):
            return s_matches
    return None


def rank_quant_screener_candidates(
    market: str = "ALL",
    sector_hint: str = "",
    snapshots: dict | None = None,
    usdinr_rate: float = DEFAULT_USDINR_RATE,
    limit: int = 12,
) -> list[dict]:
    snaps = snapshots or {}
    sector_filter = _resolve_sector_keywords(sector_hint)
    mkt_u = (market or "ALL").upper()

    pre_pool = []
    for sym, meta in STOCK_CATALOG.items():
        if mkt_u == "NSE" and meta["exchange"] != "NSE":
            continue
        if mkt_u == "US" and meta["exchange"] == "NSE":
            continue
        if sector_filter and not any(m.lower() in meta["sector"].lower() for m in sector_filter):
            continue
        pre_pool.append(sym)

    if not pre_pool:
        pre_pool = list(STOCK_CATALOG.keys())

    prelim = []
    for sym in pre_pool:
        sn = snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))
        rsi = float(sn.get("rsi", 50.0))
        pct = float(sn.get("pct", 0.0))
        above = bool(sn.get("above_sma", True))
        rsi_bonus = 2.0 if 50.0 <= rsi <= 66.0 else (0.9 if 38.0 <= rsi < 50.0 else (-1.5 if rsi >= 72.0 else -0.6))
        sma_bonus = 2.0 if above else -1.1
        prelim.append((pct * 1.35 + sma_bonus + rsi_bonus, sym))
    prelim.sort(key=lambda x: x[0], reverse=True)

    live_shortlist = [s for _, s in prelim[:24]]
    live_snaps = ensure_symbols_live(live_shortlist, snaps)

    ranked = []
    for sym in pre_pool:
        meta = STOCK_CATALOG[sym]
        sn = live_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))
        rsi = float(sn.get("rsi", 50.0))
        pct = float(sn.get("pct", 0.0))
        above = bool(sn.get("above_sma", True))
        price = float(sn.get("price", 100.0))
        fx = get_fx_rate_for_ticker(sym, usdinr_rate)
        inr_share_cost = price * fx

        rsi_bonus = 2.0 if 50.0 <= rsi <= 66.0 else (0.9 if 38.0 <= rsi < 50.0 else (-1.5 if rsi >= 72.0 else -0.6))
        sma_bonus = 2.0 if above else -1.1
        vol_bonus = 0.7 if sn.get("volume", 0.0) > sn.get("avg_volume", 1.0) * 1.15 else 0.0
        score = (pct * 1.35) + sma_bonus + rsi_bonus + vol_bonus
        proj_5d = max(1.6, pct * 1.5 + (1.5 if above else 0.4))
        ranked.append(
            {
                **meta,
                "symbol": sym,
                "score": round(score, 2),
                "proj_5d": round(proj_5d, 2),
                "inr_share_cost": inr_share_cost,
                **sn,
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]


def build_universal_stocks_screener_report(
    user_question: str,
    acct_balance: float,
    snapshots: dict,
    usdinr_rate: float,
) -> str:
    q_low = user_question.lower()
    mkt = "NSE" if any(w in q_low for w in ["nse", "indian", "india", "nifty"]) else ("US" if any(w in q_low for w in ["us ", "nasdaq", "nyse", "american"]) else "ALL")
    ranked = rank_quant_screener_candidates(mkt, q_low, snapshots, usdinr_rate, limit=10)

    rows_md = []
    for i, item in enumerate(ranked, 1):
        cur = item["currency"]
        pr = item["price"]
        tgt = pr * (1.0 + item["proj_5d"] / 100.0)
        sl = pr * 0.968
        sig = "STRONG BUY" if item["score"] > 3.5 else "ACCUMULATE"
        rows_md.append(
            f"| {i} | **{item['name']}** (`{item['symbol']}`) | {item['exchange']} • {item['sector']} | "
            f"`{cur}{pr:,.2f}` (`{item['pct']:+.2f}%`) | `{item['rsi']:.1f}` | `{cur}{tgt:,.2f}` | `{cur}{sl:,.2f}` | **{sig}** |"
        )

    return f"""
### Multi-Market Quantitative Screener (Top 10 Ranked across {len(STOCK_CATALOG)} Stocks)
Ranked across **NSE & NASDAQ/NYSE** using live momentum, 20-SMA trend, volume breakout, and 14-day Wilder RSI (tailored to your **`₹{acct_balance:,.2f}`** margin at FX `₹{usdinr_rate:.2f}/$`):

| Rank | Company (`Ticker`) | Exchange & Sector | Live Price | RSI (14) | Target | Stop-Loss | Signal |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(rows_md)}

*Tip: Say **`Find the best stock and invest ₹15000`** or use **AI Auto-Pilot** above to let the advisor pick #1 and place the trade automatically.*
"""


def execute_ai_auto_pick_trade(
    username: str,
    snapshots: dict,
    usdinr_rate: float,
    market: str = "ALL",
    sector_hint: str = "",
    budget_inr: float = 0.0,
    explicit_qty: int | None = None,
    product: str = "CNC (Delivery)",
    allow_after_hours: bool = False,
    db_path: str = DB_PATH,
) -> tuple[bool, str, str, str, list[str]]:
    acct = get_user_account_summary(username, snapshots, usdinr_rate, db_path=db_path)
    avail = float(acct["balance"])
    eff_mult = 0.20 if "MIS" in product else 1.0
    target_budget = float(budget_inr) if budget_inr > 0 else min(avail, max(5000.0, round(avail * 0.20, 2)))
    target_budget = min(target_budget, avail)

    ranked = rank_quant_screener_candidates(market, sector_hint, snapshots, usdinr_rate, limit=18)
    steps_log = [f"Scanned {len(STOCK_CATALOG)} NSE & US equities (Market: {market}, Budget: ₹{target_budget:,.2f})"]

    chosen_item = None
    for cand in ranked:
        per_share_req = float(cand["inr_share_cost"]) * eff_mult
        if float(cand.get("rsi", 50.0)) < 73.0 and per_share_req <= max(target_budget, 1.0):
            chosen_item = cand
            break
    if chosen_item is None and ranked:
        affordable = [c for c in ranked if float(c["inr_share_cost"]) * eff_mult <= avail]
        chosen_item = affordable[0] if affordable else min(ranked, key=lambda c: float(c["inr_share_cost"]))

    if not chosen_item:
        return False, "No matching equities found in the catalog for that filter.", "FinanceSight Auto-Pilot", get_logo_url("RELIANCE.NS"), steps_log

    sym = chosen_item["symbol"]
    profile = build_stock_quant_profile(sym, snapshots, usdinr_rate, avail, include_news=False)
    cur = profile["cur"]
    price = float(profile["price"])
    fx = float(profile["fx"])
    per_share_margin = max(1.0, price * fx * eff_mult)

    if explicit_qty is not None:
        qty = max(1, int(explicit_qty))
    else:
        qty = max(1, int(target_budget // per_share_margin)) if avail >= per_share_margin else 1

    steps_log.append(
        f"Selected #{1}: {profile['meta']['name']} ({sym}) | Score {profile['score']}/6 | 7D ML {cur}{profile['ml_pred_7d']:,.2f} ({profile['ml_move_pct']:+.2f}%)"
    )

    ok_t, msg_t = execute_trade(
        username,
        sym,
        "BUY",
        qty,
        price,
        product,
        order_type="MARKET",
        usdinr_rate=usdinr_rate,
        allow_after_hours=allow_after_hours,
        db_path=db_path,
    )
    steps_log.append(f"Trade engine status: {'FILLED' if ok_t else 'BLOCKED'} — {msg_t}")

    updated = get_user_account_summary(username, snapshots, usdinr_rate, db_path=db_path)
    shortlist_rows = []
    for i, c in enumerate(ranked[:5], 1):
        flag = "**SELECTED**" if c["symbol"] == sym else "Candidate"
        shortlist_rows.append(
            f"| {i} | **{c['name']}** (`{c['symbol']}`) | {c['exchange']} | `{c['currency']}{c['price']:,.2f}` (`{c['pct']:+.2f}%`) | `{c['rsi']:.1f}` | `{c['score']}` | {flag} |"
        )

    sl_px = max(0.01, price - 1.5 * profile["atr"])
    tp_px = price + 2.0 * profile["atr"]
    status_hdr = "Executed Automatically" if ok_t else "Prepared Plan (Action Needed)"
    report = f"""### AI Auto-Pilot Best-Stock Selection & Trade ({status_hdr})
* **Execution Result:** **{msg_t}**
* **Selected Asset:** **{profile['meta']['name']} (`{sym}`)** — `{qty} shares` ({product}) @ `{cur}{price:,.2f}` (`FX ₹{fx:.2f}`)
* **Quant + ML Rationale (`{profile['score']}/6` — {profile['verdict']}):**
  * **7-Day ML Forecast (`{profile['ml_model']}`):** `{cur}{profile['ml_pred_7d']:,.2f}` (`{profile['ml_move_pct']:+.2f}%` | Dir. Accuracy `{profile['ml_dir_acc']:.1f}%`)
  * **Technical Levels:** 20-SMA `{cur}{profile['sma20']:,.2f}` | RSI-14 `{profile['rsi']:.1f}` | Support S1 `{cur}{profile['s1']:,.2f}` | Resistance R1 `{cur}{profile['r1']:,.2f}`
  * **Risk Plan:** Stop-Loss (1.5× ATR) `{cur}{sl_px:,.2f}` | Target (2× ATR) `{cur}{tp_px:,.2f}`
* **Updated Cash Margin:** **`₹{updated['balance']:,.2f}`**

#### Top 5 Ranked Candidates Evaluated
| Rank | Company (`Ticker`) | Exchange | Spot Price | RSI (14) | Quant Score | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(shortlist_rows)}"""

    return ok_t, report, f"Auto-Pilot: {profile['meta']['name']} ({sym})", get_logo_url(sym), steps_log


def build_portfolio_risk_audit(
    username: str,
    snapshots: dict,
    usdinr_rate: float,
    auto_rebalance: bool = False,
    allow_after_hours: bool = False,
    db_path: str = DB_PATH,
) -> tuple[str, list[str]]:
    acct = get_user_account_summary(username, snapshots, usdinr_rate, db_path=db_path)
    port_df = acct["port_df"]
    pos_df = acct["pos_df"]
    steps_log = [f"Loaded SQLite holdings ({len(port_df)}) and open positions ({len(pos_df)})"]

    held_syms = set(port_df["ticker"].tolist() if not port_df.empty else [])
    held_syms.update(pos_df["ticker"].tolist() if not pos_df.empty else [])
    live_snaps = ensure_symbols_live(list(held_syms), snapshots) if held_syms else snapshots
    if held_syms:
        acct = get_user_account_summary(username, live_snaps, usdinr_rate, db_path=db_path)
        port_df = acct["port_df"]
        pos_df = acct["pos_df"]

    net_worth = float(acct["balance"]) + float(acct["tot_cur"])
    cash_pct = (float(acct["balance"]) / net_worth * 100.0) if net_worth > 0 else 100.0

    if port_df.empty and pos_df.empty:
        top3 = rank_quant_screener_candidates("ALL", "", live_snaps, usdinr_rate, limit=3)
        starter = "\n".join(
            f"- **{c['name']} (`{c['symbol']}`)** ({c['exchange']}) @ `{c['currency']}{c['price']:,.2f}` (`{c['pct']:+.2f}%`, RSI `{c['rsi']:.1f}`)"
            for c in top3
        )
        steps_log.append("Portfolio is 100% cash; prepared 3 starter allocations")
        return (
            f"""### Portfolio Health & Risk Audit (`@{username}`)
* **Account Net Worth:** `₹{net_worth:,.2f}` (**`100.0%` Cash Reserve**, 0 holdings)
* **Diversification Score:** `N/A — Uninvested`

#### Suggested Starter Allocation (Balanced NSE + US Leaders)
{starter}

*Say **`Find the best stock and invest ₹15000`** or click **Find Best Stock & Auto-Trade** above to deploy capital automatically.*""",
            steps_log,
        )

    rebalance_logs = []
    audit_rows = []
    tot_val = max(1.0, float(acct["tot_cur"]))
    nse_val = 0.0
    max_wt = 0.0
    sector_weights: dict[str, float] = {}

    for _, row in port_df.iterrows():
        sym = LEGACY_TICKER_REMAP.get(row["ticker"], row["ticker"])
        meta = get_ticker_meta(sym)
        sn = live_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": float(row["LTP"]), "pct": 0.0, "rsi": 50.0, "above_sma": True}))
        val_inr = float(row["Live Value (₹)"])
        wt = (val_inr / tot_val) * 100.0
        max_wt = max(max_wt, wt)
        if meta["exchange"] == "NSE":
            nse_val += val_inr
        sector_weights[meta["sector"]] = sector_weights.get(meta["sector"], 0.0) + wt

        rsi = float(sn.get("rsi", 50.0))
        ret_pct = float(row["Return (%)"])
        above = bool(sn.get("above_sma", True))

        if rsi >= 68.0 and ret_pct >= 3.0:
            action_tag = "TAKE PROFIT (Overbought)"
        elif (not above and ret_pct <= -3.0) or ret_pct <= -6.0:
            action_tag = "STOP-LOSS ALERT (<20-SMA)"
        elif wt >= 45.0:
            action_tag = "TRIM CONCENTRATION (>45%)"
        elif above and rsi < 62.0:
            action_tag = "CORE HOLD / ACCUMULATE"
        else:
            action_tag = "HOLD & MONITOR"

        audit_rows.append(
            f"| **{meta['name']}** (`{sym}`) | `{int(row['shares'])}` | `{wt:.1f}%` | `{ret_pct:+.2f}%` | `{rsi:.1f}` | **{action_tag}** |"
        )

        if auto_rebalance and ("TAKE PROFIT" in action_tag or "STOP-LOSS ALERT" in action_tag):
            sell_qty = int(row["shares"])
            _, msg_s = execute_trade(
                username, sym, "SELL", sell_qty, float(row["LTP"]), "CNC (Delivery)",
                usdinr_rate=usdinr_rate, allow_after_hours=allow_after_hours, db_path=db_path,
            )
            rebalance_logs.append(f"- **CNC Exit ({sym}, {sell_qty} sh):** {msg_s}")

    if auto_rebalance and not pos_df.empty:
        for _, pr in pos_df.iterrows():
            if float(pr["Return (%)"]) >= 3.0 or float(pr["Return (%)"]) <= -3.0:
                sym = LEGACY_TICKER_REMAP.get(pr["ticker"], pr["ticker"])
                prod = "MIS (Intraday 5x)" if pr["product_type"] == "MIS" else "CNC (Delivery)"
                _, msg_p = execute_trade(
                    username, sym, "SELL", int(pr["shares"]), float(pr["LTP"]), prod,
                    usdinr_rate=usdinr_rate, allow_after_hours=allow_after_hours, db_path=db_path,
                )
                rebalance_logs.append(f"- **{pr['product_type']} Exit ({sym}, {int(pr['shares'])} sh):** {msg_p}")

    nse_pct = (nse_val / tot_val) * 100.0
    us_pct = 100.0 - nse_pct
    n_holdings = len(port_df)
    top_sec, top_sec_wt = max(sector_weights.items(), key=lambda kv: kv[1]) if sector_weights else ("N/A", 0.0)

    div_score = min(10.0, max(1.5, round(
        (min(5, n_holdings) * 1.4) + (2.0 if 10.0 <= nse_pct <= 90.0 else 0.5) + (1.5 if max_wt <= 40.0 else 0.2) + (0.5 if 10.0 <= cash_pct <= 50.0 else 0.2),
        1,
    )))

    steps_log.append(f"Computed diversification score {div_score}/10 across {n_holdings} holdings & top sector {top_sec}")
    reb_section = ""
    if auto_rebalance:
        updated = get_user_account_summary(username, live_snaps, usdinr_rate, db_path=db_path)
        steps_log.append(f"Auto-rebalance ran {len(rebalance_logs)} order(s)")
        reb_body = "\n".join(rebalance_logs) if rebalance_logs else "- All holdings passed technical hold checks (no overbought winners >=+3% or breached stops triggered)."
        reb_section = f"\n\n#### Autonomous Rebalance Actions\n{reb_body}\n* **Updated Cash Margin:** **`₹{updated['balance']:,.2f}`**"

    return (
        f"""### Portfolio Health & Risk Audit (`@{username}`)
* **Net Worth:** `₹{net_worth:,.2f}` | **Holdings:** `₹{acct['tot_cur']:,.2f}` (`Unrealized {acct['tot_pnl']:+,.2f}`) | **Cash Buffer:** `{cash_pct:.1f}%` (`₹{acct['balance']:,.2f}`)
* **Diversification Score:** **`{div_score}/10`** | **NSE vs US Mix:** `{nse_pct:.0f}% NSE / {us_pct:.0f}% US` | **Top Sector:** `{top_sec} ({top_sec_wt:.1f}%)`

| Holding | Shares | Weight % | ROI % | RSI (14) | AI Risk Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(audit_rows)}{reb_section}""",
        steps_log,
    )


def call_groq_agentic_loop(
    user_question: str,
    username: str,
    snapshots: dict,
    usdinr_rate: float,
    groq_api_key: str,
    allow_after_hours: bool = False,
    chat_history: list[dict] | None = None,
) -> tuple[str | None, str | None, str | None, str | None, list[str], str | None]:
    active_key = (groq_api_key or "").strip()
    if not active_key.startswith("gsk_"):
        return None, None, None, None, [], "missing_key"

    try:
        from groq import Groq
    except ImportError:
        return None, None, None, None, [], "missing_sdk"

    client = Groq(api_key=active_key, timeout=18.0)
    q_clean = user_question.strip().lower()
    can_trade_via_llm = (
        "?" not in q_clean
        and any(v in q_clean for v in ["buy", "sell", "invest", "square off", "auto trade", "auto buy", "rebalance"])
        and not any(blk in q_clean for blk in ["should i", "would you", "can i", "suggest", "recommend"])
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_stock_quant_report",
                "description": "Fetch live price, multi-timeframe returns, SMA/EMA, Wilder RSI, MACD, Pivot supports/resistances, 7-day ML forecast, fundamentals, and optional news for a stock symbol or company name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Ticker symbol (e.g. RELIANCE.NS, NVDA) or company name"},
                        "include_news": {"type": "boolean", "description": "Set true to include latest news headlines"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scan_top_market_opportunities",
                "description": "Scan and rank the top live NSE and/or US equities by momentum, 20-SMA trend, RSI-14, and volume breakout.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market": {"type": "string", "enum": ["ALL", "NSE", "US"]},
                        "sector": {"type": "string", "description": "Optional sector keyword such as it, bank, defence, auto, pharma, energy, ai"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_my_portfolio",
                "description": "Inspect the user's current cash balance, CNC holdings, M2M open positions, risk diversification, and recent orders.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]
    if can_trade_via_llm:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": "place_paper_trade",
                    "description": "Execute a CNC or MIS paper trade in the user's portfolio when explicitly instructed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string", "description": "Catalog stock symbol e.g. RELIANCE.NS or AAPL"},
                            "action": {"type": "string", "enum": ["BUY", "SELL"]},
                            "qty": {"type": "integer", "minimum": 1},
                            "product": {"type": "string", "enum": ["CNC (Delivery)", "MIS (Intraday 5x)"]},
                        },
                        "required": ["ticker", "action", "qty"],
                    },
                },
            }
        )

    sys_prompt = (
        f"You are FinanceSight AI, an institutional quantitative financial analyst & portfolio co-pilot for user @{username}.\n"
        f"Current IST Time: {get_ist_now().strftime('%A, %d %B %Y %I:%M %p IST')} | Live FX: ₹{usdinr_rate:.2f}/$.\n"
        "Always call the Python quant tools before stating stock prices, RSI, ML targets, or portfolio holdings. "
        "Cite exact numbers returned by the tools, include clear Entry/Stop-Loss/Target levels when advising on trades, and stay concise."
    )
    messages = _build_llm_messages(sys_prompt, user_question, chat_history)
    tool_steps: list[str] = []
    focus_sym: str | None = None

    for active_model in _select_groq_models(client)[:3]:
        model_messages = list(messages)
        tool_steps = []
        focus_sym = None
        try:
            for _round in range(3):
                resp = client.chat.completions.create(
                    model=active_model,
                    messages=model_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.25,
                    max_tokens=2048,
                )
                msg = resp.choices[0].message
                t_calls = getattr(msg, "tool_calls", None) or []
                if not t_calls:
                    content = (msg.content or "").strip()
                    if content:
                        title = f"{get_ticker_meta(focus_sym)['name']} ({focus_sym})" if focus_sym else "FinanceSight Agentic AI"
                        logo = get_logo_url(focus_sym) if focus_sym else get_logo_url("GOOGL")
                        return content, f"Groq Agentic AI ({active_model})", title, logo, tool_steps, None
                    break

                model_messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                            }
                            for tc in t_calls
                        ],
                    }
                )

                acct_now = get_user_account_summary(username, snapshots, usdinr_rate)
                for tc in t_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments or "{}")
                    except Exception:
                        fn_args = {}

                    if fn_name == "get_stock_quant_report":
                        sym_q = fn_args.get("query", "")
                        sym, _ = detect_stock_from_text(sym_q, sym_q.upper() if sym_q.upper() in STOCK_CATALOG else None)
                        if sym and sym in STOCK_CATALOG:
                            focus_sym = focus_sym or sym
                            prof = build_stock_quant_profile(sym, snapshots, usdinr_rate, acct_now["balance"], include_news=bool(fn_args.get("include_news")))
                            out_txt = _format_stock_context_for_llm(prof)
                            tool_steps.append(f"Tool get_stock_quant_report({sym})")
                        else:
                            out_txt = f"Ticker '{sym_q}' not found in 345-stock catalog."
                    elif fn_name == "scan_top_market_opportunities":
                        mkt = fn_args.get("market", "ALL")
                        sec = fn_args.get("sector", "")
                        cands = rank_quant_screener_candidates(mkt, sec, snapshots, usdinr_rate, limit=8)
                        if cands:
                            focus_sym = focus_sym or cands[0]["symbol"]
                        out_txt = "\n".join(
                            f"{i}. {c['symbol']} ({c['name']}, {c['exchange']}): {c['currency']}{c['price']:,.2f} ({c['pct']:+.2f}%), RSI {c['rsi']:.1f}, Score {c['score']}"
                            for i, c in enumerate(cands, 1)
                        )
                        tool_steps.append(f"Tool scan_top_market_opportunities(market={mkt}, sector={sec or 'ALL'})")
                    elif fn_name == "inspect_my_portfolio":
                        out_txt = (
                            f"Cash Margin: ₹{acct_now['balance']:,.2f} | Holdings Value: ₹{acct_now['tot_cur']:,.2f} | "
                            f"Unrealized P&L: ₹{acct_now['tot_pnl']:+,.2f}\nHoldings:\n{acct_now['holdings_md']}\nPositions:\n{acct_now['positions_md']}"
                        )
                        tool_steps.append("Tool inspect_my_portfolio()")
                    elif fn_name == "place_paper_trade" and can_trade_via_llm:
                        sym, _ = detect_stock_from_text(fn_args.get("ticker", ""), None)
                        act = str(fn_args.get("action", "BUY")).upper()
                        qty_v = max(1, int(fn_args.get("qty", 1)))
                        prod_v = fn_args.get("product", "CNC (Delivery)")
                        if sym:
                            focus_sym = focus_sym or sym
                            live_s = ensure_symbols_live([sym], snapshots)
                            px = float(live_s.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0}))["price"])
                            _, msg_exec = execute_trade(
                                username, sym, act, qty_v, px, prod_v,
                                usdinr_rate=usdinr_rate, allow_after_hours=allow_after_hours,
                            )
                            out_txt = msg_exec
                            tool_steps.append(f"Tool place_paper_trade({act} {qty_v} {sym})")
                        else:
                            out_txt = "Could not resolve stock symbol."
                    else:
                        out_txt = "Tool call ignored."

                    model_messages.append({"role": "tool", "tool_call_id": tc.id, "content": out_txt})
        except Exception as exc:
            err_s = str(exc).lower()
            if "401" in err_s or "invalid_api_key" in err_s or "authentication" in err_s:
                return None, None, None, None, tool_steps, "invalid_key"
            continue

    return None, None, None, None, tool_steps, "unavailable"


def build_stock_quant_profile(
    sym: str,
    snapshots: dict,
    usdinr_rate: float,
    acct_balance: float,
    include_news: bool = False,
) -> dict:
    meta = get_ticker_meta(sym)
    cur = meta["currency"]
    fx = get_fx_rate_for_ticker(sym, usdinr_rate)
    df_live = fetch_stock_history(sym, "1y")
    sn = snapshots.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True}))

    if df_live is not None and len(df_live) >= 30:
        close = df_live["Close"].astype(float)
        price = float(close.iloc[-1])
        prev_c = float(close.iloc[-2])
        pct_1d = ((price - prev_c) / prev_c * 100.0) if prev_c else 0.0
        pct_1w = ((price / float(close.iloc[-6])) - 1.0) * 100.0 if len(close) >= 6 else pct_1d
        pct_1m = ((price / float(close.iloc[-22])) - 1.0) * 100.0 if len(close) >= 22 else pct_1w
        pct_6m = ((price / float(close.iloc[-126])) - 1.0) * 100.0 if len(close) >= 126 else pct_1m
        pct_1y = ((price / float(close.iloc[0])) - 1.0) * 100.0

        rsi = float(df_live["RSI"].iloc[-1])
        sma20 = float(df_live["SMA_20"].iloc[-1])
        ema50 = float(df_live["EMA_50"].iloc[-1])
        macd_val = float(df_live["MACD"].iloc[-1])
        macd_sig = float(df_live["MACD_Signal"].iloc[-1])
        bb_pctb = float(df_live["BB_PctB"].iloc[-1])
        high52 = float(df_live["High"].max())
        low52 = float(df_live["Low"].min())
        atr_val = float(df_live["ATR_14"].iloc[-1])
        ann_vol = float(close.pct_change().std() * np.sqrt(252) * 100.0)

        vol_last = float(df_live["Volume"].iloc[-1])
        vol_avg20 = float(df_live["Volume"].tail(20).mean())
        vol_ratio = (vol_last / vol_avg20) if vol_avg20 > 0 else 1.0

        p_high = float(df_live["High"].iloc[-2])
        p_low = float(df_live["Low"].iloc[-2])
        pivot = (p_high + p_low + prev_c) / 3.0
        r1 = (2.0 * pivot) - p_low
        s1 = (2.0 * pivot) - p_high
        r2 = pivot + (p_high - p_low)
        s2 = pivot - (p_high - p_low)

        ml_res = run_ml_forecast_suite(sym, str(df_live.index[-1]), len(df_live), df_live)
        ml_pred_7d = ml_res["target_7d"] if ml_res else price * (1.02 if price >= sma20 else 0.985)
        ml_model = ml_res["best_model"] if ml_res else "Heuristic"
        ml_dir_acc = float(ml_res["eval_df"].iloc[0]["Directional Accuracy (%)"]) if ml_res else 55.0
    else:
        price = float(sn["price"])
        pct_1d = float(sn["pct"])
        pct_1w, pct_1m, pct_6m, pct_1y = pct_1d, pct_1d, pct_1d, pct_1d
        rsi = float(sn["rsi"])
        sma20 = float(sn.get("sma20", price * 0.99))
        ema50 = float(sn.get("ema50", price * 0.97))
        macd_val, macd_sig, bb_pctb = 0.0, 0.0, 0.5
        high52, low52 = price * 1.15, price * 0.85
        atr_val = price * 0.02
        ann_vol, vol_ratio = 22.0, 1.0
        pivot = price
        r1, s1, r2, s2 = price * 1.015, price * 0.985, price * 1.03, price * 0.97
        ml_pred_7d = price * (1.02 if price >= sma20 else 0.985)
        ml_model, ml_dir_acc = "Quant Baseline", 55.0

    funds = fetch_stock_fundamentals(sym)
    news_items = fetch_stock_news_headlines(sym, meta["name"]) if include_news else []
    ml_move_pct = ((ml_pred_7d - price) / price * 100.0) if price else 0.0
    affordable_cnc = int(acct_balance // (price * fx)) if price > 0 else 0
    trend_up = price >= sma20
    golden_cross = sma20 >= ema50

    score = sum([
        price >= sma20,
        price >= ema50,
        golden_cross,
        macd_val >= macd_sig,
        40.0 <= rsi <= 68.0,
        ml_move_pct > 0.0,
    ])
    if rsi >= 72:
        verdict = "OVERBOUGHT — WAIT FOR PULLBACK"
    elif score >= 5:
        verdict = "STRONG BULLISH ACCUMULATION"
    elif score >= 3:
        verdict = "MODERATELY BULLISH / HOLD"
    else:
        verdict = "BEARISH / CAUTIOUS"

    health = compute_traffic_light_health(sym, df_live, sn)
    return {
        "sym": sym, "meta": meta, "cur": cur, "fx": fx, "price": price,
        "pct_1d": pct_1d, "pct_1w": pct_1w, "pct_1m": pct_1m, "pct_6m": pct_6m, "pct_1y": pct_1y,
        "rsi": rsi, "sma20": sma20, "ema50": ema50, "macd_val": macd_val, "macd_sig": macd_sig,
        "bb_pctb": bb_pctb, "high52": high52, "low52": low52, "atr": atr_val, "ann_vol": ann_vol,
        "vol_ratio": vol_ratio, "pivot": pivot, "r1": r1, "r2": r2, "s1": s1, "s2": s2,
        "ml_pred_7d": ml_pred_7d, "ml_move_pct": ml_move_pct, "ml_model": ml_model, "ml_dir_acc": ml_dir_acc,
        "affordable_cnc": affordable_cnc, "verdict": verdict, "score": score,
        "funds": funds, "news": news_items, "health": health,
    }


def _format_stock_context_for_llm(p: dict) -> str:
    cur = p["cur"]
    funds = p["funds"]
    h = p.get("health") or compute_traffic_light_health(p["sym"], None, {"price": p["price"], "pct": p["pct_1d"], "rsi": p["rsi"], "above_sma": p["price"] >= p["sma20"]})
    f_line = (
        f"MktCap={format_large_number(funds.get('marketCap'), cur)}, "
        f"P/E={funds.get('trailingPE') or 'N/A'}, EPS={funds.get('trailingEps') or 'N/A'}, "
        f"Beta={funds.get('beta') or 'N/A'}, Analyst={funds.get('recommendationKey') or 'N/A'}"
    )
    news_line = ""
    if p["news"]:
        news_line = "\nRecent News:\n" + "\n".join(f"- {n['title']} ({n['pubDate']})" for n in p["news"])
    return (
        f"[{p['meta']['name']} ({p['sym']}, {p['meta']['exchange']}, {p['meta']['sector']})]\n"
        f"Price={cur}{p['price']:,.2f} (1D {p['pct_1d']:+.2f}%, 1W {p['pct_1w']:+.2f}%, 1M {p['pct_1m']:+.2f}%, 6M {p['pct_6m']:+.2f}%, 1Y {p['pct_1y']:+.2f}%) | FX=₹{p['fx']:.2f}\n"
        f"Traffic-Light ML Health={h['pill']} (Score={h['score']}/100 | HealthyProb={h['probs']['Healthy']:.1f}% | HighRiskProb={h['probs']['High Risk']:.1f}%)\n"
        f"RSI(14)={p['rsi']:.1f} | 20-SMA={cur}{p['sma20']:,.2f} | 50-EMA={cur}{p['ema50']:,.2f} | MACD={p['macd_val']:+.2f} vs Sig={p['macd_sig']:+.2f} | BB%B={p['bb_pctb']:.2f}\n"
        f"VolRatio={p['vol_ratio']:.2f}x avg | ATR(14)={cur}{p['atr']:,.2f} | AnnVol={p['ann_vol']:.1f}%\n"
        f"52W={cur}{p['low52']:,.2f}-{cur}{p['high52']:,.2f} | Pivots: S2={cur}{p['s2']:,.2f}, S1={cur}{p['s1']:,.2f}, P={cur}{p['pivot']:,.2f}, R1={cur}{p['r1']:,.2f}, R2={cur}{p['r2']:,.2f}\n"
        f"7D ML Forecast ({p['ml_model']}, {p['ml_dir_acc']:.1f}% dir acc)={cur}{p['ml_pred_7d']:,.2f} ({p['ml_move_pct']:+.2f}%)\n"
        f"Fundamentals: {f_line} | Affordable CNC Qty={p['affordable_cnc']} | Quant Score={p['score']}/6 ({p['verdict']})"
        f"{news_line}"
    )


def ask_universal_ai_advisor(
    username: str,
    user_question: str,
    snapshots: dict,
    usdinr_rate: float,
    groq_api_key: str = "",
    gemini_api_key: str = "",
    allow_after_hours: bool = False,
    chat_history: list[dict] | None = None,
) -> tuple[str, str, str, str, list[str]]:
    q_clean = user_question.strip().lower()
    acct = get_user_account_summary(username, snapshots, usdinr_rate)
    matched_syms = detect_all_stocks_from_text(user_question, max_stocks=4)
    explicit_sym = matched_syms[0] if matched_syms else None
    was_explicit = len(matched_syms) > 0
    card_title = "FinanceSight Universal AI"
    card_logo = get_logo_url("GOOGL")
    steps_log = [f"Loaded account snapshot for @{username} (Cash: ₹{acct['balance']:,.2f})"]

    if any(w in q_clean for w in ["cancel", "undo", "reverse"]) and (
        any(w in q_clean for w in ["order", "trade", "last", "buy", "sell", "pending"])
        or q_clean in {"cancel", "cancel order", "cancel trade"}
    ):
        pend_match = re.search(r"#?(\d+)", q_clean)
        if "pending" in q_clean and pend_match:
            ok_c, msg_c = cancel_pending_order(username, int(pend_match.group(1)))
        else:
            ok_c, msg_c = reverse_last_executed_order(username, explicit_sym if was_explicit else None)
        steps_log.append(f"Order reversal processed: {'success' if ok_c else 'declined'}")
        updated = get_user_account_summary(username, snapshots, usdinr_rate)
        return (
            f"### Order Cancellation & Reversal\n* **Status:** {msg_c}\n* **Updated Cash Margin:** `₹{updated['balance']:,.2f}`\n\n#### Active Holdings\n{updated['holdings_md']}",
            "FinanceSight Order Manager", card_title, card_logo, steps_log,
        )

    if any(k in q_clean for k in ["square off", "close all position", "exit all position", "close position", "exit position"]):
        if acct["pos_df"].empty:
            return (
                f"### Position Square-Off Check\nNo open positions found. Available cash margin: **₹{acct['balance']:,.2f}**.",
                "FinanceSight Execution Engine", card_title, card_logo, steps_log,
            )
        closed_logs = []
        for _, r in acct["pos_df"].iterrows():
            sym = LEGACY_TICKER_REMAP.get(r["ticker"], r["ticker"])
            if was_explicit and sym not in matched_syms:
                continue
            ltp = float(snapshots.get(sym, {}).get("price", r["avg_price"]))
            _, msg = execute_trade(
                username, sym, "SELL", int(r["shares"]), ltp, r["product_type"],
                usdinr_rate=usdinr_rate, allow_after_hours=allow_after_hours,
            )
            closed_logs.append(f"- {msg}")
        new_bal = get_user_balance(username)
        steps_log.append(f"Processed {len(closed_logs)} square-off order(s)")
        return (
            "### Autonomous Square-Off Summary\n" + ("\n".join(closed_logs) or "- No matching open positions.") + f"\n\n* **Updated Margin:** `₹{new_bal:,.2f}`",
            "FinanceSight Execution Engine", card_title, card_logo, steps_log,
        )

    fund_match = re.search(r"\b(add|deposit|top up|withdraw)\b.*?(\d[\d,]*)", q_clean)
    if fund_match and any(w in q_clean for w in ["fund", "money", "cash", "margin", "wallet", "rupee", "rs", "inr", "deposit", "withdraw"]):
        verb = fund_match.group(1)
        amt = float(fund_match.group(2).replace(",", ""))
        tx_t = "WITHDRAW" if verb == "withdraw" else "DEPOSIT"
        _, msg_f = update_funds(username, amt, tx_t, "AI Advisor Instant Transfer", "AI-WALLET-TX")
        new_bal = get_user_balance(username)
        steps_log.append(f"Executed wallet {tx_t} of ₹{amt:,.2f}")
        return (
            f"### Wallet Transaction\n* **Status:** {msg_f}\n* **Updated Cash Margin:** **`₹{new_bal:,.2f}`**",
            "FinanceSight Wallet Engine", card_title, card_logo, steps_log,
        )

    if any(w in q_clean for w in ["calculate", "cost of", "margin for", "how much for", "brokerage for"]) and was_explicit and explicit_sym:
        qty_clean = re.sub(r"5x|20-sma|50-ema|14-day", "", q_clean)
        qty_nums = [int(n.replace(",", "")) for n in re.findall(r"\b(\d[\d,]*)\b", qty_clean)]
        calc_qty = max(1, qty_nums[0]) if qty_nums else 10
        meta = get_ticker_meta(explicit_sym)
        live_snaps = ensure_symbols_live([explicit_sym], snapshots)
        snap = live_snaps.get(explicit_sym, DEFAULT_STOCKS_SNAPSHOTS.get(explicit_sym, {"price": 100.0, "pct": 0.0}))
        price = float(snap["price"])
        fx = get_fx_rate_for_ticker(explicit_sym, usdinr_rate)
        inr_total = price * calc_qty * fx
        mis_margin_inr = inr_total * 0.20
        cnc_fees = compute_brokerage_breakdown("Equity Delivery (CNC)", price * fx, price * fx, calc_qty)
        mis_fees = compute_brokerage_breakdown("Equity Intraday (MIS)", price * fx, price * fx, calc_qty)
        steps_log.append(f"Calculated CNC & MIS breakdown for {calc_qty} {explicit_sym}")
        return (
            f"""### Trade & Margin Breakdown: {meta['name']} (`{explicit_sym}`)
* **Live Price:** `{meta['currency']}{price:,.2f}` (`{snap['pct']:+.2f}%`) | **FX Rate:** `₹{fx:.2f}`
* **CNC Delivery (1x) Margin:** **`₹{inr_total:,.2f}`** *(Est. round-trip statutory levies: `₹{cnc_fees['total_charges']:,.2f}`)*
* **MIS Intraday (5x) Margin:** **`₹{mis_margin_inr:,.2f}`** *(Brokerage + levies: `₹{mis_fees['total_charges']:,.2f}`)*
* **Max Buying Power (`₹{acct['balance']:,.2f}`):** `{int(acct['balance'] // (price * fx))}` CNC shares | `{int((acct['balance'] * 5) // (price * fx))}` MIS shares""",
            "FinanceSight Margin Calculator", f"{meta['name']} ({explicit_sym})", get_logo_url(explicit_sym), steps_log,
        )

    trade_cmd = parse_trade_command(user_question)
    if trade_cmd is not None:
        if not trade_cmd["ticker"]:
            return (
                "### Specify Stock Ticker\nInclude a recognized stock name and quantity, e.g. `Buy 5 Reliance` or `Buy 2 Apple`.",
                "FinanceSight Order Assistant", card_title, card_logo, steps_log,
            )
        sym = trade_cmd["ticker"]
        meta = get_ticker_meta(sym)
        live_snaps = ensure_symbols_live([sym], snapshots)
        live_p = float(live_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0})).get("price", 100.0))
        o_type = "LIMIT" if trade_cmd["limit_price"] is not None else "MARKET"
        _, msg_t = execute_trade(
            username, sym, trade_cmd["action"], trade_cmd["qty"], live_p, trade_cmd["product"],
            order_type=o_type, limit_price=trade_cmd["limit_price"],
            usdinr_rate=usdinr_rate, allow_after_hours=allow_after_hours,
        )
        steps_log.append(f"Trade engine response: {msg_t}")
        updated = get_user_account_summary(username, snapshots, usdinr_rate)
        return (
            f"### Order Execution Receipt\n* **Command:** *\"{user_question}\"*\n* **Result:** **{msg_t}**\n* **Updated Cash Margin:** **`₹{updated['balance']:,.2f}`**\n\n#### Active Holdings\n{updated['holdings_md']}",
            "FinanceSight Autonomous Order Engine", f"{meta['name']} ({sym})", get_logo_url(sym), steps_log,
        )

    auto_cmd = parse_auto_invest_command(user_question)
    if auto_cmd is not None:
        _, report_md, title_auto, logo_auto, auto_steps = execute_ai_auto_pick_trade(
            username,
            snapshots,
            usdinr_rate,
            market=auto_cmd["market"],
            sector_hint=auto_cmd["sector_hint"],
            budget_inr=auto_cmd["budget_inr"],
            explicit_qty=auto_cmd["qty"],
            product=auto_cmd["product"],
            allow_after_hours=allow_after_hours,
        )
        return report_md, "FinanceSight AI Auto-Pilot", title_auto, logo_auto, steps_log + auto_steps

    if any(k in q_clean for k in ["audit portfolio", "audit my portfolio", "portfolio risk", "portfolio health", "diversification", "rebalance", "book profit", "auto profit", "what to sell"]):
        do_reb = any(w in q_clean for w in ["rebalance", "book profit", "take profit automatically", "auto profit", "exit overbought"]) and "?" not in q_clean
        audit_md, audit_steps = build_portfolio_risk_audit(
            username, snapshots, usdinr_rate, auto_rebalance=do_reb, allow_after_hours=allow_after_hours
        )
        return audit_md, "FinanceSight Portfolio Risk Engine", "Portfolio Risk & Diversification Audit", card_logo, steps_log + audit_steps

    is_simple_portfolio_lookup = any(
        p in q_clean
        for p in ["my fund", "my balance", "my margin", "my wallet", "how much money", "my portfolio", "my holding", "my position", "my order", "account summary", "show portfolio"]
    ) and not any(w in q_clean for w in ["compare", "suggest", "recommend", "diversif", "better", "against", "optimize"])
    if is_simple_portfolio_lookup:
        steps_log.append("Compiled SQLite holdings, positions, and order book")
        return (
            f"""### Live Account & Portfolio Summary (`@{username}`)
* **Available Cash Margin:** **`₹{acct['balance']:,.2f}`**
* **Live Holdings Value:** **`₹{acct['tot_cur']:,.2f}`** *(Cost: `₹{acct['tot_inv']:,.2f}` | Unrealized P&L: `₹{acct['tot_pnl']:+,.2f}`)*
* **Open Positions M2M P&L:** **`₹{acct['tot_m2m']:+,.2f}`**
* **Total Account Net Worth:** **`₹{acct['balance'] + acct['tot_cur']:,.2f}`**

#### Active CNC Holdings
{acct['holdings_md']}

#### Open Positions
{acct['positions_md']}

#### Recent Orders
{acct['orders_md']}""",
            "FinanceSight SQLite Inspector", card_title, card_logo, steps_log,
        )

    if is_market_timing_question(q_clean):
        steps_log.append("Checked NSE (IST) & US (ET) market schedules")
        return build_market_timings_report(), "FinanceSight Schedule Engine", card_title, card_logo, steps_log

    if not was_explicit and is_explicit_screener_request(q_clean):
        full_snaps = ensure_symbols_live(list(STOCK_CATALOG.keys())[:48], snapshots)
        steps_log.append(f"Ranked {len(STOCK_CATALOG)} NSE & US equities by momentum, SMA-20 & RSI")
        top_feed = []
        for sym, meta in list(STOCK_CATALOG.items())[:40]:
            sn = full_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0}))
            top_feed.append(f"{sym} ({meta['name']}, {meta['exchange']}): {meta['currency']}{sn['price']:,.2f} ({sn['pct']:+.2f}%, RSI {sn['rsi']:.1f})")
        sys_msg = "You are FinanceSight AI. Recommend top benefitting stocks from the live feed with prices, RSI, entry, stop-loss, and targets."
        usr_msg = f"USER MARGIN: ₹{acct['balance']:,.2f} (FX ₹{usdinr_rate:.2f}/$)\nFEED:\n" + "\n".join(top_feed) + f"\nQUESTION: {user_question}"
        llm_reply, llm_badge, _ = call_groq_llm_live(sys_msg, usr_msg, groq_api_key, chat_history)
        if not llm_reply and gemini_api_key:
            llm_reply, llm_badge = call_gemini_llm_live(sys_msg, usr_msg, gemini_api_key, chat_history)
        if llm_reply:
            return llm_reply, llm_badge, "Universal Market Screener", get_logo_url("RELIANCE.NS"), steps_log
        return (
            build_universal_stocks_screener_report(user_question, acct["balance"], full_snaps, usdinr_rate),
            "FinanceSight Quant Screener", "Universal Market Screener", get_logo_url("RELIANCE.NS"), steps_log,
        )

    if was_explicit:
        want_news = any(w in q_clean for w in ["news", "headline", "why", "catalyst", "latest", "today", "earning", "update", "reason"])
        profiles = []
        for sym in matched_syms:
            p = build_stock_quant_profile(sym, snapshots, usdinr_rate, acct["balance"], include_news=want_news)
            profiles.append(p)
        steps_log.append(f"Computed multi-timeframe technicals, pivots, ML forecast & fundamentals for {', '.join(matched_syms)}")
        if want_news and any(p["news"] for p in profiles):
            steps_log.append("Fetched latest market news headlines")

        context_blocks = "\n\n".join(_format_stock_context_for_llm(p) for p in profiles)
        sys_stock = (
            "You are FinanceSight AI, an institutional quantitative market analyst. "
            "Give direct, crisp, data-backed answers using ONLY the verified metrics, pivot levels, multi-timeframe returns, fundamentals, and ML outputs provided. "
            "Include clear Entry/Support/Resistance/Stop-Loss levels and position sizing for the user's margin when relevant."
        )
        usr_stock = f"USER MARGIN: ₹{acct['balance']:,.2f} | FX: ₹{usdinr_rate:.2f}/$\n\n{context_blocks}\n\nUSER QUESTION: {user_question}"

        llm_reply, llm_badge, _ = call_groq_llm_live(sys_stock, usr_stock, groq_api_key, chat_history)
        if not llm_reply and gemini_api_key:
            llm_reply, llm_badge = call_gemini_llm_live(sys_stock, usr_stock, gemini_api_key, chat_history)

        primary = profiles[0]
        title_str = " vs ".join(f"{p['meta']['name']} ({p['sym']})" for p in profiles[:2])
        logo_url = get_logo_url(primary["sym"])
        if llm_reply:
            return llm_reply, llm_badge, title_str, logo_url, steps_log

        if len(profiles) >= 2:
            rows = []
            for p in profiles:
                c = p["cur"]
                rows.append(
                    f"| **{p['meta']['name']}** (`{p['sym']}`) | `{c}{p['price']:,.2f}` (`{p['pct_1d']:+.2f}%`) | "
                    f"`{p['pct_1m']:+.2f}%` | `{p['pct_1y']:+.2f}%` | `{p['rsi']:.1f}` | "
                    f"`{c}{p['ml_pred_7d']:,.2f}` (`{p['ml_move_pct']:+.2f}%`) | **{p['verdict']}** |"
                )
            winner = max(profiles, key=lambda x: (x["score"], x["pct_1m"]))
            return (
                f"""### Multi-Stock Quantitative Comparison
| Company | Spot Price (1D) | 1M Return | 1Y Return | RSI (14) | 7D ML Target | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(rows)}

* **Quantitative Leader:** **{winner['meta']['name']} (`{winner['sym']}`)** leads with a technical score of **`{winner['score']}/6`**, Support S1 `{winner['cur']}{winner['s1']:,.2f}`, and Resistance R1 `{winner['cur']}{winner['r1']:,.2f}`.""",
                "FinanceSight Quant Comparator", title_str, logo_url, steps_log,
            )

        p = primary
        c = p["cur"]
        safe_qty = max(1, int((acct["balance"] * 0.20) // (p["price"] * p["fx"]))) if p["price"] > 0 else 0
        pe_txt = f"{p['funds']['trailingPE']:.2f}" if p["funds"].get("trailingPE") else "N/A"
        mc_txt = format_large_number(p["funds"].get("marketCap"), c)
        news_md = ""
        if p["news"]:
            news_md = "\n\n#### Latest News Catalysts\n" + "\n".join(f"- [{n['title']}]({n['link']}) *({n['pubDate']})*" for n in p["news"])

        return (
            f"""### Institutional Stock Intelligence: {p['meta']['name']} (`{p['sym']}`)
* **Spot Quote:** `{c}{p['price']:,.2f}` (`1D {p['pct_1d']:+.2f}%` | `1W {p['pct_1w']:+.2f}%` | `1M {p['pct_1m']:+.2f}%` | `1Y {p['pct_1y']:+.2f}%`)
* **Quantitative Verdict (`{p['score']}/6`):** **{p['verdict']}**
  * **Trend:** `{((p['price'] - p['sma20'])/p['sma20'])*100:+.2f}%` vs 20-SMA (`{c}{p['sma20']:,.2f}`) | 50-EMA (`{c}{p['ema50']:,.2f}`) | Volume `{p['vol_ratio']:.2f}x` 20D avg
  * **Momentum & Risk:** Wilder RSI-14 `{p['rsi']:.1f}` | MACD `{p['macd_val']:+.2f}` | Ann. Volatility `{p['ann_vol']:.1f}%` | Market Cap `{mc_txt}` | P/E `{pe_txt}`
  * **7-Day ML Forecast (`{p['ml_model']}`):** `{c}{p['ml_pred_7d']:,.2f}` (`{p['ml_move_pct']:+.2f}%` | Dir. Accuracy `{p['ml_dir_acc']:.1f}%`)
* **Pivot & Trade Levels (`₹{acct['balance']:,.2f}` Available):**
  * **Supports:** S1 `{c}{p['s1']:,.2f}` | S2 `{c}{p['s2']:,.2f}` &nbsp;•&nbsp; **Resistances:** R1 `{c}{p['r1']:,.2f}` | R2 `{c}{p['r2']:,.2f}`
  * **Suggested Stop-Loss (1.5× ATR):** `{c}{max(0.01, p['price'] - 1.5*p['atr']):,.2f}` | **Target (2× ATR):** `{c}{p['price'] + 2.0*p['atr']:,.2f}`
  * **Position Sizing (20% Cash):** `{safe_qty} shares` *(Max affordable CNC: `{p['affordable_cnc']}` shares)*{news_md}""",
            f"FinanceSight Quant Engine ({p['sym']})", title_str, logo_url, steps_log,
        )

    math_expr, math_ans = try_solve_math_query(user_question)
    if math_expr is not None and math_ans is not None:
        steps_log.append("Evaluated expression with safe AST solver")
        fmt = f"{math_ans:,.4f}".rstrip("0").rstrip(".") if isinstance(math_ans, float) else f"{math_ans:,}"
        return f"### Calculation Result\n`{math_expr}` = **`{fmt}`**", "FinanceSight Math Engine", card_title, card_logo, steps_log

    if groq_api_key.startswith("gsk_"):
        ag_reply, ag_badge, ag_title, ag_logo, ag_steps, err_code = call_groq_agentic_loop(
            user_question, username, snapshots, usdinr_rate, groq_api_key,
            allow_after_hours=allow_after_hours, chat_history=chat_history,
        )
        if ag_reply:
            return ag_reply, ag_badge, ag_title, ag_logo, steps_log + ag_steps
    else:
        err_code = "missing_key"

    sys_gen = "You are FinanceSight AI, an accurate financial and general assistant. Answer clearly and concisely."
    usr_gen = f"Current Time: {get_ist_now().strftime('%A, %d %B %Y %I:%M %p IST')}\nUser Cash: ₹{acct['balance']:,.2f}\nQuestion: {user_question}"
    llm_reply, llm_badge, err_code = call_groq_llm_live(sys_gen, usr_gen, groq_api_key, chat_history)
    if not llm_reply and gemini_api_key:
        llm_reply, llm_badge = call_gemini_llm_live(sys_gen, usr_gen, gemini_api_key, chat_history)
    if llm_reply:
        steps_log.append(f"Generated response via {llm_badge}")
        return llm_reply, llm_badge, card_title, card_logo, steps_log

    glossary = {
        "rsi": "**RSI (Relative Strength Index)** measures momentum on a 0–100 scale using Wilder's 14-day smoothing. Above 70 suggests overbought conditions; below 30 suggests oversold conditions.",
        "sma": "**SMA (Simple Moving Average)** is the arithmetic mean of closing prices over N periods (e.g. 20-day SMA).",
        "ema": "**EMA (Exponential Moving Average)** applies exponentially higher weight to recent prices for faster trend sensitivity.",
        "macd": "**MACD (Moving Average Convergence Divergence)** compares 12-day and 26-day EMAs against a 9-day signal line to spot trend shifts.",
        "bollinger": "**Bollinger Bands** plot a 20-day SMA with ±2 standard deviation bands to gauge volatility expansion and mean reversion.",
        "sharpe": "**Sharpe Ratio** measures risk-adjusted return (annualized excess return divided by return volatility).",
        "intraday": "**MIS (Margin Intraday Square-off)** provides 5× leverage for same-day trades settled before market close.",
        "delivery": "**CNC (Cash & Carry)** is 1× margin equity delivery held across days in your Demat portfolio.",
    }
    for kw, desc in glossary.items():
        if re.search(rf"\b{re.escape(kw)}\b", q_clean):
            steps_log.append(f"Matched quantitative glossary ({kw.upper()})")
            return f"### FinanceSight Knowledge Base\n{desc}", "FinanceSight Quant KB", card_title, card_logo, steps_log

    key_hint = (
        "\n\n*Tip: Add your `GROQ_API_KEY` or `GEMINI_API_KEY` in the sidebar API Settings (or Streamlit Cloud Secrets) for full conversational LLM answers on open-ended questions.*"
        if err_code in {"missing_key", "invalid_key"}
        else ""
    )
    return (
        f"### FinanceSight Assistant\n"
        f"Your account has **`₹{acct['balance']:,.2f}`** cash margin and **`₹{acct['tot_cur']:,.2f}`** in holdings.\n\n"
        f"Try asking:\n"
        f"- *\"Analyze Reliance Industries\"* or *\"Compare TCS vs Infosys\"*\n"
        f"- *\"Latest news on NVDA\"* or *\"List top benefitting Indian NSE stocks\"*\n"
        f"- *\"Calculate margin for 10 AAPL\"* or *\"Buy 5 TCS\"*{key_hint}",
        "FinanceSight Quant Engine", card_title, card_logo, steps_log,
    )


def render_ticker_marquee(snapshots: dict, idx_snaps: dict, usdinr: float) -> None:
    fx_sn = idx_snaps.get("USDINR=X", {"pct": 0.0})
    fx_clr = "#10b981" if fx_sn.get("pct", 0.0) >= 0 else "#ef4444"
    parts = [
        f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 16px;font-family:JetBrains Mono,monospace;font-size:0.82rem;">'
        f'<span style="background:rgba(37,99,235,0.18);color:#60a5fa;border-radius:5px;padding:1px 6px;font-weight:700;font-size:0.72rem;">FX</span>'
        f'<b>USD/INR</b> ₹{usdinr:.2f} <span style="color:{fx_clr};font-weight:700;">{fx_sn.get("pct", 0.0):+.2f}%</span></span>'
    ]
    for sym, meta in MARKET_INDICES.items():
        sn = idx_snaps.get(sym, {"price": 0.0, "pct": 0.0})
        clr = "#10b981" if sn["pct"] >= 0 else "#ef4444"
        arr = "▲" if sn["pct"] >= 0 else "▼"
        parts.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 16px;font-family:JetBrains Mono,monospace;font-size:0.82rem;">'
            f'<b>{meta["name"]}</b> {sn["price"]:,.2f} <span style="color:{clr};font-weight:700;">{arr} {sn["pct"]:+.2f}%</span></span>'
        )
    for sym in CORE_TICKERS[:14]:
        sn = snapshots.get(sym, {"price": 0.0, "pct": 0.0})
        cur = get_ticker_meta(sym)["currency"]
        clr = "#10b981" if sn["pct"] >= 0 else "#ef4444"
        arr = "▲" if sn["pct"] >= 0 else "▼"
        parts.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 16px;font-family:JetBrains Mono,monospace;font-size:0.82rem;">'
            f'{stock_icon_html(sym, size=18, radius=5)}'
            f'<b>{sym.replace(".NS", "")}</b> {cur}{sn["price"]:,.2f} <span style="color:{clr};font-weight:700;">{arr} {sn["pct"]:+.2f}%</span></span>'
        )
    row = "".join(parts)
    st.html(
        f"""
        <style>
        @keyframes fsMarquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
        .fs-marquee-box {{
            width: 100%; overflow: hidden; white-space: nowrap;
            background: var(--secondary-background-color);
            color: var(--text-color);
            border: 1px solid rgba(128,128,128,0.24);
            border-radius: 10px; padding: 8px 0; margin-bottom: 12px;
        }}
        .fs-marquee-track {{ display: inline-flex; align-items: center; animation: fsMarquee 42s linear infinite; }}
        .fs-marquee-box:hover .fs-marquee-track {{ animation-play-state: paused; }}
        </style>
        <div class="fs-marquee-box"><div class="fs-marquee-track">{row}{row}</div></div>
        """
    )


def render_indices_row(idx_snaps: dict, usdinr: float) -> None:
    cols = st.columns(5)
    for i, (sym, meta) in enumerate(MARKET_INDICES.items()):
        sn = idx_snaps.get(sym, {"price": 0.0, "pct": 0.0, "sparkline": []})
        cols[i].metric(
            label=meta["name"],
            value=f"{sn['price']:,.2f}",
            delta=f"{sn['pct']:+.2f}%",
            chart_data=sn.get("sparkline") or None,
            chart_type="area",
            border=True,
            height="stretch",
        )
    fx_sn = idx_snaps.get("USDINR=X", DEFAULT_INDEX_SNAPSHOTS["USDINR=X"])
    cols[4].metric(
        label="USD / INR FX",
        value=f"₹{usdinr:.2f}",
        delta=f"{fx_sn.get('pct', 0.0):+.2f}% 1D",
        chart_data=fx_sn.get("sparkline") or None,
        chart_type="area",
        border=True,
        height="stretch",
    )


def render_brokerage_calculator_widget(key_prefix: str = "calc") -> None:
    st.subheader("Brokerage, STT & Statutory Charges Calculator", icon=":material/calculate:")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        seg = c1.selectbox(
            "Segment",
            ["Equity Delivery (CNC)", "Equity Intraday (MIS)", "F&O Futures"],
            key=f"{key_prefix}_seg",
        )
        buy_p = c2.number_input("Buy Price (₹)", min_value=1.0, value=1500.0, step=10.0, key=f"{key_prefix}_bp")
        sell_p = c3.number_input("Sell Price (₹)", min_value=1.0, value=1545.0, step=10.0, key=f"{key_prefix}_sp")
        qty = c4.number_input("Quantity (Shares)", min_value=1, max_value=100000, value=100, step=10, key=f"{key_prefix}_qty")

    res = compute_brokerage_breakdown(seg, buy_p, sell_p, int(qty))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Turnover", f"₹{res['turnover']:,.2f}", f"Brokerage: ₹{res['brokerage']:.2f}", delta_color="off", border=True, height="stretch")
    m2.metric("Total Taxes & Charges", f"₹{res['total_charges']:,.2f}", f"STT ₹{res['stt']:.2f} | GST ₹{res['gst']:.2f}", delta_color="off", border=True, height="stretch")
    m3.metric("Breakeven / Share", f"₹{res['breakeven_pts']:.2f}", "Points to cover fees", delta_color="off", border=True, height="stretch")
    m4.metric("Net P&L", f"₹{res['net_pnl']:,.2f}", f"Gross: ₹{res['gross_pnl']:+.2f}", border=True, height="stretch")

    st.table(
        {
            "Brokerage": f"₹{res['brokerage']:,.2f}",
            "STT (Securities Transaction Tax)": f"₹{res['stt']:,.2f}",
            "Exchange Transaction Charge": f"₹{res['exch_txn']:,.2f}",
            "SEBI Turnover Fee": f"₹{res['sebi_fee']:,.2f}",
            "Stamp Duty": f"₹{res['stamp_duty']:,.2f}",
            "GST (18% on Brokerage + Txn + SEBI)": f"₹{res['gst']:,.2f}",
            "**Total Charges**": f"**₹{res['total_charges']:,.2f}**",
        },
        border="horizontal",
        width="content",
    )


def render_public_footer() -> None:
    pub_pages = st.session_state.get("_pub_page_map", {})
    st.space("medium")
    with st.container(border=True):
        c_brand, c_plat, c_supp, c_acct = st.columns([1.45, 1.0, 1.0, 1.0], gap="medium")

        with c_brand:
            st.html(
                f"""
                <div style="margin-bottom:8px;">{FINANCESIGHT_LOGO_SVG}</div>
                <p style="font-size:0.82rem;opacity:0.82;line-height:1.55;margin:6px 0 12px 0;">
                    © 2026 FinanceSight.<br>
                    All rights reserved.<br>
                    Market Analytics, AI Forecasting &amp; Paper Trading Platform
                </p>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                    <a href="https://x.com" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;border:1px solid rgba(128,128,128,0.3);color:inherit;text-decoration:none;font-size:0.76rem;font-weight:600;">
                        <img src="https://www.google.com/s2/favicons?domain=x.com&sz=32" width="14" height="14" style="border-radius:3px;"> X
                    </a>
                    <a href="https://www.linkedin.com" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;border:1px solid rgba(128,128,128,0.3);color:inherit;text-decoration:none;font-size:0.76rem;font-weight:600;">
                        <img src="https://www.google.com/s2/favicons?domain=linkedin.com&sz=32" width="14" height="14" style="border-radius:3px;"> LinkedIn
                    </a>
                    <a href="https://www.facebook.com" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;border:1px solid rgba(128,128,128,0.3);color:inherit;text-decoration:none;font-size:0.76rem;font-weight:600;">
                        <img src="https://www.google.com/s2/favicons?domain=facebook.com&sz=32" width="14" height="14" style="border-radius:3px;"> Facebook
                    </a>
                    <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;border:1px solid rgba(128,128,128,0.3);color:inherit;text-decoration:none;font-size:0.76rem;font-weight:600;">
                        <img src="https://www.google.com/s2/favicons?domain=instagram.com&sz=32" width="14" height="14" style="border-radius:3px;"> Instagram
                    </a>
                    <a href="https://www.youtube.com" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;border:1px solid rgba(128,128,128,0.3);color:inherit;text-decoration:none;font-size:0.76rem;font-weight:600;">
                        <img src="https://www.google.com/s2/favicons?domain=youtube.com&sz=32" width="14" height="14" style="border-radius:3px;"> YouTube
                    </a>
                    <a href="https://telegram.org" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;border:1px solid rgba(128,128,128,0.3);color:inherit;text-decoration:none;font-size:0.76rem;font-weight:600;">
                        <img src="https://www.google.com/s2/favicons?domain=telegram.org&sz=32" width="14" height="14" style="border-radius:3px;"> Telegram
                    </a>
                </div>
                """
            )

        with c_plat:
            st.markdown("**Platform**")
            if "home" in pub_pages:
                st.page_link(pub_pages["home"], label="Home")
            if "about" in pub_pages:
                st.page_link(pub_pages["about"], label="About")
            if "products" in pub_pages:
                st.page_link(pub_pages["products"], label="Products & Tools")
            if "fees" in pub_pages:
                st.page_link(pub_pages["fees"], label="Fee & Tax Calculator")
            if st.button("SuperChart Terminal", type="tertiary", key="ftr_term"):
                st.toast("Click '1-Click Demo Login' above to open SuperChart Terminal.", icon=":material/lock_open:")
            if st.button("AI Stock Advisor", type="tertiary", key="ftr_ai"):
                st.toast("Click '1-Click Demo Login' above to open AI Stock Advisor.", icon=":material/lock_open:")

        with c_supp:
            st.markdown("**Support & Resources**")
            if "support" in pub_pages:
                st.page_link(pub_pages["support"], label="Contact us")
                st.page_link(pub_pages["support"], label="Support portal")
            if "fees" in pub_pages:
                st.page_link(pub_pages["fees"], label="Brokerage & tax breakdown")
            if st.button("Order book CSV export", type="tertiary", key="ftr_ord"):
                st.toast("Sign in to export your Tradebook CSV.", icon=":material/lock_open:")
            st.markdown("[Video tutorials](https://www.youtube.com)")
            if "home" in pub_pages:
                st.page_link(pub_pages["home"], label="Live market overview")

        with c_acct:
            st.markdown("**Account & Simulation**")
            if "home" in pub_pages:
                st.page_link(pub_pages["home"], label="Open an account")
            for lbl, fkey in [
                ("Fund transfer (Virtual Wallet)", "ftr_funds"),
                ("Portfolio holdings", "ftr_hold"),
                ("Intraday & delivery positions", "ftr_pos"),
                ("FinanceSight Algo Backtester", "ftr_algo"),
            ]:
                if st.button(lbl, type="tertiary", key=fkey):
                    st.toast(f"Sign in on Home (or use Demo Login) to access {lbl}.", icon=":material/lock_open:")

        st.divider()
        st.caption(
            "FinanceSight is a market analysis, machine learning price forecasting, and paper trading simulation platform covering global equities. "
            "Live and historical market data is fetched via the Yahoo Finance API for educational and analytical use. "
            "Stock market investments involve market risk; past backtest performance and ML projections do not guarantee future returns."
        )
        st.markdown(
            "[NSE](https://www.nseindia.com) · [BSE](https://www.bseindia.com) · [MCX](https://www.mcxindia.com) · "
            "About Platform · Fee Calculator · Help & Support",
            text_alignment="center",
        )


def get_market_context():
    return st.session_state["_mkt_snaps"], st.session_state["_idx_snaps"], st.session_state["_usdinr"], st.session_state["_is_live"], st.session_state["_mkt_stamp"]


def _hero_spotlight_html(snaps: dict, is_live: bool, stamp: str) -> str:
    total_count = len(STOCK_CATALOG)
    nse_count = sum(1 for v in STOCK_CATALOG.values() if v["exchange"] == "NSE")
    us_count = total_count - nse_count
    dot_clr = "#10b981" if is_live else "#f59e0b"
    status_txt = f"Live Yahoo Finance · {stamp}" if is_live else stamp

    showcase_syms = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ETERNAL.NS",
        "HAL.NS", "SBIN.NS", "AAPL", "NVDA",
        "TSLA", "MSFT", "GOOGL", "AMZN",
    ]
    tiles = []
    for sym in showcase_syms:
        meta = get_ticker_meta(sym)
        sn = snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 0.0, "pct": 0.0}))
        pct = float(sn.get("pct", 0.0))
        mv_clr = "#10b981" if pct >= 0 else "#ef4444"
        mv_bg = "rgba(16,185,129,0.14)" if pct >= 0 else "rgba(239,68,68,0.14)"
        short_sym = html.escape(sym.replace(".NS", ""))
        tiles.append(
            f'<div class="fs-tile">'
            f'<div class="fs-tile-top">{stock_icon_html(sym, size=26, radius=7)}'
            f'<div><div class="fs-tile-sym">{short_sym}</div>'
            f'<div class="fs-tile-ex">{meta["exchange"]}</div></div></div>'
            f'<div class="fs-tile-btm">'
            f'<span class="fs-tile-pr">{meta["currency"]}{sn["price"]:,.2f}</span>'
            f'<span class="fs-tile-pct" style="color:{mv_clr};background:{mv_bg};">{pct:+.2f}%</span>'
            f'</div></div>'
        )

    return f"""
    <style>
    .fs-hero {{
        display: grid;
        grid-template-columns: 1.15fr 1.25fr;
        gap: 22px;
        align-items: center;
        padding: 24px 26px;
        margin-bottom: 14px;
        border-radius: 16px;
        border: 1px solid rgba(59,130,246,0.28);
        background:
            radial-gradient(circle at 12% 18%, rgba(37,99,235,0.18), transparent 46%),
            radial-gradient(circle at 88% 82%, rgba(16,185,129,0.14), transparent 46%),
            var(--secondary-background-color);
        color: var(--text-color);
    }}
    @media (max-width: 960px) {{
        .fs-hero {{ grid-template-columns: 1fr; padding: 18px; }}
    }}
    .fs-live-pill {{
        display: inline-flex; align-items: center; gap: 8px;
        padding: 5px 12px; border-radius: 999px;
        font-size: 0.78rem; font-weight: 600;
        background: rgba(16,185,129,0.12);
        border: 1px solid rgba(16,185,129,0.32);
        margin-bottom: 12px;
    }}
    .fs-dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {dot_clr}; box-shadow: 0 0 8px {dot_clr};
    }}
    .fs-hero-title {{
        font-size: 2.15rem; font-weight: 800; line-height: 1.15;
        margin: 0 0 10px 0; letter-spacing: -0.02em;
    }}
    .fs-hero-grad {{
        background: linear-gradient(90deg, #3b82f6, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .fs-hero-sub {{
        font-size: 0.96rem; opacity: 0.85; line-height: 1.5; margin: 0 0 16px 0;
    }}
    .fs-kpis {{
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
    }}
    .fs-kpi-pill {{
        background: rgba(128,128,128,0.08);
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 10px; padding: 10px 12px;
    }}
    .fs-kpi-num {{ font-size: 1.08rem; font-weight: 800; font-family: JetBrains Mono, monospace; }}
    .fs-kpi-lbl {{ font-size: 0.75rem; opacity: 0.75; margin-top: 2px; }}
    .fs-mosaic {{
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px;
    }}
    @media (max-width: 640px) {{
        .fs-mosaic {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    .fs-tile {{
        background: rgba(128,128,128,0.07);
        border: 1px solid rgba(128,128,128,0.20);
        border-radius: 11px; padding: 9px 10px;
    }}
    .fs-tile-top {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
    .fs-tile-sym {{ font-size: 0.80rem; font-weight: 700; line-height: 1.1; }}
    .fs-tile-ex {{ font-size: 0.67rem; opacity: 0.68; }}
    .fs-tile-btm {{ display: flex; align-items: center; justify-content: space-between; gap: 4px; }}
    .fs-tile-pr {{ font-size: 0.78rem; font-weight: 700; font-family: JetBrains Mono, monospace; }}
    .fs-tile-pct {{ font-size: 0.70rem; font-weight: 700; padding: 1px 6px; border-radius: 5px; font-family: JetBrains Mono, monospace; }}
    </style>
    <div class="fs-hero">
      <div>
        <div class="fs-live-pill"><span class="fs-dot"></span><span>{html.escape(status_txt)}</span></div>
        <h1 class="fs-hero-title">Finance<span class="fs-hero-grad">Sight</span></h1>
        <p class="fs-hero-sub">
          Institutional quant terminal across <b>{total_count} NSE &amp; US equities</b> — combining live technical charts,
          chronological 80/20 ML price forecasting, Groq/Gemini AI advisory, and multi-currency paper trading.
        </p>
        <div class="fs-kpis">
          <div class="fs-kpi-pill"><div class="fs-kpi-num">{total_count}+ Stocks</div><div class="fs-kpi-lbl">{nse_count} NSE · {us_count} US</div></div>
          <div class="fs-kpi-pill"><div class="fs-kpi-num">₹1,00,000</div><div class="fs-kpi-lbl">Demo Paper Margin</div></div>
          <div class="fs-kpi-pill"><div class="fs-kpi-num">3-Model ML</div><div class="fs-kpi-lbl">Zero Look-Ahead</div></div>
        </div>
      </div>
      <div class="fs-mosaic">{''.join(tiles)}</div>
    </div>
    """


def page_public_home() -> None:
    snaps, idx_snaps, usdinr, is_live, stamp = get_market_context()
    render_ticker_marquee(snaps, idx_snaps, usdinr)

    st.html(_hero_spotlight_html(snaps, is_live, stamp))
    render_indices_row(idx_snaps, usdinr)
    st.space("small")

    left_col, right_col = st.columns([1.58, 1.0], gap="large")
    with left_col:
        with st.container(border=True):
            mh_l, mh_r = st.columns([1.4, 1.3], vertical_alignment="center")
            mh_l.subheader(f"Live Market Movers ({len(STOCK_CATALOG)} Stocks)", icon=":material/trending_up:")
            home_mkt = mh_r.segmented_control(
                "Market View",
                ["Flagship Movers", "NSE Leaders", "US Leaders"],
                default="Flagship Movers",
                key="home_movers_tab",
                label_visibility="collapsed",
            ) or "Flagship Movers"

            if home_mkt == "NSE Leaders":
                home_syms = [k for k, v in STOCK_CATALOG.items() if v["exchange"] == "NSE"][:18]
            elif home_mkt == "US Leaders":
                home_syms = [k for k, v in STOCK_CATALOG.items() if v["exchange"] != "NSE"][:18]
            else:
                home_syms = list(CORE_TICKERS)

            view_snaps = ensure_symbols_live(home_syms, snaps)
            movers = []
            for sym in home_syms:
                meta = get_ticker_meta(sym)
                sn = view_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 0.0, "pct": 0.0, "rsi": 50.0, "sparkline": []}))
                movers.append(
                    {
                        "Logo": get_logo_url(sym),
                        "Ticker": sym,
                        "Company": meta["name"],
                        "Exchange": meta["exchange"],
                        "Price": f"{meta['currency']}{sn['price']:,.2f}",
                        "Change (%)": round(sn["pct"], 2),
                        "RSI (14)": round(sn["rsi"], 1),
                        "20D Trend": sn.get("sparkline", []),
                    }
                )
            mov_df = pd.DataFrame(movers).sort_values("Change (%)", ascending=False)
            top_movers = pd.concat([mov_df.head(5), mov_df.tail(5)]).drop_duplicates(subset=["Ticker"])
            st.dataframe(
                top_movers,
                column_config={
                    "Logo": st.column_config.ImageColumn("", width="small"),
                    "Change (%)": st.column_config.NumberColumn("Day %", format="%.2f%%"),
                    "20D Trend": st.column_config.LineChartColumn("20D Trend"),
                },
                hide_index=True,
                alt="Top gaining and declining stocks with company logos across NSE and US markets",
            )

            sec_rows = [
                {"Sector": get_ticker_meta(sym)["sector"], "Change": view_snaps.get(sym, {}).get("pct", 0.0)}
                for sym in home_syms
            ]
            sec_df = pd.DataFrame(sec_rows).groupby("Sector", as_index=False)["Change"].mean().sort_values("Change", ascending=False)
            sec_chart = (
                alt.Chart(sec_df)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X("Change:Q", title="Avg Day Move (%)"),
                    y=alt.Y("Sector:N", sort="-x", title=None),
                    color=alt.condition(alt.datum.Change >= 0, alt.value("#10b981"), alt.value("#ef4444")),
                    tooltip=["Sector", alt.Tooltip("Change:Q", format=".2f")],
                )
                .properties(height=215, title="Live Sector Momentum Snapshot")
            )
            st.altair_chart(sec_chart, alt="Average daily percentage move by market sector")

    with right_col:
        with st.container(border=True):
            st.subheader("Sign In or Open Free Account", icon=":material/login:")
            st.caption(f"Start with a **₹1,00,000** paper wallet across **{len(STOCK_CATALOG)} NSE & US equities**.")
            st.markdown(":green-badge[₹0 Delivery Fees] :blue-badge[5x Intraday MIS] :violet-badge[AI + ML Terminal]")
            st.space("small")
            if st.button("1-Click Demo Login (Trader_XYZ)", type="primary", icon=":material/bolt:", width="stretch"):
                st.session_state.logged_in = True
                st.session_state.username = "Trader_XYZ"
                st.session_state.full_name = "Trader_XYZ"
                st.rerun()

            tab_login, tab_signup = st.tabs(["Sign In", "Create Free Account"])
            with tab_login:
                with st.form("login_form", border=False):
                    u_in = st.text_input("User ID", value="Trader_XYZ")
                    p_in = st.text_input("Password", type="password", value="demo123")
                    if st.form_submit_button("Login to Workspace", type="primary", width="stretch"):
                        ok, db_u, db_n = authenticate_user(u_in, p_in)
                        if ok and db_u:
                            st.session_state.logged_in = True
                            st.session_state.username = db_u
                            st.session_state.full_name = db_n or db_u
                            st.rerun()
                        else:
                            st.error("Invalid User ID or Password.")

            with tab_signup:
                with st.form("signup_form", border=False):
                    su_name = st.text_input("Full Name", placeholder="e.g., Vishal Babu")
                    su_user = st.text_input("Choose User ID", placeholder="e.g., Vishal_01")
                    su_email = st.text_input("Email Address", placeholder="user@financesight.in")
                    su_pass = st.text_input("Create Password (min 6 chars)", type="password")
                    if st.form_submit_button("Open Account & Claim ₹1,00,000", type="primary", width="stretch"):
                        ok_reg, res_msg = register_new_user(su_name, su_user, su_email, su_pass)
                        if ok_reg:
                            st.session_state.logged_in = True
                            st.session_state.username = res_msg
                            st.session_state.full_name = su_name.strip()
                            st.rerun()
                        else:
                            st.warning(res_msg)

    st.space("small")
    with st.container(border=True):
        s_l, s_r = st.columns([1.0, 1.4], vertical_alignment="center")
        with s_l:
            st.subheader("All-in-One Market Analysis & Trading Suite", icon=":material/analytics:")
            st.caption("Live NSE & NASDAQ Stocks · Agentic AI · Paper Trading")
        with s_r:
            st.markdown("#### Built for practical analysis and risk-free learning")
            st.write("FinanceSight brings together real-time market data, quantitative technical indicators, and virtual trade execution in one workspace:")
            g1, g2 = st.columns(2)
            g1.markdown("- Live Candlestick & Volume Charts\n- 14-Day RSI, MACD & Moving Averages\n- 7-Day Multi-Model ML Forecasting")
            g2.markdown("- Autonomous AI Order Execution\n- No-Code Strategy Backtesting\n- Multi-Currency Paper Portfolio")

    p_col1, p_col2 = st.columns([1.3, 1.0], gap="medium")
    with p_col1.container(border=True, height="stretch"):
        st.subheader("Practical tools you can rely on", icon=":material/shield:")
        st.markdown(
            "**Data-driven decision making**  \n"
            "Evaluate global equities using objective technical indicators (20-SMA, 50-EMA, Bollinger Bands, Wilder RSI, MACD) and historical backtest metrics.\n\n"
            "**Risk-free paper trading simulator**  \n"
            "Practice CNC delivery and 5× leveraged MIS intraday orders—including pending Limit orders—using a ₹1,00,000 virtual wallet.\n\n"
            "**Agentic AI & backtesting workflow**  \n"
            "Ask the AI Advisor to compare stocks, check pivots, inspect your portfolio, or execute orders directly from chat."
        )

    with p_col2.container(border=True, height="stretch"):
        st.subheader("Transparent fee simulation", icon=":material/sell:")
        st.write("Estimate real-world trading costs accurately using standard discount brokerage rates and our built-in tax & breakeven calculator.")
        f1, f2 = st.columns(2)
        f1.metric("CNC Delivery", "₹0", "Zero equity delivery brokerage", delta_color="off", border=True, height="stretch")
        f2.metric("Intraday & F&O", "₹20", "Flat ₹20 / 0.03% order cap", delta_color="off", border=True, height="stretch")

    with st.container(border=True):
        l1, l2 = st.columns([1.0, 1.5], vertical_alignment="center")
        with l1:
            st.subheader("FinanceSight Learning Hub", icon=":material/menu_book:")
            st.caption("Interactive technical analysis & AI-assisted learning")
        with l2:
            st.markdown(
                "**Interactive Indicator Guides:** Understand Candlesticks, Moving Averages, Bollinger Bands, Volume, and Wilder RSI directly on live stock charts.\n\n"
                "**FinanceSight AI Advisor:** Query live stock fundamentals, pivot levels, multi-stock comparisons, and position sizing in plain English."
            )

    with st.container(border=True):
        st.markdown("### Start Exploring with a FinanceSight Account", text_alignment="center")
        st.markdown(
            "Access live NSE & NASDAQ stocks, 7-day leak-free ML forecasting, autonomous AI order execution, and a ₹1,00,000 virtual trading wallet.",
            text_alignment="center",
        )
        _, cta_c, _ = st.columns([1.2, 1.4, 1.2])
        if cta_c.button("Launch Demo Workspace (₹1,00,000 Margin)", type="primary", icon=":material/rocket_launch:", width="stretch", key="cta_demo_home"):
            st.session_state.logged_in = True
            st.session_state.username = "Trader_XYZ"
            st.session_state.full_name = "Trader_XYZ"
            st.rerun()

    render_public_footer()


def page_public_products() -> None:
    st.title("Platform Modules & Capabilities", icon=":material/layers:")
    st.caption("Integrated quantitative charting, machine learning forecasting, strategy backtesting, and paper trading.")
    modules = [
        (":material/candlestick_chart:", "SuperChart Terminal & Fundamentals", "Multi-panel Plotly candlestick charts (`1mo`–`5y`), SMA-20, EMA-50, Bollinger Bands, Wilder RSI, MACD, company fundamentals, and normalized Peer Comparison."),
        (":material/psychology:", "3-Model ML Forecasting Suite", "Stationary next-day return prediction using Random Forest, Gradient Boosting & Ridge Regression evaluated on an 80/20 chronological split with RMSE, MAE, MAPE, R², Directional Accuracy, and Feature Importance."),
        (":material/science:", "No-Code Strategy Backtester", "Simulate SMA Crossover, RSI Reversal, Bollinger Mean Reversion & MACD strategies with mark-to-market equity curves, Buy & Hold benchmark, Alpha, Sharpe Ratio, and Max Drawdown."),
        (":material/account_balance_wallet:", "Multi-Currency Paper Trading", "Place CNC (1x) and MIS (5x) Market & real Pending Limit orders across NSE (`₹`) and US (`$`) stocks with live `USD/INR` FX conversion and market-hours validation."),
        (":material/smart_toy:", "Agentic AI Advisor (Groq + Quant RAG)", "Multi-turn AI analyst with multi-stock comparison, live pivot points, news catalysts, portfolio inspection, and strict command-driven trade execution."),
        (":material/calculate:", "Statutory Fee & Tax Simulator", "Exact Indian brokerage, STT, SEBI turnover fee, stamp duty, GST, and breakeven calculation."),
    ]
    for i in range(0, len(modules), 2):
        c1, c2 = st.columns(2, gap="medium")
        for col, (ico, title, desc) in zip([c1, c2], modules[i : i + 2]):
            with col.container(border=True, height="stretch"):
                st.subheader(title, icon=ico)
                st.write(desc)
    render_public_footer()


def page_public_fees() -> None:
    st.title("Transparent Fee Structure & Calculator", icon=":material/receipt_long:")
    k1, k2, k3 = st.columns(3)
    k1.metric("CNC Equity Delivery", "₹0", "Zero brokerage on delivery trades", delta_color="off", border=True, height="stretch")
    k2.metric("MIS Intraday & F&O", "₹20", "Flat ₹20 or 0.03% per executed leg", delta_color="off", border=True, height="stretch")
    k3.metric("Virtual Trading Capital", "₹1,00,000", "Instant simulated margin on signup", delta_color="off", border=True, height="stretch")
    st.space("small")
    render_brokerage_calculator_widget("pub_calc")
    render_public_footer()


def page_public_about() -> None:
    st.title("System Architecture & Methodology", icon=":material/architecture:")
    st.markdown(
        "FinanceSight unifies live financial market feeds, time-series machine learning, systematic strategy backtesting, "
        "and a persistent SQLite paper-trading ledger inside a multi-page Streamlit architecture."
    )
    with st.container(border=True):
        st.subheader("End-to-End Architecture Diagram", icon=":material/hub:")
        st.mermaid_chart(
            """
            flowchart LR
                UI["Streamlit Multi-Page UI<br/>(st.navigation & Fragments)"] --> DATA["Paginated Yahoo Finance Engine<br/>(345+ Equities + 4 Indices + USDINR=X)"]
                UI --> ML["3Y Offline ML Suite + Live Forecaster<br/>(Health Classifier + Basket Alpha + RF/GBR)"]
                UI --> OPT["Smart Basket Optimizer<br/>(Sector Diversity + Covariance Risk Parity)"]
                UI --> BT["Quantitative Backtester<br/>(Mark-to-Market + Sharpe + Drawdown)"]
                UI --> DB[("SQLite WAL Ledger<br/>Users, Holdings, Positions, Limit Orders")]
                UI --> AI["Agentic AI Advisor<br/>(Groq Tool-Use / Gemini / Quant RAG)"]
            """,
            alt="System architecture flowchart connecting Streamlit UI, Yahoo Finance data engine, 3Y trained ML models, Smart Basket optimizer, backtester, SQLite ledger, and AI advisor",
        )
    c1, c2 = st.columns(2)
    with c1.container(border=True, height="stretch"):
        st.subheader("ML Design Highlights", icon=":material/model_training:")
        st.markdown(
            "- **3-Year Multi-Market Training (`train_models.py`):** Offline-trained `scikit-learn` models across **242,370 historical samples (345 stocks)** power Traffic-Light Stock Health (`72.49%` ROC-AUC) & Smart Basket Alpha (`75.26%` hit rate).\n"
            "- **Stationary Target:** Predicts 1-day percentage returns rather than raw price levels so tree ensembles never flatline near all-time highs.\n"
            "- **Temporal Validation:** Strict chronological 80/20 split (`shuffle=False`) eliminates look-ahead leakage and exposes Confusion Matrix, F1, RMSE, and feature importances."
        )
    with c2.container(border=True, height="stretch"):
        st.subheader("Trading & Security Engineering", icon=":material/security:")
        st.markdown(
            "- **PBKDF2 Password Hashing:** Salted `PBKDF2-HMAC-SHA256` authentication with per-session isolation.\n"
            "- **Multi-Currency Accounting:** Live `USD/INR` FX conversion aligns US equity trades with INR wallet margin.\n"
            "- **Real Limit Order Book:** Pending limit orders reserve margin/shares and fill automatically when market prices cross."
        )
    render_public_footer()


def page_public_support() -> None:
    st.title("Help & Support Center", icon=":material/support_agent:")
    with st.form("support_ticket_form"):
        c1, c2, c3 = st.columns(3)
        tk_cat = c1.selectbox(
            "Topic",
            ["Account & Login", "SuperChart & Indicators", "Paper Trading & Limit Orders", "ML Forecasting", "AI Advisor"],
        )
        tk_email = c2.text_input("Email", value="user@financesight.in")
        tk_subj = c3.text_input("Issue Summary", placeholder="Describe your question or bug...")
        if st.form_submit_button("Submit Support Ticket", type="primary"):
            if not tk_subj.strip():
                st.warning("Please enter an issue summary.")
            else:
                t_id = f"FS-{int(datetime.now().timestamp()) % 100000}"
                with db_conn() as conn:
                    conn.execute(
                        "INSERT INTO support_tickets (ticket_id, timestamp, category, subject, email, status) VALUES (?, ?, ?, ?, ?, 'OPEN')",
                        (t_id, get_ist_now().strftime("%Y-%m-%d %H:%M"), tk_cat, tk_subj.strip(), tk_email.strip()),
                    )
                st.success(f"Ticket `{t_id}` logged successfully!")

    with db_conn() as conn:
        tk_df = pd.read_sql_query(
            "SELECT ticket_id AS Ticket, timestamp AS Created, category AS Category, subject AS Summary, status AS Status FROM support_tickets ORDER BY id DESC LIMIT 10",
            conn,
        )
    if not tk_df.empty:
        st.subheader("Recent Support Tickets")
        st.dataframe(tk_df, hide_index=True, alt="Recent support tickets submitted by users")
    render_public_footer()


def _jump_to_page(page_key: str, ticker: str | None = None) -> None:
    if ticker:
        st.session_state.selected_ticker = ticker
    target_page = st.session_state["_page_map"].get(page_key)
    if target_page is not None:
        st.switch_page(target_page)


def _shift_page_cb(key_name: str, delta: int) -> None:
    st.session_state[key_name] = max(0, int(st.session_state.get(key_name, 0)) + delta)


def _toggle_wl_cb(username: str, sym: str) -> None:
    now_watched = toggle_watchlist(username, sym)
    st.toast(f"{'Added' if now_watched else 'Removed'} {sym} {'to' if now_watched else 'from'} Watchlist.")


def _clear_chat_cb() -> None:
    st.session_state.ai_chat_history = []


def _sync_after_hours_cb(src_key: str) -> None:
    val = bool(st.session_state.get(src_key, False))
    st.session_state.allow_after_hours = val
    for k in ("sb_after_hrs", "term_after_hrs", "ap_after_hrs", "basket_after_hrs"):
        if k in st.session_state and k != src_key:
            st.session_state[k] = val


@st.fragment
def _dashboard_marketwatch_fragment() -> None:
    snaps, _, usdinr, is_live, _ = get_market_context()
    user_wl = get_user_watchlist(st.session_state.username)
    all_sectors = ["All Sectors"] + sorted({v["sector"] for v in STOCK_CATALOG.values()})

    f1, f2, f3 = st.columns([1.4, 1.0, 1.3], vertical_alignment="bottom")
    q_filter = f1.text_input("Search Marketwatch", type="search", placeholder="Search 345+ tickers, companies, or sectors...", key="dash_search")
    sec_filter = f2.selectbox("Sector", all_sectors, key="dash_sector_filter")
    ex_filter = f3.segmented_control(
        "Exchange",
        ["Featured", "NSE", "US", "Watchlist", "All"],
        default="Featured",
        key="dash_ex_filter",
    ) or "Featured"

    if ex_filter == "Featured":
        candidates = list(CORE_TICKERS)
    elif ex_filter == "NSE":
        candidates = [k for k, v in STOCK_CATALOG.items() if v["exchange"] == "NSE"]
    elif ex_filter == "US":
        candidates = [k for k, v in STOCK_CATALOG.items() if v["exchange"] != "NSE"]
    elif ex_filter == "Watchlist":
        candidates = [LEGACY_TICKER_REMAP.get(s, s) for s in (user_wl if user_wl else CORE_TICKERS[:6])]
    else:
        candidates = list(STOCK_CATALOG.keys())

    if sec_filter != "All Sectors":
        base_pool = list(STOCK_CATALOG.keys()) if ex_filter == "Featured" else candidates
        candidates = [s for s in base_pool if STOCK_CATALOG.get(s, {}).get("sector") == sec_filter]

    if q_filter.strip():
        ql = q_filter.strip().lower()
        search_pool = list(STOCK_CATALOG.keys()) if ex_filter == "Featured" and sec_filter == "All Sectors" else candidates
        candidates = [
            s for s in search_pool
            if ql in s.lower()
            or ql in STOCK_CATALOG.get(s, {}).get("name", "").lower()
            or ql in STOCK_CATALOG.get(s, {}).get("sector", "").lower()
            or ql in STOCK_CATALOG.get(s, {}).get("exchange", "").lower()
        ]

    if not candidates:
        st.info("No matching stocks found for that filter.")
        return

    page_size = 24
    total_items = len(candidates)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    filter_sig = f"{ex_filter}|{sec_filter}|{q_filter.strip().lower()}"
    if st.session_state.get("_dash_sig") != filter_sig:
        st.session_state["_dash_sig"] = filter_sig
        st.session_state["dash_page"] = 0
    cur_page = min(max(0, int(st.session_state.get("dash_page", 0))), total_pages - 1)

    start_i = cur_page * page_size
    page_syms = candidates[start_i : start_i + page_size]

    nav_l, nav_c, nav_r = st.columns([2.2, 0.9, 0.9], vertical_alignment="center")
    nav_l.caption(
        f"Showing **{start_i + 1}–{min(start_i + page_size, total_items)}** of **{total_items}** stocks "
        f"(Catalog: {len(STOCK_CATALOG)} · {'Live Yahoo Data' if is_live else 'Cached Baseline'} · FX: ₹{usdinr:.2f}/$)"
    )
    if total_pages > 1:
        nav_c.button(
            "Previous",
            icon=":material/chevron_left:",
            disabled=cur_page == 0,
            width="stretch",
            key="dash_prev",
            on_click=_shift_page_cb,
            args=("dash_page", -1),
        )
        nav_r.button(
            f"Next ({cur_page + 1}/{total_pages})",
            icon=":material/chevron_right:",
            disabled=cur_page >= total_pages - 1,
            width="stretch",
            key="dash_next",
            on_click=_shift_page_cb,
            args=("dash_page", 1),
        )

    snaps = ensure_symbols_live(page_syms, snaps)

    for row_start in range(0, len(page_syms), 3):
        cols = st.columns(3)
        for col_i in range(3):
            idx = row_start + col_i
            if idx >= len(page_syms):
                continue
            sym = page_syms[idx]
            meta = get_ticker_meta(sym)
            sn = snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 0.0, "pct": 0.0, "rsi": 50.0, "above_sma": True, "sparkline": []}))
            is_watched = sym in user_wl
            sig_badge = ":green-badge[Bullish]" if sn.get("above_sma", True) and sn.get("rsi", 50.0) < 68 else (":orange-badge[Overbought]" if sn.get("rsi", 50.0) >= 68 else ":red-badge[Bearish]")

            with cols[col_i].container(border=True, height="stretch"):
                hdr_l, hdr_r = st.columns([4.0, 1.0], vertical_alignment="center")
                hdr_l.html(
                    f'<div style="display:flex;align-items:center;gap:10px;">'
                    f'{stock_icon_html(sym, size=34, radius=9)}'
                    f'<div style="min-width:0;">'
                    f'<div style="font-weight:700;font-size:0.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html.escape(meta["name"])}</div>'
                    f'<div style="font-size:0.74rem;opacity:0.74;font-family:JetBrains Mono,monospace;">{html.escape(sym)} · {meta["exchange"]} · {html.escape(meta["sector"])}</div>'
                    f'</div></div>'
                )
                star_icon = ":material/star:" if is_watched else ":material/star_border:"
                hdr_r.button(
                    "",
                    icon=star_icon,
                    key=f"wl_{sym}",
                    help="Toggle Watchlist",
                    on_click=_toggle_wl_cb,
                    args=(st.session_state.username, sym),
                )

                st.metric(
                    label="Last Price",
                    value=f"{meta['currency']}{sn['price']:,.2f}",
                    delta=f"{sn['pct']:+.2f}%",
                    chart_data=sn.get("sparkline") or None,
                    chart_type="line",
                    label_visibility="collapsed",
                )
                st.markdown(f"RSI(14): `{sn['rsi']:.1f}` &nbsp; {sig_badge}")
                b1, b2 = st.columns(2)
                if b1.button("SuperChart", icon=":material/candlestick_chart:", key=f"go_chart_{sym}", width="stretch"):
                    _jump_to_page("Terminal", sym)
                if b2.button("AI Advisor", icon=":material/smart_toy:", key=f"go_ai_{sym}", width="stretch"):
                    _jump_to_page("Advisor", sym)


def page_dashboard() -> None:
    snaps, idx_snaps, usdinr, _, stamp = get_market_context()
    render_ticker_marquee(snaps, idx_snaps, usdinr)

    acct_pre = get_user_account_summary(st.session_state.username, snaps, usdinr)
    need_syms = set(acct_pre["pend_df"]["ticker"].tolist() if not acct_pre["pend_df"].empty else [])
    need_syms.update(acct_pre["port_df"]["ticker"].tolist() if not acct_pre["port_df"].empty else [])
    need_syms.update(acct_pre["pos_df"]["ticker"].tolist() if not acct_pre["pos_df"].empty else [])
    snaps = ensure_symbols_live(list(need_syms), snaps)

    filled = sync_pending_orders(st.session_state.username, snaps, usdinr, st.session_state.allow_after_hours)
    for msg in filled:
        st.toast(msg, icon=":material/check_circle:")

    acct = get_user_account_summary(st.session_state.username, snaps, usdinr)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Available Margin", f"₹{acct['balance']:,.2f}", f"Net Worth: ₹{acct['balance'] + acct['tot_cur']:,.2f}", delta_color="off", border=True, height="stretch")
    k2.metric("Live Holdings Value", f"₹{acct['tot_cur']:,.2f}", f"Cost: ₹{acct['tot_inv']:,.2f}", delta_color="off", border=True, height="stretch")
    pnl_pct = (acct["tot_pnl"] / acct["tot_inv"] * 100.0) if acct["tot_inv"] > 0 else 0.0
    k3.metric("Unrealized P&L", f"₹{acct['tot_pnl']:+,.2f}", f"{pnl_pct:+.2f}% ROI", border=True, height="stretch")
    nse_open, _ = check_market_trading_hours("RELIANCE.NS")
    k4.metric("NSE Market Status", "OPEN" if nse_open else "CLOSED", stamp, delta_color="off", border=True, height="stretch")

    st.space("small")
    render_indices_row(idx_snaps, usdinr)
    st.space("small")
    _dashboard_marketwatch_fragment()


@st.fragment
def _superchart_workspace_fragment(ticker: str, period: str, df: pd.DataFrame) -> None:
    meta = get_ticker_meta(ticker)
    currency = meta["currency"]

    terminal_view = st.segmented_control(
        "Terminal View",
        ["SuperChart", "ML Forecast & Evaluation", "Peer Comparison"],
        default="SuperChart",
        key="terminal_view",
        label_visibility="collapsed",
    ) or "SuperChart"

    if terminal_view == "SuperChart":
        with st.container(border=True):
            ctrl1, ctrl2, ctrl3 = st.columns([1.2, 2.0, 1.1])
            chart_style = ctrl1.segmented_control("Style", ["Candlestick", "Line"], default="Candlestick", key="sc_style") or "Candlestick"
            overlays = ctrl2.pills(
                "Overlays",
                ["20 SMA", "50 EMA", "Bollinger Bands"],
                selection_mode="multi",
                default=["20 SMA", "50 EMA"],
                key="sc_overlays",
            )
            oscillator = ctrl3.segmented_control("Oscillator", ["RSI (14)", "MACD"], default="RSI (14)", key="sc_osc") or "RSI (14)"

            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.60, 0.16, 0.24]
            )
            if chart_style == "Candlestick":
                fig.add_trace(
                    go.Candlestick(
                        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                        name="Price", increasing_line_color="#10b981", decreasing_line_color="#ef4444",
                    ),
                    row=1, col=1,
                )
            else:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color="#3b82f6", width=2.2)),
                    row=1, col=1,
                )

            if "20 SMA" in overlays:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], name="20 SMA", line=dict(color="#0ea5e9", width=1.6)), row=1, col=1)
            if "50 EMA" in overlays:
                fig.add_trace(go.Scatter(x=df.index, y=df["EMA_50"], name="50 EMA", line=dict(color="#f59e0b", width=1.6, dash="dot")), row=1, col=1)
            if "Bollinger Bands" in overlays:
                fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper", line=dict(color="rgba(139,92,246,0.55)", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower", fill="tonexty", fillcolor="rgba(139,92,246,0.08)", line=dict(color="rgba(139,92,246,0.55)", width=1.2)), row=1, col=1)

            v_colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(df["Close"], df["Open"])]
            fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=v_colors), row=2, col=1)

            if oscillator == "RSI (14)":
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)", line=dict(color="#8b5cf6", width=1.8)), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)
            else:
                hist_colors = ["#10b981" if h >= 0 else "#ef4444" for h in df["MACD_Hist"]]
                fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="MACD Hist", marker_color=hist_colors), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="#3b82f6", width=1.6)), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal", line=dict(color="#f59e0b", width=1.4)), row=3, col=1)

            fig.update_layout(
                height=610,
                xaxis_rangeslider_visible=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=24, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
            )
            fig.update_yaxes(gridcolor="rgba(128,128,128,0.16)")
            fig.update_xaxes(gridcolor="rgba(128,128,128,0.10)")
            st.plotly_chart(fig, theme="streamlit", alt=f"Multi-panel price, volume, and {oscillator} chart for {ticker}")

    elif terminal_view == "ML Forecast & Evaluation":
        with st.container(border=True):
            df_1y = df if period in {"1y", "2y", "5y"} else fetch_stock_history(ticker, "1y")
            if df_1y is None or len(df_1y) < 80:
                st.warning("At least 80 trading sessions are needed to run the 80/20 ML evaluation suite.")
            else:
                with st.spinner("Training & evaluating Random Forest, Gradient Boosting, and Ridge Regression..."):
                    ml_res = run_ml_forecast_suite(ticker, str(df_1y.index[-1]), len(df_1y), df_1y)
                if not ml_res:
                    st.warning("Not enough clean indicator rows to fit the ML suite.")
                else:
                    tgt_7d = ml_res["target_7d"]
                    diff_pct = ((tgt_7d - ml_res["last_close"]) / ml_res["last_close"]) * 100.0
                    best_row = ml_res["eval_df"].iloc[0]

                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("Best Out-of-Sample Model", ml_res["best_model"], f"Dir. Acc: {best_row['Directional Accuracy (%)']}%", delta_color="off", border=True, height="stretch")
                    mc2.metric("7-Day Projected Price", f"{currency}{tgt_7d:,.2f}", f"{diff_pct:+.2f}%", border=True, height="stretch")
                    mc3.metric("Test Set MAPE", f"{best_row['MAPE (%)']}%", f"RMSE: {currency}{best_row['RMSE']:,.2f}", delta_color="off", border=True, height="stretch")
                    mc4.metric("Out-of-Sample R²", f"{best_row['R² Score']:.4f}", "Chronological 80/20 Split", delta_color="off", border=True, height="stretch")

                    p_fig = go.Figure()
                    hist_tail = df_1y.tail(55)
                    p_fig.add_trace(go.Scatter(x=hist_tail.index, y=hist_tail["Close"], name="Historical Close", line=dict(color="#3b82f6", width=2.2)))
                    p_fig.add_trace(
                        go.Scatter(
                            x=ml_res["test_dates"], y=ml_res["test_pred"],
                            name="Test Set Predicted (Unseen 20%)", line=dict(color="#f59e0b", width=1.8, dash="dot"),
                        )
                    )
                    f_x = [hist_tail.index[-1]] + ml_res["forecast_dates"]
                    f_y = [ml_res["last_close"]] + ml_res["forecast_prices"]
                    f_up = [ml_res["last_close"]] + ml_res["forecast_upper"]
                    f_lo = [ml_res["last_close"]] + ml_res["forecast_lower"]
                    p_fig.add_trace(go.Scatter(x=f_x + f_x[::-1], y=f_up + f_lo[::-1], fill="toself", fillcolor="rgba(16,185,129,0.14)", line=dict(width=0), name="±1σ Uncertainty Band"))
                    p_fig.add_trace(go.Scatter(x=f_x, y=f_y, name="7-Day Forecast", mode="lines+markers", line=dict(color="#10b981" if diff_pct >= 0 else "#ef4444", width=2.6, dash="dash")))
                    p_fig.update_layout(height=390, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=24, b=10))
                    st.plotly_chart(p_fig, theme="streamlit", alt=f"7-day ML forecast and unseen test predictions for {ticker}")

                    c_ev, c_fi = st.columns([1.3, 1.0])
                    with c_ev:
                        st.markdown("**Out-of-Sample Model Comparison (20% Chronological Test Set)**")
                        st.dataframe(ml_res["eval_df"], hide_index=True, alt="Model accuracy comparison across RMSE, MAE, MAPE, R2, and directional accuracy")
                    with c_fi:
                        st.markdown("**Top Predictive Features (%)**")
                        fi_chart = (
                            alt.Chart(ml_res["feature_importance"].head(8))
                            .mark_bar(cornerRadiusEnd=4, color="#3b82f6")
                            .encode(x="Importance:Q", y=alt.Y("Feature:N", sort="-x"))
                            .properties(height=230)
                        )
                        st.altair_chart(fi_chart, alt="Top predictive technical feature importances")

                    with st.expander("Methodology & Leak-Free Design Notes"):
                        st.markdown(
                            "- Predicts **stationary 1-day percentage returns** instead of raw price levels so tree ensembles never flatline near all-time highs.\n"
                            "- Evaluates **Random Forest**, **Gradient Boosting**, and **Ridge Regression** on a chronological **80/20 split** (`shuffle=False`) to eliminate look-ahead leakage.\n"
                            "- Iteratively recomputes rolling lag returns, 20-SMA ratio, 50-EMA ratio, Wilder RSI, Bollinger %B, and volatility at each forecast step."
                        )

    elif terminal_view == "Peer Comparison":
        with st.container(border=True):
            same_ex = [k for k, v in STOCK_CATALOG.items() if v["exchange"] == meta["exchange"]]
            default_peers = [ticker] + [s for s in same_ex if s != ticker][:3]
            peers_sel = st.multiselect(
                "Compare Normalized Performance",
                options=list(STOCK_CATALOG.keys()),
                default=default_peers,
                max_selections=6,
                key="peer_multiselect",
            )
            if len(peers_sel) < 2:
                st.info("Select at least 2 stocks to compare normalized relative returns.")
            else:
                p_df = fetch_peer_closes(tuple(peers_sel), period if period in {"1mo", "3mo", "6mo", "1y", "2y"} else "6mo")
                if p_df is None or p_df.empty:
                    st.warning("Unable to load peer comparison data right now.")
                else:
                    norm_df = (p_df.div(p_df.bfill().iloc[0]) - 1.0) * 100.0
                    melted = norm_df.reset_index().melt(id_vars=[norm_df.index.name or "Date"], var_name="Ticker", value_name="Return (%)")
                    date_col = melted.columns[0]
                    peer_chart = (
                        alt.Chart(melted)
                        .mark_line()
                        .encode(x=alt.X(f"{date_col}:T", title="Date"), y=alt.Y("Return (%):Q", title="Cumulative Return (%)"), color="Ticker:N")
                        .properties(height=380, title=f"Normalized Cumulative Return Comparison ({period})")
                    )
                    st.altair_chart(peer_chart, alt="Normalized cumulative percentage return across selected peer equities")


def page_superchart() -> None:
    _, _, usdinr, _, _ = get_market_context()
    ticker = st.session_state.selected_ticker
    meta = get_ticker_meta(ticker)
    currency = meta["currency"]
    fx = get_fx_rate_for_ticker(ticker, usdinr)

    top_l, top_r = st.columns([2.2, 1.5], vertical_alignment="bottom")
    all_syms = list(STOCK_CATALOG.keys())
    cur_idx = all_syms.index(ticker) if ticker in all_syms else 0
    picked = top_l.selectbox(
        "Active Equity",
        all_syms,
        index=cur_idx,
        format_func=lambda s: f"{s} — {STOCK_CATALOG[s]['name']} ({STOCK_CATALOG[s]['exchange']})",
        key="terminal_ticker_pick",
    )
    if picked != ticker:
        st.session_state.selected_ticker = picked
        st.rerun()

    period = top_r.segmented_control(
        "Timeframe",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        default="1y",
        key="terminal_period",
    ) or "1y"

    chart_slot = st.container()
    with chart_slot.skeleton(height=320):
        df = fetch_stock_history(ticker, period)
    if df is None or len(df) < 20:
        chart_slot.error(f"Could not fetch live candles for `{ticker}`. Click Refresh Market Data in the sidebar or try another ticker.")
        return

    latest_c = float(df["Close"].iloc[-1])
    prev_c = float(df["Close"].iloc[-2])
    chg = latest_c - prev_c
    pct = (chg / prev_c * 100.0) if prev_c else 0.0
    rsi_val = float(df["RSI"].iloc[-1])
    sma20_val = float(df["SMA_20"].iloc[-1])
    ema50_val = float(df["EMA_50"].iloc[-1])
    high_52 = float(df["High"].max())
    low_52 = float(df["Low"].min())

    with chart_slot:
        with st.container(border=True):
            h1, h2, h3, h4, h5 = st.columns([2.1, 1.1, 1.0, 1.0, 1.0], vertical_alignment="center")
            h1.html(
                f'<div style="display:flex;align-items:center;gap:12px;">'
                f'{stock_icon_html(ticker, size=44, radius=11)}'
                f'<div>'
                f'<div style="font-size:1.18rem;font-weight:800;line-height:1.2;">{html.escape(meta["name"])} '
                f'<span style="font-size:0.86rem;font-family:JetBrains Mono,monospace;opacity:0.75;">({html.escape(ticker)})</span></div>'
                f'<div style="font-size:0.80rem;opacity:0.75;">{meta["exchange"]} · {html.escape(meta["sector"])} · FX ₹{fx:.2f}</div>'
                f'</div></div>'
            )
            h2.metric("Spot Price", f"{currency}{latest_c:,.2f}", f"{chg:+.2f} ({pct:+.2f}%)")
            h3.metric("14-Day RSI", f"{rsi_val:.1f}", "Overbought" if rsi_val >= 70 else ("Oversold" if rsi_val <= 30 else "Neutral"), delta_color="off")
            h4.metric("Period High", f"{currency}{high_52:,.2f}")
            h5.metric("Period Low", f"{currency}{low_52:,.2f}")

            h_card = compute_traffic_light_health(ticker, df)
            st.markdown(
                f"Beginner Health Rating: :{h_card['badge_clr']}-badge[{h_card['pill']} · {h_card['score']}/100] &nbsp; "
                f":small[{h_card['trend_plain']} · *{h_card['model_used']}*]"
            )

            fund_exp = st.expander("Company Fundamentals & Latest News", on_change="rerun")
            if fund_exp.open:
                with fund_exp:
                    funds = fetch_stock_fundamentals(ticker)
                    if funds:
                        f_items = {
                            "Market Cap": format_large_number(funds.get("marketCap"), currency),
                            "Trailing P/E": f"{funds['trailingPE']:.2f}" if funds.get("trailingPE") else "N/A",
                            "EPS (TTM)": f"{currency}{funds['trailingEps']:.2f}" if funds.get("trailingEps") else "N/A",
                            "Beta": f"{funds['beta']:.2f}" if funds.get("beta") else "N/A",
                            "Analyst View": str(funds.get("recommendationKey") or "N/A").upper(),
                        }
                        f_cols = st.columns(len(f_items))
                        for col, (fk, fv) in zip(f_cols, f_items.items()):
                            col.caption(f"**{fk}:** `{fv}`")
                    news = fetch_stock_news_headlines(ticker, meta["name"])
                    if news:
                        for n in news:
                            st.caption(f"- [{n['title']}]({n['link']}) *({n['pubDate']})*")

        main_col, order_col = st.columns([2.65, 1.1], gap="medium")
        with main_col:
            _superchart_workspace_fragment(ticker, period, df)

        with order_col:
            with st.container(border=True):
                st.subheader("Order Window", icon=":material/bolt:")
                is_open_t, status_t = check_market_trading_hours(ticker)
                st.badge("Market Open" if is_open_t else "Market Closed", color="green" if is_open_t else "red")
                st.caption(status_t)

                prod_mode = st.segmented_control(
                    "Product Type",
                    ["CNC (Delivery)", "MIS (Intraday 5x)"],
                    default="CNC (Delivery)",
                    key="term_prod",
                ) or "CNC (Delivery)"
                ord_type = st.segmented_control(
                    "Order Type",
                    ["MARKET", "LIMIT"],
                    default="MARKET",
                    key="term_otype",
                ) or "MARKET"
                qty = st.number_input("Quantity", min_value=1, max_value=100000, value=10, step=1, key="term_qty")
                lim_p = (
                    st.number_input(f"Limit Price ({currency})", min_value=0.01, value=round(latest_c, 2), step=0.5, key="term_lim")
                    if ord_type == "LIMIT"
                    else latest_c
                )
                eff_p = lim_p if ord_type == "LIMIT" else latest_c
                req_margin_inr = qty * eff_p * fx * (0.20 if "MIS" in prod_mode else 1.0)
                user_bal = get_user_balance(st.session_state.username)

                st.table(
                    {
                        "Spot Price": f"{currency}{latest_c:,.2f}",
                        "FX Conversion": f"₹{fx:.2f} / $" if currency == "$" else "1.00 (INR)",
                        "Required Margin": f"₹{req_margin_inr:,.2f}",
                        "Available Cash": f"₹{user_bal:,.2f}",
                    },
                    border="horizontal",
                )
                st.toggle(
                    "Allow Demo Orders Outside Market Hours",
                    value=st.session_state.allow_after_hours,
                    key="term_after_hrs",
                    on_change=_sync_after_hours_cb,
                    args=("term_after_hrs",),
                )

                ob1, ob2 = st.columns(2)
                if ob1.button("BUY", type="primary", width="stretch", key="term_buy"):
                    ok, msg = execute_trade(
                        st.session_state.username, ticker, "BUY", int(qty), latest_c, prod_mode,
                        order_type=ord_type, limit_price=lim_p if ord_type == "LIMIT" else None,
                        usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
                    )
                    if ok:
                        st.toast(msg, icon=":material/check_circle:")
                        st.rerun()
                    else:
                        st.error(msg)
                if ob2.button("SELL", width="stretch", key="term_sell"):
                    ok, msg = execute_trade(
                        st.session_state.username, ticker, "SELL", int(qty), latest_c, prod_mode,
                        order_type=ord_type, limit_price=lim_p if ord_type == "LIMIT" else None,
                        usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
                    )
                    if ok:
                        st.toast(msg, icon=":material/check_circle:")
                        st.rerun()
                    else:
                        st.error(msg)

            bull_pts = sum([latest_c > sma20_val, latest_c > ema50_val, 35 < rsi_val < 68])
            verdict = "STRONG BUY" if bull_pts == 3 else ("BUY / HOLD" if bull_pts == 2 else "SELL / CAUTION")
            st.metric("Technical Signal", verdict, f"20-SMA: {currency}{sma20_val:,.2f} | 50-EMA: {currency}{ema50_val:,.2f}", delta_color="off", border=True)


def page_orders() -> None:
    snaps, _, usdinr, _, _ = get_market_context()
    st.title("Order Book & Trade Ledger", icon=":material/receipt:")

    acct_pre = get_user_account_summary(st.session_state.username, snaps, usdinr)
    if not acct_pre["pend_df"].empty:
        snaps = ensure_symbols_live(acct_pre["pend_df"]["ticker"].tolist(), snaps)

    filled = sync_pending_orders(st.session_state.username, snaps, usdinr, st.session_state.allow_after_hours)
    for msg in filled:
        st.toast(msg, icon=":material/check_circle:")

    acct = get_user_account_summary(st.session_state.username, snaps, usdinr)

    with st.container(border=True):
        h1, h2 = st.columns([2.5, 1.0], vertical_alignment="center")
        h1.subheader("Pending Limit Orders", icon=":material/schedule:")
        if h2.button("Check & Fill Triggered Limits", icon=":material/sync:", width="stretch"):
            st.rerun()

        if acct["pend_df"].empty:
            st.caption("No open limit orders queued right now. Place a LIMIT order from SuperChart or the sidebar.")
        else:
            pend_disp = acct["pend_df"].copy()
            pend_disp.insert(0, "Logo", pend_disp["ticker"].map(get_logo_url))
            st.dataframe(
                pend_disp,
                column_config={"Logo": st.column_config.ImageColumn("", width="small")},
                hide_index=True,
                alt="Open pending limit orders with company icons",
            )
            c_sel, c_btn = st.columns([2, 1], vertical_alignment="bottom")
            cancel_id = c_sel.selectbox("Cancel Pending Order ID", acct["pend_df"]["id"].tolist(), key="cancel_pend_id")
            if c_btn.button("Cancel Selected Limit Order", type="secondary", width="stretch"):
                ok_c, msg_c = cancel_pending_order(st.session_state.username, int(cancel_id))
                if ok_c:
                    st.toast(msg_c)
                    st.rerun()
                else:
                    st.error(msg_c)

    st.space("small")
    with st.container(border=True):
        st.subheader("Executed Tradebook", icon=":material/history:")
        if acct["tx_df"].empty:
            st.info("No executed trades yet. Place a paper trade from the sidebar, SuperChart, or AI Advisor.")
        else:
            tx_disp = acct["tx_df"].copy()
            tx_disp.insert(0, "Logo", tx_disp["ticker"].map(get_logo_url))
            st.dataframe(
                tx_disp,
                column_config={
                    "Logo": st.column_config.ImageColumn("", width="small"),
                    "price": st.column_config.NumberColumn("Fill Price", format="%.2f"),
                    "inr_total": st.column_config.NumberColumn("INR Value (₹)", format="₹%.2f"),
                },
                hide_index=True,
                alt="Executed trades ledger with company icons",
            )
            b1, b2 = st.columns(2)
            if b1.button("Reverse Last Executed Order", icon=":material/undo:", width="stretch"):
                ok_r, msg_r = reverse_last_executed_order(st.session_state.username)
                if ok_r:
                    st.toast(msg_r)
                    st.rerun()
                else:
                    st.warning(msg_r)
            b2.download_button(
                "Export Tradebook CSV",
                data=acct["tx_df"].to_csv(index=False).encode("utf-8"),
                file_name="financesight_orders.csv",
                mime="text/csv",
                icon=":material/download:",
                width="stretch",
            )


def page_holdings() -> None:
    snaps, _, usdinr, _, _ = get_market_context()
    st.title("CNC Demat Holdings", icon=":material/business_center:")
    acct = get_user_account_summary(st.session_state.username, snaps, usdinr)
    if not acct["port_df"].empty:
        snaps = ensure_symbols_live(acct["port_df"]["ticker"].tolist(), snaps)
        acct = get_user_account_summary(st.session_state.username, snaps, usdinr)

    if acct["port_df"].empty:
        st.info("Your CNC Holdings are currently empty. Place a CNC (Delivery) BUY order to build your portfolio.")
        return

    port_df = acct["port_df"]
    roi_pct = (acct["tot_pnl"] / acct["tot_inv"] * 100.0) if acct["tot_inv"] > 0 else 0.0
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Account Net Worth", f"₹{acct['balance'] + acct['tot_cur']:,.2f}", "Cash + Live Holdings", delta_color="off", border=True, height="stretch")
    k2.metric("Initial Cost (INR)", f"₹{acct['tot_inv']:,.2f}", f"{len(port_df)} Stocks", delta_color="off", border=True, height="stretch")
    k3.metric("Live Value (INR)", f"₹{acct['tot_cur']:,.2f}", f"FX: ₹{usdinr:.2f}/$", delta_color="off", border=True, height="stretch")
    k4.metric("Unrealized P&L", f"₹{acct['tot_pnl']:+,.2f}", f"{roi_pct:+.2f}% ROI", border=True, height="stretch")

    c1, c2 = st.columns([1.65, 1.15])
    with c1.container(border=True, height="stretch"):
        st.subheader("Holdings Breakdown")
        display_df = port_df[["ticker", "Sector", "shares", "currency", "avg_price", "LTP", "Cost (₹)", "Live Value (₹)", "Live P&L (₹)", "Return (%)"]].copy()
        display_df.insert(0, "Logo", display_df["ticker"].map(get_logo_url))
        st.dataframe(
            display_df,
            column_config={
                "Logo": st.column_config.ImageColumn("", width="small"),
                "avg_price": st.column_config.NumberColumn("Avg Price", format="%.2f"),
                "LTP": st.column_config.NumberColumn("Live LTP", format="%.2f"),
                "Cost (₹)": st.column_config.NumberColumn("Cost (₹)", format="₹%.2f"),
                "Live Value (₹)": st.column_config.NumberColumn("Live Value (₹)", format="₹%.2f"),
                "Live P&L (₹)": st.column_config.NumberColumn("P&L (₹)", format="₹%.2f"),
                "Return (%)": st.column_config.NumberColumn("Return %", format="%.2f%%"),
            },
            hide_index=True,
            alt="Holdings table with company icons, live valuation and unrealized profit or loss",
        )
        st.download_button(
            "Download Holdings Statement (CSV)",
            data=display_df.drop(columns=["Logo"]).to_csv(index=False).encode("utf-8"),
            file_name="financesight_holdings.csv",
            mime="text/csv",
            icon=":material/download:",
        )

    with c2.container(border=True, height="stretch"):
        st.subheader("Portfolio Allocation by Stock")
        pie = go.Figure(data=[go.Pie(labels=port_df["ticker"], values=port_df["Live Value (₹)"], hole=0.52)])
        pie.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(pie, theme="streamlit", alt="Donut chart of live portfolio allocation by ticker")


def page_positions() -> None:
    snaps, _, usdinr, _, _ = get_market_context()
    st.title("Open Positions (CNC & MIS 5x)", icon=":material/monitoring:")
    acct = get_user_account_summary(st.session_state.username, snaps, usdinr)
    if not acct["pos_df"].empty:
        snaps = ensure_symbols_live(acct["pos_df"]["ticker"].tolist(), snaps)
        acct = get_user_account_summary(st.session_state.username, snaps, usdinr)

    if acct["pos_df"].empty:
        st.info("No open positions right now. Place a CNC or MIS (5x Intraday) order to track live mark-to-market P&L.")
        return

    pos_df = acct["pos_df"]
    p1, p2 = st.columns(2)
    p1.metric("Live Open Exposure (INR)", f"₹{acct['tot_pos_val']:,.2f}", f"{len(pos_df)} Active Positions", delta_color="off", border=True, height="stretch")
    p2.metric("Total M2M P&L (INR)", f"₹{acct['tot_m2m']:+,.2f}", "Real-Time Mark-to-Market", border=True, height="stretch")

    pos_disp = pos_df[["ticker", "product_type", "shares", "currency", "avg_price", "LTP", "Live Value (₹)", "M2M P&L (₹)", "Return (%)"]].copy()
    pos_disp.insert(0, "Logo", pos_disp["ticker"].map(get_logo_url))
    st.dataframe(
        pos_disp,
        column_config={"Logo": st.column_config.ImageColumn("", width="small")},
        hide_index=True,
        alt="Open delivery and intraday positions with company logos and mark-to-market profit or loss",
    )

    st.subheader("1-Click Position Square-Off")
    sq_cols = st.columns(min(4, len(pos_df)))
    for i, (_, r) in enumerate(pos_df.iterrows()):
        sym = LEGACY_TICKER_REMAP.get(r["ticker"], r["ticker"])
        if sq_cols[i % len(sq_cols)].button(
            f"Square Off {sym} ({r['product_type']})",
            key=f"sq_{sym}_{r['product_type']}",
            type="primary",
            width="stretch",
        ):
            prod = "MIS (Intraday 5x)" if r["product_type"] == "MIS" else "CNC (Delivery)"
            ok, msg = execute_trade(
                st.session_state.username, sym, "SELL", int(r["shares"]), float(r["LTP"]), prod,
                usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
            )
            if ok:
                st.toast(msg, icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(msg)


def page_funds() -> None:
    st.title("Virtual Wallet & Margin Gateway", icon=":material/account_balance_wallet:")
    user_bal = get_user_balance(st.session_state.username)
    st.metric("Available Cash Margin", f"₹{user_bal:,.2f}", "Zero Gateway Charges • Simulated Wallet", delta_color="off", border=True)

    t_dep, t_wit, t_reset = st.tabs(["Deposit Virtual Cash", "Withdraw to Bank", "Reset Demo Account"])
    with t_dep:
        c1, c2 = st.columns([1.2, 1.5])
        with c1.container(border=True):
            preset = st.segmented_control("Quick Amount", ["₹10,000", "₹25,000", "₹50,000", "₹1,00,000"], default="₹25,000", key="dep_preset") or "₹25,000"
            p_map = {"₹10,000": 10000.0, "₹25,000": 25000.0, "₹50,000": 50000.0, "₹1,00,000": 100000.0}
            dep_amt = st.number_input("Deposit Amount (₹)", min_value=500.0, max_value=10000000.0, value=p_map[preset], step=1000.0)
            pay_mode = st.selectbox("Payment Mode", ["Instant UPI (GPay / PhonePe)", "NetBanking (SBI / HDFC / ICICI)", "RuPay / Visa Debit Card"])
            pay_ref = st.text_input("Reference / UPI ID", value=f"{st.session_state.username}@okaxis")
            if st.button("Add Virtual Funds", type="primary", width="stretch"):
                ok, msg = update_funds(st.session_state.username, dep_amt, "DEPOSIT", pay_mode, pay_ref)
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with c2.container(border=True):
            st.subheader("Funding Ledger")
            with db_conn() as conn:
                f_df = pd.read_sql_query(
                    "SELECT timestamp AS Time, type AS Type, method AS Method, reference AS Reference, amount AS Amount, status AS Status FROM funding_history WHERE LOWER(username) = LOWER(?) ORDER BY id DESC",
                    conn, params=(st.session_state.username,),
                )
            st.dataframe(f_df, hide_index=True, alt="Virtual wallet deposit and withdrawal history")

    with t_wit:
        with st.container(border=True):
            if user_bal < 100.0:
                st.warning("Available cash margin is below ₹100.00 minimum withdrawal.")
            else:
                b_name = st.selectbox("Linked Bank", ["State Bank of India (SBI)", "HDFC Bank", "ICICI Bank", "Axis Bank"])
                acc_num = st.text_input("Account Number", value="XXXX-XXXX-8821")
                ifsc = st.text_input("IFSC Code", value="SBIN0004821")
                w_amt = st.number_input(
                    "Withdrawal Amount (₹)",
                    min_value=100.0, max_value=float(user_bal),
                    value=min(5000.0, float(user_bal)), step=500.0,
                )
                if st.button("Withdraw Virtual Cash", type="primary"):
                    ok, msg = update_funds(st.session_state.username, w_amt, "WITHDRAW", b_name, f"A/C {acc_num[-4:]} ({ifsc})")
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with t_reset:
        with st.container(border=True):
            st.warning("Resetting your demo account clears all Holdings, Open Positions, Pending Limit Orders, and Tradebook entries, and restores your wallet to **₹1,00,000.00**.")
            confirm_reset = st.checkbox("Yes, reset my entire paper-trading portfolio to ₹1,00,000.00", key="confirm_reset_chk")
            if st.button("Reset Wallet & Portfolio", type="primary", disabled=not confirm_reset):
                ok, msg = reset_user_wallet(st.session_state.username)
                if ok:
                    st.toast(msg)
                    st.rerun()


@st.fragment
def _ai_advisor_chat_fragment() -> None:
    snaps, _, usdinr, _, _ = get_market_context()
    groq_key = resolve_secret("GROQ_API_KEY", st.session_state.get("user_groq_api_key", ""))
    gemini_key = resolve_secret("GEMINI_API_KEY", st.session_state.get("user_gemini_api_key", ""))

    if groq_key.startswith("gsk_"):
        status_txt = ":green-badge[Groq Agentic AI Tools Active]"
    elif gemini_key:
        status_txt = ":green-badge[Gemini 3 Flash + Quant RAG Active]"
    else:
        status_txt = ":blue-badge[Local Quant + Auto-Pilot Engine Active]"

    with st.expander("AI Auto-Pilot: 1-Click Best-Stock Trader & Portfolio Risk Auditor", icon=":material/auto_awesome:"):
        ap1, ap2, ap3, ap4 = st.columns([1.0, 1.1, 1.2, 1.0])
        ap_mkt = ap1.selectbox("Market Focus", ["ALL", "NSE", "US"], key="ap_mkt")
        ap_sec = ap2.selectbox("Sector Focus", ["Any Sector", "IT & AI", "Banking & Finance", "Defence", "Auto & EV", "Pharma", "Energy"], key="ap_sec")
        ap_budget = ap3.number_input("Trade Budget (₹)", min_value=1000.0, max_value=500000.0, value=15000.0, step=1000.0, key="ap_budget")
        ap_prod = ap4.selectbox("Product", ["CNC (Delivery)", "MIS (Intraday 5x)"], key="ap_prod")

        ap_b1, ap_b2, ap_b3 = st.columns([1.4, 1.3, 1.3], vertical_alignment="center")
        ap_b3.toggle(
            "Allow Demo Orders Outside Hours",
            value=st.session_state.allow_after_hours,
            key="ap_after_hrs",
            on_change=_sync_after_hours_cb,
            args=("ap_after_hrs",),
        )
        if ap_b1.button("Find Best Stock & Auto-Trade", type="primary", icon=":material/auto_awesome:", width="stretch", key="ap_exec_btn"):
            sec_arg = "" if ap_sec == "Any Sector" else ap_sec
            _, rep_md, tit_a, logo_a, _ = execute_ai_auto_pick_trade(
                st.session_state.username,
                snaps,
                usdinr,
                market=ap_mkt,
                sector_hint=sec_arg,
                budget_inr=float(ap_budget),
                product=ap_prod,
                allow_after_hours=st.session_state.allow_after_hours,
            )
            st.session_state.ai_chat_history.append(
                {
                    "question": f"[AI Auto-Pilot] Find best {ap_mkt} ({ap_sec}) stock and invest ₹{ap_budget:,.0f} ({ap_prod})",
                    "answer": rep_md,
                    "badge": "FinanceSight AI Auto-Pilot",
                    "stock": tit_a,
                    "logo": logo_a,
                }
            )
        if ap_b2.button("Audit Portfolio Risk", icon=":material/health_and_safety:", width="stretch", key="ap_audit_btn"):
            aud_md, _ = build_portfolio_risk_audit(
                st.session_state.username,
                snaps,
                usdinr,
                auto_rebalance=False,
                allow_after_hours=st.session_state.allow_after_hours,
            )
            st.session_state.ai_chat_history.append(
                {
                    "question": "[AI Auto-Pilot] Run full portfolio risk & diversification audit",
                    "answer": aud_md,
                    "badge": "FinanceSight Risk Engine",
                    "stock": "Portfolio Risk & Diversification Audit",
                    "logo": get_logo_url("RELIANCE.NS"),
                }
            )

    acct = get_user_account_summary(st.session_state.username, snaps, usdinr)
    top_l, top_r = st.columns([3.0, 1.0], vertical_alignment="center")
    top_l.markdown(f"{status_txt} &nbsp; Available Margin: **`₹{acct['balance']:,.2f}`** &nbsp; Holdings: **`₹{acct['tot_cur']:,.2f}`**")
    top_r.button("Clear Chat", icon=":material/delete_sweep:", width="stretch", on_click=_clear_chat_cb, key="clear_ai_chat")

    SUGGESTIONS = {
        ":material/leaderboard: Top benefitting stocks": "List top benefitting stocks to invest in across Indian NSE and US markets.",
        ":material/compare_arrows: Compare TCS vs Infosys": "Compare TCS and Infosys on returns, RSI, pivots, and ML target.",
        ":material/health_and_safety: Audit my portfolio risk": "Audit my portfolio risk, diversification, and tell me what to hold or sell.",
        ":material/newspaper: Latest news & ML forecast": f"Latest news and full technical analysis for {st.session_state.selected_ticker}.",
    }

    prompt = st.chat_input(
        "Ask about any stock, compare two stocks, audit portfolio, or say 'Find best stock and invest ₹15000'...",
        submit_mode="disable",
    )
    if not st.session_state.ai_chat_history:
        chips = st.empty()
        picked = chips.pills("Suggested prompts", list(SUGGESTIONS.keys()), label_visibility="collapsed")
        if picked:
            prompt = SUGGESTIONS[picked]
        if prompt:
            chips.empty()

    for turn in st.session_state.ai_chat_history:
        with st.chat_message("user"):
            st.markdown(turn["question"])
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            logo_src = turn.get("logo")
            if logo_src:
                st.html(
                    f'<div style="display:inline-flex;align-items:center;gap:8px;padding:3px 10px;'
                    f'border-radius:8px;border:1px solid rgba(128,128,128,0.22);margin-bottom:6px;">'
                    f'<span style="width:20px;height:20px;border-radius:5px;background:#fff;padding:1px;display:inline-flex;align-items:center;justify-content:center;">'
                    f'<img src="{logo_src}" style="width:100%;height:100%;object-fit:contain;"/></span>'
                    f'<span style="font-size:0.78rem;font-weight:700;">{html.escape(turn["stock"])}</span>'
                    f'<span style="font-size:0.74rem;opacity:0.72;">· {html.escape(turn["badge"])}</span></div>'
                )
            else:
                st.caption(f"{turn['stock']} · {turn['badge']}")
            st.markdown(turn["answer"])

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            with st.status(":shimmer[Analyzing live market data, pivots & portfolio state...]", type="compact") as status:
                reply, badge, title, logo_url, steps = ask_universal_ai_advisor(
                    st.session_state.username,
                    prompt,
                    snaps,
                    usdinr,
                    groq_api_key=groq_key,
                    gemini_api_key=gemini_key,
                    allow_after_hours=st.session_state.allow_after_hours,
                    chat_history=st.session_state.ai_chat_history,
                )
                for s in steps:
                    st.write(f"- {s}")
                status.update(label=f"Completed via {badge}", state="complete")
            if logo_url:
                st.html(
                    f'<div style="display:inline-flex;align-items:center;gap:8px;padding:3px 10px;'
                    f'border-radius:8px;border:1px solid rgba(128,128,128,0.22);margin-bottom:6px;">'
                    f'<span style="width:20px;height:20px;border-radius:5px;background:#fff;padding:1px;display:inline-flex;align-items:center;justify-content:center;">'
                    f'<img src="{logo_url}" style="width:100%;height:100%;object-fit:contain;"/></span>'
                    f'<span style="font-size:0.78rem;font-weight:700;">{html.escape(title)}</span>'
                    f'<span style="font-size:0.74rem;opacity:0.72;">· {html.escape(badge)}</span></div>'
                )
            st.markdown(reply)

        st.session_state.ai_chat_history.append(
            {"question": prompt, "answer": reply, "badge": badge, "stock": title, "logo": logo_url}
        )


def page_ai_advisor() -> None:
    st.title("FinanceSight Universal AI Advisor", icon=":material/smart_toy:")
    _ai_advisor_chat_fragment()


@st.fragment
def _algo_scanner_fragment() -> None:
    snaps, _, _, _, _ = get_market_context()

    apps_view = st.segmented_control(
        "Algo & Scanner View",
        ["No-Code Strategy Backtester", "Live Multi-Market Scanner"],
        default="No-Code Strategy Backtester",
        key="apps_view",
        label_visibility="collapsed",
    ) or "No-Code Strategy Backtester"

    if apps_view == "No-Code Strategy Backtester":
        c1, c2, c3, c4 = st.columns([1.4, 1.8, 0.9, 0.9])
        all_syms = list(STOCK_CATALOG.keys())
        cur_i = all_syms.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in all_syms else 0
        bt_sym = c1.selectbox(
            "Equity (345+ Stocks)",
            all_syms,
            index=cur_i,
            format_func=lambda s: f"{s} — {STOCK_CATALOG[s]['name']} ({STOCK_CATALOG[s]['exchange']})",
            key="bt_sym",
        )
        bt_strat = c2.selectbox("Strategy Rule", BACKTEST_STRATEGIES, key="bt_strat")
        sl_pct = c3.slider("Stop-Loss (%)", 1.0, 10.0, 3.0, 0.5, key="bt_sl")
        tp_pct = c4.slider("Take-Profit (%)", 2.0, 25.0, 6.0, 0.5, key="bt_tp")

        bt_tf = st.segmented_control("Backtest Horizon", ["6mo", "1y", "2y"], default="1y", key="bt_tf") or "1y"
        meta = get_ticker_meta(bt_sym)
        cur = meta["currency"]

        st.html(
            f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0 8px 0;">'
            f'{stock_icon_html(bt_sym, size=34, radius=9)}'
            f'<div><div style="font-weight:800;font-size:1.0rem;">{html.escape(meta["name"])} '
            f'<span style="opacity:0.7;font-family:JetBrains Mono,monospace;">({html.escape(bt_sym)})</span></div>'
            f'<div style="font-size:0.78rem;opacity:0.72;">{meta["exchange"]} · {html.escape(meta["sector"])} · {bt_strat}</div></div></div>'
        )

        raw_hist = fetch_stock_history(bt_sym, bt_tf)
        if raw_hist is None or len(raw_hist) < 55:
            st.warning("Unable to load enough historical candles for this backtest window.")
        else:
            res = run_backtest_cached(bt_sym, str(raw_hist.index[-1]), raw_hist, bt_strat, 100000.0, sl_pct, tp_pct, cur)
            if res.get("empty"):
                st.warning("Not enough indicator bars for the selected window.")
            else:
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("Final Capital", f"{cur}{res['final_capital']:,.0f}", f"{res['total_ret']:+.2f}%", border=True, height="stretch")
                k2.metric("Buy & Hold", f"{res['bh_ret']:+.2f}%", f"Alpha: {res['alpha']:+.2f}%", border=True, height="stretch")
                k3.metric("Sharpe Ratio", f"{res['sharpe']:.2f}", f"Max DD: {res['max_drawdown']:.2f}%", delta_color="off", border=True, height="stretch")
                k4.metric("Win Rate", f"{res['win_rate']:.1f}%", f"{res['wins_count']}/{len(res['trades_log'])} Wins", delta_color="off", border=True, height="stretch")
                k5.metric("Profit Factor", f"{res['profit_factor']:.2f}", f"R:R 1:{tp_pct/sl_pct:.1f}", delta_color="off", border=True, height="stretch")

                eq_fig = go.Figure()
                eq_fig.add_trace(go.Scatter(x=res["eq_series"].index, y=res["eq_series"].values, name="Strategy Equity", fill="tozeroy", line=dict(color="#3b82f6", width=2.4), fillcolor="rgba(59,130,246,0.12)"))
                eq_fig.add_trace(go.Scatter(x=res["bh_series"].index, y=res["bh_series"].values, name="Buy & Hold Benchmark", line=dict(color="#94a3b8", width=1.8, dash="dot")))
                eq_fig.update_layout(title=f"Mark-to-Market Equity Curve vs. Buy & Hold ({cur}100,000 Base)", height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=36, b=10))
                st.plotly_chart(eq_fig, theme="streamlit", alt=f"Strategy equity curve versus buy and hold benchmark for {bt_sym}")

                sig_fig = go.Figure()
                bt_df = res["bt_df"]
                sig_fig.add_trace(go.Scatter(x=bt_df.index, y=bt_df["Close"], name="Close Price", line=dict(color="#0ea5e9", width=1.8)))
                buys = [p for p in res["signal_points"] if p["type"] == "BUY"]
                sells = [p for p in res["signal_points"] if p["type"] == "SELL"]
                if buys:
                    sig_fig.add_trace(go.Scatter(x=[p["date"] for p in buys], y=[p["price"] for p in buys], mode="markers", name="Entry (BUY)", marker=dict(symbol="triangle-up", size=11, color="#10b981")))
                if sells:
                    sig_fig.add_trace(go.Scatter(x=[p["date"] for p in sells], y=[p["price"] for p in sells], mode="markers", name="Exit (SELL)", marker=dict(symbol="triangle-down", size=11, color="#ef4444")))
                sig_fig.update_layout(title=f"Trade Signals on Price Chart ({bt_sym})", height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=36, b=10))
                st.plotly_chart(sig_fig, theme="streamlit", alt=f"Buy entry and sell exit markers plotted over price history for {bt_sym}")

                if res["trades_log"]:
                    t_df = pd.DataFrame(res["trades_log"])
                    st.dataframe(t_df, hide_index=True, alt="Backtest simulated trades ledger")
                    st.download_button(
                        "Download Backtest Trades (CSV)",
                        data=t_df.to_csv(index=False).encode("utf-8"),
                        file_name=f"{bt_sym}_backtest.csv",
                        mime="text/csv",
                        icon=":material/download:",
                    )
                else:
                    st.info("No entry signals triggered in this timeframe under the current strategy rules.")

    elif apps_view == "Live Multi-Market Scanner":
        sc1, sc2, sc3 = st.columns([1.4, 1.1, 1.1], vertical_alignment="bottom")
        scan_q = sc1.text_input("Search Scanner", type="search", placeholder="Ticker, company, or sector...", key="scan_q")
        scan_sec = sc2.selectbox("Sector", ["All Sectors"] + sorted({v["sector"] for v in STOCK_CATALOG.values()}), key="scan_sec")
        ex_sel = sc3.segmented_control("Filter Exchange", ["All", "NSE", "US"], default="All", key="scan_ex") or "All"

        filtered_syms = []
        ql = scan_q.strip().lower()
        for sym, meta in STOCK_CATALOG.items():
            if ex_sel == "NSE" and meta["exchange"] != "NSE":
                continue
            if ex_sel == "US" and meta["exchange"] == "NSE":
                continue
            if scan_sec != "All Sectors" and meta["sector"] != scan_sec:
                continue
            if ql and (ql not in sym.lower() and ql not in meta["name"].lower() and ql not in meta["sector"].lower()):
                continue
            filtered_syms.append(sym)

        scan_page_size = 30
        total_scan = len(filtered_syms)
        max_scan_pages = max(1, (total_scan + scan_page_size - 1) // scan_page_size)
        scan_sig = f"{ex_sel}|{scan_sec}|{ql}"
        if st.session_state.get("_scan_sig") != scan_sig:
            st.session_state["_scan_sig"] = scan_sig
            st.session_state["scan_page"] = 0
        s_page = min(max(0, int(st.session_state.get("scan_page", 0))), max_scan_pages - 1)
        s_start = s_page * scan_page_size
        vis_syms = filtered_syms[s_start : s_start + scan_page_size]

        sn_l, sn_c, sn_r = st.columns([2.2, 0.9, 0.9], vertical_alignment="center")
        sn_l.caption(f"Showing **{s_start + 1 if total_scan else 0}–{min(s_start + scan_page_size, total_scan)}** of **{total_scan}** matching stocks (Live page fetch)")
        if max_scan_pages > 1:
            sn_c.button(
                "Previous",
                icon=":material/chevron_left:",
                disabled=s_page == 0,
                width="stretch",
                key="scan_prev",
                on_click=_shift_page_cb,
                args=("scan_page", -1),
            )
            sn_r.button(
                f"Next ({s_page + 1}/{max_scan_pages})",
                icon=":material/chevron_right:",
                disabled=s_page >= max_scan_pages - 1,
                width="stretch",
                key="scan_next",
                on_click=_shift_page_cb,
                args=("scan_page", 1),
            )

        full_snaps = ensure_symbols_live(vis_syms, snaps) if vis_syms else snaps
        scan_rows = []
        for sym in vis_syms:
            meta = STOCK_CATALOG[sym]
            sn = full_snaps.get(sym, DEFAULT_STOCKS_SNAPSHOTS.get(sym, {"price": 100.0, "pct": 0.0, "rsi": 50.0, "above_sma": True, "sparkline": []}))
            sig = "Bullish Breakout" if sn.get("above_sma", True) and sn.get("rsi", 50.0) > 52 else ("Oversold Bounce" if sn.get("rsi", 50.0) < 42 else "Bearish / Neutral")
            scan_rows.append(
                {
                    "Logo": get_logo_url(sym),
                    "Symbol": sym,
                    "Company": meta["name"],
                    "Exchange": meta["exchange"],
                    "Sector": meta["sector"],
                    "Price": f"{meta['currency']}{sn['price']:,.2f}",
                    "Day %": round(sn["pct"], 2),
                    "RSI (14)": round(sn["rsi"], 1),
                    "20D Trend": sn.get("sparkline", []),
                    "Signal": [sig],
                }
            )
        st.dataframe(
            pd.DataFrame(scan_rows),
            column_config={
                "Logo": st.column_config.ImageColumn("", width="small"),
                "Day %": st.column_config.NumberColumn("Day %", format="%.2f%%"),
                "RSI (14)": st.column_config.ProgressColumn("RSI (14)", min_value=0, max_value=100, format="%.1f"),
                "20D Trend": st.column_config.LineChartColumn("20D Sparkline"),
                "Signal": st.column_config.MultiselectColumn("Signal", options=["Bullish Breakout", "Oversold Bounce", "Bearish / Neutral"], color=["green", "blue", "red"]),
            },
            hide_index=True,
            alt="Live technical scanner with company icons across 345+ NSE and US equities",
        )


def page_algo_scanner() -> None:
    st.title("Strategy Backtester & Market Scanner", icon=":material/science:")
    _algo_scanner_fragment()


def page_fee_calculator() -> None:
    st.title("Brokerage & Statutory Tax Calculator", icon=":material/calculate:")
    render_brokerage_calculator_widget("auth_calc")


def _render_traffic_light_hero_html(h: dict) -> str:
    m = h["meta"]
    cur = m["currency"]
    score = int(h["score"])
    clr = h["color"]
    probs = h["probs"]
    return f"""
    <div style="border:1px solid rgba(128,128,128,0.26);border-radius:16px;padding:20px 22px;
                background:radial-gradient(circle at 92% 15%, {clr}22, transparent 48%),var(--secondary-background-color);
                color:var(--text-color);margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;">
        <div style="display:flex;align-items:center;gap:12px;">
          {stock_icon_html(h['sym'], size=48, radius=12)}
          <div>
            <div style="font-size:1.25rem;font-weight:800;">{html.escape(m['name'])}
              <span style="font-size:0.86rem;font-family:JetBrains Mono,monospace;opacity:0.75;">({html.escape(h['sym'])})</span>
            </div>
            <div style="font-size:0.82rem;opacity:0.75;">{m['exchange']} · {html.escape(m['sector'])} · {cur}{h['price']:,.2f} ({h['pct']:+.2f}%)</div>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="display:inline-block;padding:5px 14px;border-radius:999px;font-weight:800;font-size:0.90rem;
                      color:{clr};background:{clr}1F;border:1px solid {clr}55;">
            {html.escape(h['pill'])}
          </div>
          <div style="font-size:1.55rem;font-weight:800;font-family:JetBrains Mono,monospace;margin-top:4px;">
            {score}<span style="font-size:0.92rem;opacity:0.65;"> / 100 Health Score</span>
          </div>
        </div>
      </div>
      <div style="width:100%;height:10px;background:rgba(128,128,128,0.22);border-radius:999px;overflow:hidden;margin:14px 0 12px 0;">
        <div style="width:{score}%;height:100%;background:linear-gradient(90deg,{clr},{clr}cc);border-radius:999px;"></div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;font-size:0.82rem;">
        <div style="background:rgba(16,185,129,0.10);border:1px solid rgba(16,185,129,0.26);border-radius:10px;padding:8px 11px;">
          <div style="opacity:0.78;">Healthy Probability</div>
          <div style="font-weight:800;font-size:1.05rem;color:#10b981;">{probs['Healthy']:.1f}%</div>
        </div>
        <div style="background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.26);border-radius:10px;padding:8px 11px;">
          <div style="opacity:0.78;">Moderate Probability</div>
          <div style="font-weight:800;font-size:1.05rem;color:#f59e0b;">{probs['Moderate']:.1f}%</div>
        </div>
        <div style="background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.26);border-radius:10px;padding:8px 11px;">
          <div style="opacity:0.78;">High Risk Probability</div>
          <div style="font-weight:800;font-size:1.05rem;color:#ef4444;">{probs['High Risk']:.1f}%</div>
        </div>
      </div>
    </div>
    """


def page_smart_basket() -> None:
    snaps, _, usdinr, _, _ = get_market_context()
    artifacts = load_trained_ml_artifacts()
    metrics = artifacts.get("metrics") or {}
    all_sectors = sorted({v["sector"] for v in STOCK_CATALOG.values()})

    st.title("Smart Basket Builder", icon=":material/auto_awesome:")
    trained_info = (
        f":green-badge[3Y Trained ML Active · {metrics.get('tickers_trained', 345)} Stocks]"
        if artifacts.get("loaded")
        else ":orange-badge[Baseline Risk Engine Active]"
    )
    st.markdown(f"Automated multi-stock portfolio allocation using ML health scoring & covariance risk parity. &nbsp; {trained_info}")

    acct = get_user_account_summary(st.session_state.username, snaps, usdinr)

    with st.container(border=True):
        b1, b2, b3, b4 = st.columns([1.15, 1.15, 1.25, 0.85], vertical_alignment="bottom")
        sb_budget = b1.number_input("Investment Budget (₹)", min_value=2000.0, max_value=500000.0, value=25000.0, step=2500.0, key="g_budget")
        sb_risk = b2.selectbox("Comfort Level", ["Safe & Steady", "Balanced Mix", "High Growth"], index=1, key="g_risk")
        sb_mkt = b3.selectbox("Market Region", ["Global Mix (India + US)", "India (NSE)", "US (NASDAQ/NYSE)"], key="g_mkt")
        sb_count = b4.selectbox("Stocks in Basket", [4, 5, 6, 7], index=1, key="g_count")

        o1, o2, o3 = st.columns([1.3, 1.8, 0.9], vertical_alignment="bottom")
        sb_weight_mode = o1.selectbox(
            "Allocation Strategy",
            ["Risk-Parity (Inverse Volatility)", "ML Score Weighted", "Equal Weight"],
            key="g_weight_mode",
        )
        sb_sectors = o2.multiselect(
            "Focus Sectors (Optional — leave empty for auto sector spread)",
            options=all_sectors,
            key="g_sectors",
        )
        build_clicked = o3.button("Build Basket", type="primary", icon=":material/auto_awesome:", width="stretch", key="build_basket_btn")

    basket_sig = f"{sb_budget}|{sb_risk}|{sb_mkt}|{sb_count}|{sb_weight_mode}|{','.join(sorted(sb_sectors))}"
    if build_clicked or st.session_state.get("_smart_basket_sig") != basket_sig or "_smart_basket_res" not in st.session_state:
        with st.spinner("Running 3Y-trained ML scoring & 6M return covariance optimizer..."):
            st.session_state["_smart_basket_res"] = build_beginner_smart_basket(
                budget_inr=float(sb_budget),
                risk_profile=sb_risk,
                market_pref=sb_mkt,
                snapshots=snaps,
                usdinr_rate=usdinr,
                basket_size=int(sb_count),
                weight_mode=sb_weight_mode,
                preferred_sectors=sb_sectors,
            )
            st.session_state["_smart_basket_sig"] = basket_sig

    b_res = st.session_state.get("_smart_basket_res") or {}
    items = b_res.get("items", [])
    if not items:
        st.warning("Unable to construct an affordable basket for that filter and budget. Increase budget or clear sector filters.")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Basket Cost (INR)", f"₹{b_res['total_cost_inr']:,.2f}", f"Cash Left: ₹{b_res['leftover_inr']:,.2f}", delta_color="off", border=True, height="stretch")
    k2.metric("Diversified Picks", f"{len(items)} Stocks", f"{len({it['meta']['sector'] for it in items})} Sectors · {b_res['market_pref'].split(' ')[0]}", delta_color="off", border=True, height="stretch")
    k3.metric("Risk Reduction", f"-{b_res['diversification_reduction_pct']:.1f}% Vol", f"Port {b_res['portfolio_vol_pct']:.1f}% vs {b_res['avg_indiv_vol_pct']:.1f}%", delta_color="off", border=True, height="stretch")
    k4.metric("Avg Health Score", f"{b_res['avg_health']:.0f} / 100", f"Margin: ₹{acct['balance']:,.0f}", delta_color="off", border=True, height="stretch")

    c_donut, c_cards = st.columns([1.05, 1.55], gap="medium")
    with c_donut.container(border=True, height="stretch"):
        st.subheader("Portfolio Weight Distribution", icon=":material/pie_chart:")
        fig_d = go.Figure(
            data=[
                go.Pie(
                    labels=[f"{it['sym'].replace('.NS', '')} ({it['actual_wt_pct']:.0f}%)" for it in items],
                    values=[it["cost_inr"] for it in items],
                    hole=0.55,
                )
            ]
        )
        fig_d.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=8, r=8, t=12, b=8))
        st.plotly_chart(fig_d, theme="streamlit", alt="Donut chart of allocated smart basket portfolio weights")

        st.markdown("**Estimated 1-Year Outcome Range**")
        p1, p2, p3 = st.columns(3)
        p1.metric("Safe Floor", f"₹{b_res['proj_1y_floor']:,.0f}", border=True)
        p2.metric("Projected", f"₹{b_res['proj_1y_expected']:,.0f}", border=True)
        p3.metric("Upside", f"₹{b_res['proj_1y_upside']:,.0f}", border=True)

    with c_cards.container(border=True, height="stretch"):
        st.subheader(f"Your {len(items)}-Stock Smart Basket ({sb_weight_mode.split(' ')[0]})", icon=":material/layers:")
        for it in items:
            st.html(
                f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;'
                f'padding:9px 12px;margin-bottom:7px;border-radius:11px;border:1px solid rgba(128,128,128,0.22);">'
                f'<div style="display:flex;align-items:center;gap:10px;min-width:0;">'
                f'{stock_icon_html(it["sym"], size=34, radius=9)}'
                f'<div style="min-width:0;">'
                f'<div style="font-weight:700;font-size:0.93rem;">{html.escape(it["meta"]["name"])} '
                f'<span style="font-size:0.78rem;font-family:JetBrains Mono,monospace;opacity:0.72;">({html.escape(it["sym"])}) · {it["actual_wt_pct"]:.1f}%</span></div>'
                f'<div style="font-size:0.75rem;opacity:0.78;">{html.escape(it["why_picked"])}</div>'
                f'</div></div>'
                f'<div style="text-align:right;white-space:nowrap;">'
                f'<div style="font-weight:800;font-family:JetBrains Mono,monospace;">{it["qty"]} sh · ₹{it["cost_inr"]:,.0f}</div>'
                f'<div style="font-size:0.74rem;font-weight:700;color:{it["color"]};">{html.escape(it["pill"])}</div>'
                f'</div></div>'
            )

        ex_l, ex_wl, ex_csv = st.columns([1.3, 1.0, 0.9])
        if ex_l.button(f"Invest All {len(items)} Stocks (1-Click)", type="primary", icon=":material/rocket_launch:", width="stretch", key="exec_basket_btn"):
            ok_any, msgs, spent = execute_smart_basket(
                st.session_state.username,
                b_res,
                usdinr,
                allow_after_hours=st.session_state.allow_after_hours,
            )
            if ok_any:
                st.success(f"Deployed **₹{spent:,.2f}** across your {len(items)}-stock Smart Basket!")
                st.toast("Smart Basket orders executed!", icon=":material/check_circle:")
            else:
                st.warning("Market is currently closed for one or more exchanges. Enable 'Allow Demo Orders Outside Hours' below to simulate outside hours.")
            st.markdown("\n".join(msgs))

        if ex_wl.button("Save All to Watchlist", icon=":material/star:", width="stretch", key="basket_save_wl"):
            cur_wl = set(get_user_watchlist(st.session_state.username))
            added_cnt = 0
            for it in items:
                if it["sym"] not in cur_wl:
                    toggle_watchlist(st.session_state.username, it["sym"])
                    added_cnt += 1
            st.toast(f"Added {added_cnt} new stock(s) to Watchlist!")

        basket_csv_df = pd.DataFrame([
            {
                "Symbol": it["sym"],
                "Company": it["meta"]["name"],
                "Exchange": it["meta"]["exchange"],
                "Sector": it["meta"]["sector"],
                "Shares": it["qty"],
                "Cost_INR": it["cost_inr"],
                "Weight_Pct": it["actual_wt_pct"],
                "Health_Score": it["score"],
                "Health_Rating": it["label"],
            }
            for it in items
        ])
        ex_csv.download_button(
            "Export CSV",
            data=basket_csv_df.to_csv(index=False).encode("utf-8"),
            file_name="financesight_smart_basket.csv",
            mime="text/csv",
            icon=":material/download:",
            width="stretch",
        )

        st.toggle(
            "Allow Demo Orders Outside Market Hours",
            value=st.session_state.allow_after_hours,
            key="basket_after_hrs",
            on_change=_sync_after_hours_cb,
            args=("basket_after_hrs",),
        )

    corr_df = b_res.get("corr_df")
    with st.expander("Portfolio Covariance & 6-Month Correlation Analysis"):
        st.markdown(
            f"- **Weighting Method ({sb_weight_mode}):** Balances position sizing across distinct sectors and risk profiles.\n"
            f"- **Portfolio Variance Reduction:** Weighted standalone volatility is **`{b_res['avg_indiv_vol_pct']:.1f}%`**, reduced to **`{b_res['portfolio_vol_pct']:.1f}%`** (`-{b_res['diversification_reduction_pct']:.1f}%` risk reduction) with average pairwise correlation **`{b_res['avg_corr']:.2f}`**."
        )
        if corr_df is not None and not corr_df.empty:
            hm = go.Figure(
                data=go.Heatmap(
                    z=corr_df.values,
                    x=list(corr_df.columns),
                    y=list(corr_df.index),
                    zmin=-1,
                    zmax=1,
                    colorscale="RdBu",
                    reversescale=True,
                    text=corr_df.values,
                    texttemplate="%{text:.2f}",
                )
            )
            hm.update_layout(height=320, title="6-Month Daily Return Correlation Matrix", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(hm, theme="streamlit", alt="6-month daily return correlation heatmap across smart basket equities")


def page_stock_health() -> None:
    snaps, _, usdinr, _, _ = get_market_context()
    artifacts = load_trained_ml_artifacts()
    metrics = artifacts.get("metrics") or {}
    all_sectors = ["All Sectors"] + sorted({v["sector"] for v in STOCK_CATALOG.values()})

    st.title("Traffic-Light Stock Health", icon=":material/health_and_safety:")
    trained_info = (
        f":green-badge[Trained ML Active · {metrics.get('tickers_trained', 345)} Stocks · "
        f"{metrics.get('total_rows', 0):,} Samples]"
        if artifacts.get("loaded")
        else ":orange-badge[Baseline Risk Engine Active]"
    )
    st.markdown(f"Plain-English 20-day stock health scores powered by 3-year trained classification models. &nbsp; {trained_info}")

    tab_screener, tab_inspect, tab_model = st.tabs([
        "Stock Health Explorer (10 Per Page)",
        "Single-Stock Deep Dive",
        "Model Benchmarks & Dataset",
    ])

    with tab_screener:
        f1, f2, f3, f4, f5 = st.columns([1.4, 0.85, 1.05, 0.95, 1.25], vertical_alignment="bottom")
        h_q = f1.text_input("Search Stocks", type="search", placeholder="Name, ticker, sector...", key="hl_search")
        h_ex = f2.selectbox("Exchange", ["All", "NSE", "US"], key="hl_ex")
        h_sec = f3.selectbox("Sector", all_sectors, key="hl_sec")
        h_light = f4.selectbox("Health Light", ["All Lights", "Healthy", "Moderate", "High Risk"], key="hl_light")
        h_sort = f5.selectbox(
            "Sort By",
            [
                "Health Score (High to Low)",
                "Health Score (Low to High)",
                "Day Move (% High to Low)",
                "Lowest Volatility",
                "Name (A–Z)",
            ],
            key="hl_sort",
        )

        quick_rows = []
        ql = h_q.strip().lower()
        for sym, meta in STOCK_CATALOG.items():
            if h_ex == "NSE" and meta["exchange"] != "NSE":
                continue
            if h_ex == "US" and meta["exchange"] == "NSE":
                continue
            if h_sec != "All Sectors" and meta["sector"] != h_sec:
                continue
            if ql and (ql not in sym.lower() and ql not in meta["name"].lower() and ql not in meta["sector"].lower()):
                continue
            q_item = score_quick_health_baseline(sym, snaps)
            if h_light != "All Lights" and q_item["label"] != h_light:
                continue
            quick_rows.append(q_item)

        if h_sort == "Health Score (High to Low)":
            quick_rows.sort(key=lambda r: (r["score"], r["pct"]), reverse=True)
        elif h_sort == "Health Score (Low to High)":
            quick_rows.sort(key=lambda r: (r["score"], r["pct"]), reverse=False)
        elif h_sort == "Day Move (% High to Low)":
            quick_rows.sort(key=lambda r: r["pct"], reverse=True)
        elif h_sort == "Lowest Volatility":
            quick_rows.sort(key=lambda r: r["vol_est"], reverse=False)
        else:
            quick_rows.sort(key=lambda r: r["meta"]["name"])

        if not quick_rows:
            st.info("No stocks matched those search and health filters.")
        else:
            page_size = 10
            total_rows = len(quick_rows)
            max_pages = max(1, (total_rows + page_size - 1) // page_size)
            hl_sig = f"{h_q.strip().lower()}|{h_ex}|{h_sec}|{h_light}|{h_sort}"
            if st.session_state.get("_hl_sig") != hl_sig:
                st.session_state["_hl_sig"] = hl_sig
                st.session_state["hl_page"] = 0
            cur_p = min(max(0, int(st.session_state.get("hl_page", 0))), max_pages - 1)
            start_i = cur_p * page_size
            page_items = quick_rows[start_i : start_i + page_size]
            page_syms = [r["sym"] for r in page_items]

            p_top_l, p_top_p, p_top_n = st.columns([2.2, 0.9, 0.9], vertical_alignment="center")
            p_top_l.caption(f"Showing **{start_i + 1}–{min(start_i + page_size, total_rows)}** of **{total_rows}** equities (`10` per page · Live 3Y ML Evaluation)")
            if max_pages > 1:
                p_top_p.button("Previous 10", icon=":material/chevron_left:", disabled=cur_p == 0, width="stretch", key="hl_prev_top", on_click=_shift_page_cb, args=("hl_page", -1))
                p_top_n.button(f"Next 10 ({cur_p + 1}/{max_pages})", icon=":material/chevron_right:", disabled=cur_p >= max_pages - 1, width="stretch", key="hl_next_top", on_click=_shift_page_cb, args=("hl_page", 1))

            live_page_snaps = ensure_symbols_live(page_syms, snaps)
            hist_page_map = fetch_basket_candidate_histories(tuple(page_syms))

            eval_cards = [
                compute_traffic_light_health(sym, hist_page_map.get(sym), live_page_snaps.get(sym))
                for sym in page_syms
            ]
            if h_sort == "Health Score (High to Low)":
                eval_cards.sort(key=lambda r: r["score"], reverse=True)
            elif h_sort == "Health Score (Low to High)":
                eval_cards.sort(key=lambda r: r["score"])
            elif h_sort == "Day Move (% High to Low)":
                eval_cards.sort(key=lambda r: r["pct"], reverse=True)
            elif h_sort == "Lowest Volatility":
                eval_cards.sort(key=lambda r: r["ann_vol_pct"])
            else:
                eval_cards.sort(key=lambda r: r["meta"]["name"])

            for row_i in range(0, len(eval_cards), 2):
                cols = st.columns(2, gap="medium")
                for col_i in range(2):
                    idx = row_i + col_i
                    if idx >= len(eval_cards):
                        continue
                    hc = eval_cards[idx]
                    m = hc["meta"]
                    clr = hc["color"]
                    with cols[col_i].container(border=True, height="stretch"):
                        st.html(
                            f'<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px;">'
                            f'<div style="display:flex;align-items:center;gap:10px;min-width:0;">'
                            f'{stock_icon_html(hc["sym"], size=36, radius=9)}'
                            f'<div style="min-width:0;">'
                            f'<div style="font-weight:800;font-size:0.98rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html.escape(m["name"])}</div>'
                            f'<div style="font-size:0.76rem;opacity:0.75;font-family:JetBrains Mono,monospace;">{html.escape(hc["sym"])} · {m["exchange"]} · {m["currency"]}{hc["price"]:,.2f} ({hc["pct"]:+.2f}%)</div>'
                            f'</div></div>'
                            f'<div style="text-align:right;white-space:nowrap;">'
                            f'<span style="padding:3px 9px;border-radius:999px;font-weight:700;font-size:0.76rem;color:{clr};background:{clr}1F;border:1px solid {clr}55;">{html.escape(hc["pill"])}</span>'
                            f'<div style="font-weight:800;font-size:1.05rem;font-family:JetBrains Mono,monospace;margin-top:3px;">{hc["score"]}/100</div>'
                            f'</div></div>'
                            f'<div style="width:100%;height:7px;background:rgba(128,128,128,0.20);border-radius:999px;overflow:hidden;margin-bottom:8px;">'
                            f'<div style="width:{hc["score"]}%;height:100%;background:{clr};border-radius:999px;"></div></div>'
                            f'<div style="font-size:0.76rem;opacity:0.86;line-height:1.45;">'
                            f'<div><b>Trend:</b> {html.escape(hc["trend_plain"])}</div>'
                            f'<div><b>Timing:</b> {html.escape(hc["timing_plain"])}</div>'
                            f'<div><b>Risk:</b> {html.escape(hc["risk_plain"])}</div>'
                            f'</div>'
                        )
                        st.caption(f"Healthy: `{hc['probs']['Healthy']:.0f}%` · Moderate: `{hc['probs']['Moderate']:.0f}%` · High Risk: `{hc['probs']['High Risk']:.0f}%`")
                        cb1, cb2 = st.columns(2)
                        if cb1.button("Buy 1 Share", icon=":material/shopping_bag:", width="stretch", key=f"hl_buy_{hc['sym']}"):
                            ok_b, msg_b = execute_trade(
                                st.session_state.username, hc["sym"], "BUY", 1, float(hc["price"]), "CNC (Delivery)",
                                usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
                            )
                            if ok_b:
                                st.toast(msg_b, icon=":material/check_circle:")
                            else:
                                st.warning(msg_b)
                        if cb2.button("SuperChart", icon=":material/candlestick_chart:", width="stretch", key=f"hl_sc_{hc['sym']}"):
                            _jump_to_page("Terminal", hc["sym"])

            if max_pages > 1:
                p_b_l, p_b_p, p_b_n = st.columns([2.2, 0.9, 0.9], vertical_alignment="center")
                p_b_l.caption(f"Page **{cur_p + 1}** of **{max_pages}**")
                p_b_p.button("Previous 10", icon=":material/chevron_left:", disabled=cur_p == 0, width="stretch", key="hl_prev_btm", on_click=_shift_page_cb, args=("hl_page", -1))
                p_b_n.button("Next 10", icon=":material/chevron_right:", disabled=cur_p >= max_pages - 1, width="stretch", key="hl_next_btm", on_click=_shift_page_cb, args=("hl_page", 1))

    with tab_inspect:
        st.caption("Select any stock for a full single-asset health scorecard and probability breakdown.")
        all_syms = list(STOCK_CATALOG.keys())
        cur_i = all_syms.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in all_syms else 0
        h_sym = st.selectbox(
            f"Choose Any Stock ({len(all_syms)} Equities)",
            all_syms,
            index=cur_i,
            format_func=lambda s: f"{s} — {STOCK_CATALOG[s]['name']} ({STOCK_CATALOG[s]['exchange']})",
            key="health_pick_sym",
        )
        snaps_h = ensure_symbols_live([h_sym], snaps)
        h_df = fetch_stock_history(h_sym, "1y")
        h_res = compute_traffic_light_health(h_sym, h_df, snaps_h.get(h_sym))
        st.html(_render_traffic_light_hero_html(h_res))

        p1, p2, p3 = st.columns(3)
        with p1.container(border=True, height="stretch"):
            st.markdown("#### :material/trending_up: 1. Trend Direction")
            st.write(h_res["trend_plain"])
        with p2.container(border=True, height="stretch"):
            st.markdown("#### :material/schedule: 2. Price Timing")
            st.write(h_res["timing_plain"])
        with p3.container(border=True, height="stretch"):
            st.markdown("#### :material/shield: 3. Risk & Stability")
            st.write(h_res["risk_plain"])

        st.caption(f"ML Model Used: `{h_res['model_used']}` · Suitability Score: `{h_res['suitability']:+.3f}` · 60D Drawdown: `{h_res['drawdown_pct']:+.1f}%`")
        qa1, qa2 = st.columns(2)
        if qa1.button(f"Buy 1 Share of {h_sym.replace('.NS', '')} (CNC)", type="primary", icon=":material/shopping_bag:", width="stretch", key="health_buy_1"):
            ok, msg = execute_trade(
                st.session_state.username, h_sym, "BUY", 1, float(h_res["price"]), "CNC (Delivery)",
                usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
            )
            if ok:
                st.toast(msg, icon=":material/check_circle:")
                st.success(msg)
            else:
                st.warning(msg)
        if qa2.button("Inspect Candlestick & Forecast in SuperChart", icon=":material/candlestick_chart:", width="stretch", key="health_go_sc"):
            _jump_to_page("Terminal", h_sym)

    with tab_model:
        if not metrics:
            st.info("Run `python train_models.py` to generate model benchmarks and dataset metrics.")
        else:
            mk1, mk2, mk3, mk4 = st.columns(4)
            mk1.metric("Stocks in Dataset", f"{metrics.get('tickers_trained', 0)}", f"{metrics.get('period', '3y')} Daily Yahoo OHLCV", delta_color="off", border=True, height="stretch")
            mk2.metric("Total Samples", f"{metrics.get('total_rows', 0):,}", f"Split: {metrics.get('split_date', '')}", delta_color="off", border=True, height="stretch")
            best_clf = next((r for r in metrics.get("classifier_benchmarks", []) if r["Model"] == metrics.get("best_classifier")), {})
            mk3.metric("Health Classifier AUC", f"{best_clf.get('ROC-AUC (%)', 0):.2f}%", f"{metrics.get('best_classifier', '')} · Macro F1 {best_clf.get('Macro F1 (%)', 0):.1f}%", delta_color="off", border=True, height="stretch")
            best_reg = next((r for r in metrics.get("regressor_benchmarks", []) if r["Model"] == metrics.get("best_regressor")), {})
            mk4.metric("Basket Hit Rate", f"{best_reg.get('Directional Hit Rate (%)', 0):.2f}%", f"{metrics.get('best_regressor', '')} · RMSE {best_reg.get('Test RMSE', 0):.3f}", delta_color="off", border=True, height="stretch")

            st.space("small")
            b_l, b_r = st.columns(2, gap="medium")
            with b_l.container(border=True, height="stretch"):
                st.subheader("3-Class Health Benchmarks (Unseen 20% Test)", icon=":material/fact_check:")
                st.dataframe(pd.DataFrame(metrics.get("classifier_benchmarks", [])), hide_index=True, alt="Out-of-sample classification benchmarks across Logistic Regression, Random Forest, and HistGradientBoosting")
                st.caption("Labels: `Healthy` (20D Vol <=27%, Drawdown >-5.5%, Return >=-1%), `Moderate`, `High Risk` (Vol >=37% or Drawdown <=-9.5%).")
            with b_r.container(border=True, height="stretch"):
                st.subheader("Smart Basket Alpha Benchmarks (Unseen 20% Test)", icon=":material/analytics:")
                st.dataframe(pd.DataFrame(metrics.get("regressor_benchmarks", [])), hide_index=True, alt="Out-of-sample risk-adjusted return regressor benchmarks")
                st.caption(f"Train Window: `{metrics.get('date_start')}` to `{metrics.get('split_date')}` ({metrics.get('train_rows', 0):,} rows) · Test Window up to `{metrics.get('date_end')}` ({metrics.get('test_rows', 0):,} rows).")

            c_cm, c_imp = st.columns(2, gap="medium")
            with c_cm.container(border=True, height="stretch"):
                st.subheader("Test Set Confusion Matrix", icon=":material/grid_on:")
                cm_vals = metrics.get("confusion_matrix", [])
                cm_lbls = metrics.get("confusion_matrix_labels", ["High Risk", "Moderate", "Healthy"])
                if cm_vals:
                    cm_fig = go.Figure(
                        data=go.Heatmap(
                            z=cm_vals,
                            x=[f"Pred: {l}" for l in cm_lbls],
                            y=[f"True: {l}" for l in cm_lbls],
                            colorscale="Blues",
                            text=cm_vals,
                            texttemplate="%{text:,}",
                        )
                    )
                    cm_fig.update_layout(height=310, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(cm_fig, theme="streamlit", alt="3x3 out-of-sample confusion matrix heatmap")

            with c_imp.container(border=True, height="stretch"):
                st.subheader("Top Predictive Features (%)", icon=":material/bar_chart:")
                imp_dict = metrics.get("feature_importance_pct", {})
                if imp_dict:
                    imp_df = pd.DataFrame([{"Feature": k, "Importance (%)": v} for k, v in list(imp_dict.items())[:10]])
                    imp_c = (
                        alt.Chart(imp_df)
                        .mark_bar(cornerRadiusEnd=4, color="#10b981")
                        .encode(x="Importance (%):Q", y=alt.Y("Feature:N", sort="-x"))
                        .properties(height=280)
                    )
                    st.altair_chart(imp_c, alt="Top 10 technical and volatility features learned from 3-year historical data")

            preview_path = MODELS_DIR / "dataset_preview.csv"
            if preview_path.exists():
                with st.container(border=True):
                    st.subheader("Engineered 3-Year Historical Dataset Sample (`models/dataset_preview.csv`)", icon=":material/table_view:")
                    st.dataframe(pd.read_csv(preview_path).head(25), hide_index=True, alt="Sample rows from the 3-year engineered Yahoo Finance training dataset")


def render_sidebar() -> None:
    snaps, _, usdinr, is_live, _ = get_market_context()
    user_bal = get_user_balance(st.session_state.username)

    with st.sidebar:
        st.markdown(f"### :material/person: {st.session_state.full_name}")
        st.caption(f"`@{st.session_state.username}` · {'Live Feed' if is_live else 'Cached Baseline'}")
        st.metric("Available Margin", f"₹{user_bal:,.2f}", f"USD/INR ₹{usdinr:.2f}", delta_color="off", border=True)

        c_ref, c_out = st.columns(2)
        if c_ref.button("Refresh", icon=":material/refresh:", width="stretch"):
            fetch_core_market_snapshots.clear()
            fetch_ticker_batch.clear()
            fetch_extended_market_snapshots.clear()
            fetch_stock_history.clear()
            st.toast("Market cache cleared — fetching live prices.")
            st.rerun()
        if c_out.button("Logout", icon=":material/logout:", width="stretch"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.full_name = ""
            st.session_state.ai_chat_history = []
            st.rerun()

        st.space("small")
        st.subheader("Quick Order Ticket", icon=":material/bolt:")
        all_syms = list(STOCK_CATALOG.keys())
        cur_idx = all_syms.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in all_syms else 0
        sb_sym = st.selectbox(
            f"Select Ticker ({len(all_syms)} Stocks)",
            all_syms,
            index=cur_idx,
            format_func=lambda s: f"{s.replace('.NS', '')} — {STOCK_CATALOG[s]['name']}",
            key="sb_ticker_pick",
        )
        if sb_sym != st.session_state.selected_ticker:
            st.session_state.selected_ticker = sb_sym
            st.rerun()

        snaps = ensure_symbols_live([sb_sym], snaps)
        meta = get_ticker_meta(sb_sym)
        sn = snaps.get(sb_sym, DEFAULT_STOCKS_SNAPSHOTS.get(sb_sym, {"price": 100.0, "pct": 0.0}))
        is_open, mkt_txt = check_market_trading_hours(sb_sym)
        mv_clr = "#10b981" if sn["pct"] >= 0 else "#ef4444"
        st.html(
            f'<div style="display:flex;align-items:center;gap:9px;padding:7px 9px;border-radius:10px;'
            f'border:1px solid rgba(128,128,128,0.22);margin:4px 0 6px 0;">'
            f'{stock_icon_html(sb_sym, size=30, radius=7)}'
            f'<div style="min-width:0;flex:1;">'
            f'<div style="font-size:0.82rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html.escape(meta["name"])}</div>'
            f'<div style="font-size:0.74rem;font-family:JetBrains Mono,monospace;">'
            f'<b>{meta["currency"]}{sn["price"]:,.2f}</b> <span style="color:{mv_clr};font-weight:700;">{sn["pct"]:+.2f}%</span> · {meta["exchange"]}</div>'
            f'</div></div>'
        )
        st.caption(f"{'🟢' if is_open else '🔴'} {mkt_txt}")

        sb_prod = st.segmented_control("Product", ["CNC (Delivery)", "MIS (Intraday 5x)"], default="CNC (Delivery)", key="sb_prod") or "CNC (Delivery)"
        sb_qty = st.number_input("Qty", min_value=1, max_value=100000, value=5, step=1, key="sb_qty")
        st.toggle(
            "Allow Demo Orders Outside Hours",
            value=st.session_state.allow_after_hours,
            key="sb_after_hrs",
            on_change=_sync_after_hours_cb,
            args=("sb_after_hrs",),
        )

        b1, b2 = st.columns(2)
        if b1.button("BUY", type="primary", width="stretch", key="sb_buy"):
            ok, msg = execute_trade(
                st.session_state.username, sb_sym, "BUY", int(sb_qty), float(sn["price"]), sb_prod,
                usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
            )
            if ok:
                st.toast(msg, icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(msg)
        if b2.button("SELL", width="stretch", key="sb_sell"):
            ok, msg = execute_trade(
                st.session_state.username, sb_sym, "SELL", int(sb_qty), float(sn["price"]), sb_prod,
                usdinr_rate=usdinr, allow_after_hours=st.session_state.allow_after_hours,
            )
            if ok:
                st.toast(msg, icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(msg)

        with st.popover("AI API Key Settings", icon=":material/key:", width="stretch"):
            st.caption("Session-only override if keys are not configured in Streamlit Secrets.")
            entered_groq = st.text_input(
                "Groq API Key",
                value=st.session_state.get("user_groq_api_key", ""),
                type="password",
                placeholder="gsk_...",
                key="sb_groq_key_input",
            )
            entered_gemini = st.text_input(
                "Gemini API Key (Optional)",
                value=st.session_state.get("user_gemini_api_key", ""),
                type="password",
                placeholder="AIza...",
                key="sb_gemini_key_input",
            )
            st.session_state.user_groq_api_key = entered_groq.strip()
            st.session_state.user_gemini_api_key = entered_gemini.strip()


def run_app() -> None:
    st.set_page_config(
        page_title="FinanceSight | Market Analytics, AI Forecasting & Paper Trading",
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.logo(FINANCESIGHT_LOGO_SVG, icon_image=FINANCESIGHT_ICON_SVG, size="large")

    ensure_db_initialized()

    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("selected_ticker", "RELIANCE.NS")
    st.session_state.setdefault("ai_chat_history", [])
    st.session_state.setdefault("allow_after_hours", False)
    st.session_state.setdefault("user_groq_api_key", "")
    st.session_state.setdefault("user_gemini_api_key", "")

    snaps, idx_snaps, usdinr, is_live, stamp = fetch_core_market_snapshots()
    st.session_state["_mkt_snaps"] = snaps
    st.session_state["_idx_snaps"] = idx_snaps
    st.session_state["_usdinr"] = usdinr
    st.session_state["_is_live"] = is_live
    st.session_state["_mkt_stamp"] = stamp

    if not st.session_state.logged_in:
        p_home = st.Page(page_public_home, title="Home", icon=":material/home:", url_path="home", default=True)
        p_prod = st.Page(page_public_products, title="Products", icon=":material/layers:", url_path="products")
        p_fees = st.Page(page_public_fees, title="Brokerage & Fees", icon=":material/calculate:", url_path="fees")
        p_about = st.Page(page_public_about, title="Architecture & About", icon=":material/architecture:", url_path="about")
        p_supp = st.Page(page_public_support, title="Support", icon=":material/support_agent:", url_path="support")

        st.session_state["_pub_page_map"] = {
            "home": p_home,
            "products": p_prod,
            "fees": p_fees,
            "about": p_about,
            "support": p_supp,
        }
        nav = st.navigation([p_home, p_prod, p_fees, p_about, p_supp], position="top")
        nav.run()
    else:
        p_dash = st.Page(page_dashboard, title="Dashboard", icon=":material/dashboard:", url_path="dashboard", default=True)
        p_basket = st.Page(page_smart_basket, title="Smart Basket", icon=":material/auto_awesome:", url_path="basket")
        p_health = st.Page(page_stock_health, title="Traffic-Light Health", icon=":material/health_and_safety:", url_path="health")
        p_term = st.Page(page_superchart, title="SuperChart", icon=":material/candlestick_chart:", url_path="superchart")
        p_adv = st.Page(page_ai_advisor, title="AI Advisor", icon=":material/smart_toy:", url_path="advisor")
        p_ord = st.Page(page_orders, title="Orders", icon=":material/receipt:", url_path="orders")
        p_hold = st.Page(page_holdings, title="Holdings", icon=":material/business_center:", url_path="holdings")
        p_pos = st.Page(page_positions, title="Positions", icon=":material/monitoring:", url_path="positions")
        p_fund = st.Page(page_funds, title="Funds", icon=":material/account_balance_wallet:", url_path="funds")
        p_apps = st.Page(page_algo_scanner, title="Algo & Scanner", icon=":material/science:", url_path="scanner")
        p_calc = st.Page(page_fee_calculator, title="Fee Calculator", icon=":material/calculate:", url_path="calculator")

        st.session_state["_page_map"] = {
            "Dashboard": p_dash,
            "Basket": p_basket,
            "Health": p_health,
            "Terminal": p_term,
            "Advisor": p_adv,
            "Orders": p_ord,
            "Holdings": p_hold,
            "Positions": p_pos,
            "Funds": p_fund,
            "Apps": p_apps,
            "Calculator": p_calc,
        }

        render_sidebar()
        nav = st.navigation(
            {
                "": [p_dash, p_basket, p_health, p_term, p_adv],
                "Trading": [p_ord, p_hold, p_pos, p_fund],
                "Analytics": [p_apps, p_calc],
            },
            position="top",
        )
        nav.run()


if get_script_run_ctx() is not None:
    run_app()
