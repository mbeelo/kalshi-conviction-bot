"""Paper trading logic and P&L calculations for Conviction Bot."""
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from config import Config


@dataclass
class PaperPosition:
    """Represents a paper trading position."""
    cycle_id: str
    ticker: str
    side: str  # "YES" or "NO"
    entry_price: float  # Price paid for the contracts
    contracts: int
    entry_time: datetime
    time_remaining_at_entry: float
    resolved: bool = False
    result: Optional[str] = None  # "yes" or "no"
    pnl: Optional[float] = None
    win: Optional[bool] = None


class PaperTrader:
    """Handles paper trading logic and P&L calculations."""

    def __init__(self):
        self.positions: Dict[str, PaperPosition] = {}  # cycle_id -> position
        self.yes_threshold = Config.YES_BUY_THRESHOLD  # 0.95
        self.no_threshold = Config.NO_BUY_THRESHOLD   # 0.05
        self.contract_quantity = Config.CONTRACT_QUANTITY  # 10

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

        # Check YES buy condition (yes_ask_dollars >= 0.95)
        if yes_ask >= self.yes_threshold:
            return True, "YES", yes_ask

        # Check NO buy condition (yes_ask_dollars <= 0.05)
        if yes_ask <= self.no_threshold:
            # When buying NO contracts, entry_price is (1 - yes_ask_dollars)
            no_price = 1.0 - yes_ask
            return True, "NO", no_price

        return False, None, None

    def enter_position(
        self,
        cycle_id: str,
        ticker: str,
        side: str,
        entry_price: float,
        entry_time: datetime,
        time_remaining: float
    ) -> PaperPosition:
        """
        Enter a new paper trading position.

        Args:
            cycle_id: Trading cycle identifier
            ticker: Market ticker
            side: "YES" or "NO"
            entry_price: Price paid for contracts
            entry_time: When the trade was entered
            time_remaining: Seconds remaining in cycle when trade entered

        Returns:
            The created position
        """
        # Validation
        if side not in ["YES", "NO"]:
            raise ValueError(f"Invalid side: {side}")

        if cycle_id in self.positions:
            raise ValueError(f"Position already exists for cycle {cycle_id}")

        # Create position
        position = PaperPosition(
            cycle_id=cycle_id,
            ticker=ticker,
            side=side,
            entry_price=entry_price,
            contracts=self.contract_quantity,
            entry_time=entry_time,
            time_remaining_at_entry=time_remaining
        )

        self.positions[cycle_id] = position

        print(f"PAPER TRADE: Bought {self.contract_quantity} {side} contracts at ${entry_price:.4f} for cycle {cycle_id}")
        print(f"  Cost: ${entry_price * self.contract_quantity:.2f}")

        return position

    def resolve_position(self, cycle_id: str, result: str) -> Optional[PaperPosition]:
        """
        Resolve a paper trading position with market result.

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
        # When buying NO: entry_price = no_ask_dollars at time of trade

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
        print(f"PAPER TRADE RESULT: {outcome} - {position.side} position resolved '{result}' - P&L: {pnl_sign}${position.pnl:.2f}")

        return position

    def get_position(self, cycle_id: str) -> Optional[PaperPosition]:
        """
        Get position for a specific cycle.

        Args:
            cycle_id: Trading cycle identifier

        Returns:
            Position if it exists, None otherwise
        """
        return self.positions.get(cycle_id)

    def has_position(self, cycle_id: str) -> bool:
        """
        Check if we have a position for the given cycle.

        Args:
            cycle_id: Trading cycle identifier

        Returns:
            True if position exists, False otherwise
        """
        return cycle_id in self.positions

    def get_all_positions(self) -> Dict[str, PaperPosition]:
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