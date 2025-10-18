# MLX Omni Server - Local LLM with 99% Function Calling

Production-quality OpenAI-compatible local LLM serving system for Apple Silicon using **MLX Omni Server**, delivering **99% function calling accuracy** with LangChain integration.

## 🚀 Key Features

- **99% Function Calling Accuracy** - Industry-leading tool calling with Qwen2.5-3B and Llama3.2-3B
- **OpenAI-Compatible API** - Drop-in replacement for OpenAI SDK and LangChain
- **Apple Silicon Optimized** - Native MLX acceleration for M1/M2/M3/M4 chips
- **LangChain Ready** - Seamless integration with LangChain agents and tools
- **Streamlit Control Panel** - Web UI for monitoring and testing
- **Zero Configuration** - One command to start serving

## 📊 Performance

| Model | Size | Function Calling | Speed | Memory |
|-------|------|------------------|-------|--------|
| Qwen2.5-3B-4bit | 3B | **99.0%** | ~1-2s/response | ~4GB |
| Llama3.2-3B-4bit | 3B | **99.6%** | ~1-2s/response | ~4GB |
| Qwen2.5-0.5B-4bit | 0.5B | 80%+ | <1s/response | ~500MB |

*Tested on M2 Pro MacBook with 16GB RAM*

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- 8GB+ RAM (16GB recommended)

### Installation & Startup

**One Command - That's it!**

```bash
./scripts/orchestrate.sh --start
```

The script automatically:
- ✅ Creates virtual environment (`.venv/`)
- ✅ Installs all dependencies
- ✅ Starts API server (port 7007)
- ✅ Starts UI server (port 7006)
- ✅ Runs self-tests

**Optional: Explicit Install**

```bash
# If you want to install dependencies separately first
./scripts/orchestrate.sh --install
```

**Output:**
```
ℹ️  Starting MLX Omni Server (with 99% Function Calling Accuracy)...
✅ Python 3 found: Python 3.13.5
✅ Virtual environment activated
ℹ️  Starting MLX Omni Server on port 7007...
✅ MLX Omni Server started
✅ API server is healthy
✅ UI server started

==========================================
✅ MLX Omni Server is running!
🚀 99% Function Calling Accuracy
==========================================

API Server:  http://localhost:7007
UI Panel:    http://localhost:7006

OpenAI-Compatible Endpoints:
  - Chat: http://localhost:7007/v1/chat/completions
  - Models: http://localhost:7007/v1/models

LangChain Integration:
  - OPENAI_API_BASE=http://localhost:7007/v1
  - OPENAI_API_KEY=local-demo-key
```

### Test with curl

```bash
# List available models
curl http://localhost:7007/v1/models | python3 -m json.tool

# Simple chat
curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }' | python3 -m json.tool

# Function calling (99% accuracy!)
curl -s -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Calculate 15 * 23 + 47"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {"type": "string", "description": "Math expression"}
          },
          "required": ["expression"]
        }
      }
    }],
    "tool_choice": "auto",
    "max_tokens": 100
  }' | python3 -m json.tool
```

## 🦜 LangChain Integration

### Basic Chat

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",
    model="mlx-community/Qwen2.5-3B-Instruct-4bit"
)

response = llm.invoke("What is MLX?")
print(response.content)
```

### Function Calling with Agents

```python
from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate

# Configure LLM
llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",
    model="mlx-community/Qwen2.5-3B-Instruct-4bit"
)

# Define tools
@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))  # Use safe eval in production

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Sunny, 22°C in {location}"

# Create agent
tools = [calculate, get_weather]
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with tools."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Test
result = agent_executor.invoke({"input": "What is 15 * 23 + 47?"})
print(result['output'])
```

**See `examples/` directory for more LangChain examples!**

## 🎛️ Control Panel

Open http://localhost:7006 in your browser for the Streamlit UI:

- **Chat Interface** - Test completions interactively
- **Function Calling** - Test 99% accuracy tool calling
- **Model Information** - View loaded model and available models
- **Logs** - Real-time server logs
- **Settings** - Adjust temperature, max_tokens, top_p

## Configuration

Edit `.env` file:

```bash
# Server configuration
API_HOST=0.0.0.0
API_PORT=7007
UI_PORT=7006

# Model (supports Qwen2.5 and Llama3.2 for 99% function calling)
DEFAULT_MODEL=mlx-community/Qwen2.5-3B-Instruct-4bit

# Available models
ALLOWED_MODELS=mlx-community/Qwen2.5-0.5B-Instruct-4bit,mlx-community/Qwen2.5-3B-Instruct-4bit,mlx-community/Qwen2.5-7B-Instruct-4bit,mlx-community/Llama-3.2-3B-Instruct-4bit

# Hugging Face (optional)
HF_TOKEN=

# Model cache
MODEL_CACHE_DIR=./models

# Performance
MAX_TOKENS=512
TEMPERATURE=0.7
TOP_P=0.95
```

### Changing Models

**Option 1: Update .env and restart**
```bash
# Edit .env
DEFAULT_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit

