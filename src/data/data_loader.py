import os
import pandas as pd
import yfinance as yf

def load_asset_universe():
    """
    Charge les données CSV (CAC40, S&P500, Crypto, Currencies).
    Retourne un DataFrame combiné.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Définition des fichiers et de leur "Index" associé
    files_to_load = [
        ("CAC40.csv", "CAC 40"),
        ("S&P500.csv", "S&P 500"),
        ("crypto.csv", "Crypto"),      # <--- AJOUTÉ
        ("currencies.csv", "Forex")    # <--- AJOUTÉ
    ]
    
    dfs = []
    
    for filename, idx_name in files_to_load:
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                if not df.empty:
                    df['Index'] = idx_name
                    dfs.append(df)
            except pd.errors.EmptyDataError:
                pass
    
    if not dfs:
        # Fallback de secours si tout est vide
        return pd.DataFrame({
            "Symbol": ["^FCHI", "BTC-USD"], 
            "Name": ["CAC 40", "Bitcoin"], 
            "Sector": ["Index", "Cryptocurrency"], 
            "Index": ["CAC 40", "Crypto"]
        })
        
    return pd.concat(dfs, ignore_index=True)

def get_live_prices_batch(tickers):
    """Récupère les prix en batch pour le bandeau."""
    if not tickers: return {}
    try:
        # On télécharge tout d'un coup
        data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)
        prices = {}
        
        if len(tickers) == 1:
            t = tickers[0]
            if not data.empty: 
                # Gestion robuste des colonnes (parfois 'Close', parfois 'Adj Close')
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
                    # Yahoo renvoie parfois un MultiIndex complexe
                    if (t, 'Close') in data.columns:
                        val = data[t]['Close'].dropna().iloc[-1]
                    elif t in data.columns:
                        # Si aplati
                        sub = data[t]
                        if 'Close' in sub:
                            val = sub['Close'].dropna().iloc[-1]
                    
                    prices[t] = val
                except: 
                    prices[t] = 0.0
        return prices
    except: 
        return {t: 0.0 for t in tickers}