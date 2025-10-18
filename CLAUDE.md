# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MLX Omni Server - Production-quality OpenAI-compatible local LLM server for Apple Silicon with 99% function calling accuracy. Built on mlx-omni-server with comprehensive tools ecosystem, RAG capabilities, and LangChain integration.

**Key Architecture:**
- **Server**: mlx-omni-server provides OpenAI-compatible `/v1/chat/completions` and `/v1/models` endpoints
- **Tools System**: Modular registry-based architecture with 8 tool categories (50+ total tools)
- **UI**: Streamlit-based control panel for testing and monitoring
- **Configuration**: Single source of truth in `.env` file (146 settings)

## Essential Commands

### Server Management
```bash
# Start everything (auto-installs dependencies, runs self-tests)
./scripts/orchestrate.sh --start

# Stop all services
./scripts/orchestrate.sh --stop

# Restart services
./scripts/orchestrate.sh --restart

# Check service status
./scripts/orchestrate.sh --status

# Install dependencies only
./scripts/orchestrate.sh --install
```

### Development
```bash
# Use Poetry for dependency management
poetry install          # Install dependencies
poetry add <package>    # Add new dependency
poetry lock             # Update lock file

# Run UI directly (for development)
poetry run streamlit run ui/ControlPanel.py --server.port=7006

# Run tests
poetry run pytest tests/                           # All tests
poetry run pytest tests/test_chat.py              # Single test file
poetry run pytest tests/test_chat.py::test_name   # Specific test
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:7007/health

# List models
curl http://localhost:7007/v1/models | python3 -m json.tool

# Basic chat
curl -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mlx-community/Qwen2.5-3B-Instruct-4bit", "messages": [{"role": "user", "content": "Hello"}]}'

# Test function calling
curl -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "messages": [{"role": "user", "content": "Calculate 15 * 23"}],
    "tools": [{"type": "function", "function": {"name": "calculate", "description": "Math", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}}],
    "tool_choice": "auto"
  }'
```

## Architecture Deep Dive

### 1. Tools Registry System (`server/tools/registry.py`)

**Central Pattern**: All tools follow a uniform architecture:
```python
# Each tool module exports:
TOOL_DEFINITIONS = [...]  # OpenAI function calling schema
execute_<tool>_tool(function_name, arguments) -> Dict  # Executor function

# Registry aggregates all tools by category
REGISTRY = ToolsRegistry()
REGISTRY.get_all_tools(categories=["financial", "rag"])  # Filter by category
REGISTRY.execute_tool(category, function_name, args)     # Unified execution
```

**Tool Categories** (8 total):
- `code_execution`: Python execution, plots, calculations
- `financial`: Real-time stocks/crypto (Yahoo Finance, CoinGecko)
- `web_search`: Enhanced (AI-processed) web search
- `web_search_basic`: Raw DuckDuckGo results
- `formatting`: Tables, charts, data visualization
- `voice`: Speech-to-text (Whisper), text-to-speech
- `file_analysis`: CSV, Excel, JSON, images, code
- `rag`: Document/YouTube ingestion + vector search (ChromaDB)

**Adding New Tools**:
1. Create `server/tools/your_tool.py` with `TOOL_DEFINITIONS` + `execute_your_tool()`
2. Register in `server/tools/registry.py`:
   ```python
   "your_category": {
       "name": "Display Name",
       "icon": "🎯",
       "tools": YOUR_TOOL_DEFINITIONS,
       "executor": execute_your_tool
   }
   ```
3. Import in `ui/ControlPanel.py` if UI integration needed

### 2. RAG Architecture (`server/tools/rag.py`)

**Components**:
- **RAGManager**: Singleton managing ChromaDB vector store
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2` (lightweight, CPU-friendly)
- **Search**: MMR (Maximal Marginal Relevance) for diverse results
  - Fetches `fetch_k=20` candidates, returns `k=4` diverse docs
  - Balances relevance vs diversity with `lambda_mult=0.5`
- **Storage**: Persistent ChromaDB at `./chroma_db/`

**MMR vs Similarity**:
```python
# MMR (default) - diverse results
rag.query_mmr(query, k=4, fetch_k=20, lambda_mult=0.5)

# Regular similarity - most relevant only
rag.query_with_scores(query, k=4)
```

**Document Processing**:
- Chunk size: 1000 chars, overlap: 200 chars
- Supports: PDF (pypdf), TXT, MD, YouTube transcripts
- Metadata preserved (source file, video ID, etc.)

### 3. Configuration System (`.env`)

**Single Source of Truth**: All settings in `.env` (146 lines, 11 sections)

**Critical Settings**:
```bash
# Models - Use Qwen2.5/Llama3.2 for 99% function calling
DEFAULT_MODEL=mlx-community/Llama-3.2-3B-Instruct-4bit
ALLOWED_MODELS=mlx-community/Qwen2.5-3B-Instruct-4bit,...

