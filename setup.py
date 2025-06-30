#!/usr/bin/env python3
"""
Setup script for Trading Bot
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
            f.write("# Exchange API Credentials\n")
            f.write("API_KEY=your_api_key_here\n")
            f.write("SECRET_KEY=your_secret_key_here\n")
            f.write("PASSPHRASE=your_passphrase_here  # Only needed for some exchanges like OKX\n")
            f.write("\n# Paper Trading Configuration\n")
            f.write("PAPER_TRADING=True\n")
        print("✅ .env file created - please edit with your API credentials")
    else:
        print("✅ .env file already exists")

def check_config():
    """Check if configuration is ready"""
    print("\n📋 Configuration Check:")
    
    # Check .env file
    if os.path.exists(".env"):
        print("✅ .env file exists")
    else:
        print("❌ .env file missing")
    
    # Check if API keys are set
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('API_KEY')
    secret_key = os.getenv('SECRET_KEY')
    
    if api_key and api_key != 'your_api_key_here':
        print("✅ API_KEY is configured")
    else:
        print("❌ API_KEY needs to be configured")
    
    if secret_key and secret_key != 'your_secret_key_here':
        print("✅ SECRET_KEY is configured")
    else:
        print("❌ SECRET_KEY needs to be configured")

def main():
    print("🤖 Trading Bot Setup")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        return
    
    # Create .env file
    create_env_file()
    
    # Check configuration
    check_config()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Edit .env file with your API credentials")
    print("2. Run: python main.py")
    print("3. Monitor logs in trading_bot.log")
    print("\n⚠️  Remember: This is paper trading mode by default!")

if __name__ == "__main__":
    main() 