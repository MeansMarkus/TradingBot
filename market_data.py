import ccxt
import time
import logging
from datetime import datetime
from config import Config
from database import Database

class MarketData:
    def __init__(self):
        self.exchange = None
        self.db = Database()
        self.setup_exchange()
        
    def setup_exchange(self):
        """Setup exchange connection"""
        try:
            # Initialize exchange
            exchange_class = getattr(ccxt, Config.EXCHANGE)
            self.exchange = exchange_class({
                'apiKey': Config.API_KEY,
                'secret': Config.SECRET_KEY,
                'password': Config.PASSPHRASE,
                'sandbox': Config.PAPER_TRADING,
                'enableRateLimit': True,
            })
            
            # Load markets
            self.exchange.load_markets()
            logging.info(f"Connected to {Config.EXCHANGE} exchange")
            
        except Exception as e:
            logging.error(f"Failed to setup exchange: {e}")
            raise
    
    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logging.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def get_ohlcv(self, symbol, timeframe='1m', limit=100):
        """Get OHLCV data for a symbol"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to list of dictionaries
            data = []
            for candle in ohlcv:
                data.append({
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return data
            
        except Exception as e:
            logging.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    def save_price_data(self, symbol):
        """Fetch and save current price data"""
        try:
            # Get current OHLCV data
            ohlcv_data = self.get_ohlcv(symbol, Config.TIMEFRAME, limit=1)
            
            if ohlcv_data:
                candle = ohlcv_data[0]
                
                # Save to database
                self.db.save_price_data(
                    symbol=symbol,
                    timestamp=candle['timestamp'],
                    open_price=candle['open'],
                    high=candle['high'],
                    low=candle['low'],
                    close=candle['close'],
                    volume=candle['volume']
                )
                
                logging.debug(f"Saved price data for {symbol}: {candle['close']}")
                
        except Exception as e:
            logging.error(f"Error saving price data for {symbol}: {e}")
    
    def get_account_balance(self):
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance['total'],
                'free': balance['free'],
                'used': balance['used']
            }
        except Exception as e:
            logging.error(f"Error fetching account balance: {e}")
            return None
    
    def get_positions(self):
        """Get current positions"""
        try:
            positions = self.exchange.fetch_positions()
            return positions
        except Exception as e:
            logging.error(f"Error fetching positions: {e}")
            return []
    
    def get_order_book(self, symbol, limit=20):
        """Get order book for a symbol"""
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            logging.error(f"Error fetching order book for {symbol}: {e}")
            return None
    
    def start_data_stream(self, symbol, callback=None):
        """Start real-time data stream"""
        logging.info(f"Starting data stream for {symbol}")
        
        while True:
            try:
                # Get and save current price data
                self.save_price_data(symbol)
                
                # Call callback if provided
                if callback:
                    current_price = self.get_current_price(symbol)
                    if current_price:
                        callback(current_price)
                
                # Wait for next update
                time.sleep(Config.DATA_UPDATE_INTERVAL)
                
            except KeyboardInterrupt:
                logging.info("Data stream stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in data stream: {e}")
                time.sleep(5)  # Wait before retrying 