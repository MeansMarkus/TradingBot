#!/usr/bin/env python3
"""
Trading Bot Runner Script
This script runs the trading bot with proper configuration and error handling.
"""

import sys
import os
from trading_bot import TradingBot
from config import *
from dotenv import load_dotenv
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

load_dotenv()
client = StockHistoricalDataClient(
    api_key=os.getenv('ALPACA_API_KEY'),
    secret_key=os.getenv('ALPACA_SECRET_KEY')
)

request_params = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame.Minute,
    start=datetime(2023, 7, 1),
    end=datetime(2023, 7, 2)
)

bars = client.get_stock_bars(request_params)
print(bars.df)

def main():
    """Main function to run the trading bot"""
    
    # Check if API keys are available
    if not API_KEY or not SECRET_KEY:
        print("❌ Error: API keys not found!")
        print("Please create a .env file with your Alpaca API credentials:")
        print("ALPACA_API_KEY=your_api_key_here")
        print("ALPACA_SECRET_KEY=your_secret_key_here")
        sys.exit(1)
    
    try:
        # Initialize the trading bot
        print("🚀 Initializing Trading Bot...")
        bot = TradingBot(API_KEY, SECRET_KEY, paper=PAPER_TRADING)
        
        # Test market data connection
        print("\n📊 Testing market data connection...")
        test_data = bot.get_market_data('SPY', limit=5)
        if test_data is not None and len(test_data) > 0:
            print(f"✅ Connection successful! Latest SPY price: ${test_data['close'].iloc[-1]:.2f}")
        else:
            print("❌ Failed to get market data")
            sys.exit(1)
        
        # Run the trading strategy
        print(f"\n🤖 Starting trading bot...")
        print(f"Mode: {'Paper Trading' if PAPER_TRADING else 'Live Trading'}")
        print(f"Symbols: {SYMBOLS}")
        print(f"Check interval: {CHECK_INTERVAL} seconds")
        
        bot.run_strategy(SYMBOLS, CHECK_INTERVAL)
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 