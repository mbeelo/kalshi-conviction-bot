"""Kalshi market client for fetching BTC 15-minute market data."""
import requests
import time
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config


class KalshiMarketClient:
    """Client for interacting with Kalshi BTC 15-minute markets."""

    def __init__(self):
        self.base_url = Config.KALSHI_BASE_URL
        self.series_ticker = Config.SERIES_TICKER
        self.session = requests.Session()

    def find_active_market(self) -> Optional[Dict[str, Any]]:
        """
        Find the currently active KXBTC15M market.

        Returns:
            Dict containing market data if found, None otherwise.
        """
        try:
            url = f"{self.base_url}/markets"
            params = {
                "limit": 100,
                "status": "open",  # API parameter is "open"
                "series_ticker": self.series_ticker
            }

            response = self.session.get(url, params=params, timeout=30)  # Increased timeout
            response.raise_for_status()

            data = response.json()
            markets = data.get("markets", [])

            # Add debug logging for Railway
            print(f"DEBUG: Found {len(markets)} markets from Kalshi API")

            if not markets:
                return None

            # Find the market with the soonest close_time
            # Note: API returns status="active" even though we query with status="open"
            active_markets = [m for m in markets if m.get("status") == "active"]
            if not active_markets:
                return None

            # Sort by close_time to get the soonest one
            active_markets.sort(key=lambda m: m.get("close_time", ""))
            return active_markets[0]

        except requests.RequestException as e:
            print(f"DEBUG: Network error finding active market: {e}")
            return None
        except Exception as e:
            print(f"DEBUG: Unexpected error finding active market: {e}")
            return None

    def get_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed market data for a specific ticker.

        Args:
            ticker: Market ticker symbol

        Returns:
            Dict containing market data if successful, None otherwise.
        """
        try:
            url = f"{self.base_url}/markets/{ticker}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            print(f"Error fetching market data for {ticker}: {e}")
            return None

    def parse_market_data(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse relevant information from market data response.

        Args:
            market_data: Raw market data from API

        Returns:
            Dict with parsed data: yes_ask, no_ask, close_time, result
        """
        try:
            market = market_data.get("market", {})

            # Parse ask prices (convert from string to float)
            yes_ask_str = market.get("yes_ask_dollars", "0")
            no_ask_str = market.get("no_ask_dollars", "0")
            yes_ask = float(yes_ask_str) if yes_ask_str else 0.0
            no_ask = float(no_ask_str) if no_ask_str else 0.0

            # Parse close time
            close_time_str = market.get("close_time")
            close_time = None
            if close_time_str:
                # Remove 'Z' suffix if present and parse
                close_time_str = close_time_str.rstrip('Z')
                close_time = datetime.fromisoformat(close_time_str)

            # Parse result (for resolved markets)
            result = market.get("result")  # "yes", "no", or None
            status = market.get("status")  # "open", "closed", etc.
            ticker = market.get("ticker")

            return {
                "ticker": ticker,
                "yes_ask": yes_ask,  # Parsed from yes_ask_dollars
                "no_ask": no_ask,    # Parsed from no_ask_dollars
                "close_time": close_time,
                "result": result,
                "status": status
            }

        except (ValueError, KeyError) as e:
            print(f"Error parsing market data: {e}")
            return None

    def wait_for_resolution(self, ticker: str, timeout_minutes: int = 30) -> Optional[str]:
        """
        Wait for a market to resolve and return the result.

        Args:
            ticker: Market ticker to monitor
            timeout_minutes: Maximum time to wait for resolution

        Returns:
            Result string ("yes" or "no") if resolved, None if timeout
        """
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            market_data = self.get_market_data(ticker)
            if market_data:
                parsed_data = self.parse_market_data(market_data)
                if parsed_data and parsed_data["result"]:
                    return parsed_data["result"]

            time.sleep(Config.POLLING_INTERVAL)

        print(f"Timeout waiting for resolution of market {ticker}")
        return None

    def get_current_market_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the current state of the active BTC 15-minute market.

        Returns:
            Dict with current market state or None if no active market
        """
        # First find the active market
        active_market = self.find_active_market()
        if not active_market:
            return None

        ticker = active_market.get("ticker")
        if not ticker:
            return None

        # Get detailed market data
        market_data = self.get_market_data(ticker)
        if not market_data:
            return None

        # Parse the data
        return self.parse_market_data(market_data)