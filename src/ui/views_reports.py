import streamlit as st
import pandas as pd
import time
from data.database import get_market_reports_db
from jobs.job_scheduler import run_job
from data.mock_generator import reset_and_fill_mock_data

def render_reports_view():
    st.subheader("Market Reports (Database)")
    
    # --- CONTROLS ---
    c_info, c_btn1, c_btn2 = st.columns([0.5, 0.25, 0.25])
    
    with c_info:
        st.caption("Data stored")
        
    with c_btn1:
        # BOUTON 1 : AJOUTER L'HEURE ACTUELLE (INSTANT)
        if st.button("Add Instant Snapshot", help="Run the job once now"):
            with st.spinner("Fetching live data..."):
                count = run_job(period_label='INSTANT')
                st.toast(f"{count} instant reports added!", icon="✅")
                time.sleep(1)
                st.rerun()

    with c_btn2:
        # BOUTON 2 : RESET TOTAL & MOCK
        if st.button("Reset & Mock DB", type="secondary", help="Delete all and generate 1 day history"):
            with st.spinner("Regenerating clean history..."):
                count, msg = reset_and_fill_mock_data()
                st.success(msg)
                time.sleep(1.5)
                st.rerun()

    # --- DATA FETCH ---
    df = get_market_reports_db()
    
    if df.empty:
        st.info("Database is empty. Use buttons above.")
        return

    # --- FILTERS ---
    tickers = sorted(df['symbol'].unique())
    selected_ticker = st.selectbox("Filter by Asset", ["All"] + list(tickers))
    
    if selected_ticker != "All":
        df = df[df['symbol'] == selected_ticker]

    # --- TABS (Ajout de l'onglet INSTANT si vous le souhaitez, sinon All Records suffit) ---
    tab_all, tab_daily, tab_hourly = st.tabs(["All Records", "Daily Reports", "Hourly/Instant"])
    
    col_cfg = {
        "id": st.column_config.NumberColumn("ID", width="small"),
        "timestamp": st.column_config.DatetimeColumn("Time", format="D MMM, HH:mm"),
        "symbol": "Ticker",
        "period": "Type",
        "price_close": st.column_config.NumberColumn("Close", format="$%.2f"),
        "volatility": st.column_config.NumberColumn("Vol", format="%.2f"),
        "max_drawdown": st.column_config.NumberColumn("Max DD", format="%.2f"),
        "volume": "Volume"
    }

    cols_to_show = ["id", "timestamp", "symbol", "period", "price_close", "volatility", "max_drawdown", "volume"]

    with tab_all:
        st.dataframe(df[cols_to_show], use_container_width=True, column_config=col_cfg, hide_index=True)
    
    with tab_daily:
        df_daily = df[df['period'] == 'DAILY']
        if df_daily.empty:
            st.warning("No Daily reports found yet.")
        else:
            st.dataframe(df_daily[cols_to_show], use_container_width=True, column_config=col_cfg, hide_index=True)
            if selected_ticker != "All":
                st.caption(f"Daily Closing Price - {selected_ticker}")
                st.line_chart(df_daily.set_index("timestamp")["price_close"])

    with tab_hourly:
        # On affiche ici HOURLY et INSTANT ensemble pour voir l'intraday
        df_hourly = df[df['period'].isin(['HOURLY', 'INSTANT'])]
        if df_hourly.empty:
            st.warning("No Hourly reports found yet.")
        else:
            st.dataframe(df_hourly[cols_to_show], use_container_width=True, column_config=col_cfg, hide_index=True)
            if selected_ticker != "All":
                st.caption(f"Hourly Price Action - {selected_ticker}")
                st.line_chart(df_hourly.set_index("timestamp")["price_close"])