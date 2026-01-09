import streamlit as st
import pandas as pd
from data.data_single_asset import get_price_history 
from logic.strategies_single import backtest_buy_and_hold, backtest_momentum_sma, backtest_macd
from logic.metrics import summarize_strategy

# Palette de couleurs optimisée pour le contraste (Dark & Light mode)
COLORS = [
    "#FF4B4B", # Rouge Streamlit
    "#1C83E1", # Bleu
    "#00CC96", # Vert
    "#AB63FA", # Violet
    "#FFA15A", # Orange
    "#19D3F3", # Cyan
    "#FF6692", # Rose
    "#B6E880", # Vert Lime
    "#FF9F1C", # Orange vif
    "#D0F4DE"  # Vert pâle
]

def get_full_history_for_prediction(ticker):
    """Récupère tout l'historique disponible pour la prédiction."""
    try:
        return get_price_history(ticker, years=100)
    except:
        return pd.DataFrame()

def compute_analysis_data(ticker, strategy, params, capital, years):
    """
    Calcul de la stratégie. 
    Renvoie 3 valeurs : resultat_df, nom_court, résumé_dict
    """
    try:
        data = get_price_history(ticker, years=years)
    except Exception as e:
        return None, None, None

    if data.empty: return None, None, None

    res = None
    strat_short = ""

    try:
        if strategy == "Buy & Hold":
            res = backtest_buy_and_hold(data, initial_capital=capital)
            strat_short = "B&H"
        elif strategy == "Momentum SMA":
            win = params.get('window', 50)
            res = backtest_momentum_sma(data, window=win, initial_capital=capital)
            strat_short = f"SMA({win})"
        elif strategy == "MACD":
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            sig = params.get('signal', 9)
            res = backtest_macd(data, fast=fast, slow=slow, signal=sig, initial_capital=capital)
            strat_short = f"MACD({fast},{slow},{sig})"
    except:
        return None, None, None

    if res is None: return None, None, None

    summary = summarize_strategy(res, capital)
    return res, strat_short, summary

def update_analyses_duration(new_years):
    if 'analyses' not in st.session_state: return
    updated_list = []
    for item in st.session_state['analyses']:
        res, strat_short, summary = compute_analysis_data(
            item['symbol'], item['strategy'], item['params'], item['capital'], new_years
        )
        if res is not None:
            item['data'] = res
            item['summary'] = summary
            item['years'] = new_years
        updated_list.append(item)
    st.session_state['analyses'] = updated_list
    st.toast(f"Updated history to {new_years} years", icon="🔄")

def get_next_available_color(current_analyses):
    """Trouve la première couleur de la palette qui n'est pas encore utilisée."""
    used_colors = {item['color'] for item in current_analyses}
    
    for color in COLORS:
        if color not in used_colors:
            return color
    
    # Si toutes les couleurs sont prises (cas rare car limite à 10), on recycle
    # en prenant une couleur qui dépend de la longueur actuelle
    return COLORS[len(current_analyses) % len(COLORS)]

def add_analysis_to_state(ticker, strategy, params, capital, years, auto=False):
    # Initialize list if needed
    if 'analyses' not in st.session_state: st.session_state['analyses'] = []

    # --- LIMIT CHECK (MAX 10 GRAPHS) ---
    if len(st.session_state['analyses']) >= 10:
        if not auto: st.toast("Limit reached: Max 10 charts allowed.", icon="🚫")
        return

    # Check duplicates
    for item in st.session_state['analyses']:
        if (item['symbol'] == ticker and item['strategy'] == strategy and 
            item['params'] == params and item['years'] == years):
            if not auto: st.toast(f"Graph already exists!", icon="⚠️")
            return

    res, strat_short, summary = compute_analysis_data(ticker, strategy, params, capital, years)
    
    if res is None:
        if not auto: st.toast(f"Error: No data for {ticker}", icon="❌")
        return

    new_id = len(st.session_state['analyses'])
    
    # --- GESTION COULEUR INTELLIGENTE ---
    # On force une couleur unique pour chaque carte pour bien les distinguer
    color = get_next_available_color(st.session_state['analyses'])

    st.session_state['analyses'].append({
        "id": new_id,
        "symbol": ticker,
        "strategy": strategy,
        "strat_short": strat_short,
        "legend_name": f"{ticker} ({strat_short})",
        "summary": summary,
        "data": res,
        "color": color,
        "params": params,
        "capital": capital,
        "years": years
    })
    if not auto: st.toast(f"Added {ticker}", icon="✅")

def remove_analysis(index):
    if 0 <= index < len(st.session_state['analyses']):
        st.session_state['analyses'].pop(index)
        st.rerun()

def sync_tape_to_graphs(current_years):
    tape_tickers = st.session_state.get('tape_tickers', [])
    if 'synced_tickers_snapshot' not in st.session_state: st.session_state['synced_tickers_snapshot'] = []
    
    current_set = set(tape_tickers)
    snapshot_set = set(st.session_state['synced_tickers_snapshot'])
    new_tickers = current_set - snapshot_set
    
    added = False
    for t in new_tickers:
        # L'ajout auto respectera maintenant la limite de 10
        add_analysis_to_state(t, "Buy & Hold", {}, 1000.0, current_years, auto=True)
        added = True
    
    st.session_state['synced_tickers_snapshot'] = list(tape_tickers)
    if added: st.rerun()

def get_rankings(items):
    if not items: return {}
    values = {'final_equity': [], 'total_return': [], 'max_drawdown': [], 'annualized_return': [], 'annualized_volatility': [], 'sharpe_ratio': []}
    for item in items:
        s = item['summary']
        for k in values.keys(): values[k].append(s[k])
    rankings = {}
    for k, v in values.items():
        unique_vals = list(set(v))
        if k == 'annualized_volatility': rankings[k] = sorted(unique_vals) 
        else: rankings[k] = sorted(unique_vals, reverse=True)
    return rankings