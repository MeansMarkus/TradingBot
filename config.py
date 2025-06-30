import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Exchange Configuration
    EXCHANGE = 'binance'  # or 'bybit', 'okx' for futures
    API_KEY = os.getenv('API_KEY', '')
    SECRET_KEY = os.getenv('SECRET_KEY', '')
    PASSPHRASE = os.getenv('PASSPHRASE', '')  # For some exchanges like OKX
    
    # Trading Configuration
    SYMBOL = 'BTC/USDT:USDT'  # Bitcoin perpetual futures on Binance
    TIMEFRAME = '1m'  # 1 minute candles
    PAPER_TRADING = True  # Start with paper trading
    
    # Risk Management
    MAX_POSITION_SIZE = 0.01  # Number of contracts (0.01 BTC for paper trading)
    MAX_DAILY_LOSS = 100  # Maximum daily loss in USD
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