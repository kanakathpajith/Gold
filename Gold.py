from fpdf import FPDF
import io

# ... [Keep your previous calculation code exactly the same up to the pie chart] ...

    # --- EXPORT & PRINT OPTIONS ---
    st.markdown("### 🖨️ Export & Print Options")
    
    # Function to generate a neat PDF layout
    def create_pdf_receipt(t_wt, t_gold_val, t_mak, gst_val, grand_tot, item_list):
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "GOLD PORTFOLIO & BILL RECEIPT", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 8, f"Generated on: {datetime.date.today().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # Summary Box
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "BILL SUMMARY", new_x="LMARGIN", new_y="NEXT")
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Horizontal line
        pdf.ln(3)
        
        pdf.set_font("helvetica", "", 12)
        pdf.cell(60, 8, "Total Weight:")
        pdf.cell(0, 8, f"{t_wt:.3f} g", new_x="LMARGIN", new_y="NEXT")
        
        pdf.cell(60, 8, "Raw Gold Value:")
        pdf.cell(0, 8, f"INR {t_gold_val:,.2f}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.cell(60, 8, "Making Charges:")
        pdf.cell(0, 8, f"INR {t_mak:,.2f}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.cell(60, 8, "GST (3%):")
        pdf.cell(0, 8, f"INR {gst_val:,.2f}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        
        # Grand Total
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(60, 10, "GRAND TOTAL PAYABLE:")
        pdf.cell(0, 10, f"INR {grand_tot:,.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Itemized Breakdown
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "ITEMIZED BREAKDOWN", new_x="LMARGIN", new_y="NEXT")
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        
        for item in item_list:
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 7, f"Purchase Date: {item['Date']}  |  Purity: {item['Purity']}", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 6, f"Rate Applied: INR {item['Rate (₹)']:.3f} per gram", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Raw Value: INR {item['Gold Value']:,.2f}  |  Making Charge: INR {item['Making']:,.2f}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4) # Space between items
            
        # Return PDF as bytearray for Streamlit download
        return bytes(pdf.output())

    # --- RENDER DOWNLOAD BUTTONS ---
    export_col1, export_col2 = st.columns(2)
    
    # 1. Prepare CSV Download
    csv_data = res_df.to_csv(index=False).encode('utf-8')
    with export_col1:
        st.download_button(
            label="📊 Download Excel Data (CSV)",
            data=csv_data,
            file_name=f"Gold_Rates_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 2. Prepare PDF Download
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
    # ... [Keep your chart code exactly the same] ...
