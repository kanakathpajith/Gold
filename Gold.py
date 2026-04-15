import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import yfinance as yf
import re
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Indian Gold Bullion Tracker", page_icon="🪙", layout="wide")

# --- LIVE SCRAPER: BULLIONS.CO.IN ---
@st.cache_data(ttl=3600)
def fetch_bullion_co_in_rates():
    rates = {"24K": 15535.125, "22K": 14240.531, "18K": 11651.344}
    try:
        url = "https://bullions.co.in/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()
            matches = re.findall(r'(\d{1,2}[,.]\d{2}[,.]\d{3}|\d{5,6})', page_text)
            if matches:
                raw_val = matches.replace(',', '').replace('.', '')
                val_10g = float(raw_val)
                rate_24k = val_10g / 10 if val_10g > 50000 else val_10g
                rates["24K"] = rate_24k
                rates["22K"] = rate_24k * (22/24)
                rates["18K"] = rate_24k * (18/24)
    except:
        pass
    return rates

# --- HISTORICAL DATA (HOLIDAY PROOF) ---
@st.cache_data(show_spinner=False)
def get_historical_rate(date_obj, purity):
    # Widen the search window to 7 days to easily clear long weekends
    start = date_obj - datetime.timedelta(days=7)
    end = date_obj + datetime.timedelta(days=1)
    
    try:
        g = yf.Ticker("GC=F").history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        curr = yf.Ticker("INR=X").history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        
        if g.empty or curr.empty: 
            return 0.0
            
        # Combine datasets and carry the last known price forward over weekends/holidays
        combined = pd.DataFrame({'Gold': g['Close'], 'INR': curr['Close']}).ffill().dropna()
        
        if combined.empty:
            return 0.0
            
        latest_gold = combined['Gold'].iloc[-1]
        latest_inr = combined['INR'].iloc[-1]
        
        rate_24k = ((latest_gold * latest_inr) / 31.1034) * 1.15
        m = {"24K": 1.0, "22K": (22/24), "18K": (18/24)}
        
        return rate_24k * m.get(purity, 1.0)
    except:
        return 0.0

# --- PDF GENERATOR (WITH RUPEE SYMBOL U+20B9) ---
def create_pdf_receipt(t_wt, t_gold_val, t_mak, gst_val, grand_tot, item_list):
    # 1. Download a Unicode-friendly font (Roboto) that has the ₹ symbol
    font_path = "Roboto-Regular.ttf"
    if not os.path.exists(font_path) or os.path.getsize(font_path) < 50000:
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto-Regular.ttf"
        response = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(response.content)

    pdf = FPDF()
    pdf.add_page()
    
    # 2. Add the font to FPDF
    pdf.add_font("Roboto", "", font_path)
    
    # Define the Rupee symbol explicitly via Unicode
    rupee = "\u20B9"
    
    # Header
    pdf.set_font("Roboto", "", 18)
    pdf.cell(0, 10, "GOLD PORTFOLIO & BILL RECEIPT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", "", 10)
    pdf.cell(0, 8, f"Generated on: {datetime.date.today().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Summary
    pdf.set_font("Roboto", "", 14)
    pdf.cell(0, 10, "BILL SUMMARY", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("Roboto", "", 12)
    pdf.cell(60, 8, "Total Weight:")
    pdf.cell(0, 8, f"{t_wt:.3f} g", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(60, 8, "Raw Gold Value:")
    pdf.cell(0, 8, f"{rupee} {t_gold_val:,.2f}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(60, 8, "Making Charges:")
    pdf.cell(0, 8, f"{rupee} {t_mak:,.2f}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(60, 8, "GST (3%):")
    pdf.cell(0, 8, f"{rupee} {gst_val:,.2f}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # Grand Total
    pdf.set_font("Roboto", "", 14)
    pdf.cell(60, 10, "GRAND TOTAL PAYABLE:")
    pdf.cell(0, 10, f"{rupee} {grand_tot:,.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Breakdown
    pdf.set_font("Roboto", "", 14)
    pdf.cell(0, 10, "ITEMIZED BREAKDOWN", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    for item in item_list:
        pdf.set_font("Roboto", "", 12)
        pdf.cell(0, 7, f"Purchase Date: {item['Date']}  |  Purity: {item['Purity']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Roboto", "", 10)
        # Ensure the key matches exactly what is in your dataframe definition
        pdf.cell(0, 6, f"Rate Applied: {rupee} {item['Rate (₹)']:.3f} per gram", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Raw Value: {rupee} {item['Gold Value']:,.2f}  |  Making Charge: {rupee} {item['Making']:,.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
    return bytes(pdf.output())
# --- UI LAYOUT ---
st.title("🪙 Bullion-Verified Gold Calculator")
st.info("Live rates are currently being sourced from bullions.co.in for maximum reliability.")

live_now = fetch_bullion_co_in_rates()

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
    
    with st.spinner("Fetching and calculating rates..."):
        for _, row in edited_df.iterrows():
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
        fig_pie = px.pie(
            values=[t_gold, t_making, gst], 
            names=["Gold Value", "Making Charges", "GST (3%)"],
            hole=0.5, title="Bill Breakdown",
            color_discrete_sequence=["#FFD700", "#C0C0C0", "#4CAF50"]
        )
        st.plotly_chart(fig_pie)
        
    # --- EXPORT & PRINT OPTIONS ---
    st.markdown("### 🖨️ Export & Print Options")
    
    export_col1, export_col2 = st.columns(2)
    
    csv_data = res_df.to_csv(index=False).encode('utf-8')
    with export_col1:
        st.download_button(
            label="📊 Download Excel Data (CSV)",
            data=csv_data,
            file_name=f"Gold_Rates_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    pdf_bytes = create_pdf_receipt(t_weight, t_gold, t_making, gst, grand_total, data)
    with export_col2:
        st.download_button(
            label="📄 Download Printable Receipt (PDF)",
            data=pdf_bytes,
            file_name=f"Gold_Receipt_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # --- COMPARATIVE ANALYSIS ---
    st.markdown("---")
    st.subheader("📈 Date-wise Rate Comparison")
    fig_bar = px.bar(
        res_df, x="Date", y="Rate (₹)", color="Purity", 
        text_auto='.3f', title="Price Fluctuation Across Selected Dates"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.dataframe(res_df.style.format({"Rate (₹)": "{:.3f}", "Gold Value": "{:.3f}", "Making": "{:.3f}"}))
