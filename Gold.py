import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import pandas as pd
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Gold Price Calculator", page_icon="🪙", layout="centered")

# --- AUTO-FETCHING LIVE LOCAL RETAIL DATA ---
# ttl=43200 tells Streamlit to fetch fresh data every 12 hours automatically
@st.cache_data(ttl=43200, show_spinner="Fetching today's retail rates...") 
def fetch_live_indian_retail_rates():
    # Accurate fallback rates based on current April 2026 market 
    # Used as a safety net just in case the website's HTML changes or goes offline
    rates = {"24K": 15535.000, "22K": 14240.000, "18K": 11651.000}
    
    try:
        # Scrape Goodreturns.in for the actual retail shop prices in India
        url = "https://www.goodreturns.in/gold-rates/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Isolate the standard pricing tables on the page
            tables = soup.find_all('table')
            for table in tables:
                text = table.get_text()
                # Find the table containing "1 Gram" prices
                if '1 Gram' in text:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2 and '1 Gram' in cols.text:
                            # Clean the extracted string (remove ₹ symbol and commas)
                            price_str = re.sub(r'[^\d.]', '', cols.text)
                            if price_str:
                                price = float(price_str)
                                # Logic to assign the scraped price to the correct purity
                                # 24K is typically higher than 15000, 22K is typically in the 13000-14500 range
                                if price > 14500.0:
                                    rates["24K"] = price
                                    # Extrapolate mathematically if 22K or 18K fails to scrape
                                    rates["22K"] = price * (22/24)
                                    rates["18K"] = price * (18/24)
                                    break # Stop once we find the primary 24K 1-gram price
            
    except Exception as e:
        # If the web scraper fails, it will quietly use the fallback rates
        # rather than crashing the app.
        pass
        
    return rates

# --- HEADER ---
st.title("🪙 India Gold Price Calculator")
st.write(f"**Date:** {datetime.date.today().strftime('%B %d, %Y')}")
st.markdown("---")

# Fetch the live rates
live_rates = fetch_live_indian_retail_rates()

# --- INPUT SECTION ---
st.header("1. Gold Details")
col1, col2 = st.columns(2)

with col1:
    carat = st.selectbox("Purity (Carat)", ["24K", "22K", "18K"], index=1)
    weight = st.number_input("Weight (in Grams)", min_value=0.100, value=10.000, step=0.500, format="%.3f")

# Pre-fill the rate based on purity selection
fetched_rate = live_rates.get(carat, 14240.000)

with col2:
    rate_per_gram = st.number_input(f"Today's Retail Rate for {carat} (₹/gram)", value=float(fetched_rate), step=50.000, format="%.3f")

st.header("2. Charges & Taxes")
col3, col4 = st.columns(2)

with col3:
    making_charge_pct = st.number_input("Making Charges (%)", min_value=0.000, value=12.000, step=0.500, format="%.3f")

with col4:
    gst_pct = st.number_input("GST (%)", min_value=0.000, value=3.000, disabled=True, format="%.3f") 

st.markdown("---")

# --- CALCULATION SECTION ---
if st.button("🧮 Calculate Final Bill", use_container_width=True):
    # Core Math
    gold_value = weight * rate_per_gram
    making_charges_amt = gold_value * (making_charge_pct / 100)
    subtotal = gold_value + making_charges_amt
    gst_amount = subtotal * (gst_pct / 100)
    final_total = subtotal + gst_amount

    # --- RESULTS DISPLAY ---
    st.header("🧾 Final Bill Breakdown")
    
    with st.container(border=True):
        # Text Breakdown
        st.write(f"**Gold Value:** {weight:,.3f}g × ₹{rate_per_gram:,.3f}")
        st.subheader(f"₹ {gold_value:,.3f}")
        
        st.write(f"**Making Charges (+{making_charge_pct:,.3f}%):**")
        st.subheader(f"₹ {making_charges_amt:,.3f}")
        
        st.write("**Subtotal:**")
        st.subheader(f"₹ {subtotal:,.3f}")
        
        st.write(f"**GST (+{gst_pct:,.3f}%):**")
        st.subheader(f"₹ {gst_amount:,.3f}")
        
        st.markdown("---")
        st.write("### 💰 Total Amount Payable")
        st.success(f"## ₹ {final_total:,.3f}")

    # --- DATA VISUALIZATION (PIE CHART) ---
    st.markdown("### 📊 Price Composition")
    
    # Create a DataFrame for Plotly
    chart_data = pd.DataFrame({
        "Component": ["Raw Gold Value", "Making Charges", "GST (3%)"],
        "Amount (₹)": [gold_value, making_charges_amt, gst_amount]
    })
    
    # Generate an interactive Donut chart
    fig = px.pie(
        chart_data, 
        values="Amount (₹)", 
        names="Component", 
        hole=0.4, 
        color_discrete_sequence=["#FFD700", "#FF8C00", "#4CAF50"]
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
    
    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
