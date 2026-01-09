import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
import pandas as pd

from data.data_loader import load_asset_universe, get_live_prices_batch
from ui.ui_components import apply_theme_and_css, render_ticker_tape, render_footer

from ui.views_single import render_single_asset_view
from ui.views_portfolio import render_portfolio_view
from ui.views_reports import render_reports_view 

from data.database import init_db, get_active_tickers_db, add_active_ticker_db, remove_active_ticker_db

st.set_page_config(page_title="Quant Dashboard", layout="wide", initial_sidebar_state="collapsed")

def init_global_state():
    # 1. Init DB
    init_db()
    
    # 2. Sync Session State avec la DB
    # On récupère les tickers sauvegardés
    db_tickers = get_active_tickers_db()
    
    # Si la DB est vide, on met des défauts et on les sauvegarde
    if not db_tickers:
        defaults = ["^FCHI", "^GSPC", "NVDA", "AIR.PA", "BTC-USD", "EURUSD=X"]
        for t in defaults:
            add_active_ticker_db(t)
        st.session_state['tape_tickers'] = defaults
    else:
        st.session_state['tape_tickers'] = db_tickers

def main():
    st_autorefresh(interval=5 * 60 * 1000, key="global_refresh")
    
    # Initialisation (DB + State)
    if 'tape_tickers' not in st.session_state:
        init_global_state()

    # --- SECURITE : LIMITATION STRICTE A 10 ---
    if len(st.session_state['tape_tickers']) > 10:
        st.session_state['tape_tickers'] = st.session_state['tape_tickers'][:10]

    # --- HEADER ---
    top_c1, top_c2 = st.columns([10, 1.5])
    with top_c1:
        st.title("QUANT DASHBOARD")
    with top_c2:
        col_moon, col_sw, col_sun = st.columns([0.3, 0.4, 0.3])
        with col_moon: st.write("🌙")
        with col_sw: 
            is_light = st.toggle("Theme", value=False, label_visibility="collapsed")
        with col_sun: st.write("☀️")
    
    apply_theme_and_css(is_dark_mode=not is_light)
    
    df_assets = load_asset_universe()
    
    # --- TICKER TAPE BAR ---
    st.write("") 
    c_tape, c_add, c_del = st.columns([12, 0.5, 0.5])
    
    with c_tape:
        prices = get_live_prices_batch(st.session_state['tape_tickers'])
        render_ticker_tape(prices)
        
    with c_add:
        with st.popover("➕", help="Add ticker"):
            st.markdown("**Add Asset (Max 10)**")
            
            # 1. Index
            idx_list = df_assets['Index'].unique()
            sel_idx = st.selectbox("Index", idx_list, key="tp_idx")
            
            # 2. Sector (Avec option ALL)
            avail_sec = sorted(df_assets[df_assets['Index'] == sel_idx]['Sector'].unique())
            sec_options = ["ALL"] + list(avail_sec)
            sel_sec = st.selectbox("Sector", sec_options, key="tp_sec")
            
            # 3. Filtrage
            if sel_sec == "ALL":
                mask = (df_assets['Index'] == sel_idx)
            else:
                mask = (df_assets['Index'] == sel_idx) & (df_assets['Sector'] == sel_sec)
                
            filtered = df_assets[mask].copy()
            filtered['Label'] = filtered['Name'] + " (" + filtered['Symbol'] + ")"
            
            sel_asset_label = st.selectbox("Asset", filtered['Label'], key="tp_ast")
            
            if st.button("Add", type="primary", use_container_width=True):
                # --- LOGIQUE MIXTE (DB + UI) ---
                if not filtered.empty:
                    sym = filtered[filtered['Label'] == sel_asset_label]['Symbol'].values[0]
                    
                    # 1. Appel DB
                    ok, msg = add_active_ticker_db(sym)
                    
                    if ok:
                        # 2. Mise à jour Session State (pour affichage immédiat)
                        st.session_state['tape_tickers'].append(sym)
                        st.toast(f"Success! {sym} added.", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.toast(f"Error: {msg}", icon="⚠️")
                else:
                    st.toast("Error: Selection empty", icon="❌")

    with c_del:
        with st.popover("🗑️", help="Remove ticker"):
            st.markdown("**Remove Asset**")
            to_del = st.selectbox("Select to remove", st.session_state['tape_tickers'], key="tp_del_sel")
            
            if st.button("Remove", type="primary", use_container_width=True):
                # 1. Appel DB
                remove_active_ticker_db(to_del)
                
                # 2. Mise à jour Session State
                if to_del in st.session_state['tape_tickers']:
                    st.session_state['tape_tickers'].remove(to_del)
                    st.toast(f"Success! {to_del} removed.", icon="✅")
                    time.sleep(0.5)
                    st.rerun()

    # --- NAVIGATION (TABS) ---
    st.write("")
    tab1, tab2, tab3 = st.tabs(["Assets Analysis", "Multi-Assets Portfolio", "Reports"])
    
    # Creation d'un petit dataframe compatible pour les vues existantes
    # Basé sur ce qu'il y a dans la bande défilante
    current_tickers = st.session_state['tape_tickers']
    if not current_tickers:
        df_view_assets = pd.DataFrame(columns=['Symbol', 'Name'])
    else:
        # Petit lookup rapide pour avoir les noms complets
        lookup = df_assets.set_index('Symbol')['Name'].to_dict()
        data_view = [{'Symbol': t, 'Name': lookup.get(t, t)} for t in current_tickers]
        df_view_assets = pd.DataFrame(data_view)
    
    with tab1:
        render_single_asset_view(df_view_assets)
    
    with tab2:
        render_portfolio_view(df_view_assets)

    with tab3:
        # Le nouvel onglet Reports
        render_reports_view()
        
    render_footer()

if __name__ == "__main__":
    main()