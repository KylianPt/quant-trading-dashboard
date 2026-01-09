import numpy as np
import pandas as pd
import scipy.optimize as sco

def get_portfolio_metrics(weights, mean_returns, cov_matrix):
    """Calcule Return et Volatilité annualisés pour des poids donnés."""
    weights = np.array(weights)
    ret = np.sum(mean_returns * weights) * 252
    vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return ret, vol

def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate=0.0):
    p_ret, p_vol = get_portfolio_metrics(weights, mean_returns, cov_matrix)
    return -(p_ret - risk_free_rate) / p_vol

def get_optimized_weights(price_df, objective='sharpe'):
    """
    Trouve les poids optimaux.
    objective: 'sharpe' (Max Sharpe) ou 'vol' (Min Volatility)
    """
    if price_df.empty: return None

    # Rendements log ou simples
    rets = price_df.pct_change().dropna()
    mean_returns = rets.mean()
    cov_matrix = rets.cov()
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    
    # Contraintes : Somme des poids = 1
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # Bornes : 0 <= poids <= 1 (Pas de short selling)
    bounds = tuple((0.0, 1.0) for asset in range(num_assets))
    
    # Poids initiaux (Equal Weight)
    init_guess = num_assets * [1. / num_assets,]

    if objective == 'sharpe':
        result = sco.minimize(neg_sharpe_ratio, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
    elif objective == 'vol':
        # Fonction lambda qui retourne juste la volatilité
        min_vol_func = lambda w, m, c: get_portfolio_metrics(w, m, c)[1]
        result = sco.minimize(min_vol_func, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
    else:
        return None

    return result.x

def simulate_efficient_frontier(price_df, num_portfolios=2000):
    """
    Simule N portefeuilles aléatoires pour dessiner la frontière efficiente.
    """
    if price_df.empty: return pd.DataFrame()

    rets = price_df.pct_change().dropna()
    mean_returns = rets.mean()
    cov_matrix = rets.cov()
    num_assets = len(mean_returns)
    
    results = np.zeros((3, num_portfolios)) # 0: Ret, 1: Vol, 2: Sharpe
    
    for i in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        
        p_ret, p_vol = get_portfolio_metrics(weights, mean_returns, cov_matrix)
        results[0,i] = p_ret
        results[1,i] = p_vol
        results[2,i] = p_ret / p_vol if p_vol > 0 else 0
        
    df_frontier = pd.DataFrame({
        'Return': results[0,:],
        'Volatility': results[1,:],
        'Sharpe': results[2,:]
    })
    return df_frontier