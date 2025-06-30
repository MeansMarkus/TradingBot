import sqlite3
import pandas as pd
from datetime import datetime
import logging
from config import Config

class Database:
    def __init__(self, db_path=Config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Price history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL,
                UNIQUE(symbol, timestamp)
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                order_id TEXT,
                status TEXT DEFAULT 'open'
            )
        ''')
        
        # Account balance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                balance REAL NOT NULL,
                equity REAL NOT NULL,
                margin_used REAL NOT NULL,
                free_margin REAL NOT NULL
            )
        ''')
        
        # Daily P&L table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                pnl REAL NOT NULL,
                trades_count INTEGER DEFAULT 0,
                UNIQUE(date)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
    
    def save_price_data(self, symbol, timestamp, open_price, high, low, close, volume=0):
        """Save price data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO price_history 
                (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, timestamp, open_price, high, low, close, volume))
            conn.commit()
        except Exception as e:
            logging.error(f"Error saving price data: {e}")
        finally:
            conn.close()
    
    def get_price_history(self, symbol, limit=1000):
        """Get price history for a symbol"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT timestamp, open, high, low, close, volume
            FROM price_history 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(symbol, limit))
        conn.close()
        return df
    
    def save_trade(self, symbol, side, quantity, price, order_id=None):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO trades (symbol, side, quantity, price, timestamp, order_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, side, quantity, price, datetime.now(), order_id))
            conn.commit()
            logging.info(f"Trade saved: {side} {quantity} {symbol} @ {price}")
        except Exception as e:
            logging.error(f"Error saving trade: {e}")
        finally:
            conn.close()
    
    def save_account_balance(self, balance, equity, margin_used, free_margin):
        """Save account balance snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO account_balance (timestamp, balance, equity, margin_used, free_margin)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), balance, equity, margin_used, free_margin))
            conn.commit()
        except Exception as e:
            logging.error(f"Error saving account balance: {e}")
        finally:
            conn.close()
    
    def save_daily_pnl(self, date, pnl, trades_count=0):
        """Save daily P&L"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_pnl (date, pnl, trades_count)
                VALUES (?, ?, ?)
            ''', (date, pnl, trades_count))
            conn.commit()
        except Exception as e:
            logging.error(f"Error saving daily P&L: {e}")
        finally:
            conn.close()
    
    def get_daily_pnl(self, date):
        """Get daily P&L for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT pnl FROM daily_pnl WHERE date = ?', (date,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def get_today_pnl(self):
        """Get today's P&L"""
        today = datetime.now().date()
        return self.get_daily_pnl(today)
    
    def get_account_balance(self):
        """Get latest account balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT balance, equity, margin_used, free_margin 
            FROM account_balance 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'balance': result[0],
                'equity': result[1],
                'margin_used': result[2],
                'free_margin': result[3]
            }
        else:
            # Return default values for paper trading
            return {
                'balance': 10000,  # $10,000 paper balance
                'equity': 10000,
                'margin_used': 0,
                'free_margin': 10000
            } 