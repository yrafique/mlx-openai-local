#!/usr/bin/env python3
"""Quick test script to verify the model is working."""

import requests
import json

# Test chat completion
url = "http://localhost:7007/v1/chat/completions"
payload = {
    "model": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    "messages": [
        {"role": "user", "content": "Say hello in a friendly way"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
}

print("Testing chat completion with Qwen2.5-0.5B-Instruct-4bit...")
print("-" * 60)

response = requests.post(url, json=payload, timeout=120)

if response.status_code == 200:
    data = response.json()
    print("✅ Success!")
    print("\nResponse:")
    print(json.dumps(data, indent=2))

    if "choices" in data and len(data["choices"]) > 0:
        content = data["choices"][0]["message"]["content"]
        print("\n" + "=" * 60)
        print("ASSISTANT:", content)
        print("=" * 60)

        usage = data.get("usage", {})
        print(f"\nTokens used: {usage.get('total_tokens', 'N/A')}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
