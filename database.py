# database.py
import sqlite3
from config import DB_FILE

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_positions (
            symbol TEXT PRIMARY KEY,
            is_holding INTEGER DEFAULT 0,
            average_price REAL DEFAULT 0.0,
            total_crypto REAL DEFAULT 0.0,
            total_spent REAL DEFAULT 0.0,
            margin_calls INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def load_position(symbol):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_holding, average_price, total_crypto, total_spent, margin_calls FROM active_positions WHERE symbol=?", (symbol,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'is_holding': bool(row[0]), 'average_price': row[1], 'total_crypto': row[2], 'total_spent': row[3], 'margin_calls': row[4]}
    return {'is_holding': False, 'average_price': 0.0, 'total_crypto': 0.0, 'total_spent': 0.0, 'margin_calls': 0}

def save_position(symbol, is_holding, avg_price, total_crypto, total_spent, margin_calls):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO active_positions (symbol, is_holding, average_price, total_crypto, total_spent, margin_calls)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET
            is_holding=excluded.is_holding,
            average_price=excluded.average_price,
            total_crypto=excluded.total_crypto,
            total_spent=excluded.total_spent,
            margin_calls=excluded.margin_calls
    ''', (symbol, int(is_holding), avg_price, total_crypto, total_spent, margin_calls))
    conn.commit()
    conn.close()
    
 
 # database.py ফাইলের একদম নিচে আগের কোডটি বদলে এটি পেস্ট করুন:

def update_bot_status(symbol, is_active):
    """Update bot status from mobile app"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE active_positions 
        SET is_holding = ? 
        WHERE symbol = ?
    ''', (int(is_active), symbol))
    conn.commit()
    conn.close()