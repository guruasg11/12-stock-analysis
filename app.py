import time
import random

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="NSE Historical EOD Tracker", layout="wide")

# ---------------------------------------------------------------------------
# Full NSE Sector Universe
# ---------------------------------------------------------------------------
DEFAULT_SECTORS = {
    "My Watchlist": [
        "ASTRAL", "TATAMOTORS", "BANKBARODA", "PFC", "RECLTD",
        "HUDCO", "RVNL", "GODREJIND"
    ],
    "Nifty 50": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL",
        "ITC", "LT", "HINDUNILVR", "SBIN", "BAJFINANCE", "KOTAKBANK",
        "AXISBANK", "ASIANPAINT", "MARUTI", "HCLTECH", "SUNPHARMA",
        "TITAN", "WIPRO", "ONGC", "NTPC", "POWERGRID", "ULTRACEMCO",
        "NESTLEIND", "TECHM", "INDUSINDBK", "ADANIENT", "ADANIPORTS",
        "BAJAJFINSV", "DRREDDY", "DIVISLAB", "CIPLA", "BPCL",
        "COALINDIA", "HEROMOTOCO", "M&M", "TATASTEEL", "JSWSTEEL",
        "EICHERMOT", "GRASIM"
    ],
    "Nifty Bank": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK",
        "PNB", "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB",
        "AUBANK", "BANKBARODA"
    ],
    "Nifty IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM",
        "PERSISTENT", "MPHASIS", "COFORGE", "OFSS"
    ],
    "Nifty Auto": [
        "MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO",
        "EICHERMOT", "BOSCHLTD", "MRF", "BALKRISIND", "MOTHERSON",
        "BHARATFORG", "APOLLOTYRE"
    ],
    "Nifty FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR",
        "MARICO", "COLPAL", "GODREJCP", "EMAMILTD", "TATACONSUM",
        "UBL", "MCDOWELL-N"
    ],
    "Nifty Pharma": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
        "TORNTPHARM", "ALKEM", "AUROPHARMA", "LUPIN", "BIOCON",
        "IPCALAB", "GLENMARK"
    ],
    "Nifty Metal": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA", "VEDL",
        "SAIL", "NMDC", "APLAPOLLO", "NATIONALUM", "HINDCOPPER",
        "MOIL", "WELCORP"
    ],
    "Nifty Realty": [
        "DLF", "GODREJPROP", "OBEROIRLTY", "PHOENIXLTD", "PRESTIGE",
        "BRIGADE", "SOBHA", "SUNTECK", "KOLTEPATIL", "MAHLIFE"
    ],
    "Nifty Energy": [
        "RELIANCE", "ONGC", "NTPC", "POWERGRID", "BPCL", "IOC",
        "GAIL", "TATAPOWER", "ADANIGREEN", "ADANIPOWER",
        "ADANITRANS", "CESC"
    ],
    "Nifty Infra": [
        "LT", "ADANIPORTS", "POWERGRID", "NTPC", "BHARTIARTL",
        "RVNL", "IRFC", "PFC", "RECLTD", "HUDCO",
        "NBCC", "IRB"
    ],
    "Nifty PSU Bank": [
        "SBIN", "PNB", "BANKBARODA", "CANARABANK", "UNIONBANK",
        "BANKINDIA", "CENTRALBK", "UCOBANK", "MAHABANK", "INDIANB",
        "IOB", "J&KBANK"
    ],
    "Nifty Midcap Select": [
        "PERSISTENT", "POLYCAB", "INDIANB", "FEDERALBNK", "LTTS",
        "MPHASIS", "COFORGE", "ABCAPITAL", "SUNDARMFIN", "VOLTAS",
        "ASTRAL", "PIIND", "ZYDUSLIFE", "MAXHEALTH", "STARHEALTH",
        "MEDANTA", "CAMS", "ANGELONE", "BSE", "MCX"
    ],
    "Nifty Smallcap": [
        "RVNL", "HUDCO", "RECLTD", "IRFC", "RAILTEL", "IRCON",
        "RITES", "NBCC", "HFCL", "IDEA",
        "TRIDENT", "SUZLON", "RPOWER", "NHPC", "SJVN"
    ],
    "Nifty Financial Services": [
        "HDFCBANK", "ICICIBANK", "BAJFINANCE", "KOTAKBANK", "AXISBANK",
        "SBIN", "BAJAJFINSV", "HDFCAMC", "MUTHOOTFIN", "CHOLAFIN",
        "M&MFIN", "LICHSGFIN"
    ],
    "Nifty Consumer Durables": [
        "TITAN", "VOLTAS", "HAVELLS", "WHIRLPOOL", "BLUESTAR",
        "CROMPTON", "VGUARD", "RAJESHEXPO", "KAJARIACER", "POLYCAB"
    ],
    "Nifty Oil & Gas": [
        "RELIANCE", "ONGC", "BPCL", "IOC", "GAIL", "HINDPETRO",
        "MGL", "IGL", "PETRONET", "GSPL",
        "CASTROLIND", "AEGISCHEM"
    ],
    "Custom Basket": []
}

