#!/bin/bash

# Test Tesla stock historical data (last 10 months)

echo "========================================================================"
echo "Testing Tesla (TSLA) Historical Stock Data - Last 10 Months"
echo "========================================================================"
echo ""

curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Show me Tesla (TSLA) stock price for the last 10 months in a table and chart"}],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_stock_history",
          "description": "Get historical stock price data with chart and table",
          "parameters": {
            "type": "object",
            "properties": {
              "symbol": {"type": "string", "description": "Stock ticker symbol"},
              "period": {"type": "string", "enum": ["1mo", "3mo", "6mo", "1y", "10mo"], "description": "Time period"},
              "interval": {"type": "string", "enum": ["1d", "1wk", "1mo"], "description": "Data interval"}
            },
            "required": ["symbol"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "max_tokens": 500
  }' | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)

    # Pretty print the response
    print(json.dumps(data, indent=2))

    # Check if model called the tool
    if 'choices' in data and len(data['choices']) > 0:
        message = data['choices'][0].get('message', {})

        if 'tool_calls' in message:
            print('\n' + '=' * 70)
            print('✅ SUCCESS: Model correctly identified need for historical data')
            print('=' * 70)
            tool_calls = message['tool_calls']
            for tc in tool_calls:
                print(f\"Tool Called: {tc['function']['name']}\")
                print(f\"Arguments: {tc['function']['arguments']}\")
        else:
            print('\n⚠️  Model did not call tool')
            print(f\"Response: {message.get('content', 'No content')}\")

except json.JSONDecodeError as e:
    print(f'❌ JSON Error: {e}')
    print(sys.stdin.read())
except Exception as e:
    print(f'❌ Error: {e}')
"
