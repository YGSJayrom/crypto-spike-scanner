import streamlit as st
import requests
import pandas as pd
import json
import os

st.set_page_config(page_title="🚀 Penny Crypto Spike Scanner", layout="centered")
st.markdown(
    """
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
    """,
    unsafe_allow_html=True
)

def load_supported_coins():
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
        st.error(f"Failed to load CoinGecko data: {e}")
        return pd.DataFrame()

def detect_spikes(df):
    df = df.copy()
    df['current_price'] = df['current_price'].astype(float)
    df['price_change_percentage_1h_in_currency'] = df['price_change_percentage_1h_in_currency'].astype(float)
    return df[
        (df['current_price'] < 0.01) &
        (df['price_change_percentage_1h_in_currency'] > 20)
    ]

# Load supported platforms
supported = load_supported_coins()
all_supported_ids = set(supported["coinbase"] + supported["crypto_com"] + supported["webull"])

st.markdown("<div class='title'><span class='highlight'>🚀 Penny Crypto Spike Scanner</span></div>", unsafe_allow_html=True)
st.markdown("### Only showing spikes for coins available on Coinbase, Crypto.com, or Webull.")

df = fetch_data()
if df.empty:
    st.warning("Could not retrieve data from CoinGecko.")
else:
    df = detect_spikes(df)
    df = df[df["id"].isin(all_supported_ids)]

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
