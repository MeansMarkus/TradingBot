#!/usr/bin/env python3
"""
Alpaca Trading Bot Setup
"""
import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("# Alpaca API Configuration\n")
            f.write("ALPACA_API_KEY=your_alpaca_api_key_here\n")
            f.write("ALPACA_SECRET_KEY=your_alpaca_secret_key_here\n")
            f.write("ALPACA_BASE_URL=https://paper-api.alpaca.markets\n")
            f.write("\n# Paper Trading Configuration\n")
            f.write("PAPER_TRADING=True\n")
        print("✅ .env file created - please add your Alpaca API credentials")
    else:
        print("✅ .env file already exists")

def print_alpaca_setup_instructions():
    """Print Alpaca setup instructions"""
    print("\n" + "=" * 60)
    print("🏦 ALPACA API SETUP INSTRUCTIONS")
    print("=" * 60)
    print("1. Create Alpaca Account:")
    print("   - Go to: https://alpaca.markets/")
    print("   - Click 'Get Started' → 'Individual Account'")
    print("   - Fill out application (takes 5 minutes)")
    print()
    print("2. Get API Keys:")
    print("   - Login to Alpaca Dashboard")
    print("   - Go to: Paper Trading → API Keys")
    print("   - Click 'Generate New Key'")
    print("   - Copy API Key ID and Secret Key")
    print()
    print("3. Configure .env file:")
    print("   - Edit .env file")
    print("   - Replace 'your_alpaca_api_key_here' with your API Key ID")
    print("   - Replace 'your_alpaca_secret_key_here' with your Secret Key")
    print()
    print("4. Test Connection:")
    print("   - Run: python test_alpaca.py")
    print()
    print("5. Start Trading:")
    print("   - Run: python main.py")
    print("=" * 60)

def main():
    print("🤖 Alpaca Trading Bot Setup")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        return
    
    # Create .env file
    create_env_file()
    
    # Print setup instructions
    print_alpaca_setup_instructions()
    
    print("\n🎯 Next Steps:")
    print("1. Create Alpaca account and get API keys")
    print("2. Update .env file with your credentials")
    print("3. Run: python main.py")
    print("4. Monitor logs in trading_bot.log")
    print("\n⚠️  Remember: This starts in paper trading mode!")

if __name__ == "__main__":
    main() 