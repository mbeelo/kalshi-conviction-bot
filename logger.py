"""JSON logging utilities for Conviction Bot."""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from config import Config


class ConvictionLogger:
    """Logger for poll data and trade activities."""

    def __init__(self, source: str = "live"):
        """
        Initialize logger with source identification.

        Args:
            source: "live" for real trading, "paper" for simulated trading
        """
        Config.ensure_log_directory()
        self.source = source
        self.poll_log_file = Config.POLL_LOG_FILE

        # Use separate log files for paper vs live trading
        if source == "paper":
            self.trade_log_file = Config.PAPER_TRADE_LOG_FILE
        else:
            self.trade_log_file = Config.TRADE_LOG_FILE

    def log_poll_data(
        self,
        timestamp: datetime,
        ticker: str,
        yes_ask: float,
        no_ask: float,
        time_remaining: Optional[float],
        cycle_id: str
    ) -> None:
        """
        Log polling data to JSONL file.

        Args:
            timestamp: When the poll occurred
            ticker: Market ticker
            yes_ask: YES ask price
            no_ask: NO ask price
            time_remaining: Seconds remaining in cycle (None if not in trading window)
            cycle_id: Unique cycle identifier
        """
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "ticker": ticker,
            "yes_ask": yes_ask,
            "no_ask": no_ask,
            "time_remaining": time_remaining,
            "cycle_id": cycle_id,
            "type": "poll"
        }

        self._append_to_file(self.poll_log_file, log_entry)

    def log_trade_entry(
        self,
        cycle_id: str,
        ticker: str,
        entry_time: datetime,
        time_remaining_at_entry: float,
        side: str,
        entry_price: float,
        contracts: int = 10
    ) -> None:
        """
        Log trade entry to JSONL file.

        Args:
            cycle_id: Unique cycle identifier
            ticker: Market ticker
            entry_time: When the trade was entered
            time_remaining_at_entry: Seconds remaining when trade was entered
            side: "YES" or "NO"
            entry_price: Price paid for contracts
            contracts: Number of contracts (default 10)
        """
        log_entry = {
            "timestamp": entry_time.isoformat(),
            "cycle_id": cycle_id,
            "ticker": ticker,
            "entry_time": entry_time.isoformat(),
            "time_remaining_at_entry": time_remaining_at_entry,
            "side": side,
            "entry_price": entry_price,
            "contracts": contracts,
            "source": self.source,
            "type": "trade_entry"
        }

        self._append_to_file(self.trade_log_file, log_entry)

    def log_trade_result(
        self,
        cycle_id: str,
        ticker: str,
        result: str,
        pnl: float,
        win: bool,
        resolution_time: Optional[datetime] = None
    ) -> None:
        """
        Log trade result to JSONL file.

        Args:
            cycle_id: Unique cycle identifier
            ticker: Market ticker
            result: Market result ("yes" or "no")
            pnl: Profit/loss amount in dollars
            win: Whether the trade was profitable
            resolution_time: When the market resolved
        """
        log_entry = {
            "timestamp": (resolution_time or datetime.utcnow()).isoformat(),
            "cycle_id": cycle_id,
            "ticker": ticker,
            "result": result,
            "pnl": pnl,
            "win": win,
            "resolution_time": resolution_time.isoformat() if resolution_time else None,
            "source": self.source,
            "type": "trade_result"
        }

        self._append_to_file(self.trade_log_file, log_entry)

    def log_complete_trade(
        self,
        cycle_id: str,
        ticker: str,
        entry_time: datetime,
        time_remaining_at_entry: float,
        side: str,
        entry_price: float,
        result: str,
        pnl: float,
        win: bool,
        contracts: int = 10,
        resolution_time: Optional[datetime] = None
    ) -> None:
        """
        Log complete trade with entry and result data.

        Args:
            cycle_id: Unique cycle identifier
            ticker: Market ticker
            entry_time: When the trade was entered
            time_remaining_at_entry: Seconds remaining when trade was entered
            side: "YES" or "NO"
            entry_price: Price paid for contracts
            result: Market result ("yes" or "no")
            pnl: Profit/loss amount in dollars
            win: Whether the trade was profitable
            contracts: Number of contracts (default 10)
            resolution_time: When the market resolved
        """
        log_entry = {
            "timestamp": (resolution_time or datetime.utcnow()).isoformat(),
            "cycle_id": cycle_id,
            "ticker": ticker,
            "entry_time": entry_time.isoformat(),
            "time_remaining_at_entry": time_remaining_at_entry,
            "side": side,
            "entry_price": entry_price,
            "contracts": contracts,
            "result": result,
            "pnl": pnl,
            "win": win,
            "resolution_time": resolution_time.isoformat() if resolution_time else None,
            "source": self.source,
            "type": "complete_trade"
        }

        self._append_to_file(self.trade_log_file, log_entry)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        cycle_id: Optional[str] = None,
        ticker: Optional[str] = None
    ) -> None:
        """
        Log error events.

        Args:
            error_type: Type of error (e.g., "api_error", "parsing_error")
            error_message: Description of the error
            cycle_id: Related cycle ID if applicable
            ticker: Related ticker if applicable
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "cycle_id": cycle_id,
            "ticker": ticker,
            "type": "error"
        }

        self._append_to_file(self.poll_log_file, log_entry)

    def log_bot_event(
        self,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log general bot events.

        Args:
            event_type: Type of event (e.g., "startup", "shutdown", "cycle_start")
            message: Human-readable message
            data: Additional event data
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "message": message,
            "data": data or {},
            "type": "bot_event"
        }

        self._append_to_file(self.poll_log_file, log_entry)

    def get_trade_summary(self) -> Dict[str, Any]:
        """
        Get trading performance summary from logs.

        Returns:
            Summary statistics
        """
        trades = []

        try:
            with open(self.trade_log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("type") == "complete_trade":
                        trades.append(entry)
        except FileNotFoundError:
            pass

        if not trades:
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0
            }

        wins = sum(1 for trade in trades if trade.get("win", False))
        losses = len(trades) - wins
        total_pnl = sum(trade.get("pnl", 0) for trade in trades)

        return {
            "total_trades": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate": wins / len(trades) if trades else 0.0,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(trades) if trades else 0.0
        }

    def _append_to_file(self, filepath: str, data: Dict[str, Any]) -> None:
        """
        Append JSON data to file.

        Args:
            filepath: Path to the log file
            data: Dictionary to append as JSON
        """
        try:
            with open(filepath, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            print(f"Error writing to log file {filepath}: {e}")