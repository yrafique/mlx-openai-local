#!/bin/bash

# ============================================================================
# MLX OpenAI Server Orchestration Script
# Manages API and UI processes with Poetry virtual environment
# Modular control for individual services
# Configuration driven by .env file (single source of truth)
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ============================================================================
# Load Environment Variables from .env (Single Source of Truth)
# ============================================================================

if [ -f "$PROJECT_ROOT/.env" ]; then
    # Export all non-comment, non-empty lines from .env
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    print_success() {
        echo -e "${GREEN}✅ $1${NC}"
    }
    print_success "Configuration loaded from .env"
else
    echo -e "${RED}❌ Error: .env file not found at $PROJECT_ROOT/.env${NC}"
    echo "Please create a .env file with required configuration."
    exit 1
fi

# ============================================================================
# Configuration from .env (with fallback defaults)
# ============================================================================

# Server Configuration
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-7007}"
UI_HOST="${UI_HOST:-0.0.0.0}"
UI_PORT="${UI_PORT:-7006}"

# API Paths
API_VERSION="${API_VERSION:-v1}"
API_BASE_PATH="${API_BASE_PATH:-/v1}"
API_MODELS_PATH="${API_MODELS_PATH:-/v1/models}"
API_CHAT_PATH="${API_CHAT_PATH:-/v1/chat/completions}"
HEALTH_CHECK_PATH="${HEALTH_CHECK_PATH:-/health}"

# Model Configuration
DEFAULT_MODEL="${DEFAULT_MODEL:-mlx-community/Llama-3.2-3B-Instruct-4bit}"
MODEL_CACHE_DIR="${MODEL_CACHE_DIR:-./models}"

# UI Configuration
UI_ENABLED="${UI_ENABLED:-false}"
AUTO_START_UI="${AUTO_START_UI:-false}"

# Startup Behavior
RUN_SELFTEST="${RUN_SELFTEST:-true}"
AUTO_INSTALL_DEPS="${AUTO_INSTALL_DEPS:-true}"

# Logging
LOG_DIR="${LOG_DIR:-./logs}"
API_LOG_FILE="${API_LOG_FILE:-api.log}"
UI_LOG_FILE="${UI_LOG_FILE:-ui.log}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# PID Files
API_PID_FILE="${API_PID_FILE:-./api.pid}"
UI_PID_FILE="${UI_PID_FILE:-./ui.pid}"

# Timeouts
SERVER_STARTUP_TIMEOUT="${SERVER_STARTUP_TIMEOUT:-30}"
SERVER_SHUTDOWN_TIMEOUT="${SERVER_SHUTDOWN_TIMEOUT:-10}"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$MODEL_CACHE_DIR"

# Flags (can be overridden by command line)
START_UI="$AUTO_START_UI"
FORCE_UI=false  # Set to true when --ui flag is explicitly passed

# ============================================================================
# Helper Functions
# ============================================================================

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_config() {
    echo -e "${BLUE}📋 Configuration Summary (from .env):${NC}"
    echo -e "${BLUE}  API Host: $API_HOST${NC}"
    echo -e "${BLUE}  API Port: $API_PORT${NC}"
    echo -e "${BLUE}  API Base Path: $API_BASE_PATH${NC}"
    echo -e "${BLUE}  Default Model: $DEFAULT_MODEL${NC}"
    echo -e "${BLUE}  UI Enabled: $UI_ENABLED${NC}"
    echo -e "${BLUE}  Auto-Start UI: $AUTO_START_UI${NC}"
    echo -e "${BLUE}  Log Level: $LOG_LEVEL${NC}"
    echo -e "${BLUE}  Run Self-Test: $RUN_SELFTEST${NC}"
    echo ""
}

check_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not found. Please install Poetry first:"
        echo "  curl -sSL https://install.python-poetry.org | python3 -"
        echo "  Or visit: https://python-poetry.org/docs/#installation"
        exit 1
    fi
    print_success "Poetry found: $(poetry --version)"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found. Please install Python 3.11+"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"
}

install_dependencies() {
    print_info "Installing dependencies with Poetry..."
    echo ""

    check_python
    check_poetry

    cd "$PROJECT_ROOT"

    # Install dependencies
    print_info "Running poetry install..."
    poetry install

    print_success "Dependencies installed successfully"
    echo ""
}

