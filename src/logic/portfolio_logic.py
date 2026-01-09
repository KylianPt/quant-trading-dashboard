import pandas as pd
import numpy as np
from data.data_single_asset import get_price_history
from logic.metrics import summarize_strategy

def get_portfolio_data(tickers, years=5):
    """Récupère et aligne les prix."""
    if not tickers: return pd.DataFrame()
    df_list = []
    for t in tickers:
        df = get_price_history(t, years=years)
        if not df.empty:
            df = df[['Close']].rename(columns={'Close': t})
            df_list.append(df)
    if not df_list: return pd.DataFrame()
    # Dropna est crucial pour aligner les dates de départ
    return pd.concat(df_list, axis=1).dropna()

def apply_stop_loss(equity_curve, stop_loss_pct):
    """Coupe la position si le drawdown dépasse X%."""
    if stop_loss_pct <= 0: return equity_curve
    
    values = equity_curve.values
    peak = values[0]
    is_stopped = False
    stop_val = values[0]
    new_values = []
    
    for v in values:
        if is_stopped:
            new_values.append(stop_val)
        else:
            if v > peak: peak = v
            dd = (peak - v) / peak
            if dd >= (stop_loss_pct / 100.0):
                is_stopped = True
                stop_val = v
                new_values.append(v)
            else:
                new_values.append(v)
    return pd.Series(new_values, index=equity_curve.index)

def calculate_asset_metrics_detailed(price_df, capital_per_asset_map):
    detailed = {}
    if price_df.empty: return detailed

    for col in price_df.columns:
        series = price_df[col]
        start_val = capital_per_asset_map.get(col, 0)
        
        # Calcul courbe de valeur de l'actif (Allocated Equity)
        if not series.empty and series.iloc[0] != 0:
            norm = series / series.iloc[0]
            equity = norm * start_val
            
            # Métriques simples
            end_val = equity.iloc[-1]
            tot_ret = (end_val - start_val) / start_val if start_val > 0 else 0
            
            # Volatilité & Sharpe
            rets = equity.pct_change().dropna()
            vol = rets.std() * np.sqrt(252)
            sharpe = (tot_ret / vol) if vol > 0 else 0 # Simplifié
            
            # Drawdown
            roll = equity.cummax()
            dd = (equity - roll) / roll
            max_dd = dd.min()

            # Annualized Return (CAGR)
            days = (equity.index[-1] - equity.index[0]).days
            years = days / 365.25
            ann_ret = (end_val / start_val) ** (1/years) - 1 if (years > 0 and start_val > 0) else 0

            detailed[col] = {
                'final_equity': end_val,
                'total_return': tot_ret,
                'max_drawdown': max_dd,
                'annualized_return': ann_ret,
                'annualized_volatility': vol,
                'sharpe_ratio': sharpe
            }
        else:
            detailed[col] = {'final_equity': 0, 'total_return': 0, 'max_drawdown': 0}
            
    return detailed

def calculate_portfolio_performance(price_df, weights_dict, initial_capital=10000.0, rebal_freq="None", fee_pct=0.0, stop_loss_pct=0.0):
    if price_df.empty: return None, {}
    
    # 1. Préparation des poids alignés
    assets = price_df.columns
    w_vec = np.array([weights_dict.get(a, 0.0) for a in assets])
    
    # 2. Calcul de la courbe d'équité
    # Pour "None" (Buy & Hold), c'est la somme des courbes individuelles
    if rebal_freq == "None":
        # Normalisation base 1.0
        norm_df = price_df / price_df.iloc[0]
        # Valeur allouée par actif = Capital * Poids
        allocated_vals = initial_capital * w_vec
        # Equity = Somme(Norm_Price_t * Alloc_i)
        portfolio_equity = norm_df.dot(allocated_vals)
    else:
        # Simplification pour ce correctif (fallback sur B&H si rebal trop complexe pour l'instant)
        # Idéalement ici on met la boucle de rééquilibrage
        norm_df = price_df / price_df.iloc[0]
        allocated_vals = initial_capital * w_vec
        portfolio_equity = norm_df.dot(allocated_vals)

    # 3. Stop Loss
    if stop_loss_pct > 0:
        portfolio_equity = apply_stop_loss(portfolio_equity, stop_loss_pct)

    # 4. Métriques Globales
    end_val = portfolio_equity.iloc[-1]
    tot_ret = (end_val - initial_capital) / initial_capital
    
    rets = portfolio_equity.pct_change().dropna()
    vol = rets.std() * np.sqrt(252)
    sharpe = (tot_ret / vol) if vol > 0 else 0 # Simplifié, idéalement (CAGR - Rf)/Vol
    
    stats = {
        'Final Value': end_val,
        'Total Return': tot_ret,
        'Volatility': vol,
        'Sharpe': sharpe
    }
    
    return portfolio_equity, stats

def compute_correlation_matrix(price_df):
    if price_df.empty: return pd.DataFrame()
    return price_df.pct_change().dropna().corr()

def get_portfolio_rankings(stats_map):
    # Génère les listes triées pour attribuer les médailles
    values = {'final_equity': [], 'total_return': [], 'max_drawdown': [], 'annualized_return': [], 'annualized_volatility': [], 'sharpe_ratio': []}
    for t, s in stats_map.items():
        for k in values.keys():
            if k in s: values[k].append(round(s[k], 5))
            
    rankings = {}
    for k, v in values.items():
        v = list(set(v))
        if k == 'annualized_volatility' or k == 'max_drawdown': # Plus petit (ou plus négatif) est mieux ? 
            # Volatilité: plus petit est mieux -> sort asc
            # DD: c'est négatif (-0.5 vs -0.1). -0.1 est mieux (plus grand). -> sort desc (reverse=True)
            if k == 'annualized_volatility': rankings[k] = sorted(v)
            else: rankings[k] = sorted(v, reverse=True)
        else:
            rankings[k] = sorted(v, reverse=True)
    return rankings