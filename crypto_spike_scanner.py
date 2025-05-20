import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="🚀 Penny Crypto Spike Scanner", layout="centered")
debug_mode = st.sidebar.checkbox("🛠️ Show Debug Console")

def get_current_window():
    now = datetime.utcnow()
    return f"{now.hour:02d}:00"

def should_update():
    schedule = ["00:00", "06:00", "12:00", "18:00"]
    current_time = get_current_window()
    last_update_file = "last_update.txt"
    if os.path.exists(last_update_file):
        with open(last_update_file, "r") as f:
            last_update = f.read().strip()
    else:
        last_update = ""

    if current_time in schedule and last_update != current_time:
        with open(last_update_file, "w") as f:
            f.write(current_time)
        return True
    return False

def fetch_coinbase():
    url = "https://api.exchange.coinbase.com/products"
    data = requests.get(url).json()
    return list(set([item['base_currency'].lower() for item in data]))

def fetch_crypto_com():
    url = "https://crypto.com/price"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    names = [a.text.strip().lower() for a in soup.select("a.css-1ap5wc6")]
    return names

def fetch_webull():
    url = "https://www.webull.com/quote/crypto"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    scripts = soup.find_all("script")
    coins = set()
    for script in scripts:
        if "cryptoPairList" in script.text:
            lines = script.text.splitlines()
            for line in lines:
                if 'symbol' in line:
                    start = line.find("symbol") + 9
                    end = line.find(""", start)
                    coins.add(line[start:end].lower())
    return list(coins)

def update_supported_coins():
    supported = {
        "coinbase": fetch_coinbase(),
        "crypto_com": fetch_crypto_com(),
        "webull": fetch_webull()
    }
    with open("supported_coins.json", "w") as f:
        json.dump(supported, f, indent=2)
    return supported

def load_supported_coins():
    if should_update():
        return update_supported_coins()
    else:
        with open("supported_coins.json", "r") as f:
            return json.load(f)

def fetch_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_asc',
        'per_page': 250,
        'page': 1,
        'price_change_percentage': '1h'
    }
    res = requests.get(url, params=params)
    try:
        return pd.DataFrame(res.json())
    except Exception as e:
        st.error(f"CoinGecko fetch failed: {e}")
        return pd.DataFrame()

def detect_spikes(df):
    df = df.copy()
    df['current_price'] = df['current_price'].astype(float)
    df['price_change_percentage_1h_in_currency'] = df['price_change_percentage_1h_in_currency'].astype(float)
    return df[(df['current_price'] < 0.01) & (df['price_change_percentage_1h_in_currency'] > 20)]

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background-color: #0e1117;
        color: white;
    }
    .title {
        text-align: center;
        padding: 1rem;
    }
    .highlight {
        background: linear-gradient(90deg, #00ffe5, #fff700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
    }
    .card {
        background-color: #1c1f26;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 0 12px rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'><span class='highlight'>🚀 Penny Crypto Spike Scanner</span></div>", unsafe_allow_html=True)
st.markdown("### Showing only coins listed on Coinbase, Crypto.com, or Webull.")

supported = load_supported_coins()
all_supported_ids = set(supported["coinbase"] + supported["crypto_com"] + supported["webull"])

df = fetch_data()
if debug_mode:
    st.subheader("📦 Raw CoinGecko Data")
    st.json(df.head(10).to_dict())

if not df.empty:
    df = detect_spikes(df)
    df = df[df["id"].isin(all_supported_ids)]

    if debug_mode:
        st.subheader("🧠 Filtered Spikes")
        st.json(df.to_dict(orient="records"))

    if not df.empty:
        for _, row in df.iterrows():
            platforms = []
            if row["id"] in supported["coinbase"]: platforms.append("Coinbase")
            if row["id"] in supported["crypto_com"]: platforms.append("Crypto.com")
            if row["id"] in supported["webull"]: platforms.append("Webull")
            platform_str = ", ".join(platforms)

            st.markdown(
                f"""
                <div class='card'>
                    <strong>{row['name']} ({row['symbol'].upper()})</strong><br>
                    💰 Price: ${row['current_price']:.6f}<br>
                    📈 1h Spike: {row['price_change_percentage_1h_in_currency']:.2f}%<br>
                    🌐 Available on: {platform_str}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No supported coins under $0.01 have spiked 20%+ in the last hour.")
else:
    st.warning("No data could be loaded.")
