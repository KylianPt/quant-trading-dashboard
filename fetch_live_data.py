# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 12:39:01 2026

@author: kylia
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

# Liste des actifs que tu veux suivre
TICKERS = ["^FCHI", "MC.PA", "AIR.PA"]  # CAC40, LVMH, Airbus

def fetch_intraday_data():
    """
    Récupère les données intraday (1 minute) du jour pour les tickers.
    """
    data = yf.download(
        tickers=" ".join(TICKERS),
        period="1d",      # seulement la journée courante
        interval="1m",    # résolution 1 minute
        auto_adjust=True, # ajuste pour dividendes / splits
        threads=True
    )

    # On affiche les dernières lignes pour vérifier que ça marche
    print("Dernières observations :")
    print(data.tail())

    # On affiche l'heure du dernier point pour montrer que c'est 'live'
    last_timestamp = data.index[-1]
    print("\nDernier timestamp reçu :", last_timestamp)

    # Option : sauvegarder dans un CSV pour backtesting futur
    data.to_csv("intraday_prices.csv")
    print("\nDonnées sauvegardées dans intraday_prices.csv")

if __name__ == "__main__":
    fetch_intraday_data()
