# Futures Trading Bot - Foundation

A robust foundation for building a futures trading bot with real-time market data, risk management, and order execution capabilities.

## Features

### 1. Market Data Connection
- Real-time price feeds for futures contracts
- Support for multiple exchanges (Binance, Bybit, OKX)
- OHLCV data collection and storage
- WebSocket support for live data streaming

### 2. Database Storage
- SQLite database for price history, trades, and account data
- Efficient data storage and retrieval
- Trade tracking and P&L calculation
- Account balance monitoring

### 3. Exchange API Integration
- Paper trading mode for safe testing
- Order placement, cancellation, and modification
- Position tracking and management
- Account balance and margin monitoring

### 4. Risk Management
- Fixed position sizing
- Configurable stop-loss and take-profit levels
- Daily loss limits
- Margin requirement checks
- Position risk calculation

## Project Structure

```
TradingBot/
├── config.py           # Configuration settings
├── database.py         # Database operations
├── market_data.py      # Market data connection
├── risk_manager.py     # Risk management
├── trading_engine.py   # Order execution
├── main.py            # Main application
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies

First, install the core dependencies manually to avoid compilation issues:

```bash
# Install numpy and pandas first (pre-built wheels)
pip install numpy==1.24.3 pandas==2.1.4

# Install remaining dependencies
pip install -r requirements.txt
```

### Step 2: Environment Setup

Create a `.env` file in the project root:

```env
# Exchange API Credentials
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
PASSPHRASE=your_passphrase_here  # Only for some exchanges like OKX

# Trading Settings
PAPER_TRADING=true
SYMBOL=ES  # E-mini S&P 500 futures
```

### Step 3: Configuration

Edit `config.py` to customize your trading parameters:

```python
# Risk Management
MAX_POSITION_SIZE = 1        # Number of contracts
MAX_DAILY_LOSS = 1000        # Maximum daily loss in USD
STOP_LOSS_PERCENT = 2.0      # Stop loss percentage
TAKE_PROFIT_PERCENT = 4.0    # Take profit percentage
```

## Usage

### Starting the Bot

```bash
python main.py
```

The bot will:
1. Connect to the exchange
2. Initialize the database
3. Start collecting market data
4. Begin monitoring for trading opportunities
5. Execute trades based on the configured strategy

### Paper Trading Mode

By default, the bot runs in paper trading mode (`PAPER_TRADING = True`). This allows you to:
- Test strategies without real money
- Validate risk management rules
- Debug trading logic safely

### Real Trading

To switch to real trading:
1. Set `PAPER_TRADING = False` in `config.py`
2. Ensure your API credentials are correct
3. Start with small position sizes
4. Monitor the bot closely

## Configuration Options

### Exchange Settings
- `EXCHANGE`: Choose from 'binance', 'bybit', 'okx'
- `API_KEY`: Your exchange API key
- `SECRET_KEY`: Your exchange secret key
- `PASSPHRASE`: Required for some exchanges

### Trading Parameters
- `SYMBOL`: Trading symbol (e.g., 'ES' for E-mini S&P 500)
- `TIMEFRAME`: Data timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
- `MAX_POSITION_SIZE`: Maximum position size in contracts

### Risk Management
- `MAX_DAILY_LOSS`: Maximum daily loss limit in USD
- `STOP_LOSS_PERCENT`: Stop loss percentage
- `TAKE_PROFIT_PERCENT`: Take profit percentage

## Database Schema

### Price History
```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    UNIQUE(symbol, timestamp)
);
```

### Trades
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    order_id TEXT,
    status TEXT DEFAULT 'open'
);
```

### Account Balance
```sql
CREATE TABLE account_balance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    balance REAL NOT NULL,
    equity REAL NOT NULL,
    margin_used REAL NOT NULL,
    free_margin REAL NOT NULL
);
```

## Trading Strategy

The current implementation includes a simple moving average crossover strategy:

- **Buy Signal**: 5-period SMA > 10-period SMA
- **Sell Signal**: 5-period SMA < 10-period SMA

You can replace this with your own strategy by modifying the `simple_trading_logic()` method in `main.py`.

## Risk Management Features

1. **Position Sizing**: Fixed position size per trade
2. **Stop Loss**: Automatic stop loss based on percentage
3. **Take Profit**: Automatic take profit based on percentage
4. **Daily Loss Limit**: Stops trading when daily loss limit is reached
5. **Margin Checks**: Validates margin requirements before trades

## Monitoring and Logging

The bot provides comprehensive logging:
- Trade execution logs
- Risk management alerts
- Error tracking
- Performance metrics

Logs are saved to `trading_bot.log` and also displayed in the console.

## Safety Features

- Paper trading mode for testing
- Daily loss limits
- Position size limits
- Automatic stop-loss and take-profit
- Error handling and recovery
- Graceful shutdown

## Next Steps

This foundation provides the core infrastructure. You can extend it by:

1. **Adding Technical Indicators**: Implement RSI, MACD, Bollinger Bands, etc.
2. **Machine Learning Models**: Add ML-based signal generation
3. **Backtesting**: Create historical strategy testing
4. **Web Dashboard**: Build a web interface for monitoring
5. **Multiple Strategies**: Implement strategy switching
6. **Portfolio Management**: Add multi-asset trading
7. **Advanced Risk Management**: Implement Kelly Criterion, position sizing

## Disclaimer

This software is for educational purposes only. Trading futures involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always test thoroughly in paper trading mode before using real money.

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify your API credentials
3. Ensure all dependencies are installed
4. Test in paper trading mode first

## License

This project is provided as-is for educational purposes. Use at your own risk. 