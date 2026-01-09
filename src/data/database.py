import sqlite3
import pandas as pd
from datetime import datetime
import os

# Gestion du chemin pour Fly.io ou Local
if os.path.exists("/data"):
    DB_NAME = "/data/portfolios.db"
else:
    DB_NAME = "portfolios.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table Portefeuilles
    c.execute('''
        CREATE TABLE IF NOT EXISTS shared_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_name TEXT,
            comment TEXT,
            tickers TEXT,
            years INTEGER,
            strategy_rebal TEXT,
            strategy_stoploss REAL,
            total_return REAL,
            volatility REAL,
            sharpe REAL
        )
    ''')
    
    # Table Tickers Actifs
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_tickers (
            symbol TEXT PRIMARY KEY
        )
    ''')

    # Table Rapports
    c.execute('''
        CREATE TABLE IF NOT EXISTS market_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            period TEXT,
            price_open REAL,
            price_close REAL,
            price_high REAL,
            price_low REAL,
            volatility REAL,
            max_drawdown REAL,
            volume REAL
        )
    ''')
    conn.commit()
    conn.close()

# --- ACTIVE TICKERS ---
def get_active_tickers_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        rows = conn.execute("SELECT symbol FROM active_tickers").fetchall()
        return [row[0] for row in rows]
    except: return []
    finally: conn.close()

def add_active_ticker_db(symbol):
    current = get_active_tickers_db()
    if len(current) >= 10: return False, "Max 10 tickers allowed."
    if symbol in current: return False, "Ticker already exists."
    
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("INSERT INTO active_tickers (symbol) VALUES (?)", (symbol,))
        conn.commit()
        return True, "Added."
    except Exception as e: return False, str(e)
    finally: conn.close()

def remove_active_ticker_db(symbol):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM active_tickers WHERE symbol = ?", (symbol,))
    conn.commit()
    conn.close()

# --- MARKET REPORTS ---
def log_market_report(data_dict):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO market_reports 
        (timestamp, symbol, period, price_open, price_close, price_high, price_low, volatility, max_drawdown, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data_dict['symbol'],
        data_dict['period'],
        data_dict['open'],
        data_dict['close'],
        data_dict['high'],
        data_dict['low'],
        data_dict['volatility'],
        data_dict['max_drawdown'],
        data_dict['volume']
    ))
    conn.commit()
    conn.close()

def get_market_reports_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql_query("SELECT * FROM market_reports ORDER BY id DESC", conn)
    except: return pd.DataFrame()
    finally: conn.close()

# --- SHARED PORTFOLIOS ---
def save_portfolio_db(user_name, comment, tickers_str, years, rebal, stoploss, stats):
    """
    tickers_str: Chaîne déjà formatée (ex: "AAPL (50%), MSFT (50%)")
    """
    conn = sqlite3.connect(DB_NAME)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute('''
        INSERT INTO shared_portfolios 
        (timestamp, user_name, comment, tickers, years, strategy_rebal, strategy_stoploss, total_return, volatility, sharpe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        now, user_name, comment, tickers_str, years, rebal, stoploss, 
        stats.get('Total Return', 0), stats.get('Volatility', 0), stats.get('Sharpe', 0)
    ))
    conn.commit()
    conn.close()

def get_latest_portfolios(limit=10):
    conn = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql_query(f"SELECT * FROM shared_portfolios ORDER BY id DESC LIMIT {limit}", conn)
    except: return pd.DataFrame()
    finally: conn.close()

def delete_portfolio_db(item_id):
    """Supprime un portfolio par son ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM shared_portfolios WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()