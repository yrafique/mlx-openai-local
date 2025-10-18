#!/bin/bash

# ============================================================================
# Smoke Test for MLX OpenAI Server
# Tests basic functionality: /v1/models and /v1/chat/completions
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="${API_URL:-http://localhost:7007/v1}"

echo "🧪 Running smoke tests against $API_URL"
echo ""

# ============================================================================
# Test 1: Health Check
# ============================================================================

echo "Test 1: Health Check"
HEALTH_RESPONSE=$(curl -s http://localhost:7007/health)

if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi

echo ""

# ============================================================================
# Test 2: List Models
# ============================================================================

echo "Test 2: List Models (/v1/models)"
MODELS_RESPONSE=$(curl -s "$API_URL/models")

if echo "$MODELS_RESPONSE" | grep -q '"object":"list"'; then
    echo -e "${GREEN}✅ Models endpoint passed${NC}"

    # Extract model IDs
    echo "Available models:"
    echo "$MODELS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for model in data.get('data', []):
    print(f\"  - {model['id']}\")
"
else
    echo -e "${RED}❌ Models endpoint failed${NC}"
    echo "$MODELS_RESPONSE"
    exit 1
fi

echo ""

# ============================================================================
# Test 3: Simple Chat Completion
# ============================================================================

echo "Test 3: Chat Completion (/v1/chat/completions)"

CHAT_PAYLOAD=$(cat <<'EOF'
{
  "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
  "messages": [
    {"role": "user", "content": "Say 'test passed' if you can read this"}
  ],
  "max_tokens": 20,
  "temperature": 0.7
}
EOF
)

CHAT_RESPONSE=$(curl -s -X POST "$API_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$CHAT_PAYLOAD")

if echo "$CHAT_RESPONSE" | grep -q '"choices"'; then
    echo -e "${GREEN}✅ Chat completion passed${NC}"

    # Extract response content
    echo "Model response:"
    echo "$CHAT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'choices' in data and len(data['choices']) > 0:
    content = data['choices'][0]['message']['content']
    print(f\"  {content}\")
    usage = data.get('usage', {})
    print(f\"  Tokens: {usage.get('total_tokens', 'N/A')}\")
"
else
    echo -e "${RED}❌ Chat completion failed${NC}"
    echo "$CHAT_RESPONSE"
    exit 1
fi

echo ""

# ============================================================================
# Test 4: Streaming Chat Completion (Optional)
# ============================================================================

echo "Test 4: Streaming Chat Completion"

STREAM_PAYLOAD=$(cat <<'EOF'
{
  "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
  "messages": [
    {"role": "user", "content": "Count to 3"}
  ],
  "max_tokens": 20,
  "stream": true
}
EOF
)

# Test streaming (just check if we get SSE chunks)
STREAM_OUTPUT=$(curl -s -N -X POST "$API_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$STREAM_PAYLOAD" | head -n 5)

if echo "$STREAM_OUTPUT" | grep -q "data:"; then
    echo -e "${GREEN}✅ Streaming test passed${NC}"
    echo "Received SSE chunks:"
    echo "$STREAM_OUTPUT" | head -n 3
else
    echo -e "${YELLOW}⚠️  Streaming test inconclusive${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All smoke tests passed!${NC}"
echo -e "${GREEN}========================================${NC}"

exit 0
