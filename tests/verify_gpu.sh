#!/bin/bash

echo "Starting GPU monitoring..."
echo "Open a new terminal and run: sudo powermetrics --samplers gpu_power -i 500"
echo ""
echo "Then come back here and press Enter to send a test inference request..."
read -p ""

echo "Sending inference request (watch for GPU power spike)..."
curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Count from 1 to 100"}],
    "max_tokens": 500
  }' | python3 -m json.tool

echo ""
echo "Check the powermetrics terminal - you should see GPU power usage spike!"
