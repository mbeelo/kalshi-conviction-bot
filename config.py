"""Configuration management for Conviction Bot."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the Conviction Bot."""

    # Kalshi API settings
    KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    SERIES_TICKER = "KXBTC15M"

    # Trading parameters
    CONTRACT_QUANTITY = 10
    YES_BUY_THRESHOLD = 0.94  # If yes_ask_dollars >= 0.94 → buy YES
    NO_BUY_THRESHOLD = 0.06   # If yes_ask_dollars <= 0.06 → buy NO

    # Timing parameters
    TRADING_POLLING_INTERVAL = 1      # seconds between polls during trading window (fast)
    SLEEP_POLLING_INTERVAL = 2        # seconds between polls during sleep period (slower)
    TRADING_WINDOW_MINUTES = 6        # minutes before close to start trading
    WAKE_UP_MINUTES = 6               # minutes before close to wake up
    ERROR_RETRY_DELAY = 10            # seconds to wait on API errors
    RATE_LIMIT_BACKOFF = 5            # seconds to wait on rate limits
    MARKET_DISCOVERY_RETRIES = 15     # max retries for finding active market (increased for transitions)
    MARKET_DISCOVERY_DELAY = 0.5      # initial delay for market discovery retries
    MAX_MARKET_DISCOVERY_DELAY = 2.0  # max delay for exponential backoff

    # Cycle times (minutes past the hour)
    CYCLE_TIMES = [0, 15, 30, 45]

    # Logging
    LOG_DIR = "logs"
    POLL_LOG_FILE = f"{LOG_DIR}/poll_data.jsonl"
    TRADE_LOG_FILE = f"{LOG_DIR}/trade_data.jsonl"
    PAPER_TRADE_LOG_FILE = f"{LOG_DIR}/paper_trades.jsonl"

    @classmethod
    def ensure_log_directory(cls):
        """Ensure the log directory exists."""
        os.makedirs(cls.LOG_DIR, exist_ok=True)