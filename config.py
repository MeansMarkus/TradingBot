# Configuration file for Trading Bot
# IMPORTANT: Never commit this file to version control with real API keys!

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Trading Configuration
PAPER_TRADING = True  # Set to False for live trading
SYMBOLS = ['SPY', 'QQQ']  # Symbols to trade
CHECK_INTERVAL = 300  # Seconds between strategy checks (5 minutes)

# Strategy Configuration
SHORT_WINDOW = 10  # Short moving average period
LONG_WINDOW = 30   # Long moving average period
POSITION_SIZE_PCT = 0.1  # Use 10% of buying power per trade 