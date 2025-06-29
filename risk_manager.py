import logging
from datetime import datetime, date
from config import Config
from database import Database

class RiskManager:
    def __init__(self):
        self.db = Database()
        self.daily_loss = 0
        self.max_daily_loss = Config.MAX_DAILY_LOSS
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.stop_loss_percent = Config.STOP_LOSS_PERCENT
        self.take_profit_percent = Config.TAKE_PROFIT_PERCENT
        
    def can_trade(self, symbol, side, quantity, price):
        """Check if trade is allowed based on risk management rules"""
        try:
            # Check daily loss limit
            if not self.check_daily_loss_limit():
                logging.warning("Daily loss limit reached - trading stopped")
                return False, "Daily loss limit exceeded"
            
            # Check position size
            if not self.check_position_size(quantity):
                logging.warning(f"Position size {quantity} exceeds maximum {self.max_position_size}")
                return False, "Position size too large"
            
            # Check if we have enough margin
            if not self.check_margin_requirements(symbol, quantity, price):
                logging.warning("Insufficient margin for trade")
                return False, "Insufficient margin"
            
            return True, "Trade allowed"
            
        except Exception as e:
            logging.error(f"Error in risk check: {e}")
            return False, f"Risk check error: {e}"
    
    def check_daily_loss_limit(self):
        """Check if daily loss limit has been reached"""
        today_pnl = self.db.get_today_pnl()
        return today_pnl > -self.max_daily_loss
    
    def check_position_size(self, quantity):
        """Check if position size is within limits"""
        return abs(quantity) <= self.max_position_size
    
    def check_margin_requirements(self, symbol, quantity, price):
        """Check if we have enough margin for the trade"""
        # This is a simplified check - in practice you'd calculate actual margin requirements
        # based on exchange rules and current positions
        try:
            balance = self.db.get_account_balance()
            if balance:
                # Estimate margin requirement (simplified)
                estimated_margin = abs(quantity * price * 0.1)  # 10% margin requirement
                return balance['free_margin'] >= estimated_margin
            return True  # If we can't get balance, allow trade
        except Exception as e:
            logging.error(f"Error checking margin: {e}")
            return True
    
    def calculate_stop_loss(self, entry_price, side):
        """Calculate stop loss price"""
        if side.lower() == 'buy':
            stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
        else:  # sell
            stop_loss = entry_price * (1 + self.stop_loss_percent / 100)
        return stop_loss
    
    def calculate_take_profit(self, entry_price, side):
        """Calculate take profit price"""
        if side.lower() == 'buy':
            take_profit = entry_price * (1 + self.take_profit_percent / 100)
        else:  # sell
            take_profit = entry_price * (1 - self.take_profit_percent / 100)
        return take_profit
    
    def update_daily_loss(self, pnl):
        """Update daily loss tracking"""
        self.daily_loss += pnl
        
        # Save to database
        today = date.today()
        self.db.save_daily_pnl(today, self.daily_loss)
        
        logging.info(f"Daily P&L updated: {self.daily_loss}")
    
    def should_close_position(self, current_price, entry_price, side, stop_loss=None, take_profit=None):
        """Check if position should be closed based on stop loss or take profit"""
        if stop_loss is None:
            stop_loss = self.calculate_stop_loss(entry_price, side)
        if take_profit is None:
            take_profit = self.calculate_take_profit(entry_price, side)
        
        if side.lower() == 'buy':
            # Long position
            if current_price <= stop_loss:
                return True, "Stop loss hit"
            elif current_price >= take_profit:
                return True, "Take profit hit"
        else:
            # Short position
            if current_price >= stop_loss:
                return True, "Stop loss hit"
            elif current_price <= take_profit:
                return True, "Take profit hit"
        
        return False, "Position within bounds"
    
    def get_risk_metrics(self):
        """Get current risk metrics"""
        return {
            'daily_loss': self.daily_loss,
            'max_daily_loss': self.max_daily_loss,
            'max_position_size': self.max_position_size,
            'stop_loss_percent': self.stop_loss_percent,
            'take_profit_percent': self.take_profit_percent,
            'can_trade': self.check_daily_loss_limit()
        }
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of new trading day)"""
        self.daily_loss = 0
        logging.info("Daily risk metrics reset")
    
    def calculate_position_risk(self, quantity, price, volatility=0.02):
        """Calculate position risk (Value at Risk approximation)"""
        position_value = abs(quantity * price)
        var_95 = position_value * volatility * 1.645  # 95% confidence interval
        return var_95 