import io
import streamlit as st
from openpyxl import Workbook


def export_portfolio(df):
    """
    Display a button to download the portfolio as an Excel file.
    """

    if df.empty:
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Portfolio"

    # Header
    ws.append(list(df.columns))

    # Data
    for row in df.itertuples(index=False):
        ws.append(list(row))

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    st.download_button(
        label="📥 Download Portfolio (Excel)",
        data=output,
        file_name="portfolio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )