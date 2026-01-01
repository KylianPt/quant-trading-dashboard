

from __future__ import annotations

import pandas as pd

from data_single_asset import get_price_history, DEFAULT_TICKER


def _equity_curve_from_returns(
    returns: pd.Series,
    initial_capital: float = 1_000.0,
) -> pd.Series:
    """
    Transforme une série de rendements en courbe de valeur de portefeuille.
    Garantit que le résultat est une Series 1D.
    """
    r = pd.Series(returns, copy=True)  # s'assure que c'est une Series
    r = r.fillna(0.0)

    equity = initial_capital * (1.0 + r).cumprod()
    equity.name = "strategy_equity"
    return equity


def backtest_buy_and_hold(
    data: pd.DataFrame,
    initial_capital: float = 1_000.0,
) -> pd.DataFrame:
    """
    Stratégie Buy & Hold : on achète au début et on garde jusqu'à la fin.
    """
    strategy_returns = pd.Series(data["return"], index=data.index)

    equity = _equity_curve_from_returns(strategy_returns, initial_capital)

    result = pd.DataFrame(index=data.index)
    result["Close"] = data["Close"]
    result["strategy_equity"] = equity
    result["price_norm"] = result["Close"] / result["Close"].iloc[0]
    result["strategy_norm"] = result["strategy_equity"] / initial_capital
    result["strategy_return"] = strategy_returns
    return result


def backtest_momentum_sma(
    data: pd.DataFrame,
    window: int = 50,
    initial_capital: float = 1_000.0,
) -> pd.DataFrame:
    """
    Stratégie Momentum basée sur une moyenne mobile simple (SMA).

    Règle:
    - si Close_t > SMA_t(window) -> investi (position = 1)
    - sinon -> cash (position = 0)
    On applique la position du jour t-1 au rendement du jour t
    pour éviter le look-ahead.
    """
    close = data["Close"]
    returns = data["return"]

    sma = close.rolling(window=window, min_periods=1).mean()

    # Signal brut: 1 si prix > SMA, 0 sinon
    raw_position = (close > sma).astype(float)

    # position du jour t-1 appliquée au rendement du jour t
    position = raw_position.shift(1).fillna(0.0)

    # Rendements de la stratégie (on force en Series)
    strategy_returns = pd.Series(position * returns, index=data.index)

    equity = _equity_curve_from_returns(strategy_returns, initial_capital)

    result = pd.DataFrame(index=data.index)
    result["Close"] = close
    result["SMA"] = sma
    result["position"] = position
    result["strategy_equity"] = equity
    result["price_norm"] = result["Close"] / result["Close"].iloc[0]
    result["strategy_norm"] = result["strategy_equity"] / initial_capital
    result["strategy_return"] = strategy_returns

    return result


if __name__ == "__main__":
    # Petit test rapide sur l'actif par défaut (Air Liquide)
    df = get_price_history()  # par défaut AI.PA
    bh = backtest_buy_and_hold(df)
    mom = backtest_momentum_sma(df, window=50)

    print(f"=== Buy & Hold on {DEFAULT_TICKER} ===")
    print(f"Final equity: {bh['strategy_equity'].iloc[-1]:.2f}")
    print(bh.tail())

    print(f"\n=== Momentum SMA(50) on {DEFAULT_TICKER} ===")
    print(f"Final equity: {mom['strategy_equity'].iloc[-1]:.2f}")
    print(mom.tail())

