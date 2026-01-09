import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time
from logic.portfolio_logic import (
    get_portfolio_data, 
    calculate_portfolio_performance, 
    compute_correlation_matrix, 
    calculate_asset_metrics_detailed,
    get_portfolio_rankings
)
from logic.optimization import get_optimized_weights, simulate_efficient_frontier
from ui.single_components import COLORS, get_medal
# Import de la nouvelle fonction delete_portfolio_db
from data.database import save_portfolio_db, get_latest_portfolios, get_active_tickers_db, delete_portfolio_db

def format_pct(val):
    if pd.isna(val) or np.isinf(val): return "0.0%"
    return f"{val*100:.1f}%"

def make_detailed_card_html(ticker, name, stats, capital, color, rankings):
    fin_eq = stats.get('final_equity', 0)
    tot_ret = stats.get('total_return', 0)
    max_dd = stats.get('max_drawdown', 0)
    ann_ret = stats.get('annualized_return', 0)
    ann_vol = stats.get('annualized_volatility', 0)
    sharpe = stats.get('sharpe_ratio', 0)

    m_eq = get_medal(fin_eq, 'final_equity', rankings)
    m_ret = get_medal(tot_ret, 'total_return', rankings)
    m_dd = get_medal(max_dd, 'max_drawdown', rankings)
    m_aret = get_medal(ann_ret, 'annualized_return', rankings)
    m_avol = get_medal(ann_vol, 'annualized_volatility', rankings)
    m_shp = get_medal(sharpe, 'sharpe_ratio', rankings)
    
    html = f"""
<div class="tilt-card" style="border: 2px solid {color}; border-radius: 8px; padding: 12px; margin-top: 5px; margin-bottom: 20px; background-color: rgba(128,128,128,0.05);">
<div style="font-size: 0.8em; opacity: 0.7; margin-bottom: 8px; border-bottom: 1px solid {color}; padding-bottom: 4px;">
{ticker} | Allocated: ${capital:,.0f}
</div>
<table style="width:100%; border-collapse: collapse; font-size:0.85em; color: inherit; line-height: 1.4;">
<tr><td>Final Value</td><td style="text-align:right; font-weight:bold;">${fin_eq:,.0f}</td><td style="text-align:right; font-size:0.8em; color:gray;">{m_eq}</td></tr>
<tr><td>Total Return</td><td style="text-align:right; font-weight:bold;">{format_pct(tot_ret)}</td><td style="text-align:right; font-size:0.8em; color:gray;">{m_ret}</td></tr>
<tr><td>Max Drawdown</td><td style="text-align:right; font-weight:bold; color:#ff4b4b;">{format_pct(max_dd)}</td><td style="text-align:right; font-size:0.8em; color:gray;">{m_dd}</td></tr>
<tr><td>Ann. Return</td><td style="text-align:right; font-weight:bold;">{format_pct(ann_ret)}</td><td style="text-align:right; font-size:0.8em; color:gray;">{m_aret}</td></tr>
<tr><td>Ann. Volatility</td><td style="text-align:right; font-weight:bold;">{format_pct(ann_vol)}</td><td style="text-align:right; font-size:0.8em; color:gray;">{m_avol}</td></tr>
<tr><td>Sharpe Ratio</td><td style="text-align:right; font-weight:bold;">{sharpe:.2f}</td><td style="text-align:right; font-size:0.8em; color:gray;">{m_shp}</td></tr>
</table>
</div>
"""
    return html

