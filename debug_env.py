#!/usr/bin/env python3
"""Debug script to check Railway environment variables."""

import os
import sys

print("=== RAILWAY ENVIRONMENT DEBUG ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print()

print("=== ALL ENVIRONMENT VARIABLES ===")
for key, value in sorted(os.environ.items()):
    # Hide sensitive values but show if they exist
    if any(secret in key.upper() for secret in ['KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
        print(f"{key}={'*' * len(value) if value else 'EMPTY'}")
    else:
        print(f"{key}={value}")

print()
print("=== KALSHI SPECIFIC VARIABLES ===")
kalshi_vars = ['KALSHI_API_KEY_ID', 'KALSHI_DEMO', 'KALSHI_PRIVATE_KEY_PATH', 'KALSHI_PRIVATE_KEY_BASE64']
for var in kalshi_vars:
    value = os.getenv(var)
    if var == 'KALSHI_PRIVATE_KEY_BASE64':
        print(f"{var}={'SET (' + str(len(value)) + ' chars)' if value else 'NOT SET'}")
    else:
        print(f"{var}={value if value else 'NOT SET'}")

print()
print("=== RAILWAY DETECTION ===")
railway_vars = ['RAILWAY_ENVIRONMENT_ID', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID']
for var in railway_vars:
    value = os.getenv(var)
    print(f"{var}={value if value else 'NOT SET'}")

print("=== DEBUG COMPLETE ===")