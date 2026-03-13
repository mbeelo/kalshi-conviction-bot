#!/usr/bin/env python3
"""
Debug tool to test Kalshi order submission and environment configuration.
"""
import os
from datetime import datetime
from kalshi_auth import KalshiAuth
from live_trader import LiveTrader
from market_client import KalshiMarketClient

def test_environment():
    """Test environment configuration."""
    print("=== ENVIRONMENT CONFIGURATION TEST ===")
    print(f"KALSHI_DEMO: {os.getenv('KALSHI_DEMO', 'NOT SET')}")
    print(f"KALSHI_API_KEY_ID: {os.getenv('KALSHI_API_KEY_ID', 'NOT SET')}")
    print(f"KALSHI_PRIVATE_KEY_PATH: {os.getenv('KALSHI_PRIVATE_KEY_PATH', 'NOT SET')}")
    print(f"KALSHI_PRIVATE_KEY_BASE64: {'SET' if os.getenv('KALSHI_PRIVATE_KEY_BASE64') else 'NOT SET'}")
    print(f"RAILWAY_ENVIRONMENT_ID: {os.getenv('RAILWAY_ENVIRONMENT_ID', 'NOT SET')}")
    print("")

def test_auth():
    """Test Kalshi authentication."""
    print("=== AUTHENTICATION TEST ===")
    try:
        auth = KalshiAuth()
        print(f"Demo mode: {auth.is_demo_mode()}")
        print(f"Base URL: {auth.get_base_url()}")
        print(f"API Key ID: {auth.api_key_id}")
        print(f"Private key loaded: {auth.private_key is not None}")

        # Test auth headers
        headers = auth.get_auth_headers("GET", "/portfolio/balance")
        print(f"Auth headers generated: {bool(headers)}")
        print("✅ Authentication setup successful")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def test_market_data():
    """Test market data retrieval."""
    print("\n=== MARKET DATA TEST ===")
    try:
        client = KalshiMarketClient()
        market = client.get_current_market_state()
        if market:
            print(f"✅ Market data retrieved:")
            print(f"   Ticker: {market['ticker']}")
            print(f"   YES ask: ${market['yes_ask']:.4f}")
            print(f"   NO ask: ${market['no_ask']:.4f}")
            print(f"   Close time: {market['close_time']}")
            return market
        else:
            print("❌ No market data found")
            return None
    except Exception as e:
        print(f"❌ Market data error: {e}")
        return None

def test_balance():
    """Test account balance retrieval."""
    print("\n=== BALANCE TEST ===")
    try:
        trader = LiveTrader()
        balance = trader.get_account_balance()
        if balance is not None:
            print(f"✅ Balance retrieved: ${balance:.2f}")
            return True
        else:
            print("❌ Could not retrieve balance")
            return False
    except Exception as e:
        print(f"❌ Balance error: {e}")
        return False

def test_order_detection():
    """Test if current market conditions would trigger an order."""
    print("\n=== ORDER SIGNAL TEST ===")
    try:
        trader = LiveTrader()
        client = KalshiMarketClient()
        market = client.get_current_market_state()

        if not market:
            print("❌ No market data for order test")
            return False

        cycle_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        should_trade, side, entry_price = trader.should_enter_trade(market['yes_ask'], cycle_id)

        print(f"Current market: {market['ticker']}")
        print(f"YES ask: ${market['yes_ask']:.4f}")
        print(f"Trading signal: {should_trade}")

        if should_trade:
            print(f"🎯 SIGNAL DETECTED: {side} at ${entry_price:.4f}")
            return True, side, entry_price, market
        else:
            print("⏳ No trading signal (price between 0.06 and 0.94)")
            return False, None, None, market

    except Exception as e:
        print(f"❌ Order detection error: {e}")
        return False, None, None, None

def main():
    """Run all diagnostic tests."""
    print("🔍 KALSHI ORDER DEBUGGING TOOL")
    print("=" * 50)

    test_environment()

    auth_ok = test_auth()
    if not auth_ok:
        print("\n❌ Authentication failed - stopping tests")
        return

    market = test_market_data()
    balance_ok = test_balance()

    if market:
        has_signal, side, price, market_data = test_order_detection()

        if has_signal:
            print(f"\n⚠️  LIVE SIGNAL DETECTED!")
            print(f"   This would trigger a {side} order at ${price:.4f}")
            print(f"   Market: {market_data['ticker']}")

            # Don't actually place the order, just show what would happen
            print("\n🚫 Not placing actual order (debug mode)")

    print("\n=== DIAGNOSTIC COMPLETE ===")
    print("Check the output above for any issues with:")
    print("1. Environment variables")
    print("2. Authentication")
    print("3. Market data access")
    print("4. Balance retrieval")
    print("5. Signal detection")

if __name__ == "__main__":
    main()