# Performance
MAX_TOKENS=4000          # High for RAG contexts
LOG_LEVEL=info           # MUST be lowercase (argmaxtools requirement)

# Features
ENABLE_VOICE=true        # Whisper transcription
AUTO_START_UI=true       # Launch Streamlit on startup
```

**Important**: `LOG_LEVEL` must be lowercase (`info` not `INFO`) - argmaxtools compatibility.

### 4. Server Process Architecture

**Two-Process Model**:
1. **API Server** (port 7007): mlx-omni-server with OpenAI endpoints
   - Managed by mlx-omni-server binary (not our code)
   - PID tracked in `api.pid`
   - Logs to `logs/api.log`

2. **UI Server** (port 7006): Streamlit control panel
   - Our code: `ui/ControlPanel.py`
   - PID tracked in `ui.pid`
   - Logs to `logs/ui.log`

**orchestrate.sh** handles both:
- Auto-install dependencies if missing (Poetry)
- Health checks (polls `/v1/models` endpoint)
- Graceful shutdown (SIGTERM → 10s timeout → SIGKILL)
- Environment validation (Python 3.11+, virtual env)

### 5. Model Management (`server/model_manager.py`)

**Singleton Pattern**: `model_manager = ModelManager()`

**Key Features**:
- **Memory Estimation**: Pre-load check via config.json (vocab_size, hidden_size, etc.)
- **Performance Tracking**: TPS (tokens/sec), TTFT (time to first token)
- **Download Management**: HuggingFace Hub with progress tracking
- **System Stats**: MLX memory (`mx.metal.get_active_memory()`) + psutil

**Usage Pattern**:
```python
from server.model_manager import model_manager

# Check memory before loading
estimate = await model_manager.estimate_model_memory(repo_id)
if not estimate["will_fit"]:
    print(f"Needs {estimate['estimated_memory_gb']}GB, only {estimate['system_available_memory_gb']}GB available")

# Load model
info = await model_manager.load_model(repo_id)

# Get performance stats
stats = model_manager.get_performance_stats()
print(f"TPS: {stats['last_generation']['tokens_per_second']}")
```

### 6. UI Integration Patterns (`ui/ControlPanel.py`)

**Streamlit Session State Management**:
- `st.session_state.messages`: Chat history
- Tool toggles stored in component state (not session)
- Real-time updates via `st.rerun()` on changes

**Tool Integration Pattern**:
```python
# 1. Import tool executor
from server.tools.your_tool import execute_your_tool

# 2. Add toggle
enable_your_tool = st.toggle("🎯 Your Tool", value=False)

# 3. Execute in chat flow
if enable_your_tool:
    result = execute_your_tool(function_name, arguments)
    result_data = json.loads(result) if isinstance(result, str) else result
    # Handle result_data
```

**Performance Metrics Display**:
Located in sidebar → Model Information:
```python
perf_stats = model_manager.get_performance_stats()
st.metric("⚡ Performance", f"{tps:.1f} tok/s", delta=f"{tokens} tokens")
```

### 7. Testing Architecture

**Test Files**:
- `tests/test_chat.py`: Basic chat completions
- `tests/test_model.py`: Model endpoints
- `tests/test_direct_tool.py`: Direct tool execution
- `tests/comprehensive_test_suite.py`: Full integration tests

**Running Specific Tests**:
```bash
# Test single function
poetry run pytest tests/test_chat.py::test_basic_completion -v

# Test with specific model
MODEL=mlx-community/Qwen2.5-0.5B-Instruct-4bit poetry run pytest tests/

# Debug mode
poetry run pytest tests/ -vv --tb=short
```

## Critical Implementation Notes

### Function Calling Best Practices

**Model Selection**: Only Qwen2.5-3B and Llama3.2-3B achieve 99% accuracy
- Qwen2.5-0.5B: ~80% (acceptable for simple tools)
- Other models: <50% (do not use for production)

**Tool Definition Schema**: Must match OpenAI format exactly:
```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "Clear, specific description",  # Critical for accuracy
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "What it does"}
            },
            "required": ["param"]
        }
    }
}
```

### RAG Implementation Details

**MMR Search** (default enabled in UI):
- Always prefer MMR over similarity search for production
- Reduces redundancy in retrieved documents
- Lambda_mult = 0.5 balances relevance/diversity (don't change unless testing)

**Document Ingestion**:
- PDFs must have text (no OCR support)
- YouTube videos must have English captions
- Clear collection before switching contexts (to avoid contamination)

**Performance**:
- First query: ~2-3s (includes embedding generation)
- Subsequent queries: <1s (embeddings cached)
- Collection stats: `get_knowledge_base_stats()` shows document count

### Logging Configuration

**Log Level Format**: MUST be lowercase for argmaxtools compatibility
```bash
# Correct
LOG_LEVEL=info

