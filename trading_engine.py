import logging
from datetime import datetime
from config import Config
from market_data import MarketData
from risk_manager import RiskManager
from database import Database

class TradingEngine:
    def __init__(self):
        self.market_data = MarketData()
        self.risk_manager = RiskManager()
        self.db = Database()
        self.positions = {}
        self.orders = {}
        
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
            
            # Place order on exchange
            if Config.PAPER_TRADING:
                # Simulate order placement for paper trading
                order = self._simulate_order(symbol, side, quantity, order_type, price)
            else:
                # Real order placement
                order = self._place_real_order(symbol, side, quantity, order_type, price)
            
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
    
    def _simulate_order(self, symbol, side, quantity, order_type, price):
        """Simulate order placement for paper trading"""
        order_id = f"sim_{datetime.now().timestamp()}"
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'type': order_type,
            'status': 'filled',
            'timestamp': datetime.now()
        }
        self.orders[order_id] = order
        return order
    
    def _place_real_order(self, symbol, side, quantity, order_type, price):
        """Place real order on exchange"""
        try:
            if order_type == 'market':
                order = self.market_data.exchange.create_market_order(symbol, side, quantity)
            elif order_type == 'limit':
                order = self.market_data.exchange.create_limit_order(symbol, side, quantity, price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            return order
        except Exception as e:
            logging.error(f"Error placing real order: {e}")
            return None
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        try:
            if Config.PAPER_TRADING:
                if order_id in self.orders:
                    self.orders[order_id]['status'] = 'cancelled'
                    logging.info(f"Order cancelled: {order_id}")
                    return True, "Order cancelled"
                else:
                    return False, "Order not found"
            else:
                result = self.market_data.exchange.cancel_order(order_id)
                logging.info(f"Order cancelled: {order_id}")
                return True, result
        except Exception as e:
            logging.error(f"Error cancelling order: {e}")
            return False, f"Cancel error: {e}"
    
    def close_position(self, symbol, side=None, quantity=None):
        """Close a position"""
        try:
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
                
        except Exception as e:
            logging.error(f"Error closing position: {e}")
            return False, f"Close error: {e}"
    
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
        
        should_close, reason = self.risk_manager.should_close_position(
            current_price, 
            position['entry_price'], 
            position['side'],
            position['stop_loss'],
            position['take_profit']
        )
        
        if should_close:
            return self.close_position(symbol)
        
        return False, None
    
    def get_positions(self):
        """Get current positions"""
        return self.positions
    
    def get_orders(self):
        """Get current orders"""
        return self.orders
    
    def get_account_summary(self):
        """Get account summary"""
        try:
            balance = self.market_data.get_account_balance()
            positions = self.market_data.get_positions()
            
            return {
                'balance': balance,
                'positions': positions,
                'risk_metrics': self.risk_manager.get_risk_metrics()
            }
        except Exception as e:
            logging.error(f"Error getting account summary: {e}")
            return None 