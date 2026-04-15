import streamlit as st
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Gold Price Calculator", page_icon="🪙", layout="centered")

# --- FETCHING FUNCTION ---
def fetch_todays_gold_price(carat):
    """
    Simulates fetching today's gold rate per gram in India.
    In a production app, replace this with a live API call (e.g., GoldAPI, Metals-API).
    Currently defaults to April 2026 market estimates.
    """
    live_rates = {
        "24K": 15093.00,
        "22K": 13835.00,
        "18K": 11320.00
    }
    return live_rates.get(carat, 13835.00)

# --- HEADER ---
st.title("🪙 India Gold Price Calculator")
st.write(f"**Date:** {datetime.date.today().strftime('%B %d, %Y')}")
st.markdown("---")

# --- INPUT SECTION ---
st.header("1. Gold Details")
col1, col2 = st.columns(2)

with col1:
    carat = st.selectbox("Purity (Carat)", ["24K", "22K", "18K"], index=1) # Defaults to 22K (Standard for jewelry)
    weight = st.number_input("Weight (in Grams)", min_value=0.1, value=10.0, step=0.5)

# Fetch price based on selected purity
fetched_rate = fetch_todays_gold_price(carat)

with col2:
    # Allow the user to tweak the rate manually if the shop's board rate differs slightly
    rate_per_gram = st.number_input(f"Today's Rate for {carat} (₹/gram)", value=fetched_rate, step=50.0)

st.header("2. Charges & Taxes")
col3, col4 = st.columns(2)

with col3:
    making_charge_pct = st.number_input("Making Charges / Value Addition (%)", min_value=0.0, value=12.0, step=0.5)

with col4:
    # GST on gold in India is strictly 3%
    gst_pct = st.number_input("GST (%)", min_value=0.0, value=3.0, disabled=True) 

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
    
    # Use a clean container for the bill
    with st.container(border=True):
        st.write(f"**Gold Value:** {weight}g × ₹{rate_per_gram:,.2f}")
        st.subheader(f"₹ {gold_value:,.2f}")
        
        st.write(f"**Making Charges (+{making_charge_pct}%):**")
        st.subheader(f"₹ {making_charges_amt:,.2f}")
        
        st.write("**Subtotal:**")
        st.subheader(f"₹ {subtotal:,.2f}")
        
        st.write(f"**GST (+{gst_pct}%):**")
        st.subheader(f"₹ {gst_amount:,.2f}")
        
        st.markdown("---")
        st.write("### 💰 Total Amount Payable")
        st.success(f"## ₹ {final_total:,.2f}")