SECTOR_INDEX_MAP = {
    "Nifty 50":                 "^NSEI",
    "Nifty Bank":               "^NSEBANK",
    "Nifty IT":                 "^CNXIT",
    "Nifty Auto":               "^CNXAUTO",
    "Nifty FMCG":               "^CNXFMCG",
    "Nifty Pharma":             "^CNXPHARMA",
    "Nifty Metal":              "^CNXMETAL",
    "Nifty Realty":             "^CNXREALTY",
    "Nifty Energy":             "^CNXENERGY",
    "Nifty Infra":              "^CNXINFRA",
    "Nifty PSU Bank":           "^CNXPSUBANK",
    "Nifty Midcap Select":      "^NSMIDCP100",
    "Nifty Financial Services": "^CNXFIN",
    "Nifty Consumer Durables":  "^CNXCONDUMD",
    "Nifty Oil & Gas":          "^CNXOILGAS",
}

# ---------------------------------------------------------------------------
# Shared curl_cffi session (created ONCE per process)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_yf_session():
    try:
        from curl_cffi import requests as curl_requests
        return curl_requests.Session(impersonate="chrome")
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Core fetch + calculate (cached 24 h)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=86400)
def fetch_and_calculate(ticker_symbol, _session, is_index=False):
    clean_symbol = ticker_symbol.strip()
    yf_symbol = clean_symbol if is_index else f"{clean_symbol.replace('.NS','').upper()}.NS"

    try:
        ticker = (yf.Ticker(yf_symbol, session=_session)
                  if _session is not None else yf.Ticker(yf_symbol))
        df_raw = ticker.history(period="1y", interval="1d")
    except Exception as e:
        return {"Symbol": clean_symbol, "Error": f"Fetch error: {e}"}

    if df_raw.empty:
        return {"Symbol": clean_symbol, "Error": "No data – invalid ticker"}

    close = df_raw['Close']
    high  = df_raw['High']
    low   = df_raw['Low']
    current_price = float(close.iloc[-1])

    # Returns
    periods = {
        '1D %': 1, '3D %': 3, '1W %': 5, '2W %': 10,
        '1M %': 21, '2M %': 42, '3M %': 63, '6M %': 126
    }
    returns = {}
    for label, days in periods.items():
        if len(close) > days:
            past = float(close.iloc[-(days + 1)])
            returns[label] = ((current_price - past) / past) * 100
        else:
            returns[label] = np.nan
    returns['1Y %'] = ((current_price - float(close.iloc[0])) / float(close.iloc[0])) * 100

    # EMAs
    ema4  = float(close.ewm(span=4,  adjust=False).mean().iloc[-1])
    ema10 = float(close.ewm(span=10, adjust=False).mean().iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])

    # 52-week extremes
    high_52w = float(high.max())
    low_52w  = float(low.min())

    # EMA diff columns (positive = price above EMA = bullish)
    ema4_diff  = ((current_price - ema4)  / ema4)  * 100
    ema10_diff = ((current_price - ema10) / ema10) * 100
    ema20_diff = ((current_price - ema20) / ema20) * 100

    return {
        "Symbol":        clean_symbol if is_index else clean_symbol.replace('.NS','').upper(),
        "LTP (EOD)":     current_price,
        **returns,
        "4 EMA":         ema4,
        "vs 4EMA %":     ema4_diff,
        "10 EMA":        ema10,
        "vs 10EMA %":    ema10_diff,
        "20 EMA":        ema20,
        "vs 20EMA %":    ema20_diff,
        "52W High":      high_52w,
        "% Below 52W H": ((current_price - high_52w) / high_52w) * 100,
        "52W Low":       low_52w,
        "% Above 52W L": ((current_price - low_52w)  / low_52w)  * 100,
        "Error":         None,
    }


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------
# All columns where positive = green, negative = red (background)
BG_COLOR_COLS = [
    '1D %','3D %','1W %','2W %','1M %','2M %','3M %','6M %','1Y %',
    'vs 4EMA %','vs 10EMA %','vs 20EMA %',
    '% Below 52W H',   # always ≤ 0 → always red shades; closer to 0 = lighter
    '% Above 52W L',   # always ≥ 0 → always green shades
]

def bg_color(val):
    """
    0.0  → white (neutral)
    positive → white fading to strong green (capped at 20 %)
    negative → white fading to strong red  (capped at 20 %)
    """
    if pd.isna(val):
        return ''
    intensity = min(abs(val) / 20, 1.0)   # 0.0 … 1.0
    if val >= 0:
        # white (255,255,255) → strong green (60,200,60)
        r = int(255 - intensity * 195)
        g = int(255 - intensity * 55)
        b = int(255 - intensity * 195)
        return f'background-color: rgb({r},{g},{b}); color: #000; font-weight: bold;'
    else:
        # white (255,255,255) → strong red (220,50,50)
        r = int(255 - intensity * 35)
        g = int(255 - intensity * 205)
        b = int(255 - intensity * 205)
        return f'background-color: rgb({r},{g},{b}); color: #000; font-weight: bold;'


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("📈 NSE Historical EOD Tracker")
st.markdown("Track returns, EMAs, and 52-week extremes for any NSE basket. 🟢 green = positive / above EMA &nbsp;|&nbsp; 🔴 red = negative / below EMA")

