"""Live trading logic with real Kalshi API calls for Conviction Bot."""
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from kalshi_auth import KalshiAuth
from config import Config


@dataclass
class LivePosition:
    """Represents a live trading position."""
    cycle_id: str
    ticker: str
    side: str  # "YES" or "NO"
    entry_price: float  # Price paid for the contracts
    contracts: int
    entry_time: datetime
    time_remaining_at_entry: float
    order_id: Optional[str] = None
    resolved: bool = False
    result: Optional[str] = None  # "yes" or "no"
    pnl: Optional[float] = None
    win: Optional[bool] = None


class LiveTrader:
    """Handles live trading with real Kalshi API calls and P&L calculations."""

    def __init__(self):
        self.auth = KalshiAuth()
        self.positions: Dict[str, LivePosition] = {}  # cycle_id -> position
        self.yes_threshold = Config.YES_BUY_THRESHOLD  # 0.94
        self.no_threshold = Config.NO_BUY_THRESHOLD   # 0.06
        self.contract_quantity = Config.CONTRACT_QUANTITY  # 10
        self.session = requests.Session()

    def should_enter_trade(self, yes_ask: float, cycle_id: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Determine if we should enter a trade based on yes_ask_dollars price only.

        Args:
            yes_ask: Current YES ask price (parsed from yes_ask_dollars)
            cycle_id: Current trading cycle ID

        Returns:
            Tuple of (should_trade, side, entry_price)
        """
        # Check if we already have a position for this cycle
        if cycle_id in self.positions:
            return False, None, None

        # Check YES buy condition (yes_ask_dollars >= 0.94)
        if yes_ask >= self.yes_threshold:
            return True, "YES", yes_ask

        # Check NO buy condition (yes_ask_dollars <= 0.06)
        if yes_ask <= self.no_threshold:
            # When buying NO contracts, entry_price is (1 - yes_ask_dollars)
            no_price = 1.0 - yes_ask
            return True, "NO", no_price

        return False, None, None

    def submit_order(self, ticker: str, side: str, quantity: int, price_cents: int) -> Optional[Dict[str, Any]]:
        """
        Submit a live order to Kalshi API with retry logic for "No contracts available".

        Args:
            ticker: Market ticker symbol
            side: "yes" or "no" (lowercase for API)
            quantity: Number of contracts
            price_cents: Price in cents (e.g., 94 for $0.94)

        Returns:
            Order response dict if successful, None if failed
        """
        endpoint = "/portfolio/orders"

        order_data = {
            "ticker": ticker,
            "action": "buy",
            "side": side,
            "count": quantity,
            "type": "market",  # Use market orders for immediate execution
        }

        max_retries = 60  # Retry for up to 5 minutes (60 * 5 seconds)
        retry_count = 0

        while retry_count < max_retries:
            try:
                headers = self.auth.get_auth_headers("POST", endpoint)
                url = self.auth.get_base_url() + endpoint

                response = self.session.post(url, json=order_data, headers=headers, timeout=10)

                if response.status_code == 200 or response.status_code == 201:
                    order_result = response.json()
                    print(f"✅ Order submitted successfully: {order_result}")
                    return order_result

                elif response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', '')

                    if 'No contracts available' in error_message or 'insufficient liquidity' in error_message.lower():
                        retry_count += 1
                        print(f"⚠️ No contracts available, retrying ({retry_count}/{max_retries})...")
                        time.sleep(5)  # Wait 5 seconds before retry
                        continue
                    else:
                        print(f"❌ Order failed with error: {error_message}")
                        return None

                else:
                    print(f"❌ Order failed with status {response.status_code}: {response.text}")
                    return None

            except requests.RequestException as e:
                print(f"❌ Network error submitting order: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
                    continue
                else:
                    return None

        print(f"❌ Order failed after {max_retries} retries - giving up")
        return None

    def enter_position(
        self,
        cycle_id: str,
        ticker: str,
        side: str,
        entry_price: float,
        entry_time: datetime,
        time_remaining: float
    ) -> Optional[LivePosition]:
        """
        Enter a new live trading position.

        Args:
            cycle_id: Trading cycle identifier
            ticker: Market ticker
            side: "YES" or "NO"
            entry_price: Price paid for contracts
            entry_time: When the trade was entered
            time_remaining: Seconds remaining in cycle when trade entered

        Returns:
            The created position if successful, None if order failed
        """
        # Validation
        if side not in ["YES", "NO"]:
            raise ValueError(f"Invalid side: {side}")

        if cycle_id in self.positions:
            raise ValueError(f"Position already exists for cycle {cycle_id}")

        # Convert to API format
        api_side = side.lower()  # "yes" or "no" for API
        price_cents = int(entry_price * 100)  # Convert to cents

        print(f"🎯 Entering LIVE trade: {self.contract_quantity} {side} contracts at ${entry_price:.4f}")
        print(f"   Market: {ticker}")
        print(f"   Cost: ${entry_price * self.contract_quantity:.2f}")

        # Submit the order
        order_response = self.submit_order(ticker, api_side, self.contract_quantity, price_cents)

        if not order_response:
            print(f"❌ Failed to submit order for {ticker}")
            return None

        # Extract order ID from response
        order_id = order_response.get('order', {}).get('order_id')

        # Create position
        position = LivePosition(
            cycle_id=cycle_id,
            ticker=ticker,
            side=side,
            entry_price=entry_price,
            contracts=self.contract_quantity,
            entry_time=entry_time,
            time_remaining_at_entry=time_remaining,
            order_id=order_id
        )

        self.positions[cycle_id] = position

        print(f"✅ LIVE TRADE EXECUTED: {self.contract_quantity} {side} at ${entry_price:.4f}")
        print(f"   Order ID: {order_id}")

        return position

    def resolve_position(self, cycle_id: str, result: str) -> Optional[LivePosition]:
        """
        Resolve a live trading position with market result.

        Args:
            cycle_id: Trading cycle identifier
            result: Market result ("yes" or "no")

        Returns:
            The resolved position if it exists, None otherwise
        """
        if cycle_id not in self.positions:
            return None

        position = self.positions[cycle_id]

        if position.resolved:
            return position

        # Calculate P&L based on the corrected logic:
        # When buying YES: entry_price = yes_ask_dollars at time of trade
        # When buying NO: entry_price = no_ask_dollars at time of trade (calculated as 1 - yes_ask)

        if position.side == "YES":
            if result == "yes":
                # YES position wins: profit = (1.00 - entry_price) × contracts
                position.pnl = (1.00 - position.entry_price) * position.contracts
                position.win = True
            else:
                # YES position loses: loss = entry_price × contracts
                position.pnl = -position.entry_price * position.contracts
                position.win = False

        elif position.side == "NO":
            if result == "no":
                # NO position wins: profit = (1.00 - entry_price) × contracts
                position.pnl = (1.00 - position.entry_price) * position.contracts
                position.win = True
            else:
                # NO position loses: loss = entry_price × contracts
                position.pnl = -position.entry_price * position.contracts
                position.win = False

        position.result = result
        position.resolved = True

        # Print result
        outcome = "WIN" if position.win else "LOSS"
        pnl_sign = "+" if position.pnl >= 0 else ""
        print(f"💰 LIVE TRADE RESULT: {outcome} - {position.side} position resolved '{result}' - P&L: {pnl_sign}${position.pnl:.2f}")

        return position

    def get_position(self, cycle_id: str) -> Optional[LivePosition]:
        """Get position for a specific cycle."""
        return self.positions.get(cycle_id)

    def has_position(self, cycle_id: str) -> bool:
        """Check if we have a position for the given cycle."""
        return cycle_id in self.positions

    def get_all_positions(self) -> Dict[str, LivePosition]:
        """Get all positions."""
        return self.positions.copy()

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Calculate performance statistics across all positions.

        Returns:
            Dictionary with performance metrics
        """
        resolved_positions = [pos for pos in self.positions.values() if pos.resolved]

        if not resolved_positions:
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0
            }

        wins = sum(1 for pos in resolved_positions if pos.win)
        total_pnl = sum(pos.pnl for pos in resolved_positions if pos.pnl is not None)
        pnls = [pos.pnl for pos in resolved_positions if pos.pnl is not None]

        return {
            "total_trades": len(resolved_positions),
            "wins": wins,
            "losses": len(resolved_positions) - wins,
            "win_rate": wins / len(resolved_positions),
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(resolved_positions),
            "best_trade": max(pnls) if pnls else 0.0,
            "worst_trade": min(pnls) if pnls else 0.0
        }

    def get_account_balance(self) -> Optional[float]:
        """
        Get current account balance from Kalshi.

        Returns:
            Account balance in dollars, or None if failed
        """
        try:
            endpoint = "/portfolio/balance"
            headers = self.auth.get_auth_headers("GET", endpoint)
            url = self.auth.get_base_url() + endpoint

            response = self.session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                balance_data = response.json()
                balance_cents = balance_data.get('balance', 0)
                return balance_cents / 100  # Convert cents to dollars
            else:
                print(f"Failed to get balance: {response.status_code} {response.text}")
                return None

        except Exception as e:
            print(f"Error getting account balance: {e}")
            return None