# Incorrect (will fail)
LOG_LEVEL=INFO
```

**Log Files**:
- `logs/api.log`: mlx-omni-server output
- `logs/ui.log`: Streamlit output
- Both rotated automatically (no size limit configured)

### Dependency Management

**Poetry Quirks**:
- NumPy pinned to `<2.0.0` (ChromaDB incompatibility)
- LangChain split into multiple packages (langchain-core, langchain-text-splitters)
- Whisper requires system-level ffmpeg (not in pyproject.toml)

**Installation Order**:
1. Poetry creates virtual env in `.venv/`
2. `poetry install` installs all dependencies
3. First run downloads model (4-8GB depending on size)

## Common Development Workflows

### Adding a New Tool

1. Create tool module:
```python
# server/tools/my_tool.py
MY_TOOL_DEFINITIONS = [{
    "type": "function",
    "function": {
        "name": "my_function",
        "description": "Does something useful",
        "parameters": {...}
    }
}]

def execute_my_tool(function_name: str, arguments: dict) -> dict:
    if function_name == "my_function":
        # Implementation
        return {"success": True, "result": "..."}
    return {"error": "Unknown function"}
```

2. Register in `server/tools/registry.py`:
```python
from .my_tool import MY_TOOL_DEFINITIONS, execute_my_tool

self.tool_categories["my_category"] = {
    "name": "My Tools",
    "icon": "🔧",
    "tools": MY_TOOL_DEFINITIONS,
    "executor": execute_my_tool
}
```

3. Add UI toggle (optional):
```python
# ui/ControlPanel.py
enable_my_tool = st.toggle("🔧 My Tool")
if enable_my_tool:
    selected_tools.extend(MY_TOOL_DEFINITIONS)
```

### Debugging Server Issues

**Check process status**:
```bash
# View PIDs
cat api.pid ui.pid

# Check if processes running
ps aux | grep mlx-omni-server
ps aux | grep streamlit

# Kill stuck processes
kill $(cat api.pid ui.pid)
```

**Check logs**:
```bash
# Real-time API logs
tail -f logs/api.log

# Last 50 lines of UI logs
tail -50 logs/ui.log

# Search for errors
grep -i error logs/*.log
```

**Port conflicts**:
```bash
# Find what's using ports
lsof -i :7007
lsof -i :7006

# Kill process on port
kill -9 $(lsof -t -i:7007)
```

### Performance Optimization

**Model Selection by RAM**:
- 8GB RAM: Qwen2.5-0.5B (500MB model)
- 16GB RAM: Qwen2.5-3B or Llama3.2-3B (4GB model)
- 32GB+ RAM: Qwen2.5-7B (8GB model)

**UI Performance**:
- Disable voice if not needed (saves memory)
- Limit MAX_TOKENS in .env (default 4000 is high for RAG)
- Use streaming for long responses

**RAG Performance**:
- Keep collection small (<1000 documents)
- Use specific queries (not broad questions)
- Clear collection regularly with `clear_knowledge_base()`

## LangChain Integration Patterns

**Basic Usage**:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",  # Required but arbitrary
    model="mlx-community/Qwen2.5-3B-Instruct-4bit"
)
```

**With Tools** (examples in `examples/langchain_function_calling.py`):
```python
from langchain.agents import tool, create_tool_calling_agent

@tool
def my_tool(param: str) -> str:
    """Tool description for LLM."""
    return execute_my_tool("my_function", {"param": param})

agent = create_tool_calling_agent(llm, tools=[my_tool], prompt)
```

## Project-Specific Conventions

**File Naming**:
- Tools: `server/tools/<category>_<name>.py`
- Tests: `tests/test_<feature>.py`
- Docs: `docs/<FEATURE>_<PURPOSE>.md` (all caps)

**Code Style**:
- Tool executors return `Dict[str, Any]` with `"success"` or `"error"` key
- Use type hints everywhere
- Docstrings: Google style (Args, Returns, Raises)

**Error Handling**:
- Tools catch all exceptions, return `{"error": "message"}`
- UI displays errors with `st.error()`
- Never let exceptions propagate to mlx-omni-server

**Commit Messages**:
Include "🤖 Generated with Claude Code" footer (convention in this repo).