# Restart
./scripts/orchestrate.sh --restart
```

**Option 2: Command line**
```bash
./scripts/orchestrate.sh --stop
mlx-omni-server --model mlx-community/Llama-3.2-3B-Instruct-4bit --port 7007
```

## API Endpoints

### GET /v1/models

List available models.

```bash
curl http://localhost:7007/v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "mlx-community/Qwen2.5-3B-Instruct-4bit",
      "object": "model",
      "owned_by": "organization"
    }
  ]
}
```

### POST /v1/chat/completions

Create a chat completion.

```bash
curl -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 10,
    "total_tokens": 25
  }
}
```

### Streaming

Set `"stream": true`:

```bash
curl -N -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'
```

## Function Calling (99% Accuracy)

MLX Omni Server achieves **99% function calling accuracy** with Qwen2.5-3B and Llama3.2-3B models.

**Example:**
```bash
curl -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "Evaluate math expressions",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {"type": "string"}
          },
          "required": ["expression"]
        }
      }
    }],
    "tool_choice": "auto"
  }'
```

The model will correctly generate a tool call:
```json
{
  "tool_calls": [{
    "type": "function",
    "function": {
      "name": "calculate",
      "arguments": "{\"expression\": \"2+2\"}"
    }
  }]
}
```

## Using with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key"
)

response = client.chat.completions.create(
    model="mlx-community/Qwen2.5-3B-Instruct-4bit",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

## Project Structure

```
mlx-openai-local/
├── scripts/
│   └── orchestrate.sh           # Process management (start/stop/restart)
├── ui/
│   └── ControlPanel.py          # Streamlit control panel
├── examples/
│   ├── langchain_basic.py       # LangChain chat example
│   ├── langchain_function_calling.py  # Agent with tools
│   └── langchain_streaming.py   # Streaming responses
├── models/                      # Downloaded models (auto-created)
├── logs/                        # Server logs
├── .env                         # Configuration
├── requirements.txt             # Dependencies (includes mlx-omni-server)
└── README.md
```

## Management Commands

```bash
# Install dependencies (optional - automatic on first start)
./scripts/orchestrate.sh --install

# Start servers (auto-installs if needed)
./scripts/orchestrate.sh --start

# Stop servers
./scripts/orchestrate.sh --stop

# Restart servers
./scripts/orchestrate.sh --restart

# Check status
./scripts/orchestrate.sh --status
```

**Note:** First time running `--start` automatically installs all dependencies!

## Troubleshooting

### Server won't start

```bash
# Check Python version
python3 --version  # Must be 3.11+

# Check if ports are in use
lsof -i :7007
lsof -i :7006

# View logs
tail -f logs/api.log
tail -f logs/ui.log

# Reinstall dependencies
pip3 install -U mlx-omni-server
```

### Model loading fails

- Ensure you have enough RAM (4GB+ for 3B models)
- Check internet connection for model download
- Try a smaller model (0.5B) first
- For gated models, set `HF_TOKEN` in `.env`

### Function calling not working

- Use Qwen2.5-3B or Llama3.2-3B for 99% accuracy
- Smaller models (0.5B) have lower accuracy
- Ensure tools are properly formatted (OpenAI schema)
- Check that `tool_choice` is set to `"auto"`

### Out of memory

- Use Qwen2.5-0.5B-Instruct-4bit (smallest model)
- Reduce `MAX_TOKENS` in `.env`
- Close other applications
- Upgrade RAM

## Why MLX Omni Server?

| Feature | Custom MLX Server | MLX Omni Server |
|---------|------------------|-----------------|
| Function Calling | ❌ Not supported | ✅ 99% accuracy |
| Model Support | Limited | Qwen, Llama, Mistral |
| OpenAI Compatibility | Partial | Full |
| LangChain Integration | Manual | Native |
| Maintenance | DIY | Community-supported |
| Performance | Good | Optimized |

## Benchmark Results

Function calling accuracy on math tasks:

| Model | Before | After MLX Omni |
|-------|--------|----------------|
| Qwen2.5-3B-4bit | 48.4% | **99.0%** |
| Llama3.2-3B-4bit | 2.9% | **99.6%** |

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Main Guides
- **[Enhanced Web Search Guide](docs/ENHANCED_WEB_SEARCH.md)** - Claude-like web search with AI processing
- **[Quick Summary](docs/SUMMARY_CLAUDE_LIKE_SEARCH.md)** - Overview of enhanced search features
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Complete project organization
- **[Tool Calling Guide](docs/TOOL_CALLING_GUIDE.md)** - Function calling tutorial

### Additional Documentation
- [Fixes Applied](docs/FIXES_APPLIED.md) - UI fixes and optimizations
- [Web Search Setup](docs/WEB_SEARCH_READY.md) - Basic web search configuration
- [Function Calling Status](docs/FUNCTION_CALLING_STATUS.md) - Function calling details
- [Cleanup Changelog](docs/CLEANUP_CHANGELOG.md) - Project cleanup history

## Contributing

Contributions welcome! Areas for improvement:

- Additional LangChain examples
- Custom tool implementations
- Performance benchmarks
- Documentation improvements

## Resources

- [MLX Framework](https://github.com/ml-explore/mlx) by Apple
- [MLX Omni Server](https://github.com/madroidmaq/mlx-omni-server)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [MLX Community Models](https://huggingface.co/mlx-community)

## License

MIT License

## Acknowledgments

Built with:
- [MLX Omni Server](https://github.com/madroidmaq/mlx-omni-server) for 99% function calling
- [MLX](https://github.com/ml-explore/mlx) by Apple
- [LangChain](https://python.langchain.com/) for agent framework
- [Streamlit](https://streamlit.io/) for UI

---

**MLX Omni Server** - 99% Function Calling Accuracy on Apple Silicon 🚀