# --- SECTION COMMUNAUTAIRE UNIFIÉE ---
# Tout ce qui est dans ce bloc se rafraichit ensemble (Formulaire + Liste)
@st.fragment
def render_community_section(weights, years, rebal_freq, stop_loss, stats):
    st.divider()
    st.markdown("### Community Portfolios")

    # 1. FORMULAIRE DE PUBLICATION
    st.caption("Share your strategy with the community.")
    with st.form("publish_form", clear_on_submit=True):
        c_usr, c_com = st.columns([0.3, 0.7])
        with c_usr: user_name = st.text_input("User Name", placeholder="e.g. TraderJohn")
        with c_com: comment = st.text_input("Comment", placeholder="Aggressive growth strategy...")
        
        submitted = st.form_submit_button("Publish Portfolio")
        
        if submitted:
            if user_name and comment:
                # Création de la chaîne formatée avec les pourcentages : "AAPL (50%), MSFT (50%)"
                tickers_str_list = []
                for ticker, w in weights.items():
                    if w > 0:
                        tickers_str_list.append(f"{ticker} ({w*100:.0f}%)")
                tickers_formatted = ", ".join(tickers_str_list)
                
                # Sauvegarde
                save_portfolio_db(user_name, comment, tickers_formatted, years, rebal_freq, stop_loss, stats)
                st.success("Published successfully!")
                time.sleep(0.5)
                st.rerun() # Rafraichit le fragment pour afficher le nouveau commentaire
            else:
                st.error("Please fill Name and Comment.")

    # 2. FLUX DES COMMENTAIRES (FEED)
    st.markdown("#### Latest Strategies")
    try:
        df_shared = get_latest_portfolios(10) # On en prend 10
        if not df_shared.empty:
            for index, row in df_shared.iterrows():
                # Conteneur pour aligner le bouton supprimer à droite
                with st.container():
                    # Carte stylisée
                    st.markdown(f"""
                    <div style="border:1px solid #444; border-radius:8px; padding:15px; margin-bottom:5px; background-color:rgba(255,255,255,0.02); position: relative;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                            <span style="font-weight:bold; color:#1C83E1;">{row['user_name']}</span>
                            <span style="font-size:0.8em; color:gray;">{row['timestamp']}</span>
                        </div>
                        <div style="font-style:italic; margin-bottom:10px; color:#ddd;">"{row['comment']}"</div>
                        <div style="font-size:0.85em; color:gray; margin-bottom:8px;">
                            <strong>Allocation:</strong> <span style="color:#D0F4DE;">{row['tickers']}</span> <br>
                            <strong>Settings:</strong> {row['years']}Y | {row['strategy_rebal']} | StopLoss: {row['strategy_stoploss']}%
                        </div>
                        <div style="display:flex; gap:15px; font-size:0.9em; border-top:1px solid #444; padding-top:8px;">
                            <span style="color:#00CC96;">Ret: {row['total_return']*100:.1f}%</span>
                            <span>Vol: {row['volatility']*100:.1f}%</span>
                            <span>Sharpe: {row['sharpe']:.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Bouton Supprimer (Petit et discret)
                    # On utilise une colonne pour le placer à droite sous la carte ou à côté
                    col_space, col_del = st.columns([0.9, 0.1])
                    with col_del:
                        if st.button("🗑️", key=f"del_comm_{row['id']}", help="Delete this portfolio"):
                            delete_portfolio_db(row['id'])
                            st.rerun() # Rafraichit le fragment immédiatement
                
        else:
            st.info("No shared portfolios yet. Be the first!")
    except Exception as e:
        st.error(f"Error loading feed: {e}")


def render_portfolio_view(df_assets):
    tickers = get_active_tickers_db() 
    if not tickers: tickers = st.session_state.get('tape_tickers', [])
        
    name_map = df_assets.set_index('Symbol')['Name'].to_dict()

    if len(tickers) < 2:
        st.warning("Please add at least 2 assets in the ticker tape to build a portfolio.")
        return

    st.subheader("Portfolio Strategy & Optimization")

    st.markdown("#### Configuration")
    c1, c2, c3, c4 = st.columns(4)
    with c1: years = st.slider("History (Years)", 1, 10, 5, key="port_years")
    with c2: capital = st.number_input("Initial Capital ($)", 1000.0, 1000000.0, 10000.0, step=1000.0, key="port_cap")
    with c3: rebal_freq = st.selectbox("Rebalancing", ["None", "Monthly", "Quarterly", "Yearly"], index=0)
    with c4: stop_loss = st.number_input("Stop Loss Threshold (%)", 0.0, 50.0, 0.0, step=1.0)
    fee = 0.1

    st.markdown("#### Weight Optimization Strategies")
    st.caption("Click to automatically set weights based on historical data.")
    
    for t in tickers:
        if f"w_{t}" not in st.session_state: st.session_state[f"w_{t}"] = int(100/len(tickers))
            
    c_opt1, c_opt2, c_opt3, _ = st.columns([1,1,1,1])
    
    if c_opt1.button("Equal Weight"):
        eq = int(100/len(tickers))
        for t in tickers: st.session_state[f"w_{t}"] = eq
        st.rerun()

    if c_opt2.button("Maximize Sharpe"):
        with st.spinner("Optimizing weights..."):
            df_opt = get_portfolio_data(tickers, years)
            if not df_opt.empty:
                best_w = get_optimized_weights(df_opt, 'sharpe')
                if best_w is not None:
                    for i, t in enumerate(tickers):
                        st.session_state[f"w_{t}"] = int(best_w[i]*100)
                    st.rerun()

    if c_opt3.button("Minimize Volatility"):
        with st.spinner("Optimizing weights..."):
            df_opt = get_portfolio_data(tickers, years)
            if not df_opt.empty:
                best_w = get_optimized_weights(df_opt, 'vol')
                if best_w is not None:
                    for i, t in enumerate(tickers):
                        st.session_state[f"w_{t}"] = int(best_w[i]*100)
                    st.rerun()

    st.divider()

    st.markdown("#### Asset Allocation")
    
    with st.form("portfolio_allocation_form"):
        weights = {}
        total_w = 0.0
        asset_colors = {t: COLORS[i % len(COLORS)] for i, t in enumerate(tickers)}
        
        for i in range(0, len(tickers), 5):
            cols = st.columns(5)
            for idx, t in enumerate(tickers[i:i+5]):
                with cols[idx]:
                    col = asset_colors[t]
                    st.markdown(f"<div style='color:{col}; font-weight:bold; border-bottom:1px solid {col}; margin-bottom:5px;'>{t}</div>", unsafe_allow_html=True)
                    w_val = st.number_input("% Allocation", 0, 100, key=f"w_{t}", label_visibility="collapsed")
                    weights[t] = w_val / 100.0
                    total_w += w_val
        
        st.write("")
        submitted = st.form_submit_button("RUN SIMULATION", type="primary", use_container_width=True)

    if abs(total_w - 100.0) > 0.1: 
        st.warning(f"Total Allocation: {total_w:.1f}% (Target: 100%)")

    # Si la simulation a été lancée, on affiche les résultats
    if submitted:
        
        with st.spinner("Running Simulation..."):
            df_prices = get_portfolio_data(tickers, years)
            if df_prices.empty:
                st.error("No data available.")
                return

            cap_map = {t: capital * weights.get(t,0) for t in tickers}
            port_equity, stats = calculate_portfolio_performance(df_prices, weights, capital, rebal_freq, fee, stop_loss)
            
            if port_equity is None:
                st.error("Simulation failed.")
                return

            detailed_stats_map = calculate_asset_metrics_detailed(df_prices, cap_map)
            rankings = get_portfolio_rankings(detailed_stats_map)
            
            st.divider()
            
            col_L, col_R = st.columns([0.65, 0.35])
            
            with col_L:
                st.markdown("#### Performance Over Time")
                
                df_p = port_equity.reset_index()
                df_p.columns = ['Date', 'Value']
                df_p['Legend'] = 'PORTFOLIO'
                
                df_assets_list = []
                for t in tickers:
                    if t in df_prices.columns:
                        start_p = df_prices[t].iloc[0]
                        allocated_cap = cap_map[t]
                        if start_p > 0:
                            val_curve = (df_prices[t] / start_p) * allocated_cap
                            dsub = val_curve.reset_index()
                            dsub.columns = ['Date', 'Value']
                            dsub['Legend'] = t
                            df_assets_list.append(dsub)
                
                full_chart_df = pd.concat([df_p] + df_assets_list)
                domain = ['PORTFOLIO'] + tickers
                range_c = ['#FF0000'] + [asset_colors[t] for t in tickers]
                
                chart = alt.Chart(full_chart_df).mark_line().encode(
                    x=alt.X('Date:T', axis=alt.Axis(title=None)),
                    y=alt.Y('Value:Q', axis=alt.Axis(title="Value ($)")),
                    color=alt.Color('Legend:N', scale=alt.Scale(domain=domain, range=range_c)),
                    tooltip=['Date', 'Legend', alt.Tooltip('Value', format=",.0f")]
                ).properties(height=450).configure(background='transparent').interactive()
                st.altair_chart(chart, use_container_width=True)

                st.divider()

                st.markdown("#### Individual Asset Contribution")
                cols_cards = st.columns(3) 
                for i, t in enumerate(tickers):
                    with cols_cards[i % 3]:
                        stats_asset = detailed_stats_map.get(t)
                        full_name = name_map.get(t, t)
                        col_asset = asset_colors[t]
                        if stats_asset:
                            html_card = make_detailed_card_html(t, full_name, stats_asset, cap_map[t], col_asset, rankings)
                            st.markdown(html_card, unsafe_allow_html=True)

            with col_R:
                st.markdown("### Simulation Results")
                
                def make_simple_card(title, value, color=None):
                    style_col = f"color: {color};" if color else ""
                    return f"""
                    <div class="tilt-card" style="padding: 15px; text-align: center; border: 1px solid #4a4a4a; margin-bottom: 10px;">
                    <div style="font-size: 0.9em; color: gray;">{title}</div>
                    <div style="font-size: 1.4em; font-weight: bold; {style_col}">{value}</div>
                    </div>
                    """
                
                r1, r2 = st.columns(2)
                c_ret = "#00CC96" if stats['Total Return'] >= 0 else "#FF4B4B"
                with r1:
                    st.markdown(make_simple_card("Final Value", f"${stats['Final Value']:,.0f}"), unsafe_allow_html=True)
                    st.markdown(make_simple_card("Volatility (Ann.)", f"{stats['Volatility']*100:.2f}%"), unsafe_allow_html=True)
                with r2:
                    st.markdown(make_simple_card("Total Return", f"{stats['Total Return']*100:.2f}%", c_ret), unsafe_allow_html=True)
                    st.markdown(make_simple_card("Sharpe Ratio", f"{stats['Sharpe']:.2f}"), unsafe_allow_html=True)
                
                st.divider()

                st.markdown("#### Correlation Matrix")
                raw_corr = compute_correlation_matrix(df_prices)
                if not raw_corr.empty:
                    corr_reset = raw_corr.reset_index()
                    first_col_name = corr_reset.columns[0]
                    corr_melt = corr_reset.melt(id_vars=first_col_name, var_name='Asset', value_name='Corr')
                    heatmap = alt.Chart(corr_melt).mark_rect().encode(
                        x=alt.X(f'{first_col_name}:O', title=None, axis=alt.Axis(labels=False)), 
                        y=alt.Y('Asset:O', title=None),
                        color=alt.Color('Corr:Q', scale=alt.Scale(scheme='redblue', domain=[-1, 1]), legend=None),
                        tooltip=['Asset', 'Corr']
                    ).properties(height=300).configure(background='transparent').configure_view(stroke=None)
                    st.altair_chart(heatmap, use_container_width=True)
                
                st.divider()

                st.markdown("#### Monte Carlo Simulation")
                st.caption("Efficient Frontier analysis (1000 sims).")
                
                df_frontier = simulate_efficient_frontier(df_prices, num_portfolios=1000)
                
                base = alt.Chart(df_frontier).mark_circle(size=25, opacity=0.6).encode(
                    x=alt.X('Volatility', axis=alt.Axis(title='Volatility'), scale=alt.Scale(padding=5)),
                    y=alt.Y('Return', axis=alt.Axis(title='Ann. Return')),
                    color=alt.Color('Sharpe', scale=alt.Scale(scheme='viridis'), legend=None),
                    tooltip=[alt.Tooltip('Return', format='.2%'), alt.Tooltip('Volatility', format='.2%'), alt.Tooltip('Sharpe', format='.2f')]
                )
                
                curr_df = pd.DataFrame([{
                    'Volatility': float(stats['Volatility']), 
                    'Return': float(stats['Total Return']), 
                    'Label': 'Your Portfolio'
                }])
                
                curr = alt.Chart(curr_df).mark_point(shape='star', size=250, fill='red', color='red').encode(
                    x='Volatility', y='Return', tooltip=['Label']
                )
                
                chart_front = (base + curr).properties(height=300).configure(background='transparent').configure_view(stroke=None).configure_axis(labelColor='#aaaaaa', titleColor='#aaaaaa')
                st.altair_chart(chart_front, use_container_width=True)

            # --- APPEL DE LA SECTION COMMUNAUTAIRE ---
            # Uniquement si simulation réussie pour avoir les stats
            render_community_section(weights, years, rebal_freq, stop_loss, stats)
    
    else:
        # Si pas encore simulé, on affiche quand même le feed en bas, mais sans formulaire
        st.divider()
        st.markdown("### Community Portfolios")
        st.info("Run a simulation above to publish your strategy.")
        
        # On affiche juste la liste pour que l'utilisateur puisse voir ce qui existe
        # Je duplique légèrement la logique d'affichage ici pour éviter de devoir passer des stats vides au fragment
        try:
            df_shared = get_latest_portfolios(10)
            if not df_shared.empty:
                for index, row in df_shared.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="border:1px solid #444; border-radius:8px; padding:15px; margin-bottom:5px; background-color:rgba(255,255,255,0.02); position: relative;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                <span style="font-weight:bold; color:#1C83E1;">{row['user_name']}</span>
                                <span style="font-size:0.8em; color:gray;">{row['timestamp']}</span>
                            </div>
                            <div style="font-style:italic; margin-bottom:10px; color:#ddd;">"{row['comment']}"</div>
                            <div style="font-size:0.85em; color:gray; margin-bottom:8px;">
                                <strong>Allocation:</strong> <span style="color:#D0F4DE;">{row['tickers']}</span> <br>
                                <strong>Settings:</strong> {row['years']}Y | {row['strategy_rebal']} | StopLoss: {row['strategy_stoploss']}%
                            </div>
                            <div style="display:flex; gap:15px; font-size:0.9em; border-top:1px solid #444; padding-top:8px;">
                                <span style="color:#00CC96;">Ret: {row['total_return']*100:.1f}%</span>
                                <span>Vol: {row['volatility']*100:.1f}%</span>
                                <span>Sharpe: {row['sharpe']:.2f}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        col_space, col_del = st.columns([0.9, 0.1])
                        with col_del:
                            if st.button("🗑️", key=f"del_comm_idle_{row['id']}", help="Delete this portfolio"):
                                delete_portfolio_db(row['id'])
                                st.rerun()
            else:
                st.info("No shared portfolios yet.")
        except Exception: pass