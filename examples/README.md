# LangChain Integration Examples

This directory contains examples of using **MLX Omni Server** with **LangChain** on Apple Silicon.

## Prerequisites

Make sure the MLX Omni Server is running:

```bash
./scripts/orchestrate.sh --start
```

## Examples

### 1. Basic Chat (`langchain_basic.py`)

Simple chat completion and multi-turn conversations with LangChain.

```bash
python3 examples/langchain_basic.py
```

**Features:**
- Simple chat completion
- Multi-turn conversations
- System messages

### 2. Function Calling (`langchain_function_calling.py`)

Demonstrates **99% accuracy function calling** with custom tools.

```bash
python3 examples/langchain_function_calling.py
```

**Features:**
- Calculator tool
- Weather lookup tool
- Web search tool
- ReAct agent with tool calling
- Verbose output showing reasoning

**Sample output:**
```
Query: What is 15 multiplied by 23 plus 47?

> Entering new AgentExecutor chain...
> Invoking: `calculate` with `{'expression': '15 * 23 + 47'}`

The result of 15 * 23 + 47 is 392

✅ Final Answer: The result is 392
```

### 3. Streaming Responses (`langchain_streaming.py`)

Real-time streaming responses from the local model.

```bash
python3 examples/langchain_streaming.py
```

**Features:**
- Token-by-token streaming
- Real-time output
- Low latency responses

## Configuration

All examples use the environment variables from `.env`:

```bash
OPENAI_API_BASE=http://localhost:7007/v1
OPENAI_API_KEY=local-demo-key
DEFAULT_MODEL=mlx-community/Qwen2.5-3B-Instruct-4bit
```

## Custom Tool Development

You can create custom tools for LangChain:

```python
from langchain.agents import tool

@tool
def my_custom_tool(input: str) -> str:
    """Description of what this tool does."""
    # Your implementation here
    return "Result"

tools = [my_custom_tool]
```

## Performance

- **Model:** Qwen2.5-3B-Instruct-4bit
- **Function Calling Accuracy:** 99%
- **Latency:** ~1-2 seconds per response on M2 Pro
- **Memory:** ~4GB RAM

## Troubleshooting

**Server not responding:**
```bash
./scripts/orchestrate.sh --status
./scripts/orchestrate.sh --restart
```

**Function calling not working:**
- Ensure you're using Qwen2.5-3B or Llama3.2-3B (best function calling support)
- Check that tools are properly decorated with `@tool`
- Verify the agent is created with `create_tool_calling_agent`

## Next Steps

- Add more custom tools for your use case
- Fine-tune prompts for better performance
- Integrate with LangChain chains and workflows
- Build full applications with LangSmith monitoring
