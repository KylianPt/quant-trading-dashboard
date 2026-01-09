import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
from data.database import DB_NAME, get_active_tickers_db

def reset_and_fill_mock_data():
    """
    Génère des données de test propres :
    - IDs ordonnés chronologiquement.
    - Heures arrondies (HH:00).
    - Un rapport DAILY garanti par jour (sur la dernière bougie).
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. VIDER LA TABLE
    c.execute("DELETE FROM market_reports")
    # On reset la séquence d'auto-incrément pour repartir de l'ID 1
    c.execute("DELETE FROM sqlite_sequence WHERE name='market_reports'")
    conn.commit()
    
    tickers = get_active_tickers_db()
    if not tickers:
        conn.close()
        return 0, "No active tickers."

    # Liste tampon pour tout stocker avant d'insérer (pour le tri)
    # Format: (timestamp_obj, tuple_sql)
    all_entries = []
    
    print("Downloading mock data...")
    
    for t in tickers:
        try:
            # 10 jours de données
            df = yf.download(t, period="10d", interval="60m", progress=False)
            if df.empty: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Identifier la dernière bougie de chaque jour pour le tag DAILY
            # On crée une colonne jour pour grouper
            df['day_str'] = df.index.date
            # On récupère les index des dernières lignes de chaque groupe jour
            last_indices = df.groupby('day_str').apply(lambda x: x.index[-1]).tolist()
            
            for idx, row in df.iterrows():
                # NETTOYAGE HEURE : On force HH:00:00
                clean_ts = idx.replace(minute=0, second=0, microsecond=0)
                ts_str = clean_ts.strftime("%Y-%m-%d %H:%M:%S")
                
                # Simu Volatilité/DD
                sim_vol = np.random.uniform(0.10, 0.40)
                sim_dd = np.random.uniform(-0.10, 0.0)
                
                # Données communes
                params = (
                    ts_str, t, 'HOURLY',
                    float(row['Open']), float(row['Close']), float(row['High']), float(row['Low']),
                    sim_vol, sim_dd, int(row['Volume'])
                )
                
                # 1. Ajout de l'entrée HORAIRE
                all_entries.append((clean_ts, params))
                
                # 2. Ajout de l'entrée DAILY (si c'est la dernière bougie du jour)
                if idx in last_indices:
                    # On crée une entrée identique mais taggée DAILY
                    daily_params = list(params)
                    daily_params[2] = 'DAILY' # Change 'HOURLY' to 'DAILY'
                    all_entries.append((clean_ts, tuple(daily_params)))

        except Exception as e:
            print(f"Error generating {t}: {e}")

    # TRI CHRONOLOGIQUE GLOBAL
    # On trie la liste par la clé 0 (l'objet datetime)
    # Ainsi, l'ID 1 sera la date la plus ancienne, tous tickers confondus.
    all_entries.sort(key=lambda x: x[0])
    
    print(f"Inserting {len(all_entries)} sorted records...")
    
    # INSERTION EN MASSE
    # On ne garde que la partie SQL (params)
    sql_data = [x[1] for x in all_entries]
    
    c.executemany('''
        INSERT INTO market_reports 
        (timestamp, symbol, period, price_open, price_close, price_high, price_low, volatility, max_drawdown, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sql_data)
    
    conn.commit()
    conn.close()
    
    return len(all_entries), f"Generated {len(all_entries)} sorted reports."