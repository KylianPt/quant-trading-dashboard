import streamlit as st
import pandas as pd
import altair as alt

COLORS = [
    "#FF4B4B", "#1C83E1", "#00CC96", "#AB63FA", "#FFA15A", 
    "#19D3F3", "#FF6692", "#B6E880", "#FF9F1C", "#D0F4DE"
]

# --- CORRECTION HERE: ROUNDING IN COMPARISON ---
def get_medal(value, metric_key, rankings):
    ref_list = rankings.get(metric_key, [])
    if not ref_list: return ""
    
    # Round value to compare with ranking list
    try:
        val_round = round(float(value), 5)
    except:
        return ""
        
    if len(ref_list) > 0 and val_round == ref_list[0]: return "🥇"
    if len(ref_list) > 1 and val_round == ref_list[1]: return "🥈"
    if len(ref_list) > 2 and val_round == ref_list[2]: return "🥉"
    return ""

def style_chart(chart, title_y):
    return chart.configure_view(
        fill='transparent',
        stroke='#aaaaaa',   
        strokeWidth=1
    ).configure_axis(
        grid=True,
        gridColor='#444444', 
        gridOpacity=0.3,
        domainColor='#aaaaaa',
        tickColor='#aaaaaa',
        labelColor='#aaaaaa',
        titleColor='#aaaaaa'
    ).configure_legend(
        labelColor='#aaaaaa'
    ).properties(
        background='transparent'
    ).interactive()

def render_main_chart(items, show_absolute=False):
    if not items:
        st.info("No active strategy charts.")
        return

    hist_dfs = []
    domain_names, range_colors = [], []
    
    if show_absolute:
        y_title = "Portfolio Value ($)"
        tooltip_fmt = ",.2f"
    else:
        y_title = "Normalized Return (Base 1.0)"
        tooltip_fmt = ".3f"
    
    for item in items:
        df = item['data'].copy().reset_index()
        if 'Date' not in df.columns: df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
        
        if 'Equity' in df.columns:
            equity_curve = df['Equity']
        else:
            start_price = df['Close'].iloc[0]
            equity_curve = (df['Close'] / start_price) * item['capital']

        if show_absolute:
            val = equity_curve
        else:
            start_val = equity_curve.iloc[0]
            val = equity_curve / start_val

        mini_df = pd.DataFrame({'Date': df['Date'], 'Value': val, 'Legend': item['legend_name']})
        hist_dfs.append(mini_df)
        domain_names.append(item['legend_name'])
        range_colors.append(item['color'])

    if hist_dfs:
        full_df = pd.concat(hist_dfs)
        base_chart = alt.Chart(full_df).mark_line(strokeWidth=2).encode(
            x=alt.X('Date:T', axis=alt.Axis(title=None)),
            y=alt.Y('Value:Q', axis=alt.Axis(title=y_title)),
            color=alt.Color('Legend:N', scale=alt.Scale(domain=domain_names, range=range_colors), legend=alt.Legend(title=None, orient='bottom')),
            tooltip=['Date', 'Legend', alt.Tooltip('Value', format=tooltip_fmt, title="Value")]
        )
        final_chart = style_chart(base_chart, y_title)
        st.altair_chart(final_chart, use_container_width=True)

