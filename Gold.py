import streamlit as st
import datetime
import yfinance as yf
import plotly.express as px
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Gold Price Calculator", page_icon="🪙", layout="centered")

# --- AUTO-FETCHING LIVE DATA ---
@st.cache_data(ttl=3600) # Refreshes data once an hour
def fetch_live_indian_gold_rate():
    try:
        # Fetch live global gold price (USD per Troy Ounce)
        gold_usd_oz = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        
        # Fetch live USD to INR exchange rate
        usd_inr = yf.Ticker("INR=X").history(period="1d")['Close'].iloc[-1]
        
        # Convert to INR per gram (1 Troy Oz = 31.1034768 grams)
        global_inr_gram = (gold_usd_oz * usd_inr) / 31.1034768
        
        # Add Indian Custom Duty (~15%)
        indian_24k = global_inr_gram * 1.15 
        
        return {
            "24K": indian_24k,
            "22K": indian_24k * (22/24),
            "18K": indian_24k * (18/24)
        }
    except Exception:
        # Fallback rates if Yahoo Finance is temporarily unreachable
        return {"24K": 15535.125, "22K": 14240.531, "18K": 11651.344}

# --- HEADER ---
st.title("🪙 India Gold Price Calculator")
st.write(f"**Date:** {datetime.date.today().strftime('%B %d, %Y')}")
st.markdown("---")

# Fetch the live rates
live_rates = fetch_live_indian_gold_rate()

# --- INPUT SECTION ---
st.header("1. Gold Details")
col1, col2 = st.columns(2)

with col1:
    carat = st.selectbox("Purity (Carat)", ["24K", "22K", "18K"], index=1)
    weight = st.number_input("Weight (in Grams)", min_value=0.100, value=10.000, step=0.500, format="%.3f")

# Pre-fill the rate based on purity selection
fetched_rate = live_rates.get(carat, 14240.531)

with col2:
    rate_per_gram = st.number_input(f"Today's Rate for {carat} (₹/gram)", value=float(fetched_rate), step=50.000, format="%.3f")

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
        hole=0.4, # Creates the donut hole in the middle
        color_discrete_sequence=["#FFD700", "#FF8C00", "#4CAF50"] # Gold, Orange, Green
    )
    
    # Style the chart text
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
    
    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
