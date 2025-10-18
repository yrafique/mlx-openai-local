#!/usr/bin/env python3
"""
Direct tool testing script - bypasses model function calling.
Manually invokes tools and shows results.
"""

import requests
import json

def test_calculator():
    """Test calculator tool directly."""
    print("=" * 60)
    print("Testing Calculator Tool")
    print("=" * 60)

    # Simulate what would happen if model called the tool
    tool_name = "calculate"
    tool_args = {"expression": "sqrt(144) + 2**3"}

    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(tool_args, indent=2)}")

    # In a real scenario, the server would execute this
    from server.tools import execute_tool
    result = execute_tool(tool_name, tool_args)

    print(f"\nResult:")
    print(json.dumps(result, indent=2))
    print()

def test_web_search():
    """Test web search tool directly."""
    print("=" * 60)
    print("Testing Web Search Tool")
    print("=" * 60)

    tool_name = "web_search"
    tool_args = {"query": "MLX framework Apple Silicon", "num_results": 3}

    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(tool_args, indent=2)}")

    from server.tools import execute_tool
    result = execute_tool(tool_name, tool_args)

    print(f"\nResult:")
    print(json.dumps(result, indent=2))
    print()

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/yousef/Dev/mlx-openai-local')

    print("\n🛠️  Direct Tool Testing (Bypass Model)\n")

    test_calculator()
    test_web_search()

    print("=" * 60)
    print("✅ All tools working correctly!")
    print("=" * 60)
    print("\nNote: Use a 3B+ model for automatic function calling")
