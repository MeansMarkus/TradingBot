import ccxt
import time
import logging
from datetime import datetime, timedelta
from config import Config
from database import Database

# Import Alpaca API
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca API not available. Install with: pip install alpaca-trade-api")

class MarketData:
    def __init__(self):
        self.exchange = None
        self.alpaca_api = None
        self.db = Database()
        self.setup_exchange()
        
    def setup_exchange(self):
        """Setup exchange connection"""
        try:
            if Config.EXCHANGE == 'alpaca' and ALPACA_AVAILABLE:
                self.setup_alpaca_connection()
            else:
                # Fallback to CCXT for other exchanges
                self.setup_ccxt_connection()
                
        except Exception as e:
            logging.error(f"Failed to setup exchange: {e}")
            raise
    
    def setup_alpaca_connection(self):
        """Setup Alpaca connection"""
        try:
            # Initialize Alpaca API
            self.alpaca_api = tradeapi.REST(
                key_id=Config.API_KEY,
                secret_key=Config.SECRET_KEY,
                base_url=Config.BASE_URL,
                api_version='v2'
            )
            
            # Test connection
            account = self.alpaca_api.get_account()
            logging.info(f"Connected to Alpaca - Account: {account.status}")
            
        except Exception as e:
            logging.error(f"Failed to setup Alpaca connection: {e}")
            raise
    
    def setup_ccxt_connection(self):
        """Setup CCXT connection for other exchanges"""
        try:
            exchange_class = getattr(ccxt, Config.EXCHANGE)
            self.exchange = exchange_class({
                'apiKey': Config.API_KEY,
                'secret': Config.SECRET_KEY,
                'password': Config.PASSPHRASE,
                'sandbox': Config.PAPER_TRADING,
                'enableRateLimit': True,
            })
            
            self.exchange.load_markets()
            logging.info(f"Connected to {Config.EXCHANGE} exchange")
            
        except Exception as e:
            logging.error(f"Failed to setup CCXT exchange: {e}")
            raise
    
    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                return self.get_alpaca_price(symbol)
            else:
                return self.get_ccxt_price(symbol)
                
        except Exception as e:
            logging.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def get_alpaca_price(self, symbol):
        """Get price from Alpaca"""
        try:
            # Get latest trade
            latest_trade = self.alpaca_api.get_latest_trade(symbol)
            
            # Get current quote for bid/ask
            quote = self.alpaca_api.get_latest_quote(symbol)
            
            return {
                'symbol': symbol,
                'price': float(latest_trade.price),
                'bid': float(quote.bid) if quote else float(latest_trade.price),
                'ask': float(quote.ask) if quote else float(latest_trade.price),
                'volume': int(latest_trade.size),
                'timestamp': datetime.now()
            }
                
        except Exception as e:
            logging.error(f"Error getting Alpaca price: {e}")
            return None
    
    def get_ccxt_price(self, symbol):
        """Get price from CCXT exchange"""
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
            logging.error(f"Error fetching CCXT price for {symbol}: {e}")
            return None
    
    def get_ohlcv(self, symbol, timeframe='1m', limit=100):
        """Get OHLCV data for a symbol"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                return self.get_alpaca_ohlcv(symbol, timeframe, limit)
            else:
                return self.get_ccxt_ohlcv(symbol, timeframe, limit)
                
        except Exception as e:
            logging.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    def get_alpaca_ohlcv(self, symbol, timeframe, limit):
        """Get OHLCV from Alpaca"""
        try:
            # Convert timeframe to Alpaca format
            tf_map = {
                '1m': '1Min',
                '5m': '5Min',
                '15m': '15Min',
                '1h': '1Hour',
                '1d': '1Day'
            }
            
            alpaca_timeframe = tf_map.get(timeframe, '1Min')
            
            # Get bars
            bars = self.alpaca_api.get_bars(
                symbol,
                alpaca_timeframe,
                limit=limit
            )
            
            data = []
            for bar in bars:
                data.append({
                    'timestamp': bar.t,
                    'open': bar.o,
                    'high': bar.h,
                    'low': bar.l,
                    'close': bar.c,
                    'volume': bar.v
                })
            
            return data
            
        except Exception as e:
            logging.error(f"Error fetching Alpaca OHLCV for {symbol}: {e}")
            return []
    
    def get_ccxt_ohlcv(self, symbol, timeframe, limit):
        """Get OHLCV from CCXT exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
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
            logging.error(f"Error fetching CCXT OHLCV for {symbol}: {e}")
            return []
    
    def save_price_data(self, symbol):
        """Fetch and save current price data"""
        try:
            current_price = self.get_current_price(symbol)
            if current_price:
                # Save to database
                self.db.save_price_data(
                    symbol=symbol,
                    timestamp=current_price['timestamp'],
                    open_price=current_price['price'],
                    high=current_price['price'],
                    low=current_price['price'],
                    close=current_price['price'],
                    volume=current_price.get('volume', 0)
                )
                
                logging.debug(f"Saved price data for {symbol}: {current_price['price']}")
                
        except Exception as e:
            logging.error(f"Error saving price data for {symbol}: {e}")
    
    def get_account_balance(self):
        """Get account balance"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                account = self.alpaca_api.get_account()
                return {
                    'total': {'USD': float(account.equity)},
                    'free': {'USD': float(account.cash)},
                    'used': {'USD': float(account.equity) - float(account.cash)}
                }
            else:
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
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                positions = self.alpaca_api.list_positions()
                return positions
            else:
                positions = self.exchange.fetch_positions()
                return positions
        except Exception as e:
            logging.error(f"Error fetching positions: {e}")
            return []
    
    def get_order_book(self, symbol, limit=20):
        """Get order book for a symbol"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                # Alpaca doesn't provide order book in basic API
                return None
            else:
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