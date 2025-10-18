# 📁 MLX OpenAI Local - Project Structure

**Last Updated:** October 18, 2025

---

## 📂 Directory Structure

```
mlx-openai-local/
├── 📁 .claude/                    # Claude Code configuration
│   └── settings.local.json
│
├── 📁 .venv/                      # Python virtual environment
│   └── (all dependencies)
│
├── 📁 examples/                   # LangChain integration examples
│   ├── langchain_basic.py         # Basic chat example
│   ├── langchain_function_calling.py  # Function calling with agents
│   ├── langchain_streaming.py     # Streaming responses
│   └── README.md                  # Examples documentation
│
├── 📁 logs/                       # Server logs
│   ├── api.log                    # API server logs
│   ├── server_YYYYMMDD.log        # Daily server logs
│   └── ui.log                     # UI server logs
│
├── 📁 models/                     # Downloaded MLX models
│   ├── mlx-community--Qwen2.5-0.5B-Instruct-4bit/
│   ├── mlx-community--Qwen2.5-3B-Instruct-4bit/
│   └── (other models as downloaded)
│
├── 📁 scripts/                    # Management scripts
│   └── orchestrate.sh             # Start/stop/restart servers
│
├── 📁 server/                     # Main server code
│   ├── __init__.py
│   ├── app.py                     # Main API server (MLX Omni Server)
│   ├── model_manager.py           # Model loading/management
│   ├── openai_schemas.py          # OpenAI API schemas
│   ├── smart_router.py            # Request routing logic
│   ├── utils.py                   # Utility functions
│   │
│   └── 📁 tools/                  # Tool/function implementations
│       ├── __init__.py
│       ├── calculator.py          # Math calculator tool
│       ├── web_search.py          # Basic web search (raw results)
│       ├── web_search_stub.py     # Legacy stub
│       └── enhanced_web_search.py # ⭐ AI-processed web search
│
├── 📁 tests/                      # Test files
│   ├── test_chat.py               # Chat endpoint tests
│   └── test_smoke.sh              # Smoke tests
│
├── 📁 ui/                         # Streamlit control panel
│   └── ControlPanel.py            # Main UI application
│
├── 📄 .env                        # Environment configuration
├── 📄 .env.example                # Example environment file
├── 📄 .gitignore                  # Git ignore rules
│
├── 📄 pyproject.toml              # Poetry configuration
├── 📄 requirements.txt            # Pip dependencies
│
├── 📄 README.md                   # Main documentation
├── 📄 ENHANCED_WEB_SEARCH.md      # ⭐ Enhanced search guide
├── 📄 WEB_SEARCH_READY.md         # Basic search setup
├── 📄 TOOL_CALLING_GUIDE.md       # Function calling guide
├── 📄 FUNCTION_CALLING_STATUS.md  # Function calling status
├── 📄 MIGRATION_COMPLETE.md       # Migration notes
├── 📄 ORCHESTRATION_SCRIPT_UPDATE.md
├── 📄 REAL_WEBSEARCH_INTEGRATION.md
├── 📄 SUCCESS.md                  # Success metrics
├── 📄 TEST_RESULTS.md             # Test results
│
├── 📄 api.pid                     # API server process ID
├── 📄 ui.pid                      # UI server process ID
│
└── 📄 test_*.py, test_*.json      # Various test files
```

---

## 🔑 Key Files

### Core Server Files

| File | Purpose | Dependencies |
|------|---------|--------------|
| `server/app.py` | Main API server, uses MLX Omni Server | mlx-omni-server |
| `server/model_manager.py` | Model loading and caching | mlx, mlx-lm |
| `server/openai_schemas.py` | OpenAI API compatibility | pydantic |
| `server/smart_router.py` | Request routing logic | - |

### Tool Implementations

| File | Purpose | Type |
|------|---------|------|
| `server/tools/calculator.py` | Math evaluation | Basic |
| `server/tools/web_search.py` | Web search (raw results) | Basic |
| `server/tools/enhanced_web_search.py` | **AI-processed web search** | **Enhanced** |

