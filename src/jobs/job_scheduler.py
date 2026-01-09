import time
import yfinance as yf
import pandas as pd
import numpy as np
from data.database import get_active_tickers_db, log_market_report

def calculate_metrics(ticker, period_label='HOURLY'):
    """
    Calcule les métriques.
    period_label: 'HOURLY', 'DAILY', ou 'INSTANT'
    """
    try:
        # Téléchargement standard (Derniers 5 jours)
        df = yf.download(ticker, period="5d", interval="60m", progress=False)
        
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # On prend la dernière ligne disponible
        last_slice = df.tail(24) 
        
        if last_slice.empty: return None

        # Valeurs actuelles
        price_open = float(last_slice['Open'].iloc[0])
        price_close = float(last_slice['Close'].iloc[-1])
        price_high = float(last_slice['High'].max())
        price_low = float(last_slice['Low'].min())
        volume = int(last_slice['Volume'].sum())
        
        rets = last_slice['Close'].pct_change().dropna()
        vol = float(rets.std() * np.sqrt(24)) if not rets.empty else 0.0
        
        roll_max = last_slice['Close'].cummax()
        daily_dd = (last_slice['Close'] - roll_max) / roll_max
        max_dd = float(daily_dd.min())
        
        return {
            'symbol': ticker,
            'period': period_label, # <--- Utilisation du paramètre dynamique
            'open': price_open,
            'close': price_close,
            'high': price_high,
            'low': price_low,
            'volatility': vol,
            'max_drawdown': max_dd,
            'volume': volume
        }
    except Exception as e:
        print(f"Error {ticker}: {e}")
        return None

def run_job(period_label='HOURLY'):
    """
    Lance le job. 
    Par défaut 'HOURLY' (pour le Cron).
    Peut être appelé avec 'INSTANT' pour le bouton manuel.
    """
    print(f"--- Starting Job ({period_label}) ---")
    tickers = get_active_tickers_db()
    count = 0
    for t in tickers:
        data = calculate_metrics(t, period_label=period_label)
        if data:
            log_market_report(data)
            count += 1
    print(f"--- Job Finished. {count} reports. ---")
    return count

if __name__ == "__main__":
    # Si lancé en ligne de commande (Cron), c'est HOURLY par défaut
    run_job()