"""
Conviction Bot - Paper trading bot for Kalshi BTC 15-minute markets.

Strategy: In the final 5 minutes of each 15-minute cycle, monitor the yes_ask price.
If yes_ask >= 0.95, buy 10 YES contracts. If yes_ask <= 0.05, buy 10 NO contracts.
Hold to resolution. One trade per cycle maximum.
"""
import time
import signal
import sys
from datetime import datetime
import pytz
from typing import Optional

from market_client import KalshiMarketClient
from scheduler import TradingScheduler
from paper_trader import PaperTrader
from logger import ConvictionLogger
from config import Config


class ConvictionBot:
    """Main bot class orchestrating all components."""

    def __init__(self):
        self.market_client = KalshiMarketClient()
        self.scheduler = TradingScheduler()
        self.trader = PaperTrader()
        self.logger = ConvictionLogger(source="paper")

        self.running = False
        self.current_cycle_id = None
        self.current_ticker = None
        self.trade_entered_this_cycle = False

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}. Shutting down...")
        self.running = False

    def start(self):
        """Start the conviction bot."""
        print("🚀 Starting Conviction Bot")
        print(f"Strategy: If yes_ask_dollars >= ${Config.YES_BUY_THRESHOLD} → buy YES, if yes_ask_dollars <= ${Config.NO_BUY_THRESHOLD} → buy NO")
        print(f"Contract size: {Config.CONTRACT_QUANTITY}")
        print(f"Polling interval: {Config.POLLING_INTERVAL}s")
        print("-" * 50)

        self.running = True
        self.logger.log_bot_event("startup", "Conviction Bot started")

        try:
            self._main_loop()
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.logger.log_error("unexpected_error", str(e))
        finally:
            self._shutdown()

    def _main_loop(self):
        """Main event loop."""
        while self.running:
            try:
                current_time = datetime.now(pytz.UTC)
                in_trading_window, next_cycle_close = self.scheduler.should_be_trading_now(current_time)

                if in_trading_window:
                    self._handle_trading_window(current_time, next_cycle_close)
                else:
                    self._handle_sleep_period(current_time)

            except Exception as e:
                print(f"Error in main loop: {e}")
                self.logger.log_error("main_loop_error", str(e))
                time.sleep(Config.ERROR_RETRY_DELAY)

    def _handle_trading_window(self, current_time: datetime, cycle_close_time: datetime):
        """Handle active trading window."""
        cycle_id = self.scheduler.get_cycle_id(cycle_close_time)

        # Check if this is a new cycle
        if self.current_cycle_id != cycle_id:
            self._start_new_cycle(cycle_id, cycle_close_time)

        # Get market data
        market_data = self._get_market_data_with_retry()
        if not market_data:
            return

        # Calculate time remaining
        time_remaining = self.scheduler.get_time_remaining_in_cycle(current_time)
        if time_remaining is None:
            return

        # Log poll data
        self.logger.log_poll_data(
            timestamp=current_time,
            ticker=market_data["ticker"],
            yes_ask=market_data["yes_ask"],
            no_ask=market_data["no_ask"],  # Still log for reference
            time_remaining=time_remaining,
            cycle_id=cycle_id
        )

        # Check for trading opportunity
        if not self.trade_entered_this_cycle:
            self._check_trading_opportunity(market_data, cycle_id, current_time, time_remaining)

        # Sleep until next poll
        time.sleep(Config.POLLING_INTERVAL)

    def _handle_sleep_period(self, current_time: datetime):
        """Handle period between trading windows."""
        # Check if we have any unresolved positions to monitor
        self._check_unresolved_positions()

        # Sleep until next trading window
        sleep_time = self.scheduler.time_until_next_wake_up(current_time)
        if sleep_time > 0:
            self.scheduler.sleep_until_next_cycle(current_time)

    def _start_new_cycle(self, cycle_id: str, cycle_close_time: datetime):
        """Initialize a new trading cycle."""
        print(f"\n🔄 Starting new cycle: {cycle_id}")
        print(f"Cycle closes at: {cycle_close_time} UTC")

        self.current_cycle_id = cycle_id
        self.trade_entered_this_cycle = False

        self.logger.log_bot_event(
            "cycle_start",
            f"New trading cycle started: {cycle_id}",
            {"cycle_id": cycle_id, "close_time": cycle_close_time.isoformat()}
        )

    def _get_market_data_with_retry(self) -> Optional[dict]:
        """Get market data with retry logic."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            market_data = self.market_client.get_current_market_state()

            if market_data:
                self.current_ticker = market_data["ticker"]
                return market_data

            retry_count += 1
            if retry_count < max_retries:
                print(f"No market data found, retrying ({retry_count}/{max_retries})...")
                time.sleep(Config.ERROR_RETRY_DELAY)

        self.logger.log_error("market_data_error", "Failed to get market data after retries")
        return None

    def _check_trading_opportunity(self, market_data: dict, cycle_id: str, current_time: datetime, time_remaining: float):
        """Check if we should enter a trade."""
        yes_ask = market_data["yes_ask"]

        should_trade, side, entry_price = self.trader.should_enter_trade(yes_ask, cycle_id)

        if should_trade:
            self._enter_trade(
                cycle_id=cycle_id,
                ticker=market_data["ticker"],
                side=side,
                entry_price=entry_price,
                current_time=current_time,
                time_remaining=time_remaining
            )

    def _enter_trade(self, cycle_id: str, ticker: str, side: str, entry_price: float, current_time: datetime, time_remaining: float):
        """Enter a paper trade."""
        try:
            position = self.trader.enter_position(
                cycle_id=cycle_id,
                ticker=ticker,
                side=side,
                entry_price=entry_price,
                entry_time=current_time,
                time_remaining=time_remaining
            )

            # Log trade entry
            self.logger.log_trade_entry(
                cycle_id=cycle_id,
                ticker=ticker,
                entry_time=current_time,
                time_remaining_at_entry=time_remaining,
                side=side,
                entry_price=entry_price
            )

            self.trade_entered_this_cycle = True

        except Exception as e:
            print(f"Error entering trade: {e}")
            self.logger.log_error("trade_entry_error", str(e), cycle_id, ticker)

    def _check_unresolved_positions(self):
        """Check for unresolved positions and try to resolve them."""
        for cycle_id, position in self.trader.get_all_positions().items():
            if not position.resolved:
                result = self.market_client.wait_for_resolution(position.ticker, timeout_minutes=1)
                if result:
                    resolved_position = self.trader.resolve_position(cycle_id, result)
                    if resolved_position:
                        self.logger.log_trade_result(
                            cycle_id=cycle_id,
                            ticker=resolved_position.ticker,
                            result=result,
                            pnl=resolved_position.pnl,
                            win=resolved_position.win,
                            resolution_time=datetime.now(pytz.UTC)
                        )

    def _shutdown(self):
        """Graceful shutdown."""
        print("\n📊 Final Performance Summary:")
        self._print_performance_summary()

        self.logger.log_bot_event("shutdown", "Conviction Bot shutting down")
        print("👋 Conviction Bot stopped")

    def _print_performance_summary(self):
        """Print performance statistics."""
        stats = self.trader.get_performance_stats()
        log_stats = self.logger.get_trade_summary()

        print(f"Total Trades: {stats['total_trades']}")
        print(f"Wins: {stats['wins']}, Losses: {stats['losses']}")
        print(f"Win Rate: {stats['win_rate']:.1%}")
        print(f"Total P&L: ${stats['total_pnl']:.2f}")
        print(f"Average P&L: ${stats['avg_pnl']:.2f}")

        if stats['total_trades'] > 0:
            print(f"Best Trade: ${stats['best_trade']:.2f}")
            print(f"Worst Trade: ${stats['worst_trade']:.2f}")


def main():
    """Main entry point."""
    bot = ConvictionBot()
    bot.start()


if __name__ == "__main__":
    main()