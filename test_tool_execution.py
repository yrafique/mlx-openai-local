#!/usr/bin/env python3
"""
Complete Tool Calling Example with MLX Omni Server
Demonstrates the full multi-turn conversation flow
"""

import json
from openai import OpenAI

# Configure client to use local MLX Omni Server
client = OpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key"
)

# Define the tool/function
tools = [{
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression",
        "parameters": {
            "type": "object",
            "properties": {
                "expr": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expr"]
        }
    }
}]

# Tool execution function
def execute_tool(function_name: str, arguments: dict) -> str:
    """Execute the tool locally and return the result"""
    if function_name == "calculate":
        expr = arguments["expr"]
        try:
            result = eval(expr)  # In production, use a safe eval
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    else:
        return f"Unknown function: {function_name}"

def chat_with_tools(user_message: str):
    """Complete tool calling conversation flow"""

    print(f"\n{'='*60}")
    print(f"USER: {user_message}")
    print(f"{'='*60}\n")

    # Step 1: Send initial message with tools
    messages = [{"role": "user", "content": user_message}]

    print("📤 Step 1: Sending request to LLM with tools...")
    response = client.chat.completions.create(
        model="mlx-community/Llama-3.2-3B-Instruct-4bit",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message
    print(f"📥 Step 1 Response: finish_reason = {response.choices[0].finish_reason}")

    # Step 2: Check if tool was called
    if assistant_message.tool_calls:
        print(f"\n🔧 Step 2: LLM requested tool execution!")

        # Add assistant's tool call to messages
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })

        # Execute each tool call
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"   - Function: {function_name}")
            print(f"   - Arguments: {function_args}")

            # Execute the tool
            result = execute_tool(function_name, function_args)
            print(f"   - Result: {result}")

            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": result
            })

        # Step 3: Send tool results back to get final answer
        print(f"\n📤 Step 3: Sending tool results back to LLM...")
        final_response = client.chat.completions.create(
            model="mlx-community/Llama-3.2-3B-Instruct-4bit",
            messages=messages
        )

        final_message = final_response.choices[0].message.content
        print(f"📥 Step 3 Response: finish_reason = {final_response.choices[0].finish_reason}")
        print(f"\n✅ FINAL ANSWER: {final_message}\n")

    else:
        # No tool call needed, direct response
        print(f"\n✅ DIRECT ANSWER: {assistant_message.content}\n")

if __name__ == "__main__":
    # Test 1: Math calculation (should use tool)
    chat_with_tools("What is 123 * 456?")

    # Test 2: Another calculation
    chat_with_tools("Calculate 15 * 23 + 47")

    # Test 3: Direct question (no tool needed)
    chat_with_tools("What is the capital of France?")
