#!/bin/bash
# Complete Tool Calling Flow with curl
# Demonstrates multi-turn conversation

echo "============================================"
echo "Complete Tool Calling Example with curl"
echo "============================================"
echo ""

# Step 1: Send initial request with tools
echo "📤 STEP 1: Sending request to LLM with tools..."
echo ""

RESPONSE_1=$(curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "messages": [
      {"role": "user", "content": "What is 123 * 456?"}
    ],
    "tools": [{
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression",
        "parameters": {
          "type": "object",
          "properties": {
            "expr": {"type": "string"}
          },
          "required": ["expr"]
        }
      }
    }],
    "tool_choice": "auto"
  }')

echo "📥 STEP 1 Response:"
echo "$RESPONSE_1" | python3 -m json.tool
echo ""

# Extract tool call details
TOOL_CALL_ID=$(echo "$RESPONSE_1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['tool_calls'][0]['id'])")
FUNCTION_NAME=$(echo "$RESPONSE_1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['tool_calls'][0]['function']['name'])")
FUNCTION_ARGS=$(echo "$RESPONSE_1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['tool_calls'][0]['function']['arguments'])")
EXPRESSION=$(echo "$FUNCTION_ARGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['expr'])")

echo "🔧 STEP 2: Executing tool locally..."
echo "   Function: $FUNCTION_NAME"
echo "   Expression: $EXPRESSION"

# Execute the calculation
RESULT=$(python3 -c "print($EXPRESSION)")
echo "   Result: $RESULT"
echo ""

# Step 3: Send tool result back to get final answer
echo "📤 STEP 3: Sending tool result back to LLM..."
echo ""

RESPONSE_2=$(curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mlx-community/Llama-3.2-3B-Instruct-4bit\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"What is 123 * 456?\"},
      {
        \"role\": \"assistant\",
        \"content\": null,
        \"tool_calls\": [{
          \"id\": \"$TOOL_CALL_ID\",
          \"type\": \"function\",
          \"function\": {
            \"name\": \"$FUNCTION_NAME\",
            \"arguments\": $(echo "$FUNCTION_ARGS" | python3 -m json.tool -c)
          }
        }]
      },
      {
        \"role\": \"tool\",
        \"tool_call_id\": \"$TOOL_CALL_ID\",
        \"name\": \"$FUNCTION_NAME\",
        \"content\": \"$RESULT\"
      }
    ]
  }")

echo "📥 STEP 3 Response:"
echo "$RESPONSE_2" | python3 -m json.tool
echo ""

# Extract and display final answer
FINAL_ANSWER=$(echo "$RESPONSE_2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['content'])")
echo "============================================"
echo "✅ FINAL ANSWER: $FINAL_ANSWER"
echo "============================================"
