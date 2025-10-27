#!/usr/bin/env python3
"""
Test script to verify stock queries work with company names
"""

from server.tools.financial_data import get_stock_price
import json

print("=" * 80)
print("Testing Stock Price Tool with Company Names")
print("=" * 80)

# Test cases
test_queries = [
    ("AAPL", "Ticker symbol"),
    ("Apple", "Company name (lowercase)"),
    ("apple", "Company name (lowercase)"),
    ("MSFT", "Microsoft ticker"),
    ("Microsoft", "Microsoft company name"),
    ("TSLA", "Tesla ticker"),
    ("tesla", "Tesla company name (lowercase)"),
    ("Google", "Google company name"),
    ("NVDA", "Nvidia ticker")
]

for symbol, description in test_queries:
    print(f"\n{'─' * 80}")
    print(f"Query: {symbol} ({description})")
    print(f"{'─' * 80}")

    result = get_stock_price(symbol)
    result_data = json.loads(result)

    if result_data.get("status") == "success":
        print(f"✅ SUCCESS")
        print(f"   Symbol: {result_data['symbol']}")
        print(f"   Price: ${result_data['price']}")
        print(f"   Change: {result_data['change']} ({result_data['change_percent']}%)")
        print(f"   Exchange: {result_data['exchange']}")
        print(f"   Source: {result_data['source']}")
    else:
        print(f"❌ ERROR")
        print(f"   {result_data.get('error', 'Unknown error')}")

print(f"\n{'=' * 80}")
print("Test Complete!")
print("=" * 80)