if "custom_stocks" not in st.session_state:
    st.session_state.custom_stocks = []

all_sector_names = [s for s in DEFAULT_SECTORS.keys() if s != "Custom Basket"] + ["Custom Basket"]
selected_sector  = st.sidebar.selectbox("Choose a Sector / Basket", all_sector_names)

default_stocks = DEFAULT_SECTORS.get(selected_sector, [])

# Build multiselect options (union of defaults + any previously added custom stocks)
all_options = sorted(set(default_stocks + st.session_state.custom_stocks + ["RELIANCE","TCS","INFY"]))

if selected_sector == "Custom Basket":
    ms_default = list(dict.fromkeys(st.session_state.custom_stocks))
else:
    ms_default = default_stocks

selected_stocks = st.sidebar.multiselect("Modify Stocks in Basket", options=all_options, default=ms_default)

new_stock_input = st.sidebar.text_input("Add Custom Stock (e.g., ZOMATO)").upper().strip()
col_add, col_clear = st.sidebar.columns(2)
with col_add:
    if st.button("Add Stock") and new_stock_input:
        if new_stock_input not in st.session_state.custom_stocks:
            st.session_state.custom_stocks.append(new_stock_input)
            st.rerun()
with col_clear:
    if st.button("Clear Custom"):
        st.session_state.custom_stocks = []
        st.rerun()

final_stocks = list(dict.fromkeys(selected_stocks + st.session_state.custom_stocks))

# ---------------------------------------------------------------------------
# Fetch & Display
# ---------------------------------------------------------------------------
if final_stocks:
    session = get_yf_session()
    results = []
    errors  = []

    # ---- Sector index row (if applicable) ----
    sector_index_symbol = SECTOR_INDEX_MAP.get(selected_sector)
    sector_row = None
    if sector_index_symbol:
        with st.spinner(f"Fetching sector index ({selected_sector})..."):
            try:
                idx_data = fetch_and_calculate(sector_index_symbol, session, is_index=True)
                if idx_data and idx_data.get("Error") is None:
                    idx_data.pop("Error", None)
                    idx_data["Symbol"] = f"▶ {selected_sector} INDEX"
                    sector_row = idx_data
            except Exception:
                pass

    # ---- Individual stocks ----
    progress_text = st.empty()
    progress_bar  = st.progress(0)
    total = len(final_stocks)

    for i, stock in enumerate(final_stocks):
        progress_text.text(f"Fetching: {stock}  ({i+1}/{total})")
        try:
            data = fetch_and_calculate(stock, session)
        except Exception as e:
            data = {"Symbol": stock, "Error": str(e)}

        if data and data.get("Error") is None:
            data.pop("Error", None)
            results.append(data)
        else:
            errors.append(f"**{stock}**: {data.get('Error','Unknown error')}")

        progress_bar.progress((i + 1) / total)
        if i < total - 1:
            time.sleep(0.15 + random.random() * 0.15)

    progress_text.empty()
    progress_bar.empty()

    if errors:
        st.error("⚠️ Some stocks were skipped:")
        for err in errors:
            st.write(err)

    if results:
        df_stocks = pd.DataFrame(results)

        # ---- Sector average summary row ----
        numeric_cols = [c for c in df_stocks.columns if c != "Symbol"]
        avg_vals     = df_stocks[numeric_cols].mean(numeric_only=True)
        avg_row      = {"Symbol": f"📊 {selected_sector} AVG"}
        avg_row.update(avg_vals.to_dict())
        df_avg = pd.DataFrame([avg_row])

        # ---- Build combined dataframe: sector index | avg | stocks ----
        frames = []
        if sector_row:
            frames.append(pd.DataFrame([sector_row]))
        frames.append(df_avg)
        frames.append(df_stocks)
        df_all = pd.concat(frames, ignore_index=True)

        # ---- Format & colour ----
        existing_bg_cols = [c for c in BG_COLOR_COLS if c in df_all.columns]
        format_dict = {col: "{:.2f}" for col in df_all.columns if col != "Symbol"}

        if hasattr(df_all.style, 'map'):
            styled = (df_all.style
                      .format(format_dict, na_rep="—")
                      .map(bg_color, subset=existing_bg_cols))
        else:
            styled = (df_all.style
                      .format(format_dict, na_rep="—")
                      .applymap(bg_color, subset=existing_bg_cols))

        st.dataframe(styled, use_container_width=True, height=650)

        st.caption("🟢 Darker green = stronger positive return / price well above EMA / far above 52W low  |  🔴 Darker red = stronger negative / price below EMA / closer to 52W high")

else:
    st.info("Please select or add stocks from the sidebar to view data.")
