import logging
from datetime import datetime
from config import Config
from market_data import MarketData
from risk_manager import RiskManager
from database import Database

# Import Alpaca API
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca API not available. Install with: pip install alpaca-trade-api")

class TradingEngine:
    def __init__(self):
        self.market_data = MarketData()
        self.risk_manager = RiskManager()
        self.db = Database()
        self.positions = {}
        self.orders = {}
        self.alpaca_api = None
        
        if Config.EXCHANGE == 'alpaca' and ALPACA_AVAILABLE:
            self.setup_alpaca()
        
    def setup_alpaca(self):
        """Setup Alpaca API"""
        try:
            self.alpaca_api = tradeapi.REST(
                key_id=Config.API_KEY,
                secret_key=Config.SECRET_KEY,
                base_url=Config.BASE_URL,
                api_version='v2'
            )
            logging.info("Alpaca API initialized")
        except Exception as e:
            logging.error(f"Failed to setup Alpaca: {e}")
        
    def place_order(self, symbol, side, quantity, order_type='market', price=None, stop_loss=None, take_profit=None):
        """Place an order with risk management checks"""
        try:
            # Get current price if not provided
            if price is None:
                current_price_data = self.market_data.get_current_price(symbol)
                if current_price_data:
                    price = current_price_data['price']
                else:
                    return False, "Unable to get current price"
            
            # Risk management check
            can_trade, reason = self.risk_manager.can_trade(symbol, side, quantity, price)
            if not can_trade:
                return False, reason
            
            # Place order
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                order = self._place_alpaca_order(symbol, side, quantity, order_type, price)
            else:
                order = self._place_ccxt_order(symbol, side, quantity, order_type, price)
            
            if order:
                # Save trade to database
                self.db.save_trade(symbol, side, quantity, price, order.get('id'))
                
                # Update positions
                self._update_position(symbol, side, quantity, price)
                
                # Set stop loss and take profit if provided
                if stop_loss or take_profit:
                    self._set_stop_loss_take_profit(symbol, side, quantity, price, stop_loss, take_profit)
                
                logging.info(f"Order placed: {side} {quantity} {symbol} @ {price}")
                return True, order
            else:
                return False, "Failed to place order"
                
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return False, f"Order error: {e}"
    
    def _place_alpaca_order(self, symbol, side, quantity, order_type, price):
        """Place order on Alpaca"""
        try:
            if order_type == 'market':
                order = self.alpaca_api.submit_order(
                    symbol=symbol,
                    qty=quantity,
                    side=side,
                    type='market',
                    time_in_force='day'
                )
            elif order_type == 'limit':
                order = self.alpaca_api.submit_order(
                    symbol=symbol,
                    qty=quantity,
                    side=side,
                    type='limit',
                    time_in_force='day',
                    limit_price=price
                )
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            return {
                'id': order.id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'type': order_type,
                'status': order.status,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Error placing Alpaca order: {e}")
            return None
    
    def _place_ccxt_order(self, symbol, side, quantity, order_type, price):
        """Place order on CCXT exchange"""
        try:
            if order_type == 'market':
                order = self.market_data.exchange.create_market_order(symbol, side, quantity)
            elif order_type == 'limit':
                order = self.market_data.exchange.create_limit_order(symbol, side, quantity, price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            return order
        except Exception as e:
            logging.error(f"Error placing CCXT order: {e}")
            return None
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                result = self.alpaca_api.cancel_order(order_id)
                logging.info(f"Order cancelled: {order_id}")
                return True, result
            else:
                if order_id in self.orders:
                    self.orders[order_id]['status'] = 'cancelled'
                    logging.info(f"Order cancelled: {order_id}")
                    return True, "Order cancelled"
                else:
                    return False, "Order not found"
        except Exception as e:
            logging.error(f"Error cancelling order: {e}")
            return False, f"Cancel error: {e}"
    
    def close_position(self, symbol, side=None, quantity=None):
        """Close a position"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                return self._close_alpaca_position(symbol, side, quantity)
            else:
                return self._close_ccxt_position(symbol, side, quantity)
                
        except Exception as e:
            logging.error(f"Error closing position: {e}")
            return False, f"Close error: {e}"
    
    def _close_alpaca_position(self, symbol, side=None, quantity=None):
        """Close position on Alpaca"""
        try:
            # Get current position
            positions = self.alpaca_api.list_positions()
            position = None
            
            for pos in positions:
                if pos.symbol == symbol:
                    position = pos
                    break
            
            if not position:
                return False, "No position found for symbol"
            
            # Determine side and quantity
            if side is None:
                side = 'sell' if float(position.qty) > 0 else 'buy'
            if quantity is None:
                quantity = abs(float(position.qty))
            
            # Place closing order
            order = self.alpaca_api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            # Calculate P&L
            entry_price = float(position.avg_entry_price)
            current_price = float(position.current_price)
            position_size = abs(float(position.qty))
            
            if float(position.qty) > 0:  # Long position
                pnl = (current_price - entry_price) * position_size
            else:  # Short position
                pnl = (entry_price - current_price) * position_size
            
            # Update risk manager
            self.risk_manager.update_daily_loss(pnl)
            
            logging.info(f"Position closed: {symbol}, P&L: ${pnl:.2f}")
            return True, f"Position closed, P&L: ${pnl:.2f}"
            
        except Exception as e:
            logging.error(f"Error closing Alpaca position: {e}")
            return False, f"Close error: {e}"
    
    def _close_ccxt_position(self, symbol, side=None, quantity=None):
        """Close position on CCXT exchange"""
        if symbol not in self.positions:
            return False, "No position found for symbol"
        
        position = self.positions[symbol]
        if side is None:
            side = 'sell' if position['side'] == 'buy' else 'buy'
        if quantity is None:
            quantity = position['quantity']
        
        # Place closing order
        success, result = self.place_order(symbol, side, quantity)
        
        if success:
            # Calculate P&L
            pnl = self._calculate_pnl(position, result['price'], side)
            
            # Update risk manager
            self.risk_manager.update_daily_loss(pnl)
            
            # Clear position
            del self.positions[symbol]
            
            logging.info(f"Position closed: {symbol}, P&L: {pnl}")
            return True, f"Position closed, P&L: {pnl}"
        else:
            return False, result
    
    def _update_position(self, symbol, side, quantity, price):
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
    
    def _calculate_pnl(self, position, exit_price, exit_side):
        """Calculate P&L for a position"""
        if position['side'] == 'buy':
            # Long position
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:
            # Short position
            pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        return pnl
    
    def _set_stop_loss_take_profit(self, symbol, side, quantity, entry_price, stop_loss=None, take_profit=None):
        """Set stop loss and take profit orders"""
        if stop_loss is None:
            stop_loss = self.risk_manager.calculate_stop_loss(entry_price, side)
        if take_profit is None:
            take_profit = self.risk_manager.calculate_take_profit(entry_price, side)
        
        # Store stop loss and take profit levels
        if symbol not in self.positions:
            self.positions[symbol] = {}
        
        self.positions[symbol]['stop_loss'] = stop_loss
        self.positions[symbol]['take_profit'] = take_profit
        
        logging.info(f"Set SL: {stop_loss}, TP: {take_profit} for {symbol}")
    
    def check_stop_loss_take_profit(self, symbol, current_price):
        """Check if stop loss or take profit should be triggered"""
        if symbol not in self.positions:
            return False, None
        
        position = self.positions[symbol]
        if 'stop_loss' not in position or 'take_profit' not in position:
            return False, None
        
        if position['side'] == 'buy':
            # Long position
            if current_price <= position['stop_loss']:
                return True, "Stop loss hit"
            elif current_price >= position['take_profit']:
                return True, "Take profit hit"
        else:
            # Short position
            if current_price >= position['stop_loss']:
                return True, "Stop loss hit"
            elif current_price <= position['take_profit']:
                return True, "Take profit hit"
        
        return False, None
    
    def get_positions(self):
        """Get current positions"""
        if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
            try:
                positions = self.alpaca_api.list_positions()
                return {pos.symbol: pos for pos in positions}
            except Exception as e:
                logging.error(f"Error getting Alpaca positions: {e}")
                return {}
        else:
            return self.positions
    
    def get_orders(self):
        """Get current orders"""
        return self.orders
    
    def get_account_summary(self):
        """Get account summary"""
        try:
            if Config.EXCHANGE == 'alpaca' and self.alpaca_api:
                account = self.alpaca_api.get_account()
                return {
                    'balance': float(account.equity),
                    'cash': float(account.cash),
                    'buying_power': float(account.buying_power),
                    'portfolio_value': float(account.portfolio_value),
                    'status': account.status
                }
            else:
                return {
                    'balance': 100000,  # Default for paper trading
                    'cash': 100000,
                    'buying_power': 100000,
                    'portfolio_value': 100000,
                    'status': 'ACTIVE'
                }
        except Exception as e:
            logging.error(f"Error getting account summary: {e}")
            return None 