### UI & Control

| File | Purpose | Framework |
|------|---------|-----------|
| `ui/ControlPanel.py` | Web UI for testing and monitoring | Streamlit |
| `scripts/orchestrate.sh` | Server management (start/stop/restart) | Bash |

### Documentation

| File | Contents |
|------|----------|
| `README.md` | Main project documentation |
| `ENHANCED_WEB_SEARCH.md` | Enhanced web search guide (NEW) |
| `WEB_SEARCH_READY.md` | Basic web search setup |
| `TOOL_CALLING_GUIDE.md` | Function calling guide |

---

## 🧩 Component Interaction

```
┌─────────────────┐
│   User/Client   │
└────────┬────────┘
         │
    HTTP Request
         │
         ↓
┌─────────────────────────────────────────────┐
│         server/app.py (Port 7007)           │
│  - OpenAI-compatible API                     │
│  - Uses MLX Omni Server                      │
│  - 99% function calling accuracy             │
└─────────┬──────────────────────┬────────────┘
          │                      │
          │                      │
    Regular Chat          Function Calling
          │                      │
          ↓                      ↓
┌─────────────────────┐  ┌──────────────────┐
│  model_manager.py   │  │   tools/         │
│  - Load models      │  │   - calculator   │
│  - MLX inference    │  │   - web_search   │
└─────────────────────┘  │   - enhanced_*   │
                         └──────────┬───────┘
                                    │
                         Enhanced Tool Uses:
                                    │
                                    ↓
                         ┌──────────────────┐
                         │  _call_local_llm │
                         │  (synthesize)    │
                         └──────────────────┘
```

---

## 🌟 Enhanced Web Search Architecture

### Flow Diagram

```
User Query: "What's the weather in Ottawa?"
           │
           ↓
    ┌──────────────────┐
    │  ControlPanel.py │  (UI)
    │  Mode: Enhanced  │
    └────────┬─────────┘
             │
        POST /v1/chat/completions
             │
             ↓
    ┌─────────────────────┐
    │    server/app.py    │
    │  (MLX Omni Server)  │
    └────────┬────────────┘
             │
    Detects tool need (99% accuracy)
             │
             ↓
    ┌───────────────────────────┐
    │  tools/enhanced_web_search │
    │  get_weather_enhanced()    │
    └───────┬───────────────────┘
            │
      ┌─────┴─────┐
      │           │
   Search      Synthesize
   DuckDuckGo   (LLM call)
      │           │
      └─────┬─────┘
            │
    Return processed answer
            │
            ↓
         User gets:
    "Ottawa: 10°C, partly cloudy..."
```

---

## 📦 Dependencies

### Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.12"

# MLX and AI
mlx = "^0.22.7"
mlx-lm = "^0.22.0"
mlx-omni-server = "^0.1.6"      # 99% function calling

# Web & API
fastapi = "^0.115.6"
uvicorn = "^0.34.0"
aiohttp = "^3.13.1"
requests = "^2.32.3"

# UI
streamlit = "^1.41.1"

# Tools
ddgs = "^9.6.1"                 # DuckDuckGo search
python-dotenv = "^1.0.1"

# Utilities
pydantic = "^2.10.5"
numpy = "^1.26.4"
```

### Development Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.3.4"
langchain = "^0.3.15"
langchain-openai = "^0.2.13"
```

### Installation

```bash
# Using pip
pip3 install -r requirements.txt

# Using poetry
poetry install
```

---

## 🔧 Configuration Files

### `.env` - Environment Variables

```bash
# Server Configuration
API_HOST=0.0.0.0
API_PORT=7007
UI_PORT=7006

# Model Configuration
DEFAULT_MODEL=mlx-community/Qwen2.5-3B-Instruct-4bit
ALLOWED_MODELS=mlx-community/Qwen2.5-0.5B-Instruct-4bit,mlx-community/Qwen2.5-3B-Instruct-4bit

# Model Cache
MODEL_CACHE_DIR=./models

# Generation Settings
MAX_TOKENS=512
TEMPERATURE=0.7
TOP_P=0.95

# API Settings (for enhanced search)
OPENAI_API_BASE=http://localhost:7007/v1

# Optional
HF_TOKEN=your_huggingface_token
```

