import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
from data.database import DB_NAME, get_active_tickers_db

def reset_and_fill_mock_data():
    """
    Generates clean mock data:
    - IDs ordered chronologically.
    - Times rounded to the hour (HH:00).
    - Aggregated DAILY report (Sum of volume, true Day High/Low).
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. CLEAR TABLE
    c.execute("DELETE FROM market_reports")
    c.execute("DELETE FROM sqlite_sequence WHERE name='market_reports'")
    conn.commit()
    
    tickers = get_active_tickers_db()
    if not tickers:
        tickers = ["AAPL", "BTC-USD", "EURUSD=X", "GC=F"]
        for t in tickers:
             c.execute("INSERT OR IGNORE INTO active_tickers (symbol) VALUES (?)", (t,))
        conn.commit()

    all_entries = []
    
    print("Downloading mock data (10 days)...")
    
    for t in tickers:
        try:
            # Fetch 10 days of hourly data
            df = yf.download(t, period="10d", interval="60m", progress=False)
            if df.empty: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Helper column for grouping by day
            df['day_str'] = df.index.date
            
            # Get indices of the last rows for each day group
            last_indices = df.groupby('day_str').apply(lambda x: x.index[-1]).tolist()
            
            for idx, row in df.iterrows():
                clean_ts = idx.replace(minute=0, second=0, microsecond=0)
                ts_str = clean_ts.strftime("%Y-%m-%d %H:%M:%S")
                
                # --- HOURLY ENTRY ---
                # Simulated Metrics for the hour
                h_open = float(row['Open'])
                h_close = float(row['Close'])
                h_high = float(row['High'])
                h_low = float(row['Low'])
                h_vol = int(row['Volume'])
                
                # Hourly volatility is small (noise)
                h_volatility = (h_high - h_low) / h_open if h_open > 0 else 0.0
                h_dd = (h_low - h_high) / h_high if h_high > 0 else 0.0

                params_hourly = (
                    ts_str, t, 'HOURLY',
                    h_open, h_close, h_high, h_low,
                    h_volatility, h_dd, h_vol
                )
                all_entries.append((clean_ts, params_hourly))
                
                # --- DAILY ENTRY (Aggregation) ---
                if idx in last_indices:
                    # Filter data for the entire day
                    day_df = df[df['day_str'] == row['day_str']]
                    
                    # 1. Open = Open of the FIRST candle of the day
                    d_open = float(day_df['Open'].iloc[0])
                    
                    # 2. Close = Close of the LAST candle (current row)
                    d_close = float(row['Close'])
                    
                    # 3. High/Low = Extremes of the day
                    d_high = float(day_df['High'].max())
                    d_low = float(day_df['Low'].min())
                    
                    # 4. Volume = Sum of the day
                    d_volume = int(day_df['Volume'].sum())
                    
                    # 5. Volatility & Drawdown calculated on the full day range
                    d_volatility = (d_high - d_low) / d_open if d_open > 0 else 0.0
                    d_dd = (d_low - d_high) / d_high if d_high > 0 else 0.0
                    
                    params_daily = (
                        ts_str, t, 'DAILY',
                        d_open, d_close, d_high, d_low,
                        d_volatility, d_dd, d_volume
                    )
                    all_entries.append((clean_ts, params_daily))

        except Exception as e:
            print(f"Error generating {t}: {e}")

    # GLOBAL SORT
    all_entries.sort(key=lambda x: x[0])
    
    print(f"Inserting {len(all_entries)} sorted records...")
    
    sql_data = [x[1] for x in all_entries]
    
    c.executemany('''
        INSERT INTO market_reports 
        (timestamp, symbol, period, price_open, price_close, price_high, price_low, volatility, max_drawdown, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sql_data)
    
    conn.commit()
    conn.close()
    
    return len(all_entries), f"Generated {len(all_entries)} reports (Hourly & Daily aggregated)."

if __name__ == "__main__":
    reset_and_fill_mock_data()