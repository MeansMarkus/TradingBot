#!/usr/bin/env python3
"""
Offline Trading Bot - No APIs Required
Uses historical data and simulation for backtesting and paper trading
"""
import pandas as pd
import numpy as np
import yfinance as yf
import sqlite3
import logging
from datetime import datetime, timedelta
import time
import schedule
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('offline_trading_bot.log'),
        logging.StreamHandler()
    ]
)

class OfflineMarketData:
    """Offline market data using historical data and simulation"""
    
    def __init__(self, symbol: str = "ES=F"):
        self.symbol = symbol
        self.current_price = None
        self.price_history = []
        self.simulation_mode = True
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical data for simulation"""
        try:
            logging.info(f"Loading historical data for {self.symbol}")
            
            # Download 2 years of historical data
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period="2y", interval="1m")
            
            # Convert to list of price points
            self.price_history = []
            for timestamp, row in data.iterrows():
                self.price_history.append({
                    'timestamp': timestamp,
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                })
            
            # Set initial price
            if self.price_history:
                self.current_price = self.price_history[-1]['close']
            
            logging.info(f"Loaded {len(self.price_history)} price points")
            
        except Exception as e:
            logging.error(f"Error loading historical data: {e}")
            # Create simulated data if download fails
            self.create_simulated_data()
    
    def create_simulated_data(self):
        """Create simulated price data for testing"""
        logging.info("Creating simulated price data")
        
        base_price = 4500  # ES futures around 4500
        self.price_history = []
        current_time = datetime.now() - timedelta(days=365)
        
        for i in range(10000):  # 10,000 minutes of data
            # Random walk with trend
            change = np.random.normal(0, 2)  # $2 standard deviation
            base_price += change
            
            # Add some volatility
            volatility = np.random.normal(0, 5)
            
            self.price_history.append({
                'timestamp': current_time + timedelta(minutes=i),
                'open': base_price,
                'high': base_price + abs(volatility),
                'low': base_price - abs(volatility),
                'close': base_price + volatility,
                'volume': np.random.randint(100, 1000)
            })
        
        self.current_price = self.price_history[-1]['close']
        logging.info(f"Created {len(self.price_history)} simulated price points")
    
    def get_current_price(self) -> Optional[Dict]:
        """Get current simulated price"""
        if not self.price_history:
            return None
        
        # Simulate price movement
        if self.simulation_mode:
            # Use next historical price or create realistic movement
            if len(self.price_history) > 0:
                last_price = self.current_price
                # Add realistic price movement
                change = np.random.normal(0, 1.5)  # $1.50 standard deviation
                self.current_price = last_price + change
                
                return {
                    'symbol': self.symbol,
                    'price': self.current_price,
                    'bid': self.current_price - 0.25,
                    'ask': self.current_price + 0.25,
                    'volume': np.random.randint(100, 500),
                    'timestamp': datetime.now()
                }
        
        return None
    
    def get_ohlcv(self, timeframe: str = '1m', limit: int = 100) -> List[Dict]:
        """Get OHLCV data for strategy"""
        if not self.price_history:
            return []
        
        # Return recent price history
        recent_data = self.price_history[-limit:]
        
        # Convert to OHLCV format
        ohlcv = []
        for point in recent_data:
            ohlcv.append({
                'timestamp': point['timestamp'],
                'open': point['open'],
                'high': point['high'],
                'low': point['low'],
                'close': point['close'],
                'volume': point['volume']
            })
        
        return ohlcv

class OfflineTradingEngine:
    """Offline trading engine with simulation"""
    
    def __init__(self):
        self.positions = {}
        self.orders = []
        self.account_balance = 100000  # $100k starting balance
        self.trades = []
        self.paper_trading = True
    
    def place_order(self, symbol: str, side: str, quantity: int, 
                   order_type: str = 'market', price: float = None) -> tuple:
        """Place a simulated order"""
        try:
            # Get current price if not provided
            if price is None:
                # Simulate market price with slippage
                base_price = 4500  # ES futures
                slippage = np.random.normal(0, 0.5)  # $0.50 slippage
                price = base_price + slippage
            
            # Create order
            order = {
                'id': f"sim_{int(time.time())}",
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'type': order_type,
                'status': 'filled',
                'timestamp': datetime.now()
            }
            
            self.orders.append(order)
            
            # Update positions
            self._update_position(symbol, side, quantity, price)
            
            # Record trade
            self.trades.append({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now(),
                'pnl': 0  # Will be calculated when position is closed
            })
            
            logging.info(f"Order placed: {side} {quantity} {symbol} @ {price}")
            return True, order
            
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return False, f"Order error: {e}"
    
    def _update_position(self, symbol: str, side: str, quantity: int, price: float):
        """Update internal position tracking"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'side': side,
                'quantity': 0,
                'entry_price': 0,
                'timestamp': datetime.now()
            }
        
        position = self.positions[symbol]
        
        if side == position['side']:
            # Adding to position
            total_quantity = position['quantity'] + quantity
            total_value = (position['quantity'] * position['entry_price']) + (quantity * price)
            position['entry_price'] = total_value / total_quantity
            position['quantity'] = total_quantity
        else:
            # Reducing position
            position['quantity'] -= quantity
            if position['quantity'] <= 0:
                del self.positions[symbol]
    
    def close_position(self, symbol: str) -> tuple:
        """Close a position"""
        if symbol not in self.positions:
            return False, "No position found"
        
        position = self.positions[symbol]
        side = 'sell' if position['side'] == 'buy' else 'buy'
        
        # Simulate exit price
        exit_price = 4500 + np.random.normal(0, 1)  # Current price with noise
        
        # Calculate P&L
        if position['side'] == 'buy':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        # Update account balance
        self.account_balance += pnl
        
        # Record trade
        self.trades.append({
            'symbol': symbol,
            'side': side,
            'quantity': position['quantity'],
            'price': exit_price,
            'timestamp': datetime.now(),
            'pnl': pnl
        })
        
        # Clear position
        del self.positions[symbol]
        
        logging.info(f"Position closed: {symbol}, P&L: ${pnl:.2f}")
        return True, f"Position closed, P&L: ${pnl:.2f}"
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        return self.positions
    
    def get_account_summary(self) -> Dict:
        """Get account summary"""
        total_pnl = sum(trade['pnl'] for trade in self.trades)
        
        return {
            'balance': self.account_balance,
            'total_pnl': total_pnl,
            'positions_count': len(self.positions),
            'trades_count': len(self.trades)
        }

