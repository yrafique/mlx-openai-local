#!/bin/bash

# Complete curl test for enhanced web search
# This demonstrates the full tool calling flow

set -e

echo "======================================================================"
echo "Testing Enhanced Web Search with curl"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Initial request
echo -e "${BLUE}Step 1: Sending initial request...${NC}"
echo "Query: 'What's the weather in Ottawa?'"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [
      {"role": "user", "content": "What is the weather in Ottawa right now?"}
    ],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather_enhanced",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          },
          "required": ["location"]
        }
      }
    }],
    "tool_choice": "auto",
    "max_tokens": 200
  }')

echo -e "${GREEN}✓ Response received${NC}"
echo ""

# Extract tool call
TOOL_NAME=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['tool_calls'][0]['function']['name'])" 2>/dev/null || echo "")
TOOL_ARGS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['tool_calls'][0]['function']['arguments'])" 2>/dev/null || echo "")
TOOL_CALL_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['tool_calls'][0]['id'])" 2>/dev/null || echo "")

if [ -z "$TOOL_NAME" ]; then
  echo "❌ Model did not call a tool!"
  echo "Response:"
  echo "$RESPONSE" | python3 -m json.tool
  exit 1
fi

echo -e "${GREEN}✓ Model called tool: ${TOOL_NAME}${NC}"
echo "  Arguments: $TOOL_ARGS"
echo ""

# Step 2: Execute the tool
echo -e "${BLUE}Step 2: Executing tool locally...${NC}"

TOOL_RESULT=$(python3 -c "
from server.tools.enhanced_web_search import execute_enhanced_tool
import json
result = execute_enhanced_tool('$TOOL_NAME', json.loads('$TOOL_ARGS'))
print(result)
" 2>&1)

echo -e "${GREEN}✓ Tool executed${NC}"
echo ""

# Parse and display the answer
ANSWER=$(echo "$TOOL_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', 'N/A'))" 2>/dev/null || echo "Parse error")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}ANSWER:${NC}"
echo ""
echo "$ANSWER"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display sources
echo -e "${BLUE}Sources:${NC}"
echo "$TOOL_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
sources = data.get('sources', [])
for i, source in enumerate(sources, 1):
    print(f\"  {i}. {source.get('title', 'Unknown')}\")
    print(f\"     {source.get('url', '')}\")
" 2>/dev/null || echo "  (Could not parse sources)"

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ Enhanced web search test complete!${NC}"
echo "======================================================================"
