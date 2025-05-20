import streamlit as st
import requests
import pandas as pd

# Title styling
st.set_page_config(page_title="🚀 Penny Crypto Spike Scanner", layout="centered")
st.markdown(
    """
    <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', sans-serif;
            background-color: #0e1117;
            color: white;
        }
        .title {
            text-align: center;
            padding: 1rem;
        }
        .highlight {
            background: linear-gradient(90deg, #ff0066, #ffcc00);
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

API_KEY = None  # We're using public endpoint for now

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
        df = pd.DataFrame(res.json())
        if 'current_price' not in df.columns:
            st.error("CoinGecko response missing expected fields.")
            st.write("Returned columns:", df.columns)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def detect_spikes(df):
    df = df.copy()
    df['current_price'] = df['current_price'].astype(float)
    df['price_change_percentage_1h_in_currency'] = df['price_change_percentage_1h_in_currency'].astype(float)
    return df[
        (df['current_price'] < 0.01) &
        (df['price_change_percentage_1h_in_currency'] > 20)
    ][['name', 'symbol', 'current_price', 'price_change_percentage_1h_in_currency', 'market_cap_rank']]

# UI
st.markdown("<div class='title'><span class='highlight'>🚀 Penny Crypto Spike Scanner</span></div>", unsafe_allow_html=True)
st.markdown("### Live scan of sub-penny cryptos spiking 20%+ in the last hour.")

df = fetch_data()
spike_df = detect_spikes(df)

if not spike_df.empty:
    for _, row in spike_df.iterrows():
        st.markdown(
            f"""
            <div class='card'>
                <strong>{row['name']} ({row['symbol'].upper()})</strong><br>
                💰 Price: ${row['current_price']:.6f}<br>
                📈 1h Spike: {row['price_change_percentage_1h_in_currency']:.2f}%<br>
                🏷️ Market Rank: {row['market_cap_rank'] if row['market_cap_rank'] else 'N/A'}
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("No coins under $0.01 have spiked 20%+ in the last hour. Try again later.")
