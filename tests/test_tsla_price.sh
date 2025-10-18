#!/bin/bash

# Test Tesla stock price query

echo "Testing Tesla (TSLA) stock price query..."
echo "=========================================="

curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "What is the current price of Tesla (TSLA) stock?"}],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_stock_price",
          "description": "Get real-time stock price",
          "parameters": {
            "type": "object",
            "properties": {
              "symbol": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["symbol"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "max_tokens": 300
  }' | python3 -m json.tool
