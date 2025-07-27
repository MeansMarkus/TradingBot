import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

class TradingBot:
    def __init__(self, api_key, secret_key, paper=True):
        """Initialize the trading bot with Alpaca API"""
        base_url = 'https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets'
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        
        # Verify connection
        try:
            account = self.api.get_account()
            print(f"Connected! Account status: {account.status}")
            print(f"Buying power: ${float(account.buying_power):,.2f}")
        except Exception as e:
            print(f"Connection failed: {e}")
    
    def get_market_data(self, symbol, timeframe='1Day', limit=100):
        """Get historical market data for a symbol"""
        try:
            bars = self.api.get_bars(symbol, timeframe, limit=limit).df
            return bars
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def is_market_open(self):
        """Check if market is currently open"""
        clock = self.api.get_clock()
        return clock.is_open
    
    def get_position(self, symbol):
        """Get current position for a symbol"""
        try:
            position = self.api.get_position(symbol)
            return float(position.qty)
        except:
            return 0  # No position
    
    def place_order(self, symbol, qty, side, order_type='market'):
        """Place an order"""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=abs(qty),
                side=side,
                type=order_type,
                time_in_force='day'
            )
            print(f"Order placed: {side} {qty} shares of {symbol}")
            return order
        except Exception as e:
            print(f"Order failed: {e}")
            return None
    
    def simple_momentum_strategy(self, symbol, short_window=10, long_window=30):
        """
        Simple momentum strategy using moving averages
        Buy when short MA crosses above long MA
        Sell when short MA crosses below long MA
        """
        # Get historical data
        data = self.get_market_data(symbol, limit=long_window + 10)
        if data is None or len(data) < long_window:
            print(f"Not enough data for {symbol}")
            return
        
        # Calculate moving averages
        data[f'MA_{short_window}'] = data['close'].rolling(window=short_window).mean()
        data[f'MA_{long_window}'] = data['close'].rolling(window=long_window).mean()
        
        # Get current and previous values
        current_short_ma = data[f'MA_{short_window}'].iloc[-1]
        current_long_ma = data[f'MA_{long_window}'].iloc[-1]
        prev_short_ma = data[f'MA_{short_window}'].iloc[-2]
        prev_long_ma = data[f'MA_{long_window}'].iloc[-2]
        
        current_price = data['close'].iloc[-1]
        current_position = self.get_position(symbol)
        
        print(f"\n{symbol} Analysis:")
        print(f"Price: ${current_price:.2f}")
        print(f"Short MA ({short_window}): ${current_short_ma:.2f}")
        print(f"Long MA ({long_window}): ${current_long_ma:.2f}")
        print(f"Current position: {current_position} shares")
        
        # Trading logic
        if (prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma and current_position == 0):
            # Golden cross - buy signal
            account = self.api.get_account()
            buying_power = float(account.buying_power)
            shares_to_buy = int(buying_power * 0.1 / current_price)  # Use 10% of buying power
            
            if shares_to_buy > 0:
                print(f"📈 BUY SIGNAL: Golden cross detected!")
                self.place_order(symbol, shares_to_buy, 'buy')
        
        elif (prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma and current_position > 0):
            # Death cross - sell signal
            print(f"📉 SELL SIGNAL: Death cross detected!")
            self.place_order(symbol, current_position, 'sell')
        
        else:
            print("No trading signal")
    
    def run_strategy(self, symbols=['SPY'], check_interval=300):
        """
        Run the trading strategy continuously
        check_interval: seconds between checks (300 = 5 minutes)
        """
        print("🤖 Trading bot started!")
        print(f"Monitoring: {symbols}")
        print(f"Check interval: {check_interval} seconds\n")
        
        while True:
            try:
                if self.is_market_open():
                    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Market is open")
                    
                    for symbol in symbols:
                        self.simple_momentum_strategy(symbol)
                        time.sleep(2)  # Small delay between symbols
                    
                else:
                    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Market is closed")
                
                print(f"💤 Sleeping for {check_interval} seconds...\n")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying