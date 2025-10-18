# MLX Omni Server - Configuration Guide

## Overview

The `.env` file is the **single source of truth** for all system configurations. All server behavior, API paths, model settings, and feature toggles are controlled through this file.

## Quick Start

1. **Edit `.env`** to configure your server
2. **Run** `./scripts/orchestrate.sh --start`
3. **Done!** Server starts with your settings

## Configuration Sections

### 1. Server Configuration

```bash
# API Server
API_HOST=0.0.0.0              # Host address (0.0.0.0 = all interfaces)
API_PORT=7007                 # API server port

# API Path Configuration
API_VERSION=v1                # API version
API_BASE_PATH=/v1             # Base path for all endpoints
API_MODELS_PATH=/v1/models    # Models endpoint path
API_CHAT_PATH=/v1/chat/completions  # Chat completions path

# UI Server Configuration
UI_ENABLED=false              # Enable/disable UI functionality
UI_PORT=7006                  # UI server port
UI_HOST=0.0.0.0              # UI host address
AUTO_START_UI=false          # Auto-start UI with API (true/false)
```

**Key Points:**
- `UI_ENABLED=false`: UI is disabled (even with --ui flag, shows warning)
- `AUTO_START_UI=false`: UI won't start automatically (requires --ui flag)
- `AUTO_START_UI=true`: UI starts automatically with API

### 2. Model Configuration

```bash
# Default Model
DEFAULT_MODEL=mlx-community/Llama-3.2-3B-Instruct-4bit

# Alternative Models (comma-separated)
ALLOWED_MODELS=mlx-community/Qwen2.5-0.5B-Instruct-4bit,mlx-community/Qwen2.5-3B-Instruct-4bit,mlx-community/Qwen2.5-7B-Instruct-4bit,mlx-community/Llama-3.2-3B-Instruct-4bit

# Model Storage
MODEL_CACHE_DIR=./models

# Hugging Face Configuration
HF_TOKEN=                     # Optional: For gated models
```

**Supported Models for 99% Function Calling:**
- Qwen2.5-3B-4bit (99.0% accuracy)
- Llama3.2-3B-4bit (99.6% accuracy)

### 3. Performance Tuning

```bash
# Generation Parameters
MAX_TOKENS=10000              # Maximum tokens per response
TEMPERATURE=0                 # 0 = deterministic, 1 = creative
TOP_P=1.0                     # Nucleus sampling threshold

# Server Performance
MAX_CONCURRENT_REQUESTS=10    # Max parallel requests
REQUEST_TIMEOUT=300           # Request timeout in seconds
```

### 4. Features

```bash
# Core Features
ENABLE_FUNCTION_CALLING=true  # 99% accurate tool calling
ENABLE_STREAMING=true         # Streaming responses
ENABLE_WEB_SEARCH=true        # Web search capability
ENABLE_CODE_EXECUTION=false   # Code execution (use with caution)
ENABLE_VOICE=false           # Voice input/output
```

### 5. Logging

```bash
# Log Level (lowercase required)
LOG_LEVEL=info               # debug, info, warning, error, critical

# Log Directory and Files
LOG_DIR=./logs
API_LOG_FILE=api.log
UI_LOG_FILE=ui.log

# Request Logging
ENABLE_REQUEST_LOGGING=true  # Log all API requests
```

**Important:** `LOG_LEVEL` must be lowercase (`info`, not `INFO`)

### 6. Startup Behavior

```bash
# Automatic Behaviors
AUTO_START_UI=false          # Start UI automatically with API
RUN_SELFTEST=true           # Run health checks on startup
AUTO_INSTALL_DEPS=true      # Auto-install if Poetry env missing
```

**Recommendations:**
- Development: `RUN_SELFTEST=true`, `AUTO_INSTALL_DEPS=true`
- Production: `RUN_SELFTEST=true`, `AUTO_INSTALL_DEPS=false`

### 7. Advanced Settings

```bash
# Process Management
API_PID_FILE=./api.pid       # API server PID file location
UI_PID_FILE=./ui.pid         # UI server PID file location

# Health Checks
HEALTH_CHECK_PATH=/health    # Health endpoint path

# Timeouts
SERVER_STARTUP_TIMEOUT=30    # Startup wait time (seconds)
SERVER_SHUTDOWN_TIMEOUT=10   # Graceful shutdown time (seconds)
```

### 8. Security

```bash
# CORS Configuration
ENABLE_CORS=true            # Enable cross-origin requests
ALLOWED_ORIGINS=*           # Allowed origins (comma-separated or *)

# Authentication
REQUIRE_API_KEY=false       # Require API key for requests
```

### 9. OpenAI Compatibility

```bash
# LangChain Integration
OPENAI_API_BASE=http://localhost:7007/v1
OPENAI_API_KEY=local-demo-key
```

## Usage Examples

### Example 1: API-Only Server (Default)

`.env`:
```bash
UI_ENABLED=false
AUTO_START_UI=false
```

Start:
```bash
./scripts/orchestrate.sh --start
# ✅ API running on http://localhost:7007
# ⚠️  UI not running
```

### Example 2: API + UI Always On

`.env`:
```bash
UI_ENABLED=true
AUTO_START_UI=true
```

Start:
```bash
./scripts/orchestrate.sh --start
# ✅ API running on http://localhost:7007
# ✅ UI running on http://localhost:7006
```

### Example 3: API Only, UI on Demand

