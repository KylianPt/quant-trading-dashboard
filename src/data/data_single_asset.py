from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

# Actif principal pour le module Quant A : Air Liquide
DEFAULT_TICKER = "AI.PA"


def get_price_history(
    ticker: str = DEFAULT_TICKER,
    years: int = 5,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Télécharge l'historique de prix pour un seul actif via Yahoo Finance.

    Parameters
    ----------
    ticker : str
        Code Yahoo Finance de l'actif (ex: 'AI.PA' pour Air Liquide).
    years : int
        Horizon historique en années (approximation, on convertit en jours).
    interval : str
        Fréquence des données ('1d', '1h', '1wk', etc.).
        Pour les backtests daily, on utilisera '1d'.

    Returns
    -------
    data : pd.DataFrame
        DataFrame indexé par Date, colonnes :
        - 'Open', 'High', 'Low', 'Close', 'Volume'
        - 'return' : rendement simple quotidien (Close_t / Close_{t-1} - 1)
    """
    end = date.today()
    start = end - timedelta(days=365 * years)

    raw = yf.download(
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,  # ajuste pour dividendes / splits
        progress=False,
    )

    if raw.empty:
        raise ValueError(f"No data returned for ticker {ticker!r}")

    # IMPORTANT : aplatit les colonnes si yfinance renvoie un MultiIndex
    # Exemple de colonnes brutes :
    #   Price   Open   High   Low   Close   Volume
    #   Ticker  AI.PA  AI.PA  AI.PA AI.PA   AI.PA
    if isinstance(raw.columns, pd.MultiIndex):
        # on garde seulement le premier niveau: 'Open', 'High', 'Low', 'Close', 'Volume'
        raw.columns = raw.columns.get_level_values(0)

    # On garde les colonnes principales
    cols_to_keep = ["Open", "High", "Low", "Close", "Volume"]
    data = raw[cols_to_keep].copy()

    # Assure que l'index est trié et nommé
    data = data.sort_index()
    data.index.name = "Date"

    # Rendements simples à partir d'une vraie Series 1D
    close = data["Close"]
    data["return"] = close.pct_change(fill_method=None)

    # On supprime la première ligne (return NaN) pour simplifier les backtests
    data = data.iloc[1:]

    return data


if __name__ == "__main__":
    # Petit test manuel : affiche les 5 dernières lignes pour l'actif par défaut
    df = get_price_history()
    print(
        f"Downloaded history for {DEFAULT_TICKER} "
        f"({len(df)} rows, from {df.index[0].date()} to {df.index[-1].date()})"
    )
    print(df.tail())

