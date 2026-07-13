import time
import random

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# --- Page Configuration ---
st.set_page_config(page_title="NSE Historical EOD Tracker", layout="wide")

# --- Default Data (NOTE: "L&T" fixed -> "LT", the real NSE symbol) ---
DEFAULT_SECTORS = {
    "My Watchlist": ["ASTRAL", "TATAMOTORS", "BANKBARODA", "PFC", "RECLTD", "HUDCO", "RVNL", "GODREJIND"],
    "Nifty 50": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "LT"],
    "Nifty Bank": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "PNB", "INDUSINDBK"],
    "Nifty IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT"]
}


# --- Shared, browser-impersonated session (created ONCE per app process) ---
@st.cache_resource(show_spinner=False)
def get_yf_session():
    """
    yfinance ships with curl_cffi, which impersonates a real browser's TLS/JA3
    fingerprint. That's what Yahoo actually checks to detect bot / cloud
    traffic -- a spoofed User-Agent header on a plain requests.Session does
    NOT fool it, and creating a fresh session per-ticker forces Yahoo's
    cookie/crumb handshake to run once per stock instead of once per app run.
    Building one impersonated session and reusing it fixes both problems.
    """
    try:
        from curl_cffi import requests as curl_requests
        return curl_requests.Session(impersonate="chrome")
    except ImportError:
        # curl_cffi not installed for some reason -> let yfinance manage
        # its own (still better than us handing it a plain session).
        return None


# --- Core Calculation ---
@st.cache_data(show_spinner=False, ttl=86400)
def fetch_and_calculate(ticker_symbol, _session):
    # NOTE: the leading underscore on _session tells st.cache_data to skip
    # hashing that argument (sessions aren't hashable), while still letting
    # us pass it in.
    clean_symbol = ticker_symbol.replace('.NS', '').strip().upper()
    yf_symbol = f"{clean_symbol}.NS"

    ticker = yf.Ticker(yf_symbol, session=_session) if _session is not None else yf.Ticker(yf_symbol)
    df_raw = ticker.history(period="1y", interval="1d")

    if df_raw.empty:
        return {"Symbol": clean_symbol, "Error": "No data returned - check the ticker symbol"}

    close = df_raw['Close']
    high = df_raw['High']
    low = df_raw['Low']

    current_price = float(close.iloc[-1])

    # RETURNS
    periods = {'1D %': 1, '3D %': 3, '1W %': 5, '2W %': 10, '1M %': 21, '2M %': 42, '3M %': 63, '6M %': 126}
    returns = {}
    for label, days in periods.items():
        if len(close) > days:
            past_price = float(close.iloc[-(days + 1)])
            returns[label] = ((current_price - past_price) / past_price) * 100
        else:
            returns[label] = np.nan

    returns['1Y %'] = ((current_price - float(close.iloc[0])) / float(close.iloc[0])) * 100

    # INDICATORS
    ema4 = close.ewm(span=4, adjust=False).mean().iloc[-1]
    ema10 = close.ewm(span=10, adjust=False).mean().iloc[-1]
    ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]

    high_52w = float(high.max())
    low_52w = float(low.min())

    return {
        "Symbol": clean_symbol,
        "LTP (EOD)": current_price,
        **returns,
        "4 EMA": float(ema4), "10 EMA": float(ema10), "20 EMA": float(ema20),
        "52W High": high_52w, "% Below 52W H": ((current_price - high_52w) / high_52w) * 100,
        "52W Low": low_52w, "% Above 52W L": ((current_price - low_52w) / low_52w) * 100,
        "Error": None
    }


# --- UI and Layout ---
st.title("📈 NSE Historical EOD Tracker")
st.markdown("Track absolute returns, EMAs, and 52-week extremes using reliable EOD data.")

if "custom_stocks" not in st.session_state:
    st.session_state.custom_stocks = []

selected_sector = st.sidebar.selectbox("Choose a Sector / Basket", list(DEFAULT_SECTORS.keys()) + ["Custom Basket"])

default_stocks = [] if selected_sector == "Custom Basket" else DEFAULT_SECTORS[selected_sector]

all_options = sorted(set(default_stocks + ["RELIANCE", "TCS", "INFY"] + st.session_state.custom_stocks))

selected_stocks = st.sidebar.multiselect(
    "Modify Stocks in Basket",
    options=all_options,
    default=list(dict.fromkeys(default_stocks + st.session_state.custom_stocks))
    if selected_sector == "Custom Basket" else default_stocks
)

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

# Custom stocks always ride along, even if the multiselect above doesn't show them yet
final_stocks = list(dict.fromkeys(selected_stocks + st.session_state.custom_stocks))

# --- Data Fetching Engine ---
if final_stocks:
    session = get_yf_session()
    results = []
    errors = []

    progress_text = st.empty()
    progress_bar = st.progress(0)
    total_stocks = len(final_stocks)

    for index, stock in enumerate(final_stocks):
        progress_text.text(f"Fetching data for: {stock} ({index + 1}/{total_stocks})...")

        try:
            data = fetch_and_calculate(stock, session)
        except Exception as e:
            # Transient failures are NOT cached (they're raised, not returned),
            # so a rate-limit blip today won't stay "stuck" for 24 hours.
            data = {"Symbol": stock, "Error": f"Fetch failed: {e}"}

        if data and data.get("Error") is None:
            data.pop("Error", None)
            results.append(data)
        elif data and data.get("Error"):
            errors.append(f"**{stock}**: {data['Error']}")

        progress_bar.progress((index + 1) / total_stocks)

        # Gentle pacing between requests so we don't burst Yahoo with a
        # dozen back-to-back calls, even with a good session.
        if index < total_stocks - 1:
            time.sleep(0.15 + random.random() * 0.15)

    progress_text.empty()
    progress_bar.empty()

    if errors:
        st.error("⚠️ **Some stocks were skipped:**")
        for err in errors:
            st.write(err)

    if results:
        df_results = pd.DataFrame(results)

        color_cols = ['1D %', '3D %', '1W %', '2W %', '1M %', '2M %', '3M %', '6M %', '1Y %', '% Below 52W H', '% Above 52W L']
        existing_color_cols = [col for col in color_cols if col in df_results.columns]

        def color_negative_red(val):
            if pd.isna(val):
                return ''
            color = '#ff4b4b' if val < 0 else '#09ab3b'
            return f'color: {color}; font-weight: bold;'

        format_dict = {col: "{:.2f}" for col in df_results.columns if col != 'Symbol'}

        if hasattr(df_results.style, 'map'):
            styled_df = df_results.style.format(format_dict).map(color_negative_red, subset=existing_color_cols)
        else:
            styled_df = df_results.style.format(format_dict).applymap(color_negative_red, subset=existing_color_cols)

        st.dataframe(styled_df, use_container_width=True, height=600)
else:
    st.info("Please select or add stocks from the sidebar to view data.")