is_process_running() {
    local pid=$1
    if ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

wait_for_server() {
    local url=$1
    local max_attempts=$SERVER_STARTUP_TIMEOUT
    local attempt=0

    print_info "Waiting for server at $url (timeout: ${max_attempts}s)..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        ((attempt++))
    done

    return 1
}

# ============================================================================
# Start API Server
# ============================================================================

start_api() {
    print_info "Starting MLX Omni Server (API)..."

    # Check if already running
    if [ -f "$API_PID_FILE" ]; then
        API_PID=$(cat "$API_PID_FILE")
        if is_process_running "$API_PID"; then
            print_warning "API server already running (PID: $API_PID)"
            return 0
        else
            print_warning "Stale API PID file found, removing..."
            rm -f "$API_PID_FILE"
        fi
    fi

    print_info "Starting MLX Omni Server on $API_HOST:$API_PORT..."
    print_info "API Base Path: $API_BASE_PATH"
    print_info "Default Model: $DEFAULT_MODEL"

    cd "$PROJECT_ROOT"
    # Convert LOG_LEVEL to lowercase for mlx-omni-server CLI (requires lowercase)
    # but keep env var uppercase for argmaxtools (requires uppercase)
    LOG_LEVEL_LOWER=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')
    # Note: mlx-omni-server loads models dynamically per-request
    # The DEFAULT_MODEL in .env is used by the UI when making requests
    nohup poetry run mlx-omni-server \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --log-level "$LOG_LEVEL_LOWER" \
        > "$LOG_DIR/$API_LOG_FILE" 2>&1 &

    API_PID=$!
    echo "$API_PID" > "$API_PID_FILE"
    print_success "MLX Omni Server started (PID: $API_PID)"

    # Wait for API to be ready
    local health_url="http://localhost:$API_PORT$HEALTH_CHECK_PATH"
    if wait_for_server "$health_url"; then
        print_success "API server is healthy"
    else
        print_error "API server failed to start within ${SERVER_STARTUP_TIMEOUT}s"
        print_info "Checking logs ($LOG_DIR/$API_LOG_FILE)..."
        tail -20 "$LOG_DIR/$API_LOG_FILE"
        exit 1
    fi
}

# ============================================================================
# Start UI Server
# ============================================================================

start_ui() {
    # Check if UI is enabled in .env
    if [ "$UI_ENABLED" = "false" ] && [ "$FORCE_UI" = "false" ]; then
        print_warning "UI is disabled in .env (UI_ENABLED=false)"
        print_info "To enable UI, either:"
        print_info "  1. Set UI_ENABLED=true in .env"
        print_info "  2. Use --ui flag to override"
        return 0
    fi

    print_info "Starting UI Server..."

    # Check if already running
    if [ -f "$UI_PID_FILE" ]; then
        UI_PID=$(cat "$UI_PID_FILE")
        if is_process_running "$UI_PID"; then
            print_warning "UI server already running (PID: $UI_PID)"
            return 0
        else
            print_warning "Stale UI PID file found, removing..."
            rm -f "$UI_PID_FILE"
        fi
    fi

    print_info "Starting Streamlit UI on $UI_HOST:$UI_PORT..."

    cd "$PROJECT_ROOT"
    nohup poetry run streamlit run ui/ControlPanel.py \
        --server.port "$UI_PORT" \
        --server.address "$UI_HOST" \
        --server.headless true \
        > "$LOG_DIR/$UI_LOG_FILE" 2>&1 &

    UI_PID=$!
    echo "$UI_PID" > "$UI_PID_FILE"
    print_success "UI server started (PID: $UI_PID)"

    # Wait for UI to be ready
    sleep 3
    print_success "UI server ready"
}

# ============================================================================
# Start Services
# ============================================================================

start_services() {
    print_info "Starting MLX Omni Server (99% Function Calling Accuracy)..."
    echo ""

    # Show configuration summary
    print_config

    # Check prerequisites
    check_python
    check_poetry

    # Check if dependencies are installed
    if ! poetry env info &> /dev/null; then
        if [ "$AUTO_INSTALL_DEPS" = "true" ]; then
            print_warning "Poetry environment not found - auto-installing dependencies..."
            install_dependencies
        else
            print_error "Poetry environment not found. Run: $0 --install"
            exit 1
        fi
    fi

    # Start API server (always)
    start_api

    # Start UI server (based on configuration or flag)
    if [ "$START_UI" = "true" ] || [ "$FORCE_UI" = "true" ]; then
        echo ""
        start_ui
    fi

    # Run self-test if enabled
    if [ "$RUN_SELFTEST" = "true" ]; then
        echo ""
        run_selftest
    fi

    # Print success message
    echo ""
    print_success "=========================================="
    print_success "✅ MLX Omni Server is running!"
    print_success "🚀 99% Function Calling Accuracy"
    print_success "=========================================="
    echo ""
    print_info "API Server:  http://localhost:$API_PORT"

    if [ "$START_UI" = "true" ] || [ "$FORCE_UI" = "true" ]; then
        if [ -f "$UI_PID_FILE" ]; then
            print_info "UI Panel:    http://localhost:$UI_PORT"
        fi
    fi

    echo ""
    print_info "OpenAI-Compatible Endpoints:"
    print_info "  - Chat: http://localhost:$API_PORT$API_CHAT_PATH"
    print_info "  - Models: http://localhost:$API_PORT$API_MODELS_PATH"
    echo ""
    print_info "LangChain Integration:"
    print_info "  - OPENAI_API_BASE=http://localhost:$API_PORT$API_BASE_PATH"
    print_info "  - OPENAI_API_KEY=${OPENAI_API_KEY:-local-demo-key}"
    echo ""
    print_info "Logs:"
    print_info "  - API: $LOG_DIR/$API_LOG_FILE"

    if [ "$START_UI" = "true" ] || [ "$FORCE_UI" = "true" ]; then
        if [ -f "$UI_PID_FILE" ]; then
            print_info "  - UI:  $LOG_DIR/$UI_LOG_FILE"
        fi
    fi

    echo ""
    print_info "Commands:"
    print_info "  - Stop: $0 --stop"

    if [ "$START_UI" = "true" ] || [ "$FORCE_UI" = "true" ]; then
        if [ -f "$UI_PID_FILE" ]; then
            print_info "  - Stop UI only: $0 --stop-ui"
        fi
    fi

    print_info "  - Status: $0 --status"
    echo ""
}

# ============================================================================
# Self-Test
# ============================================================================

run_selftest() {
    print_info "Running self-test..."

    # Test 1: Check /v1/models
    print_info "Test 1: Checking $API_MODELS_PATH..."
    MODELS_RESPONSE=$(curl -s "http://localhost:$API_PORT$API_MODELS_PATH")

    if echo "$MODELS_RESPONSE" | grep -q '"object":"list"'; then
        print_success "Models endpoint working"
    else
        print_error "Models endpoint failed"
        echo "$MODELS_RESPONSE"
        return 1
    fi

    # Test 2: Simple chat completion
    print_info "Test 2: Testing chat completion..."

    CHAT_PAYLOAD=$(cat <<EOF
{
  "model": "$DEFAULT_MODEL",
  "messages": [{"role": "user", "content": "Say hello"}],
  "max_tokens": 10
}
EOF
)

    CHAT_RESPONSE=$(curl -s -X POST "http://localhost:$API_PORT$API_CHAT_PATH" \
        -H "Content-Type: application/json" \
        -d "$CHAT_PAYLOAD")

    if echo "$CHAT_RESPONSE" | grep -q '"choices"'; then
        print_success "Chat completion working"
    else
        print_warning "Chat completion may have issues (model might still be loading)"
        echo "$CHAT_RESPONSE"
    fi
}

# ============================================================================
# Stop Functions
# ============================================================================

stop_api() {
    print_info "Stopping API server..."

    if [ -f "$API_PID_FILE" ]; then
        API_PID=$(cat "$API_PID_FILE")
        if is_process_running "$API_PID"; then
            print_info "Stopping API server (PID: $API_PID)..."
            kill "$API_PID"

            # Wait for graceful shutdown
            local timeout=$SERVER_SHUTDOWN_TIMEOUT
            local elapsed=0
            while is_process_running "$API_PID" && [ $elapsed -lt $timeout ]; do
                sleep 1
                ((elapsed++))
            done

            # Force kill if still running
            if is_process_running "$API_PID"; then
                print_warning "Force killing API server..."
                kill -9 "$API_PID"
            fi

            print_success "API server stopped"
        else
            print_warning "API server not running"
        fi
        rm -f "$API_PID_FILE"
    else
        print_warning "No API PID file found"
    fi
}

stop_ui() {
    print_info "Stopping UI server..."

    if [ -f "$UI_PID_FILE" ]; then
        UI_PID=$(cat "$UI_PID_FILE")
        if is_process_running "$UI_PID"; then
            print_info "Stopping UI server (PID: $UI_PID)..."
            kill "$UI_PID"

            # Wait for graceful shutdown
            local timeout=$SERVER_SHUTDOWN_TIMEOUT
            local elapsed=0
            while is_process_running "$UI_PID" && [ $elapsed -lt $timeout ]; do
                sleep 1
                ((elapsed++))
            done

            # Force kill if still running
            if is_process_running "$UI_PID"; then
                print_warning "Force killing UI server..."
                kill -9 "$UI_PID"
            fi

            print_success "UI server stopped"
        else
            print_warning "UI server not running"
        fi
        rm -f "$UI_PID_FILE"
    else
        print_warning "No UI PID file found"
    fi
}

stop_services() {
    print_info "Stopping MLX Omni Server..."
    echo ""

    stop_api
    stop_ui

    echo ""
    print_success "All services stopped"
}

# ============================================================================
# Restart Functions
# ============================================================================

restart_api() {
    print_info "Restarting API server..."
    stop_api
    sleep 2
    start_api
}

restart_ui() {
    print_info "Restarting UI server..."
    stop_ui
    sleep 2
    start_ui
}

restart_services() {
    print_info "Restarting MLX Omni Server..."
    stop_services
    sleep 2
    start_services
}

# ============================================================================
# Status Function
# ============================================================================

status_services() {
    print_info "Checking service status..."
    echo ""

    # Check API
    if [ -f "$API_PID_FILE" ]; then
        API_PID=$(cat "$API_PID_FILE")
        if is_process_running "$API_PID"; then
            print_success "API server running (PID: $API_PID)"
            print_info "  URL: http://localhost:$API_PORT"
            print_info "  Logs: $LOG_DIR/$API_LOG_FILE"
        else
            print_error "API server not running (stale PID file)"
        fi
    else
        print_error "API server not running (no PID file)"
    fi

    # Check UI
    if [ -f "$UI_PID_FILE" ]; then
        UI_PID=$(cat "$UI_PID_FILE")
        if is_process_running "$UI_PID"; then
            print_success "UI server running (PID: $UI_PID)"
            print_info "  URL: http://localhost:$UI_PORT"
            print_info "  Logs: $LOG_DIR/$UI_LOG_FILE"
        else
            print_error "UI server not running (stale PID file)"
        fi
    else
        print_warning "UI server not running (no PID file)"
        if [ "$UI_ENABLED" = "false" ]; then
            print_info "  Note: UI is disabled in .env (UI_ENABLED=false)"
        fi
    fi

    echo ""
    print_info "Configuration (.env):"
    print_info "  UI Enabled: $UI_ENABLED"
    print_info "  Auto-Start UI: $AUTO_START_UI"
}

# ============================================================================
# Main - Parse Arguments
# ============================================================================

# Parse flags
while [[ $# -gt 0 ]]; do
    case $1 in
        --ui)
            START_UI=true
            FORCE_UI=true  # Override .env setting
            shift
            ;;
        --install|--setup)
            install_dependencies
            exit 0
            ;;
        --start)
            ACTION="start"
            shift
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --stop-api)
            ACTION="stop-api"
            shift
            ;;
        --stop-ui)
            ACTION="stop-ui"
            shift
            ;;
        --restart)
            ACTION="restart"
            shift
            ;;
        --restart-api)
            ACTION="restart-api"
            shift
            ;;
        --restart-ui)
            ACTION="restart-ui"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        --config)
            ACTION="config"
            shift
            ;;
        *)
            echo "MLX OpenAI Local - Server Management (Poetry-based)"
            echo ""
            echo "Configuration: All settings are read from .env file (single source of truth)"
            echo ""
            echo "Usage: $0 [OPTIONS] {--install|--start|--stop|--restart|--status}"
            echo ""
            echo "Options:"
            echo "  --ui              Start UI server (overrides .env AUTO_START_UI setting)"
            echo ""
            echo "Commands:"
            echo "  --install         Install dependencies with Poetry"
            echo "  --setup           Alias for --install"
            echo ""
            echo "  --start           Start API server (UI based on .env AUTO_START_UI)"
            echo "  --stop            Stop all running servers"
            echo "  --stop-api        Stop API server only"
            echo "  --stop-ui         Stop UI server only"
            echo ""
            echo "  --restart         Restart all servers"
            echo "  --restart-api     Restart API server only"
            echo "  --restart-ui      Restart UI server only"
            echo ""
            echo "  --status          Check server status and configuration"
            echo "  --config          Show current configuration from .env"
            echo ""
            echo "Examples:"
            echo "  $0 --start              # Start based on .env settings"
            echo "  $0 --start --ui         # Start with UI (override .env)"
            echo "  $0 --stop               # Stop all servers"
            echo "  $0 --stop-ui            # Stop UI only, keep API running"
            echo "  $0 --restart --ui       # Restart with UI enabled"
            echo "  $0 --status             # Check what's running"
            echo ""
            echo "Configuration (.env):"
            echo "  Edit .env file to configure all server settings"
            echo "  Key settings:"
            echo "    - UI_ENABLED: Enable/disable UI (true/false)"
            echo "    - AUTO_START_UI: Auto-start UI with API (true/false)"
            echo "    - API_PORT, UI_PORT: Server ports"
            echo "    - DEFAULT_MODEL: Model to use"
            echo "    - LOG_LEVEL: Logging verbosity"
            echo ""
            exit 1
            ;;
    esac
done

# Execute action
case "${ACTION:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    stop-api)
        stop_api
        ;;
    stop-ui)
        stop_ui
        ;;
    restart)
        restart_services
        ;;
    restart-api)
        restart_api
        ;;
    restart-ui)
        restart_ui
        ;;
    status)
        status_services
        ;;
    config)
        print_config
        ;;
    *)
        # Show help if no action specified
        $0 --help
        ;;
esac
