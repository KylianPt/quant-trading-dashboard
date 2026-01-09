import streamlit as st
import pandas as pd
from logic.single_logic import (
    update_analyses_duration, sync_tape_to_graphs, add_analysis_to_state, 
    remove_analysis, get_rankings, get_full_history_for_prediction, COLORS
)
from ui.single_components import render_main_chart, render_metric_card_html, render_prediction_chart
from logic.prediction import run_prediction_model

def render_single_asset_view(df_assets):
    name_map = df_assets.set_index('Symbol')['Name'].to_dict()

    if 'analyses' not in st.session_state: st.session_state['analyses'] = []
    if 'pred_results' not in st.session_state: st.session_state['pred_results'] = {}
    if 'selected_pred_tickers' not in st.session_state:
        tape_tickers = st.session_state.get('tape_tickers', [])
        st.session_state['selected_pred_tickers'] = set(tape_tickers)

    # --- LAYOUT FIXE ---
    col_strat, col_pred = st.columns([0.7, 0.3])

    # ==============================================================================
    # COL 1 : STRATEGY
    # ==============================================================================
    with col_strat:
        st.subheader("Performance Comparison")
        prev_years = st.session_state.get('last_years_val', 5)
        years = st.slider("Strategy History (Years)", 1, 10, 5, key="strat_years_slider")
        if years != prev_years:
            st.session_state['last_years_val'] = years
            update_analyses_duration(years)
            st.rerun()

        sync_tape_to_graphs(years)
        items = st.session_state['analyses']
        
        # --- GRAPH PRINCIPAL ---
        show_abs = st.session_state.get("show_abs_val", False) 
        render_main_chart(items, show_absolute=show_abs)

        # --- CHECKBOX (ESPACEMENT RÉDUIT) ---
        st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
        st.checkbox("Show Absolute Value ($)", value=False, key="show_abs_val")
        st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)

        st.divider()

        rankings = get_rankings(items)
        cols_count = 3 
        total_items = len(items) + 1
        rows = (total_items // cols_count) + (1 if total_items % cols_count > 0 else 0)

        for row_idx in range(rows):
            cols = st.columns(cols_count)
            for c_idx in range(cols_count):
                idx = row_idx * cols_count + c_idx
                if idx < total_items:
                    col = cols[c_idx]
                    with col:
                        if idx < len(items):
                            item = items[idx]
                            border_c = item['color']
                            full_name = name_map.get(item['symbol'], "")
                            with st.container():
                                h1, h2 = st.columns([0.85, 0.15])
                                with h1: 
                                    st.markdown(f"""
                                    <div style='color:{border_c}; font-weight:bold; font-size:1.1em;'>
                                       {item['symbol']} 
                                       <span style='font-size:0.8em; color:gray; font-weight:normal;'>- {full_name}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.caption(f"{item['strategy']} | {item['strat_short']}")
                                with h2:
                                    if st.button("🗑️", key=f"del_{item['id']}"): remove_analysis(idx)
                                st.markdown(render_metric_card_html(item, rankings), unsafe_allow_html=True)
                                st.write("")
                        else:
                            # BOUTON AJOUTER STRATEGIE
                            st.markdown('<div class="big-add-button">', unsafe_allow_html=True)
                            with st.popover("➕", use_container_width=True):
                                tape_tickers = st.session_state.get('tape_tickers', [])
                                if tape_tickers:
                                    s_tick = st.selectbox("Asset", tape_tickers, key="s_add_t")
                                    s_st = st.selectbox("Strategy", ["Buy & Hold", "Momentum SMA", "MACD"], key="s_add_s")
                                    p = {}
                                    if s_st == "Momentum SMA": p["window"] = st.slider("Win", 10, 200, 50, key="sw")
                                    elif s_st == "MACD": 
                                        p["fast"] = st.number_input("Fast", value=12, key="mf")
                                        p["slow"] = st.number_input("Slow", value=26, key="ms")
                                        p["signal"] = st.number_input("Sig", value=9, key="msig")
                                    cap = st.number_input("Cap", value=1000.0, key="scap")
                                    
                                    if st.button("Add", type="primary"):
                                        add_analysis_to_state(s_tick, s_st, p, cap, years)
                                        st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                            st.markdown("""
                            <div style='text-align:center; font-size:0.85em; color:gray; margin-top:10px;'>
                                Can't find an asset? Edit your current assets on the top right of the website!
                            </div>
                            """, unsafe_allow_html=True)

    # ==============================================================================
    # COL 2 : PRICE HISTORY & PREDICTION
    # ==============================================================================
    with col_pred:
        st.subheader("Price History")
        vis_years = st.slider("Visible History", 1, 10, 2, key="vis_years_slider")
        
        tape_tickers = st.session_state.get('tape_tickers', [])
        color_map = {}
        for item in st.session_state['analyses']: color_map[item['symbol']] = item['color']
        for i, t in enumerate(tape_tickers):
            if t not in color_map: color_map[t] = COLORS[i % len(COLORS)]
        
        current_selection = list(st.session_state['selected_pred_tickers'])
        
        display_data = {}
        for t in current_selection:
            if t in tape_tickers:
                col = color_map.get(t, "#ffffff")
                hist_data = get_full_history_for_prediction(t)
                pred_data = None
                if t in st.session_state['pred_results']:
                     pred_data = st.session_state['pred_results'][t].get('pred')
                display_data[t] = {"hist": hist_data, "pred": pred_data, "color": col}
        
        # --- GRAPH PREDICTION ---
        show_ci_val = st.session_state.get("tog_ci", False)
        render_prediction_chart(display_data, show_ci=show_ci_val, visible_years=vis_years)
        
        # --- CHECKBOX ---
        st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
        st.checkbox("Show Confidence Interval", value=False, key="tog_ci")
        st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
        
        # --- SELECT ASSETS LIST ---
        st.write("") 
        st.write("") 
        st.write("###### Select Assets")
        
        for t in tape_tickers:
            t_col = color_map.get(t, "#ffffff")
            c_chk, c_lbl = st.columns([0.1, 0.9])
            with c_chk:
                is_checked = t in st.session_state['selected_pred_tickers']
                new_state = st.checkbox("Select", value=is_checked, key=f"chk_{t}", label_visibility="collapsed")
                if new_state != is_checked:
                    if new_state: st.session_state['selected_pred_tickers'].add(t)
                    else: st.session_state['selected_pred_tickers'].remove(t)
                    st.rerun()
            with c_lbl:
                st.markdown(f"<div style='margin-top: -5px; color: {t_col}; font-weight: bold;'>{t}</div>", unsafe_allow_html=True)

        st.divider()
        
        st.subheader("Run Prediction")
        c_mod, c_hor = st.columns(2)
        with c_mod: p_model = st.selectbox("Model", ["Linear Regression", "Random Forest", "ARIMA"], key="pm_mod")
        with c_hor: p_days = st.number_input("Horizon (Days)", 7, 365, 30, key="pm_day")
        
        p_params = {}
        if p_model == "Random Forest": p_params["n_estimators"] = st.slider("Trees", 10, 200, 100, step=10, key="rf_t")
        elif p_model == "ARIMA": p_params["p"] = st.slider("Lag (p)", 1, 10, 5, key="ar_p")
        
        if st.button("Generate Forecast", type="primary", use_container_width=True):
            new_results = st.session_state['pred_results'].copy()
            progress = st.progress(0)
            targets = [t for t in current_selection if t in tape_tickers]
            for i, t in enumerate(targets):
                if t in display_data: hist_data = display_data[t]['hist']
                else: hist_data = get_full_history_for_prediction(t)
                    
                if not hist_data.empty:
                    f_df, metrics = run_prediction_model(hist_data, p_model, p_days, p_params)
                    new_results[t] = {"pred": f_df, "metrics": metrics}
                progress.progress((i + 1) / len(targets))
            st.session_state['pred_results'] = new_results
            st.rerun()

        active_preds = [t for t in current_selection if t in st.session_state['pred_results']]
        if active_preds:
            st.caption("Model Statistics")
            for t in active_preds:
                t_col = color_map.get(t, "#ffffff")
                mets = st.session_state['pred_results'][t].get('metrics', {})
                if mets:
                    with st.expander(f"📊 {t} Stats", expanded=False):
                        st.markdown(f"<div style='border-left: 3px solid {t_col}; padding-left: 5px; margin-bottom: 5px;'>Model Fit Metrics</div>", unsafe_allow_html=True)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("MAE", f"{mets.get('MAE',0):.2f}")
                        c2.metric("RMSE", f"{mets.get('RMSE',0):.2f}")
                        c3.metric("R²", f"{mets.get('R2',0):.2f}")