`.env`:
```bash
UI_ENABLED=false
AUTO_START_UI=false
```

Start API only:
```bash
./scripts/orchestrate.sh --start
# ✅ API running
```

Start with UI (override .env):
```bash
./scripts/orchestrate.sh --start --ui
# ✅ API running
# ✅ UI running (overridden)
```

### Example 4: Custom API Path

`.env`:
```bash
API_BASE_PATH=/api/v2
API_MODELS_PATH=/api/v2/models
API_CHAT_PATH=/api/v2/chat/completions
```

Endpoints become:
- Chat: `http://localhost:7007/api/v2/chat/completions`
- Models: `http://localhost:7007/api/v2/models`

### Example 5: Development Mode

`.env`:
```bash
LOG_LEVEL=debug
RUN_SELFTEST=true
AUTO_INSTALL_DEPS=true
ENABLE_REQUEST_LOGGING=true
DEBUG_MODE=true
```

### Example 6: Production Mode

`.env`:
```bash
LOG_LEVEL=warning
RUN_SELFTEST=true
AUTO_INSTALL_DEPS=false
ENABLE_REQUEST_LOGGING=false
DEBUG_MODE=false
REQUIRE_API_KEY=true
```

## Configuration Priority

The configuration system follows this priority order:

1. **Command-line flags** (highest priority)
   - `--ui` overrides `UI_ENABLED` and `AUTO_START_UI`

2. **.env file settings** (middle priority)
   - All configuration values read from `.env`

3. **Script defaults** (lowest priority)
   - Fallback values if `.env` is missing settings

## Common Scenarios

### Disable Self-Tests (Faster Startup)

```bash
RUN_SELFTEST=false
```

### Change Default Model

```bash
DEFAULT_MODEL=mlx-community/Qwen2.5-3B-Instruct-4bit
```

### Increase Startup Timeout (Slow System)

```bash
SERVER_STARTUP_TIMEOUT=60
```

### Enable Debug Logging

```bash
LOG_LEVEL=debug
ENABLE_REQUEST_LOGGING=true
```

### Custom Ports

```bash
API_PORT=8080
UI_PORT=8081
```

Then update:
```bash
OPENAI_API_BASE=http://localhost:8080/v1
```

## Validation

Check your current configuration:

```bash
./scripts/orchestrate.sh --config
```

Output:
```
📋 Configuration Summary (from .env):
  API Host: 0.0.0.0
  API Port: 7007
  API Base Path: /v1
  Default Model: mlx-community/Llama-3.2-3B-Instruct-4bit
  UI Enabled: false
  Auto-Start UI: false
  Log Level: info
  Run Self-Test: true
```

## Troubleshooting

### Issue: "Invalid choice for --log-level"

**Problem:** `LOG_LEVEL` is uppercase
**Solution:** Change to lowercase in `.env`:
```bash
LOG_LEVEL=info  # ✅ Correct
# LOG_LEVEL=INFO  # ❌ Wrong
```

### Issue: UI won't start with --ui flag

**Problem:** `UI_ENABLED=false` blocks UI
**Solution:** Set `UI_ENABLED=true` in `.env`

### Issue: Server times out on startup

**Problem:** Slow system or large model
**Solution:** Increase timeout:
```bash
SERVER_STARTUP_TIMEOUT=60
```

### Issue: Dependencies not installing

**Problem:** `AUTO_INSTALL_DEPS=false`
**Solution:** Either:
1. Set `AUTO_INSTALL_DEPS=true`, or
2. Run `./scripts/orchestrate.sh --install` manually

## Best Practices

1. **Version Control:**
   - Keep `.env` in `.gitignore`
   - Create `.env.example` with safe defaults
   - Document any custom settings

2. **Security:**
   - Never commit `HF_TOKEN` or API keys
   - Use `REQUIRE_API_KEY=true` in production
   - Limit `ALLOWED_ORIGINS` in production

3. **Performance:**
   - Start with `DEFAULT_MODEL` set to smallest model (0.5B)
   - Increase `MAX_TOKENS` only if needed
   - Monitor with `ENABLE_REQUEST_LOGGING=true`

4. **Development:**
   - Use `LOG_LEVEL=debug` for troubleshooting
   - Enable `RUN_SELFTEST=true` to catch issues early
   - Use `AUTO_START_UI=false` to save resources

5. **Production:**
   - Use `LOG_LEVEL=warning` or `error`
   - Set `AUTO_INSTALL_DEPS=false`
   - Configure proper `SERVER_STARTUP_TIMEOUT`

## Environment Variables for LangChain

When using LangChain, export these from your `.env`:

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("DEFAULT_MODEL")
)
```

Or set in shell:
```bash
export OPENAI_API_BASE=http://localhost:7007/v1
export OPENAI_API_KEY=local-demo-key
```

## Summary

The `.env` file gives you complete control over:
- ✅ Server ports and hosts
- ✅ API endpoint paths
- ✅ Model selection
- ✅ UI enable/disable
- ✅ Logging verbosity
- ✅ Performance tuning
- ✅ Feature flags
- ✅ Startup behavior

**Remember:** After changing `.env`, restart the server:
```bash
./scripts/orchestrate.sh --restart
```

For more information, see:
- [README.md](../README.md) - Quick start guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project organization
- [TOOL_CALLING_GUIDE.md](TOOL_CALLING_GUIDE.md) - Function calling tutorial
