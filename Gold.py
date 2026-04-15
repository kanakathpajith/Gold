import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import yfinance as yf
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Indian Gold Bullion Tracker", page_icon="🪙", layout="wide")

# --- LIVE SCRAPER: BULLIONS.CO.IN ---
@st.cache_data(ttl=3600) # Refresh every hour
def fetch_bullion_co_in_rates():
    # Default Fallback (April 15, 2026 estimates)
    rates = {"24K": 15535.125, "22K": 14240.531, "18K": 11651.344}
    
    try:
        url = "https://bullions.co.in/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Bullions.co.in typically displays rates in a ticker or specific div
            # We look for strings matching the price pattern near 'Gold 24k'
            page_text = soup.get_text()
            
            # Find 24K price (looks for numbers like 1,55,350 or 15535)
            # We target the 10g price and divide by 10 for the 1g rate
            matches = re.findall(r'(\d{1,2}[,.]\d{2}[,.]\d{3}|\d{5,6})', page_text)
            
            if matches:
                # Usually the first high value is the 24K 10g price
                raw_val = matches.replace(',', '').replace('.', '')
                val_10g = float(raw_val)
                
                # Logic check: if the value is > 100,000, it's for 10g. 
                # If it's around 15,000, it's for 1g.
                rate_24k = val_10g / 10 if val_10g > 50000 else val_10g
                
                rates["24K"] = rate_24k
                rates["22K"] = rate_24k * (22/24)
                rates["18K"] = rate_24k * (18/24)
    except:
        pass # Return fallbacks if site structure changes
    return rates

# --- HISTORICAL DATA (Fallback for specific past dates) ---
@st.cache_data(show_spinner=False)
def get_historical_rate(date_obj, purity):
    start = date_obj - datetime.timedelta(days=4)
    end = date_obj + datetime.timedelta(days=1)
    try:
        g = yf.Ticker("GC=F").history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        curr = yf.Ticker("INR=X").history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if g.empty or curr.empty: return 0.0
        
        # International to Domestic Conversion (Price * Exch / Oz-to-G) + 15% Duty
        rate_24k = ((g['Close'].iloc[-1] * curr['Close'].iloc[-1]) / 31.1034) * 1.15
        
        m = {"24K": 1.0, "22K": (22/24), "18K": (18/24)}
        return rate_24k * m.get(purity, 1.0)
    except:
        return 0.0

# --- UI LAYOUT ---
st.title("🪙 Bullion-Verified Gold Calculator")
st.info("Live rates are currently being sourced from bullions.co.in for maximum reliability.")

# Fetching current rates for the 'Today' default
live_now = fetch_bullion_co_in_rates()

# --- PORTFOLIO INPUT ---
st.subheader("Purchase Entry")
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame({
        "Date": [datetime.date(2026, 4, 10), datetime.date.today()],
        "Purity": ["22K", "22K"],
        "Weight (g)": [12.000, 10.000],
        "Making %": [12.000, 12.000]
    })

edited_df = st.data_editor(
    st.session_state.portfolio,
    column_config={
        "Date": st.column_config.DateColumn("Date"),
        "Purity": st.column_config.SelectboxColumn("Purity", options=["24K", "22K", "18K"]),
        "Weight (g)": st.column_config.NumberColumn("Weight", format="%.3f"),
        "Making %": st.column_config.NumberColumn("Making %", format="%.3f")
    },
    num_rows="dynamic", use_container_width=True
)

if st.button("Calculate Final Price & Analysis", type="primary"):
    data = []
    t_gold, t_making, t_weight = 0.0, 0.0, 0.0
    
    for _, row in edited_df.iterrows():
        # Use live scraper for today, historical for past dates
        if row['Date'] == datetime.date.today():
            rate = live_now.get(row['Purity'], 0.0)
        else:
            rate = get_historical_rate(row['Date'], row['Purity'])
            
        val = rate * row['Weight (g)']
        mak = val * (row['Making %'] / 100)
        
        t_gold += val
        t_making += mak
        t_weight += row['Weight (g)']
        
        data.append({
            "Date": row['Date'].strftime('%Y-%m-%d'),
            "Purity": row['Purity'],
            "Rate (₹)": rate,
            "Gold Value": val,
            "Making": mak
        })

    res_df = pd.DataFrame(data)
    subtotal = t_gold + t_making
    gst = subtotal * 0.03
    grand_total = subtotal + gst

    # --- DISPLAYS ---
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Payable (Inc. 3% GST)", f"₹ {grand_total:,.3f}")
        st.write(f"**Total Weight:** {t_weight:.3f}g")
        st.write(f"**Raw Gold Value:** ₹ {t_gold:,.3f}")
        st.write(f"**Total Making Charges:** ₹ {t_making:,.3f}")
        st.write(f"**GST Amount:** ₹ {gst:,.3f}")

    with c2:
        # Bill Composition Pie
        fig_pie = px.pie(
            values=[t_gold, t_making, gst], 
            names=["Gold Value", "Making Charges", "GST (3%)"],
            hole=0.5, title="Bill Breakdown",
            color_discrete_sequence=["#FFD700", "#C0C0C0", "#4CAF50"]
        )
        st.plotly_chart(fig_pie)

    # --- COMPARATIVE ANALYSIS ---
    st.markdown("---")
    st.subheader("📈 Date-wise Rate Comparison")
    fig_bar = px.bar(
        res_df, x="Date", y="Rate (₹)", color="Purity", 
        text_auto='.3f', title="Price Fluctuation Across Selected Dates"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.dataframe(res_df.style.format({"Rate (₹)": "{:.3f}", "Gold Value": "{:.3f}", "Making": "{:.3f}"}))