def render_prediction_chart(ticker_data_map, show_ci=True, visible_years=1):
    if not ticker_data_map:
        st.info("No assets selected.")
        return

    hist_layers = []
    pred_layers = []
    band_layers = []
    
    for ticker, data in ticker_data_map.items():
        color = data['color']
        
        # 1. HISTORIQUE
        df_hist = data['hist'].reset_index()
        # On s'assure que la colonne s'appelle 'Date'
        if 'Date' not in df_hist.columns: 
            df_hist.rename(columns={df_hist.columns[0]: 'Date'}, inplace=True)
        
        # --- FIX CRITIQUE ICI : On force la conversion en Datetime ---
        df_hist['Date'] = pd.to_datetime(df_hist['Date'])
        
        max_date = df_hist['Date'].max()
        
        # Maintenant la soustraction fonctionnera car max_date est un Timestamp
        cutoff_date = max_date - pd.DateOffset(years=visible_years)
        
        df_hist_zoom = df_hist[df_hist['Date'] > cutoff_date].copy()
        df_hist_zoom['Legend'] = ticker
        
        l_hist = alt.Chart(df_hist_zoom).mark_line(color=color).encode(
            x='Date:T',
            y=alt.Y('Close:Q', scale=alt.Scale(zero=False)), 
            tooltip=['Date', 'Close']
        )
        hist_layers.append(l_hist)
        
        # 2. PREDICTION
        if data.get('pred') is not None and not data['pred'].empty:
            df_pred = data['pred'].copy()
            # On s'assure aussi que la prédiction a bien des dates correctes
            if 'Date' in df_pred.columns:
                df_pred['Date'] = pd.to_datetime(df_pred['Date'])
            else:
                df_pred = df_pred.reset_index()
                df_pred.rename(columns={df_pred.columns[0]: 'Date'}, inplace=True)
                df_pred['Date'] = pd.to_datetime(df_pred['Date'])

            df_pred['Legend'] = f"{ticker} (Pred)"
            
            l_pred = alt.Chart(df_pred).mark_line(strokeDash=[5, 5], color=color).encode(
                x='Date:T',
                y='Forecast:Q',
                tooltip=['Date', 'Forecast']
            )
            pred_layers.append(l_pred)
            
            # 3. CONFIDENCE INTERVAL
            if show_ci:
                l_band = alt.Chart(df_pred).mark_area(opacity=0.2, color=color).encode(
                    x='Date:T',
                    y='Lower:Q',
                    y2='Upper:Q'
                )
                band_layers.append(l_band)

    layers = hist_layers + pred_layers + band_layers
    
    if layers:
        combined = alt.layer(*layers).resolve_scale(y='shared')
        # Mise à jour de la syntaxe dépréciée style_chart si nécessaire, 
        # mais le fix principal est ci-dessus.
        final_chart = style_chart(combined, 'Price')
        st.altair_chart(final_chart, use_container_width=True)
    
def render_metric_card_html(item, rankings):
    s = item['summary']
    border_c = item['color']
    m_eq = get_medal(s['final_equity'], 'final_equity', rankings)
    m_ret = get_medal(s['total_return'], 'total_return', rankings)
    m_dd = get_medal(s['max_drawdown'], 'max_drawdown', rankings)
    m_aret = get_medal(s['annualized_return'], 'annualized_return', rankings)
    m_avol = get_medal(s['annualized_volatility'], 'annualized_volatility', rankings)
    m_shp = get_medal(s['sharpe_ratio'], 'sharpe_ratio', rankings)

    html = f"""
    <div class="tilt-card" style="border: 2px solid {border_c}; border-radius: 8px; padding: 12px; background-color: rgba(128,128,128,0.05); margin-top: 5px;">
        <table style="width:100%; border-collapse: collapse; font-size:0.85em; color: inherit;">
            <tr style="border-bottom: 1px solid rgba(128,128,128,0.2);">
                <td style="padding:3px 0; color:gray;">Initial Equity</td>
                <td style="text-align:right; color:gray;">{item['capital']:.2f}</td><td style="width:20px;"></td>
            </tr>
            <tr><td>Final Equity</td><td style="text-align:right; font-weight:bold;">{s['final_equity']:.2f}</td><td style="text-align:right;">{m_eq}</td></tr>
            <tr><td>Total Return</td><td style="text-align:right; font-weight:bold;">{s['total_return']*100:.1f}%</td><td style="text-align:right;">{m_ret}</td></tr>
            <tr><td>Max Drawdown</td><td style="text-align:right; font-weight:bold; color:#ff4b4b;">{s['max_drawdown']*100:.1f}%</td><td style="text-align:right;">{m_dd}</td></tr>
            <tr><td>Ann. Return</td><td style="text-align:right; font-weight:bold;">{s['annualized_return']*100:.1f}%</td><td style="text-align:right;">{m_aret}</td></tr>
            <tr><td>Ann. Volatility</td><td style="text-align:right; font-weight:bold;">{s['annualized_volatility']*100:.1f}%</td><td style="text-align:right;">{m_avol}</td></tr>
            <tr><td>Sharpe Ratio</td><td style="text-align:right; font-weight:bold;">{s['sharpe_ratio']:.2f}</td><td style="text-align:right;">{m_shp}</td></tr>
        </table>
    </div>
    """
    return html