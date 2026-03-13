#!/usr/bin/env python3
"""Quick monitor to watch for bot activity."""

import time
import json
import os
from datetime import datetime

def watch_logs():
    """Watch for new log entries."""
    log_file = "logs/poll_data.jsonl"

    if not os.path.exists(log_file):
        print("No log file yet...")
        return

    with open(log_file, 'r') as f:
        lines = f.readlines()

    # Get last few entries
    for line in lines[-3:]:
        try:
            entry = json.loads(line.strip())
            timestamp = entry.get('timestamp', '')[:19]  # Just date/time

            if entry.get('type') == 'poll':
                yes_ask = entry.get('yes_ask', 0)
                time_remaining = entry.get('time_remaining', 0)
                ticker = entry.get('ticker', '')
                print(f"📊 {timestamp} | {ticker} | YES: ${yes_ask:.4f} | Time: {time_remaining:.0f}s")

            elif entry.get('type') == 'bot_event':
                event_type = entry.get('event_type', '')
                message = entry.get('message', '')
                print(f"🤖 {timestamp} | {event_type}: {message}")

            elif entry.get('type') == 'error':
                error_type = entry.get('error_type', '')
                print(f"❌ {timestamp} | {error_type}")

        except:
            pass

def main():
    print("👀 Watching Conviction Bot...")
    print(f"Current time: {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    print("Waiting for trading window to start at 04:25 UTC...")
    print("=" * 60)

    while True:
        watch_logs()
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    main()