class OfflineRiskManager:
    """Offline risk management"""
    
    def __init__(self):
        self.max_daily_loss = 1000  # $1,000 daily loss limit
        self.max_position_size = 5   # 5 contracts max
        self.daily_loss = 0
        self.daily_trades = []
    
    def can_trade(self, symbol: str, side: str, quantity: int, price: float) -> tuple:
        """Check if trade is allowed"""
        # Check daily loss limit
        if self.daily_loss <= -self.max_daily_loss:
            return False, "Daily loss limit reached"
        
        # Check position size
        if abs(quantity) > self.max_position_size:
            return False, "Position size too large"
        
        # Check margin requirements (simplified)
        estimated_margin = abs(quantity * price * 0.1)  # 10% margin
        if estimated_margin > 50000:  # $50k margin limit
            return False, "Insufficient margin"
        
        return True, "Trade allowed"
    
    def update_daily_loss(self, pnl: float):
        """Update daily loss tracking"""
        self.daily_loss += pnl
        logging.info(f"Daily P&L: ${self.daily_loss:.2f}")
    
    def reset_daily_metrics(self):
        """Reset daily metrics"""
        self.daily_loss = 0
        self.daily_trades = []
        logging.info("Daily risk metrics reset")

class OfflineTradingBot:
    """Complete offline trading bot"""
    
    def __init__(self, symbol: str = "ES=F"):
        self.symbol = symbol
        self.market_data = OfflineMarketData(symbol)
        self.trading_engine = OfflineTradingEngine()
        self.risk_manager = OfflineRiskManager()
        self.running = False
        
        # Strategy parameters
        self.sma_short = 5
        self.sma_long = 20
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_trading_signals(self) -> Dict:
        """Generate trading signals using multiple indicators"""
        ohlcv = self.market_data.get_ohlcv(limit=50)
        if len(ohlcv) < 20:
            return {'action': 'hold', 'reason': 'Insufficient data'}
        
        closes = [candle['close'] for candle in ohlcv]
        
        # Calculate indicators
        sma_short = self.calculate_sma(closes, self.sma_short)
        sma_long = self.calculate_sma(closes, self.sma_long)
        rsi = self.calculate_rsi(closes, self.rsi_period)
        
        # Generate signals
        signals = {
            'sma_signal': 'buy' if sma_short > sma_long else 'sell',
            'rsi_signal': 'buy' if rsi < self.rsi_oversold else 'sell' if rsi > self.rsi_overbought else 'hold',
            'sma_short': sma_short,
            'sma_long': sma_long,
            'rsi': rsi
        }
        
        # Combine signals
        if signals['sma_signal'] == 'buy' and signals['rsi_signal'] == 'buy':
            signals['action'] = 'buy'
            signals['reason'] = 'SMA bullish + RSI oversold'
        elif signals['sma_signal'] == 'sell' and signals['rsi_signal'] == 'sell':
            signals['action'] = 'sell'
            signals['reason'] = 'SMA bearish + RSI overbought'
        else:
            signals['action'] = 'hold'
            signals['reason'] = 'Mixed signals'
        
        return signals
    
    def execute_trading_logic(self):
        """Execute trading strategy"""
        try:
            # Get current price
            current_price_data = self.market_data.get_current_price()
            if not current_price_data:
                return
            
            current_price = current_price_data['price']
            
            # Generate signals
            signals = self.generate_trading_signals()
            
            # Get current positions
            positions = self.trading_engine.get_positions()
            
            # Execute trades based on signals
            if signals['action'] == 'buy' and self.symbol not in positions:
                # Check risk management
                can_trade, reason = self.risk_manager.can_trade(
                    self.symbol, 'buy', 1, current_price
                )
                
                if can_trade:
                    success, result = self.trading_engine.place_order(
                        self.symbol, 'buy', 1, 'market', current_price
                    )
                    if success:
                        logging.info(f"Buy signal executed: {signals['reason']}")
                    else:
                        logging.warning(f"Buy order failed: {result}")
                else:
                    logging.warning(f"Risk check failed: {reason}")
            
            elif signals['action'] == 'sell' and self.symbol in positions:
                success, result = self.trading_engine.close_position(self.symbol)
                if success:
                    pnl = float(result.split('$')[1].split()[0])
                    self.risk_manager.update_daily_loss(pnl)
                    logging.info(f"Sell signal executed: {signals['reason']}")
                else:
                    logging.warning(f"Sell order failed: {result}")
            
            # Log current status
            logging.debug(f"Signals: {signals}")
            
        except Exception as e:
            logging.error(f"Error in trading logic: {e}")
    
    def start(self):
        """Start the offline trading bot"""
        logging.info("Starting Offline Trading Bot...")
        self.running = True
        
        # Schedule daily reset
        schedule.every().day.at("09:30").do(self.risk_manager.reset_daily_metrics)
        
        # Main trading loop
        while self.running:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Execute trading logic
                self.execute_trading_logic()
                
                # Print status every 10 iterations
                if hasattr(self, '_iteration_count'):
                    self._iteration_count += 1
                else:
                    self._iteration_count = 1
                
                if self._iteration_count % 10 == 0:
                    self.print_status()
                
                time.sleep(1)  # 1 second loop
                
            except KeyboardInterrupt:
                logging.info("Bot stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(5)
        
        self.stop()
    
    def print_status(self):
        """Print current bot status"""
        summary = self.trading_engine.get_account_summary()
        positions = self.trading_engine.get_positions()
        
        print(f"\n{'='*50}")
        print(f"🤖 OFFLINE TRADING BOT STATUS")
        print(f"{'='*50}")
        print(f"Account Balance: ${summary['balance']:,.2f}")
        print(f"Total P&L: ${summary['total_pnl']:,.2f}")
        print(f"Daily P&L: ${self.risk_manager.daily_loss:,.2f}")
        print(f"Open Positions: {len(positions)}")
        print(f"Total Trades: {summary['trades_count']}")
        
        if positions:
            for symbol, pos in positions.items():
                print(f"  {symbol}: {pos['side']} {pos['quantity']} @ ${pos['entry_price']:.2f}")
        
        print(f"{'='*50}")
    
    def stop(self):
        """Stop the bot"""
        logging.info("Stopping offline trading bot...")
        self.running = False
        
        # Close all positions
        positions = self.trading_engine.get_positions()
        for symbol in positions:
            self.trading_engine.close_position(symbol)
        
        # Print final summary
        self.print_status()
        logging.info("Offline trading bot stopped")

def main():
    """Main entry point"""
    print("🤖 OFFLINE TRADING BOT")
    print("=" * 50)
    print("This bot runs completely offline using:")
    print("- Historical data from Yahoo Finance")
    print("- Simulated price movements")
    print("- Paper trading simulation")
    print("- No APIs required!")
    print("=" * 50)
    
    bot = OfflineTradingBot("ES=F")  # E-mini S&P 500 futures
    
    try:
        bot.start()
    except KeyboardInterrupt:
        logging.info("Bot interrupted by user")

if __name__ == "__main__":
    main() 