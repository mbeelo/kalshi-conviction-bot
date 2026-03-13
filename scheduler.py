"""Scheduler for managing BTC 15-minute trading cycles."""
import time
from datetime import datetime, timedelta
from typing import Tuple, Optional
import pytz
from config import Config


class TradingScheduler:
    """Manages timing for BTC 15-minute trading cycles."""

    def __init__(self):
        self.cycle_times = Config.CYCLE_TIMES  # [0, 15, 30, 45]
        self.wake_up_minutes = Config.WAKE_UP_MINUTES  # 6
        self.trading_window_minutes = Config.TRADING_WINDOW_MINUTES  # 5

    def get_next_cycle_close(self, current_time: Optional[datetime] = None) -> datetime:
        """
        Get the next cycle close time.

        Args:
            current_time: Current time (defaults to now in UTC)

        Returns:
            Next cycle close time in UTC
        """
        if current_time is None:
            current_time = datetime.now(pytz.UTC)

        # Ensure we're working with UTC
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        elif current_time.tzinfo != pytz.UTC:
            current_time = current_time.astimezone(pytz.UTC)

        # Start with current hour
        next_close = current_time.replace(second=0, microsecond=0)

        # Find next cycle time
        current_minute = current_time.minute

        for cycle_minute in self.cycle_times:
            if cycle_minute > current_minute:
                next_close = next_close.replace(minute=cycle_minute)
                return next_close

        # If no cycle time is found in current hour, go to next hour
        next_close = next_close.replace(minute=self.cycle_times[0]) + timedelta(hours=1)
        return next_close

    def get_wake_up_time(self, cycle_close_time: datetime) -> datetime:
        """
        Get the time when bot should wake up for a given cycle.

        Args:
            cycle_close_time: When the trading cycle closes

        Returns:
            Time to wake up (6 minutes before close)
        """
        return cycle_close_time - timedelta(minutes=self.wake_up_minutes)

    def get_trading_window_start(self, cycle_close_time: datetime) -> datetime:
        """
        Get the time when trading window starts.

        Args:
            cycle_close_time: When the trading cycle closes

        Returns:
            Time when trading window opens (5 minutes before close)
        """
        return cycle_close_time - timedelta(minutes=self.trading_window_minutes)

    def should_be_trading_now(self, current_time: Optional[datetime] = None) -> Tuple[bool, Optional[datetime]]:
        """
        Check if we should be in trading mode now.

        Args:
            current_time: Current time (defaults to now in UTC)

        Returns:
            Tuple of (should_trade, next_cycle_close_time)
        """
        if current_time is None:
            current_time = datetime.now(pytz.UTC)

        # Ensure UTC
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        elif current_time.tzinfo != pytz.UTC:
            current_time = current_time.astimezone(pytz.UTC)

        next_cycle_close = self.get_next_cycle_close(current_time)
        trading_window_start = self.get_trading_window_start(next_cycle_close)

        # Check if we're within the trading window
        in_trading_window = trading_window_start <= current_time < next_cycle_close

        return in_trading_window, next_cycle_close

    def time_until_next_wake_up(self, current_time: Optional[datetime] = None) -> float:
        """
        Calculate seconds until next wake up time.

        Args:
            current_time: Current time (defaults to now in UTC)

        Returns:
            Seconds until next wake up time
        """
        if current_time is None:
            current_time = datetime.now(pytz.UTC)

        # Ensure UTC
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        elif current_time.tzinfo != pytz.UTC:
            current_time = current_time.astimezone(pytz.UTC)

        in_trading_window, next_cycle_close = self.should_be_trading_now(current_time)

        if in_trading_window:
            # Already in trading window, no need to sleep
            return 0

        # Calculate time until next wake up
        wake_up_time = self.get_wake_up_time(next_cycle_close)
        time_diff = wake_up_time - current_time
        return max(0, time_diff.total_seconds())

    def get_time_remaining_in_cycle(self, current_time: Optional[datetime] = None) -> Optional[float]:
        """
        Get time remaining in current trading cycle in seconds.

        Args:
            current_time: Current time (defaults to now in UTC)

        Returns:
            Seconds remaining until cycle close, or None if not in trading window
        """
        if current_time is None:
            current_time = datetime.now(pytz.UTC)

        # Ensure UTC
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        elif current_time.tzinfo != pytz.UTC:
            current_time = current_time.astimezone(pytz.UTC)

        in_trading_window, next_cycle_close = self.should_be_trading_now(current_time)

        if not in_trading_window:
            return None

        time_diff = next_cycle_close - current_time
        return max(0, time_diff.total_seconds())

    def sleep_until_next_cycle(self, current_time: Optional[datetime] = None) -> None:
        """
        Sleep until the next trading cycle begins.

        Args:
            current_time: Current time (defaults to now in UTC)
        """
        sleep_seconds = self.time_until_next_wake_up(current_time)

        if sleep_seconds > 0:
            next_cycle_close = self.get_next_cycle_close(current_time)
            wake_up_time = self.get_wake_up_time(next_cycle_close)

            print(f"Sleeping for {sleep_seconds:.0f} seconds until {wake_up_time} UTC")
            print(f"Next cycle closes at {next_cycle_close} UTC")

            time.sleep(sleep_seconds)

    def get_cycle_id(self, cycle_close_time: datetime) -> str:
        """
        Generate a unique identifier for a trading cycle.

        Args:
            cycle_close_time: When the cycle closes

        Returns:
            Unique cycle identifier
        """
        return cycle_close_time.strftime("%Y%m%d_%H%M")