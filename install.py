#!/usr/bin/env python3
"""Installation script for Conviction Bot."""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "requests>=2.31.0",
            "python-dotenv>=1.0.0",
            "pytz>=2023.3"
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Try running: pip install requests python-dotenv pytz")
        return False

def check_environment():
    """Check if environment is set up correctly."""
    print("🔍 Checking environment...")

    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - bot may not work without Kalshi credentials")

    return True

def main():
    """Run installation."""
    print("🚀 Installing Conviction Bot")
    print("-" * 40)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Check environment
    check_environment()

    print("\n🎉 Installation complete!")
    print("\n📋 Next steps:")
    print("1. Test the bot logic: python test_logic.py")
    print("2. Run the bot: python conviction_bot.py")
    print("\n📊 The bot will:")
    print("- Monitor Kalshi BTC 15-min markets")
    print("- If yes_ask >= $0.95 → buy YES contracts")
    print("- If yes_ask <= $0.05 → buy NO contracts")
    print("- Log all activity to logs/ directory")
    print("- Only simulate trades (paper trading)")

if __name__ == "__main__":
    main()