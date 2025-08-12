# Trading Bot Created by Markus Means
IF you choose to use this outside of paper trading, i am not responsible for money lost or gained.

A simple algorithmic trading bot using the Alpaca API with a momentum strategy based on moving average crossovers.

## Features

- 📊 Real-time market data from Alpaca
- 🤖 Automated trading strategy (Golden Cross/Death Cross)
- 📈 Paper trading support for testing
- 🔒 Secure API credential management
- ⏰ Configurable check intervals

## Setup

### 1. Install Dependencies

```bash
pip install alpaca-trade-api pandas numpy python-dotenv
```

### 2. Get Alpaca API Credentials

1. Sign up at [Alpaca Markets](https://alpaca.markets/)
2. Go to your [Paper Trading Dashboard](https://app.alpaca.markets/paper/dashboard/overview)
3. Copy your API Key and Secret Key

### 3. Configure Environment

1. Copy `env_example.txt` to `.env`
2. Fill in your API credentials:

```bash
ALPACA_API_KEY=your_actual_api_key
ALPACA_SECRET_KEY=your_actual_secret_key
```

### 4. Configure Trading Settings

Edit `config.py` to customize:
- Trading symbols
- Check intervals
- Strategy parameters
- Paper vs live trading

## Usage

### Run the Bot

```bash
python run_bot.py
```

### Test Individual Functions

```python
from trading_bot import TradingBot
from config import API_KEY, SECRET_KEY

# Initialize bot
bot = TradingBot(API_KEY, SECRET_KEY, paper=True)

# Test market data
data = bot.get_market_data('SPY')
print(f"Latest SPY price: ${data['close'].iloc[-1]:.2f}")

# Run single strategy check
bot.simple_momentum_strategy('SPY')
```

## Strategy

The bot uses a simple momentum strategy:
- **Buy Signal**: When short-term moving average crosses above long-term moving average (Golden Cross)
- **Sell Signal**: When short-term moving average crosses below long-term moving average (Death Cross)

## Safety Features

- ✅ Paper trading by default
- ✅ Position size limits (10% of buying power per trade)
- ✅ Market hours checking
- ✅ Error handling and retry logic
- ✅ Secure credential management

## ⚠️ Important Notes

- **Never commit your `.env` file** with real API keys
- **Start with paper trading** to test your strategy
- **Monitor the bot** when running live
- **Understand the risks** of algorithmic trading

## Files

- `trading_bot.py` - Main bot class and strategy
- `config.py` - Configuration settings
- `run_bot.py` - Bot runner script
- `env_example.txt` - Example environment file
- `README.md` - This file
  
