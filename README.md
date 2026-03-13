# Conviction Bot - Kalshi BTC Trading Bot

A Python trading bot for Kalshi's BTC 15-minute markets that implements a conviction-based strategy with both paper trading and live trading capabilities.

## Strategy

The bot monitors BTC 15-minute prediction markets and trades based on extreme price movements:

- **Monitor**: In the final 6 minutes of each 15-minute cycle
- **Buy YES**: When yes_ask ≥ $0.94 (high confidence BTC will be up)
- **Buy NO**: When yes_ask ≤ $0.06 (high confidence BTC will be down)
- **Hold**: All positions until market resolution
- **Limit**: Maximum one trade per cycle

## Features

- **Paper Trading**: Simulation mode for strategy testing
- **Live Trading**: Real money trading with Kalshi API
- **Authentication**: Secure HMAC signature authentication
- **Retry Logic**: Handles "no contracts available" scenarios
- **Logging**: Comprehensive JSON logging of all trades and polls
- **Safety**: Confirmation prompts for live trading mode

## Files

### Core Bot Components
- `conviction_bot.py` - Paper trading main bot
- `conviction_bot_live.py` - Live trading main bot (real money)
- `market_client.py` - Kalshi API client for market data
- `paper_trader.py` - Simulated trading logic
- `live_trader.py` - Real trading with order submission
- `scheduler.py` - Trading cycle timing and windows
- `logger.py` - JSON logging system
- `config.py` - Configuration parameters

### Authentication & Monitoring
- `kalshi_auth.py` - HMAC signature authentication
- `quick_monitor.py` - Real-time market monitoring

## Setup

### Prerequisites
- Python 3.8+
- Kalshi account and API credentials
- Private key file for authentication

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd kalshi-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file with:
```bash
# Kalshi API credentials
KALSHI_API_KEY_ID=your_api_key_id
KALSHI_PRIVATE_KEY_PATH=/path/to/your/private_key.pem

# Set to 'false' for live trading, 'true' for demo
KALSHI_DEMO=true
```

## Usage

### Paper Trading (Recommended for Testing)
```bash
python conviction_bot.py
```

### Live Trading (Real Money)
```bash
python conviction_bot_live.py
```
**⚠️ Warning**: Live trading uses real money. You'll be prompted to type 'CONFIRM' before starting.

### Market Monitoring
```bash
python quick_monitor.py
```

## Configuration

Edit `config.py` to adjust:
- **YES_BUY_THRESHOLD**: Price threshold for YES trades (default: 0.94)
- **NO_BUY_THRESHOLD**: Price threshold for NO trades (default: 0.06)
- **CONTRACT_QUANTITY**: Number of contracts per trade (default: 10)
- **TRADING_WINDOW_MINUTES**: Trading window length (default: 6)
- **POLLING_INTERVAL**: How often to check prices (default: 2 seconds)

## Performance Tracking

The bot logs all trades and market data:
- `logs/trade_data.jsonl` - Trade entries and results
- `logs/poll_data.jsonl` - Market price polling data

BTC 15-minute cycles close at :00, :15, :30, :45 every hour.
Bot wakes up 6 minutes before each close and polls every 2 seconds.

## Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Upload your private key file securely
4. Deploy with automatic builds on git push

### Manual Server Deployment
```bash
# Install screen for persistent sessions
sudo apt install screen

# Start bot in background
screen -S conviction-bot
python conviction_bot_live.py
# Press Ctrl+A then D to detach

# Reattach later with
screen -r conviction-bot
```

## Risk Management

- **Start Small**: Begin with small position sizes
- **Monitor Closely**: Watch performance in paper trading first
- **Set Limits**: The bot naturally limits to one trade per cycle
- **Check Balance**: Bot displays account balance at startup and after trades

## Backtesting Results

Paper trading results from 12+ hour test:
- **Total Trades**: 48+
- **Win Rate**: 100%
- **Total P&L**: $20+
- **Strategy**: Highly profitable in trending markets

## Legal & Disclaimer

This software is for educational and research purposes only. Trading involves financial risk, and you may lose money. The authors are not responsible for any financial losses. Use at your own risk and ensure compliance with all applicable laws and regulations.