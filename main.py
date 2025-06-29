import logging
import time
import schedule
from datetime import datetime
from config import Config
from market_data import MarketData
from trading_engine import TradingEngine
from risk_manager import RiskManager

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

class TradingBot:
    def __init__(self):
        self.market_data = MarketData()
        self.trading_engine = TradingEngine()
        self.risk_manager = RiskManager()
        self.running = False
        
    def start(self):
        """Start the trading bot"""
        logging.info("Starting Futures Trading Bot...")
        self.running = True
        
        try:
            # Schedule daily tasks
            schedule.every().day.at("09:30").do(self.risk_manager.reset_daily_metrics)
            schedule.every().day.at("16:00").do(self.end_of_day_summary)
            
            # Start market data stream
            self.start_market_data_stream()
            
            # Main trading loop
            while self.running:
                try:
                    # Run scheduled tasks
                    schedule.run_pending()
                    
                    # Check for stop loss/take profit triggers
                    self.check_positions()
                    
                    # Simple trading logic (example)
                    self.simple_trading_logic()
                    
                    time.sleep(1)  # 1 second loop
                    
                except KeyboardInterrupt:
                    logging.info("Bot stopped by user")
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    time.sleep(5)
                    
        except Exception as e:
            logging.error(f"Fatal error: {e}")
        finally:
            self.stop()
    
    def start_market_data_stream(self):
        """Start real-time market data stream"""
        logging.info(f"Starting market data stream for {Config.SYMBOL}")
        
        # Start data stream in background
        def price_callback(price_data):
            # Check stop loss/take profit
            self.check_positions()
            
            # Log price updates
            logging.debug(f"Price update: {price_data['symbol']} @ {price_data['price']}")
        
        # For now, we'll use a simple polling approach
        # In production, you'd use websockets for real-time data
        import threading
        
        def data_stream():
            while self.running:
                try:
                    self.market_data.save_price_data(Config.SYMBOL)
                    time.sleep(Config.DATA_UPDATE_INTERVAL)
                except Exception as e:
                    logging.error(f"Error in data stream: {e}")
                    time.sleep(5)
        
        self.data_thread = threading.Thread(target=data_stream, daemon=True)
        self.data_thread.start()
    
    def check_positions(self):
        """Check all positions for stop loss/take profit"""
        try:
            current_price_data = self.market_data.get_current_price(Config.SYMBOL)
            if current_price_data:
                current_price = current_price_data['price']
                
                # Check each position
                positions = self.trading_engine.get_positions()
                for symbol in positions:
                    self.trading_engine.check_stop_loss_take_profit(symbol, current_price)
                    
        except Exception as e:
            logging.error(f"Error checking positions: {e}")
    
    def simple_trading_logic(self):
        """Simple example trading logic - replace with your strategy"""
        try:
            # Get current price
            current_price_data = self.market_data.get_current_price(Config.SYMBOL)
            if not current_price_data:
                return
            
            current_price = current_price_data['price']
            
            # Get recent price history
            price_history = self.market_data.get_ohlcv(Config.SYMBOL, Config.TIMEFRAME, limit=20)
            if len(price_history) < 10:
                return
            
            # Simple moving average strategy
            closes = [candle['close'] for candle in price_history]
            sma_5 = sum(closes[:5]) / 5
            sma_10 = sum(closes[:10]) / 10
            
            positions = self.trading_engine.get_positions()
            
            # Trading signals
            if sma_5 > sma_10 and Config.SYMBOL not in positions:
                # Buy signal
                success, result = self.trading_engine.place_order(
                    Config.SYMBOL, 'buy', Config.MAX_POSITION_SIZE
                )
                if success:
                    logging.info(f"Buy order placed: {result}")
                else:
                    logging.warning(f"Buy order failed: {result}")
                    
            elif sma_5 < sma_10 and Config.SYMBOL in positions:
                # Sell signal
                success, result = self.trading_engine.close_position(Config.SYMBOL)
                if success:
                    logging.info(f"Position closed: {result}")
                else:
                    logging.warning(f"Position close failed: {result}")
                    
        except Exception as e:
            logging.error(f"Error in trading logic: {e}")
    
    def end_of_day_summary(self):
        """End of day summary and cleanup"""
        logging.info("=== End of Day Summary ===")
        
        try:
            # Get account summary
            summary = self.trading_engine.get_account_summary()
            if summary:
                logging.info(f"Account Summary: {summary}")
            
            # Get today's P&L
            today_pnl = self.risk_manager.daily_loss
            logging.info(f"Today's P&L: {today_pnl}")
            
            # Close all positions (optional - depends on your strategy)
            # self.close_all_positions()
            
        except Exception as e:
            logging.error(f"Error in end of day summary: {e}")
    
    def close_all_positions(self):
        """Close all open positions"""
        positions = self.trading_engine.get_positions()
        for symbol in positions:
            success, result = self.trading_engine.close_position(symbol)
            if success:
                logging.info(f"Closed position {symbol}: {result}")
            else:
                logging.error(f"Failed to close position {symbol}: {result}")
    
    def stop(self):
        """Stop the trading bot"""
        logging.info("Stopping trading bot...")
        self.running = False
        
        # Close all positions
        self.close_all_positions()
        
        logging.info("Trading bot stopped")

def main():
    """Main entry point"""
    bot = TradingBot()
    
    try:
        bot.start()
    except KeyboardInterrupt:
        logging.info("Bot interrupted by user")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
    finally:
        bot.stop()

if __name__ == "__main__":
    main() 