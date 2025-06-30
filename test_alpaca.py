#!/usr/bin/env python3
"""
Test Alpaca API Connection
"""
import os
from dotenv import load_dotenv

def test_alpaca_connection():
    """Test Alpaca API connection"""
    print("🔌 Testing Alpaca API Connection...")
    
    try:
        import alpaca_trade_api as tradeapi
        
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not api_key or api_key == 'your_alpaca_api_key_here':
            print("❌ ALPACA_API_KEY not configured in .env file")
            return False
        
        if not secret_key or secret_key == 'your_alpaca_secret_key_here':
            print("❌ ALPACA_SECRET_KEY not configured in .env file")
            return False
        
        print(f"Connecting to: {base_url}")
        
        # Initialize API
        api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url=base_url,
            api_version='v2'
        )
        
        # Test account connection
        account = api.get_account()
        print(f"✅ Connected to Alpaca!")
        print(f"   Account Status: {account.status}")
        print(f"   Account Type: {'Paper Trading' if 'paper' in base_url else 'Live Trading'}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        
        # Test market data
        try:
            spy_trade = api.get_latest_trade('SPY')
            print(f"✅ Market data working - SPY: ${float(spy_trade.price):.2f}")
        except Exception as e:
            print(f"⚠️  Market data test failed: {e}")
        
        return True
        
    except ImportError:
        print("❌ Alpaca API not installed. Run: pip install alpaca-trade-api")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    print("🤖 Alpaca API Connection Test")
    print("=" * 40)
    
    if test_alpaca_connection():
        print("\n🎉 Alpaca API connection successful!")
        print("You're ready to start trading!")
    else:
        print("\n❌ Alpaca API connection failed.")
        print("Please check your API credentials and try again.")

if __name__ == "__main__":
    main() 