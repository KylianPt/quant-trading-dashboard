import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from data.database import log_market_report, get_active_tickers_db

def generate_daily_report():
    """
    Fetches the latest daily session for all active tickers.
    Extracts Open, High, Low, Close directly from Yahoo Finance.
    Calculates intraday volatility and drawdown based on the daily range.
    """
    tickers = get_active_tickers_db()
    if not tickers:
        print("No active tickers found for report.")
        return

    for t in tickers:
        try:
            # Fetch only the last trading day
            df = yf.download(t, period="1d", progress=False)
            
            if df.empty:
                print(f"No data found for {t}")
                continue

            # Handle MultiIndex columns if present (common in new yfinance versions)
            # We want to access the scalar values of the first (and only) row
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten or access directly
                row = df.iloc[-1]
                # Assuming level 0 is Price Type, level 1 is Ticker
                # We try to extract values regardless of structure
                try:
                    open_p = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
                    high_p = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
                    low_p = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
                    close_p = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])
                    volume = float(row['Volume'].iloc[0]) if isinstance(row['Volume'], pd.Series) else float(row['Volume'])
                except:
                    # Fallback for simple index
                    open_p = float(row['Open'])
                    high_p = float(row['High'])
                    low_p = float(row['Low'])
                    close_p = float(row['Close'])
                    volume = float(row['Volume'])
            else:
                # Standard DataFrame
                row = df.iloc[-1]
                open_p = float(row['Open'])
                high_p = float(row['High'])
                low_p = float(row['Low'])
                close_p = float(row['Close'])
                volume = float(row['Volume'])

            # Simple Intraday Metrics
            # Volatility: (High - Low) / Open (Daily Range %)
            volatility = (high_p - low_p) / open_p if open_p > 0 else 0.0
            
            # Max Drawdown: (Low - High) / High (Worst drop from daily peak)
            max_drawdown = (low_p - high_p) / high_p if high_p > 0 else 0.0

            # Prepare data dict
            report_data = {
                'symbol': t,
                'period': 'Daily (1d)',
                'open': open_p,
                'close': close_p,
                'high': high_p,
                'low': low_p,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'volume': volume
            }

            # Save to DB
            log_market_report(report_data)
            print(f"Report generated for {t}: Open={open_p}, Close={close_p}")

        except Exception as e:
            print(f"Error generating report for {t}: {e}")

if __name__ == "__main__":
    generate_daily_report()