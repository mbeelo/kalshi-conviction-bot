#!/usr/bin/env python3
"""Monitor script to check bot activity and logs."""

import time
import json
import os
from datetime import datetime
import pytz

def monitor_logs():
    """Monitor log files for bot activity."""
    print("🔍 Monitoring Conviction Bot Activity")
    print("=" * 50)

    logs_dir = "logs"
    poll_log = os.path.join(logs_dir, "poll_data.jsonl")
    trade_log = os.path.join(logs_dir, "trade_data.jsonl")

    # Check if logs directory exists
    if not os.path.exists(logs_dir):
        print("⚠️  Logs directory not found yet...")
        return

    # Monitor poll data
    if os.path.exists(poll_log):
        print(f"\n📊 Recent polling data:")
        try:
            with open(poll_log, 'r') as f:
                lines = f.readlines()
                # Show last 5 entries
                for line in lines[-5:]:
                    entry = json.loads(line.strip())
                    timestamp = entry.get('timestamp', '')
                    yes_ask = entry.get('yes_ask', 0)
                    time_remaining = entry.get('time_remaining', 0)
                    cycle_id = entry.get('cycle_id', '')

                    print(f"  {timestamp[:19]} | Cycle: {cycle_id} | YES: ${yes_ask:.4f} | Time: {time_remaining:.0f}s")
        except Exception as e:
            print(f"Error reading poll log: {e}")
    else:
        print("📊 No poll data yet...")

    # Monitor trade data
    if os.path.exists(trade_log):
        print(f"\n💰 Trade activity:")
        try:
            with open(trade_log, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    entry = json.loads(line.strip())
                    print(f"  🎯 {entry}")
        except Exception as e:
            print(f"Error reading trade log: {e}")
    else:
        print("💰 No trades yet...")

def main():
    """Monitor bot for a period."""
    start_time = time.time()
    duration_minutes = 25

    print(f"🚀 Starting {duration_minutes}-minute test of Conviction Bot")
    print(f"Current time: {datetime.now(pytz.UTC)} UTC")

    iteration = 0
    while time.time() - start_time < duration_minutes * 60:
        iteration += 1
        print(f"\n--- Check #{iteration} at {datetime.now(pytz.UTC).strftime('%H:%M:%S')} UTC ---")

        monitor_logs()

        # Wait 30 seconds between checks
        time.sleep(30)

    print(f"\n🎉 {duration_minutes}-minute test completed!")

    # Final summary
    print("\n📋 Final Summary:")
    monitor_logs()

if __name__ == "__main__":
    main()