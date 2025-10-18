# Tool Calling Guide

## Current Status

✅ **Tool Registry:** Working perfectly
✅ **Tool Execution:** Calculator and Web Search both functional
❌ **Automatic Tool Calling:** Requires larger model (3B+)

## Why Tool Calling Fails

The current model (`Qwen2.5-0.5B-Instruct-4bit`) is **too small** for function calling:

- **0.5B parameters**: Basic chat only
- **No function calling training**: Can't detect when to use tools
- **No JSON schema understanding**: Can't generate tool call syntax

## Solutions

### Option 1: Upgrade to Larger Model (Recommended)

**Models with Good Function Calling:**

| Model | Size | RAM | Function Calling |
|-------|------|-----|------------------|
| Qwen2.5-0.5B-Instruct-4bit | 0.5B | ~500MB | ❌ No |
| Qwen2.5-1.5B-Instruct-4bit | 1.5B | ~2GB | ⚠️ Limited |
| Qwen2.5-3B-Instruct-4bit | 3B | ~4GB | ✅ Good |
| Qwen2.5-7B-Instruct-4bit | 7B | ~8GB | ✅ Excellent |

**How to Switch:**

```bash
# 1. Edit .env
vim .env

# Change DEFAULT_MODEL to:
DEFAULT_MODEL=mlx-community/Qwen2.5-3B-Instruct-4bit

# 2. Restart server
./scripts/orchestrate.sh --restart

# 3. Test in UI
open http://localhost:7006
# Go to Tools tab → Enable Calculator → Test
```

### Option 2: Manual Tool Invocation

Test tools directly without model function calling:

```python
from server.tools import execute_tool

# Calculator
result = execute_tool("calculate", {"expression": "sqrt(144)"})
# Returns: {"success": true, "result": 12.0}

# Web Search (mock)
result = execute_tool("web_search", {"query": "Python", "num_results": 3})
# Returns mock search results
```

### Option 3: Add Real Web Search API

Replace the stub with a real search API:

**Edit `server/tools/web_search_stub.py`:**

```python
import os
import requests

def web_search(query: str, num_results: int = 3) -> Dict[str, Any]:
    """Perform real web search using SerpAPI."""

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return {"error": "SERPAPI_KEY not set in .env"}

    response = requests.get(
        "https://serpapi.com/search",
        params={
            "q": query,
            "num": num_results,
            "api_key": api_key
        }
    )

    if response.status_code == 200:
        data = response.json()
        results = []

        for item in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "snippet": item.get("snippet")
            })

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results
        }

    return {"error": f"Search failed: {response.status_code}"}
```

**Add to `.env`:**
```bash
# Get free API key from https://serpapi.com
SERPAPI_KEY=your_api_key_here
```

## Testing Function Calling

### With 3B+ Model:

```bash
# Via curl
curl -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Calculate sqrt(144) + 2^3"}],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "calculate",
          "description": "Evaluate a mathematical expression",
          "parameters": {
            "type": "object",
            "properties": {
              "expression": {"type": "string"}
            },
            "required": ["expression"]
          }
        }
      }
    ]
  }'
```

### Expected Response (3B+ model):

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_xxx",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\": \"sqrt(144) + 2**3\"}"
        }
      }]
    }
  }]
}
```

The server will then:
1. Execute the calculator tool
2. Get result: 20.0
3. Pass result back to model
4. Model generates final answer

## Current Behavior (0.5B Model)

The model responds directly instead of calling tools:

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "To calculate sqrt(144) + 2^3, first..."
    }
  }]
}
```

## Recommended Path Forward

1. **Keep 0.5B for now** - Great for basic chat, testing API
2. **Upgrade to 3B when needed** - For function calling
3. **Test with direct execution** - Use `test_direct_tool.py` script
4. **Integrate real APIs** - Replace mock search with SerpAPI/Google

## Tool Registry Architecture

The system is ready for function calling:

```
User Request
     ↓
Model (needs 3B+)
     ↓
Detects tool needed
     ↓
Generates tool call
     ↓
Server executes tool → Tool Registry
     ↓                      ↓
Tool result          (calculate, web_search, etc.)
     ↓
Model generates final response
     ↓
User gets answer
```

**Current bottleneck:** Model size (0.5B → 3B needed)

## Additional Resources

- MLX Models: https://huggingface.co/mlx-community
- OpenAI Function Calling Docs: https://platform.openai.com/docs/guides/function-calling
- Tool Implementation: `server/tools/`

**The infrastructure is perfect - just need a bigger model! 🚀**