### `pyproject.toml` - Poetry Configuration

Project metadata, dependencies, and build configuration.

---

## 🚀 Server Management

### Process IDs

- `api.pid` - API server process ID
- `ui.pid` - UI server process ID

### Log Files

- `logs/api.log` - API server logs
- `logs/ui.log` - UI server logs
- `logs/server_YYYYMMDD.log` - Daily logs

### Management Commands

```bash
# Start all servers
./scripts/orchestrate.sh --start

# Stop all servers
./scripts/orchestrate.sh --stop

# Restart all servers
./scripts/orchestrate.sh --restart

# Check status
./scripts/orchestrate.sh --status
```

---

## 🧪 Testing Structure

### Unit Tests
- `tests/test_chat.py` - Chat API tests
- `test_model.py` - Model loading tests
- `test_direct_tool.py` - Tool execution tests

### Integration Tests
- `test_chat.json` - Chat request payload
- `test_function_call.json` - Function calling payload
- `test_weather.json` - Weather tool payload
- `test_websearch_tool.json` - Web search payload

### Smoke Tests
- `tests/test_smoke.sh` - Quick health checks

---

## 📊 Model Storage

Models are cached in `models/` directory:

```
models/
├── mlx-community--Qwen2.5-0.5B-Instruct-4bit/
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── ...
│
├── mlx-community--Qwen2.5-3B-Instruct-4bit/
│   └── (same structure)
│
└── models--mlx-community--{model-name}/
    └── refs/
```

**Storage Requirements:**
- 0.5B model: ~500MB
- 3B model: ~2-4GB
- 7B model: ~5-8GB

---

## 🔍 Finding Files

### By Purpose

**Need to modify API behavior?**
→ `server/app.py`

**Need to add a new tool?**
→ `server/tools/` (create new .py file)

**Need to change UI?**
→ `ui/ControlPanel.py`

**Need to adjust model settings?**
→ `.env`

**Need to update dependencies?**
→ `requirements.txt` or `pyproject.toml`

### By Feature

**Function Calling:**
- Implementation: `server/app.py` (MLX Omni Server)
- Tools: `server/tools/`
- Examples: `examples/langchain_function_calling.py`

**Web Search (Basic):**
- Implementation: `server/tools/web_search.py`
- Documentation: `WEB_SEARCH_READY.md`

**Web Search (Enhanced):**
- Implementation: `server/tools/enhanced_web_search.py`
- Documentation: `ENHANCED_WEB_SEARCH.md`
- UI Integration: `ui/ControlPanel.py`

---

## 🎯 Quick Navigation

| I want to... | Go to... |
|--------------|----------|
| Start the server | `./scripts/orchestrate.sh --start` |
| Test in browser | http://localhost:7006 |
| Add a new tool | `server/tools/` |
| Change model | `.env` → `DEFAULT_MODEL` |
| See logs | `logs/` directory |
| Run examples | `examples/` directory |
| Read docs | `*.md` files in root |
| Test enhanced search | `python3 server/tools/enhanced_web_search.py` |

---

## 📚 Documentation Index

1. **README.md** - Project overview, quick start
2. **ENHANCED_WEB_SEARCH.md** - AI-processed web search guide
3. **WEB_SEARCH_READY.md** - Basic web search setup
4. **TOOL_CALLING_GUIDE.md** - Function calling tutorial
5. **PROJECT_STRUCTURE.md** - This file
6. **examples/README.md** - LangChain examples

---

## 🔄 Update History

- **Oct 18, 2025** - Added enhanced web search
- **Oct 18, 2025** - Integrated MLX Omni Server (99% function calling)
- **Oct 17, 2025** - Added basic web search
- **Oct 15, 2025** - Initial project structure

---

**Status:** ✅ **Well-Organized & Production-Ready**
**Version:** 2.0
