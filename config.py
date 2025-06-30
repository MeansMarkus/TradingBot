import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Exchange Configuration - Alpaca (Best for US citizens)
    EXCHANGE = 'alpaca'  # Alpaca Markets - excellent for US traders
    API_KEY = os.getenv('ALPACA_API_KEY', '')
    SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
    BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')  # Paper trading URL
    
    # Trading Configuration
    SYMBOL = 'SPY'  # S&P 500 ETF (most liquid)
    TIMEFRAME = '1m'  # 1 minute candles
    PAPER_TRADING = True  # Start with paper trading
    
    # Risk Management
    MAX_POSITION_SIZE = 100  # Number of shares
    MAX_DAILY_LOSS = 500  # Maximum daily loss in USD
    STOP_LOSS_PERCENT = 2.0  # Stop loss percentage
    TAKE_PROFIT_PERCENT = 4.0  # Take profit percentage
    
    # Database Configuration
    DATABASE_PATH = 'trading_bot.db'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'trading_bot.log'
    
    # Market Data
    WEBSOCKET_ENABLED = True
    DATA_UPDATE_INTERVAL = 1  # seconds
    
    # Alpaca Specific Settings
    ALPACA_PAPER = True  # Use paper trading account
    ALPACA_LIVE_URL = 'https://api.alpaca.markets'  # Live trading URL 