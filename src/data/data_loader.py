import os
import pandas as pd
import yfinance as yf

def load_asset_universe():
    """
    Loads CSV data (CAC40, S&P500, Crypto, Currencies) from the 'assets' directory.
    Returns a combined DataFrame.
    """
    # 1. Get current directory (src/data)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up two levels to find project root (src/data -> src -> root)
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    
    # 3. Target the 'assets' directory
    assets_dir = os.path.join(root_dir, 'assets')
    
    # Define files and their associated "Index"
    files_to_load = [
        ("CAC40.csv", "CAC 40"),
        ("S&P500.csv", "S&P 500"),
        ("crypto.csv", "Crypto"),
        ("currencies.csv", "Forex")
    ]
    
    dfs = []
    
    for filename, idx_name in files_to_load:
        path = os.path.join(assets_dir, filename) # Use assets_dir here
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                if not df.empty:
                    df['Index'] = idx_name
                    dfs.append(df)
            except pd.errors.EmptyDataError:
                pass
    
    if not dfs:
        # Fallback if everything is empty
        return pd.DataFrame({
            "Symbol": ["^FCHI", "BTC-USD"], 
            "Name": ["CAC 40", "Bitcoin"], 
            "Sector": ["Index", "Cryptocurrency"], 
            "Index": ["CAC 40", "Crypto"]
        })
        
    return pd.concat(dfs, ignore_index=True)

def get_live_prices_batch(tickers):
    """Fetches batch prices for the ticker tape."""
    if not tickers: return {}
    try:
        # Download everything at once
        data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)
        prices = {}
        
        if len(tickers) == 1:
            t = tickers[0]
            if not data.empty: 
                # Robust column handling (sometimes 'Close', sometimes 'Adj Close')
                if 'Close' in data.columns:
                    prices[t] = data['Close'].iloc[-1]
                elif 'Price' in data.columns:
                    prices[t] = data['Price'].iloc[-1]
                else:
                    prices[t] = 0.0
        else:
            for t in tickers:
                try:
                    val = 0.0
                    # Yahoo sometimes returns a complex MultiIndex
                    if (t, 'Close') in data.columns:
                        val = data[t]['Close'].dropna().iloc[-1]
                    elif t in data.columns:
                        # If flattened
                        sub = data[t]
                        if 'Close' in sub:
                            val = sub['Close'].dropna().iloc[-1]
                    
                    prices[t] = val
                except: 
                    prices[t] = 0.0
        return prices
    except: 
        return {t: 0.0 for t in tickers}