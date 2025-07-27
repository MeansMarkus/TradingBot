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
    
    def enhanced_strategy(self, symbol, short_window=10, long_window=30):
        """
        Enhanced strategy with multiple technical indicators
        - Moving Average Crossover
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - Volume confirmation
        - Trend strength
        """
        # Get historical data
        data = self.get_market_data(symbol, limit=long_window + 50)
        if data is None or len(data) < long_window:
            print(f"Not enough data for {symbol}")
            return
        
        # Calculate moving averages
        data[f'MA_{short_window}'] = data['close'].rolling(window=short_window).mean()
        data[f'MA_{long_window}'] = data['close'].rolling(window=long_window).mean()
        
        # Calculate RSI (14-period)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        data['EMA_12'] = data['close'].ewm(span=12).mean()
        data['EMA_26'] = data['close'].ewm(span=26).mean()
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
        
        # Calculate volume moving average
        data['Volume_MA'] = data['volume'].rolling(window=20).mean()
        data['Volume_Ratio'] = data['volume'] / data['Volume_MA']
        
        # Calculate trend strength (ADX-like)
        data['Price_Change'] = data['close'].pct_change()
        data['Trend_Strength'] = data['Price_Change'].rolling(window=14).std()
        
        # Get current values
        current_price = data['close'].iloc[-1]
        current_position = self.get_position(symbol)
        
        # Current indicator values
        current_short_ma = data[f'MA_{short_window}'].iloc[-1]
        current_long_ma = data[f'MA_{long_window}'].iloc[-1]
        prev_short_ma = data[f'MA_{short_window}'].iloc[-2]
        prev_long_ma = data[f'MA_{long_window}'].iloc[-2]
        
        current_rsi = data['RSI'].iloc[-1]
        current_macd = data['MACD'].iloc[-1]
        current_macd_signal = data['MACD_Signal'].iloc[-1]
        current_volume_ratio = data['Volume_Ratio'].iloc[-1]
        current_trend_strength = data['Trend_Strength'].iloc[-1]
        
        print(f"\n{symbol} Enhanced Analysis:")
        print(f"Price: ${current_price:.2f}")
        print(f"Short MA ({short_window}): ${current_short_ma:.2f}")
        print(f"Long MA ({long_window}): ${current_long_ma:.2f}")
        print(f"RSI: {current_rsi:.1f}")
        print(f"MACD: {current_macd:.3f} | Signal: {current_macd_signal:.3f}")
        print(f"Volume Ratio: {current_volume_ratio:.2f}")
        print(f"Trend Strength: {current_trend_strength:.4f}")
        print(f"Current position: {current_position} shares")
        
        # Enhanced trading logic
        buy_signals = 0
        sell_signals = 0
        
        # 1. Moving Average Crossover
        if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma:
            buy_signals += 1
        elif prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma:
            sell_signals += 1
        
        # 2. RSI conditions
        if current_rsi < 30:  # Oversold
            buy_signals += 1
        elif current_rsi > 70:  # Overbought
            sell_signals += 1
        
        # 3. MACD conditions
        if current_macd > current_macd_signal and data['MACD'].iloc[-2] <= data['MACD_Signal'].iloc[-2]:
            buy_signals += 1
        elif current_macd < current_macd_signal and data['MACD'].iloc[-2] >= data['MACD_Signal'].iloc[-2]:
            sell_signals += 1
        
        # 4. Volume confirmation
        if current_volume_ratio > 1.5:  # High volume
            if buy_signals > sell_signals:
                buy_signals += 1
            elif sell_signals > buy_signals:
                sell_signals += 1
        
        # 5. Trend strength filter
        if current_trend_strength < 0.02:  # Low volatility - avoid trading
            print("⚠️ Low volatility - skipping trade")
            return
        
        # Decision making
        if buy_signals >= 2 and current_position == 0:
            # Strong buy signal
            account = self.api.get_account()
            buying_power = float(account.buying_power)
            shares_to_buy = int(buying_power * 0.1 / current_price)
            
            if shares_to_buy > 0:
                print(f"📈 STRONG BUY SIGNAL ({buy_signals} indicators)!")
                self.place_order(symbol, shares_to_buy, 'buy')
        
        elif sell_signals >= 2 and current_position > 0:
            # Strong sell signal
            print(f"📉 STRONG SELL SIGNAL ({sell_signals} indicators)!")
            self.place_order(symbol, current_position, 'sell')
        
        else:
            print(f"No strong signal (Buy: {buy_signals}, Sell: {sell_signals})")
    
    def backtest_strategy(self, symbol, start_date=None, end_date=None):
        """
        Backtest the strategy to see historical performance
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"🔍 Backtesting {symbol} from {start_date} to {end_date}")
        
        try:
            # Get historical data
            bars = self.api.get_bars(symbol, '1Day', start=start_date, end=end_date).df
            if len(bars) < 50:
                print("Not enough data for backtesting")
                return
            
            # Initialize backtest variables
            position = 0
            cash = 10000  # Starting cash
            trades = []
            equity_curve = []
            
            # Calculate indicators
            bars['MA_10'] = bars['close'].rolling(window=10).mean()
            bars['MA_30'] = bars['close'].rolling(window=30).mean()
            
            # RSI
            delta = bars['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            bars['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            bars['EMA_12'] = bars['close'].ewm(span=12).mean()
            bars['EMA_26'] = bars['close'].ewm(span=26).mean()
            bars['MACD'] = bars['EMA_12'] - bars['EMA_26']
            bars['MACD_Signal'] = bars['MACD'].ewm(span=9).mean()
            
            # Volume
            bars['Volume_MA'] = bars['volume'].rolling(window=20).mean()
            bars['Volume_Ratio'] = bars['volume'] / bars['Volume_MA']
            
            # Simulate trading
            for i in range(30, len(bars)):
                current_price = bars['close'].iloc[i]
                current_date = bars.index[i]
                
                # Calculate signals
                buy_signals = 0
                sell_signals = 0
                
                # MA Crossover
                if (bars['MA_10'].iloc[i-1] <= bars['MA_30'].iloc[i-1] and 
                    bars['MA_10'].iloc[i] > bars['MA_30'].iloc[i]):
                    buy_signals += 1
                elif (bars['MA_10'].iloc[i-1] >= bars['MA_30'].iloc[i-1] and 
                      bars['MA_10'].iloc[i] < bars['MA_30'].iloc[i]):
                    sell_signals += 1
                
                # RSI
                if bars['RSI'].iloc[i] < 30:
                    buy_signals += 1
                elif bars['RSI'].iloc[i] > 70:
                    sell_signals += 1
                
                # MACD
                if (bars['MACD'].iloc[i] > bars['MACD_Signal'].iloc[i] and 
                    bars['MACD'].iloc[i-1] <= bars['MACD_Signal'].iloc[i-1]):
                    buy_signals += 1
                elif (bars['MACD'].iloc[i] < bars['MACD_Signal'].iloc[i] and 
                      bars['MACD'].iloc[i-1] >= bars['MACD_Signal'].iloc[i-1]):
                    sell_signals += 1
                
                # Volume confirmation
                if bars['Volume_Ratio'].iloc[i] > 1.5:
                    if buy_signals > sell_signals:
                        buy_signals += 1
                    elif sell_signals > buy_signals:
                        sell_signals += 1
                
                # Execute trades
                if buy_signals >= 2 and position == 0:
                    shares = int(cash * 0.1 / current_price)
                    if shares > 0:
                        position = shares
                        cash -= shares * current_price
                        trades.append({
                            'date': current_date,
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'signals': buy_signals
                        })
                
                elif sell_signals >= 2 and position > 0:
                    cash += position * current_price
                    trades.append({
                        'date': current_date,
                        'action': 'SELL',
                        'price': current_price,
                        'shares': position,
                        'signals': sell_signals
                    })
                    position = 0
                
                # Track equity
                current_equity = cash + (position * current_price)
                equity_curve.append(current_equity)
            
            # Calculate final position value
            final_price = bars['close'].iloc[-1]
            final_equity = cash + (position * final_price)
            
            # Results
            total_return = ((final_equity - 10000) / 10000) * 100
            buy_hold_return = ((final_price - bars['close'].iloc[30]) / bars['close'].iloc[30]) * 100
            
            print(f"\n📊 Backtest Results:")
            print(f"Starting Capital: $10,000")
            print(f"Final Equity: ${final_equity:,.2f}")
            print(f"Total Return: {total_return:.2f}%")
            print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
            print(f"Number of Trades: {len(trades)}")
            
            if len(trades) > 0:
                winning_trades = [t for t in trades if t['action'] == 'SELL']
                win_rate = len(winning_trades) / len([t for t in trades if t['action'] == 'BUY']) * 100
                print(f"Win Rate: {win_rate:.1f}%")
            
            return {
                'total_return': total_return,
                'trades': trades,
                'equity_curve': equity_curve
            }
            
        except Exception as e:
            print(f"Backtest error: {e}")
            return None

    def risk_management(self, symbol, position_size_pct=0.1, stop_loss_pct=0.05, take_profit_pct=0.15):
        """
        Enhanced risk management with stop-loss and take-profit
        """
        current_position = self.get_position(symbol)
        if current_position == 0:
            return
        
        # Get current price
        data = self.get_market_data(symbol, limit=1)
        if data is None:
            return
        
        current_price = data['close'].iloc[-1]
        
        # Get average entry price (simplified - in real implementation you'd track this)
        # For now, we'll use a simple approach
        account = self.api.get_account()
        portfolio_value = float(account.portfolio_value)
        position_value = current_position * current_price
        estimated_entry_price = position_value / current_position  # Simplified
        
        # Calculate stop-loss and take-profit levels
        stop_loss_price = estimated_entry_price * (1 - stop_loss_pct)
        take_profit_price = estimated_entry_price * (1 + take_profit_pct)
        
        # Check if stop-loss or take-profit triggered
        if current_price <= stop_loss_price:
            print(f"🛑 STOP-LOSS triggered at ${current_price:.2f}")
            self.place_order(symbol, current_position, 'sell')
        elif current_price >= take_profit_price:
            print(f"🎯 TAKE-PROFIT triggered at ${current_price:.2f}")
            self.place_order(symbol, current_position, 'sell')
    
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
                        # Use enhanced strategy for better accuracy
                        self.enhanced_strategy(symbol)
                        # Apply risk management
                        self.risk_management(symbol)
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