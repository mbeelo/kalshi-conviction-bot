#!/usr/bin/env python3
"""Debug script to test market client."""

from market_client import KalshiMarketClient

def main():
    client = KalshiMarketClient()

    print("🔍 Testing Market Client")
    print("=" * 40)

    # Test finding active market
    print("1. Finding active market...")
    active_market = client.find_active_market()
    if active_market:
        print(f"✅ Found active market: {active_market.get('ticker')}")
        print(f"   Status: {active_market.get('status')}")
        print(f"   Close time: {active_market.get('close_time')}")
    else:
        print("❌ No active market found")
        return

    # Test getting market data
    ticker = active_market.get('ticker')
    print(f"\n2. Getting detailed data for {ticker}...")
    market_data = client.get_market_data(ticker)
    if market_data:
        print(f"✅ Got market data")
        print(f"   Raw response keys: {list(market_data.keys())}")
    else:
        print("❌ Failed to get market data")
        return

    # Test parsing
    print(f"\n3. Parsing market data...")
    parsed_data = client.parse_market_data(market_data)
    if parsed_data:
        print(f"✅ Parsed successfully:")
        for key, value in parsed_data.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Failed to parse market data")

    # Test current market state
    print(f"\n4. Getting current market state...")
    current_state = client.get_current_market_state()
    if current_state:
        print(f"✅ Current state:")
        for key, value in current_state.items():
            print(f"   {key}: {value}")

        # Test trading logic
        yes_ask = current_state['yes_ask']
        print(f"\n5. Trading logic test with yes_ask = {yes_ask}:")
        if yes_ask >= 0.95:
            print(f"   → Would BUY YES at ${yes_ask}")
        elif yes_ask <= 0.05:
            print(f"   → Would BUY NO at ${1.0 - yes_ask} (calculated from 1 - yes_ask)")
        else:
            print(f"   → NO TRADE (yes_ask = {yes_ask})")
    else:
        print("❌ Failed to get current market state")

if __name__ == "__main__":
    main()