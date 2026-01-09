"""
Performance metrics for a single-asset strategy.

We assume the input DataFrame `result` comes from strategies_single,
with at least:
- 'strategy_equity' : valeur cumulée du portefeuille
- 'strategy_return' : rendements simples quotidiens
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    """
    Max drawdown (perte relative maximale par rapport au plus-haut précédent).
    Retourne une valeur négative (ex: -0.25 pour -25%).
    """
    equity = pd.Series(equity).dropna()
    cum_max = equity.cummax()
    drawdown = equity / cum_max - 1.0
    return float(drawdown.min())


def annualized_return(
    returns: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """
    Rendement annualisé à partir de rendements simples.
    """
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan
    mean_daily = r.mean()
    return float((1.0 + mean_daily) ** periods_per_year - 1.0)


def annualized_volatility(
    returns: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """
    Volatilité annualisée à partir de rendements simples.
    """
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan
    return float(r.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """
    Sharpe ratio annualisé (rendement excès / volatilité).
    risk_free_rate est annualisé.
    """
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan

    ar = annualized_return(r, periods_per_year)
    vol = annualized_volatility(r, periods_per_year)
    if vol == 0 or np.isnan(vol):
        return np.nan

    # on retire le taux sans risque annualisé
    excess = ar - risk_free_rate
    return float(excess / vol)


def summarize_strategy(
    result: pd.DataFrame,
    initial_capital: float = 1_000.0,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    """
    Construit un petit résumé des performances à partir d'un DataFrame
    contenant 'strategy_equity' et 'strategy_return'.
    """
    equity = result["strategy_equity"]
    rets = result["strategy_return"]

    total_return = float(equity.iloc[-1] / initial_capital - 1.0)
    ar = annualized_return(rets, periods_per_year)
    vol = annualized_volatility(rets, periods_per_year)
    sr = sharpe_ratio(rets, risk_free_rate, periods_per_year)
    mdd = max_drawdown(equity)

    summary = pd.Series(
        {
            "final_equity": float(equity.iloc[-1]),
            "total_return": total_return,
            "annualized_return": ar,
            "annualized_volatility": vol,
            "sharpe_ratio": sr,
            "max_drawdown": mdd,
        }
    )
    return summary


if __name__ == "__main__":
    # Petit test rapide en branchant sur les modules existants
    from data.data_single_asset import get_price_history, DEFAULT_TICKER
    from logic.strategies_single import backtest_buy_and_hold

    df = get_price_history()
    res = backtest_buy_and_hold(df, initial_capital=1_000.0)
    summary = summarize_strategy(res, initial_capital=1_000.0)

    print(f"=== Summary for Buy & Hold on {DEFAULT_TICKER} ===")
    print(summary)
