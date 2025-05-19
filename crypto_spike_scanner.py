import streamlit as st
import requests
import pandas as pd

API_KEY = "CG-7dmjAuZuHAFT1pv5pxyPW7ZL"

def fetch_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    headers = {
        "x-cg-pro-api-key": API_KEY
    }
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_asc',
        'per_page': 250,
        'page': 1,
        'price_change_percentage': '1h'
    }
    res = requests.get(url, params=params, headers=headers)

    try:
        df = pd.DataFrame(res.json())
        if 'current_price' not in df.columns:
            st.error("CoinGecko response missing expected fields. API key might be invalid or rate-limited.")
            st.write("Returned columns:", df.columns)
        return df
    except Exception as e:
        st.error(f"Error parsing CoinGecko response: {e}")
        return pd.DataFrame()

def detect_spikes(df):
    df = df.copy()
    df['current_price'] = df['current_price'].astype(float)
    df['price_change_percentage_1h_in_currency'] = df['price_change_percentage_1h_in_currency'].astype(float)
    return df[(df['current_price'] < 0.01) & (df['price_change_percentage_1h_in_currency'] > 20)][[
        'name', 'symbol', 'current_price', 'price_change_percentage_1h_in_currency', 'market_cap_rank'
    ]]

st.set_page_config(page_title="Penny Crypto Spike Scanner")
st.title("🚀 Penny Crypto Spike Scanner")
st.write("Live scan of sub-penny cryptos spiking 20%+ in the last hour.")

df = fetch_data()
spike_df = detect_spikes(df)

st.dataframe(spike_df.sort_values(by='price_change_percentage_1h_in_currency', ascending=False))
