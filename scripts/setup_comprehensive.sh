#!/bin/bash

# ============================================================================
# Comprehensive Platform Setup Script
# Installs all dependencies for ChatGPT-level capabilities
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Comprehensive ChatGPT-Level Platform Setup${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check/create venv
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi
echo -e "${GREEN}✅ Virtual environment ready${NC}"

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip -q
echo -e "${GREEN}✅ Pip upgraded${NC}"

# Install core dependencies
echo -e "${BLUE}📚 Installing core dependencies...${NC}"
echo ""

echo "  • MLX Omni Server (LLM engine)"
pip install mlx-omni-server>=0.3.4 -q

echo "  • LangChain & LangGraph (Agent orchestration)"
pip install langchain>=0.2.0 langchain-community>=0.2.0 langchain-openai>=0.1.0 langgraph>=0.0.40 -q

echo "  • Streamlit (UI framework)"
pip install streamlit>=1.30.0 -q

echo "  • Data processing (pandas, numpy)"
pip install pandas>=2.0.0 numpy>=1.24.0 openpyxl>=3.1.0 -q

echo "  • Visualization (matplotlib, plotly)"
pip install matplotlib>=3.7.0 plotly>=5.17.0 -q

echo "  • Web search (DuckDuckGo)"
pip install duckduckgo-search>=4.0.0 -q

echo "  • Voice capabilities (TTS/STT)"
pip install pyttsx3>=2.90 -q
# Note: openai-whisper is large (~1GB), installing separately
echo -e "${YELLOW}    ⚠️  Skipping Whisper (large download) - install manually if needed:${NC}"
echo -e "${YELLOW}       pip install openai-whisper${NC}"

echo "  • Image processing (Pillow)"
pip install Pillow>=10.0.0 -q

echo "  • Utilities"
pip install python-dotenv>=1.0.0 requests>=2.31.0 pydantic>=2.5.0 -q

echo ""
echo -e "${GREEN}✅ All dependencies installed${NC}"

# Check installation
echo ""
echo -e "${BLUE}🔍 Verifying installation...${NC}"
python3 -c "
import sys

try:
    # Check core imports
    import mlx_omni_server
    print('✅ MLX Omni Server')

    import langchain
    import langgraph
    print('✅ LangChain & LangGraph')

    import streamlit
    print('✅ Streamlit')

    import pandas
    import numpy
    print('✅ Pandas & Numpy')

    import matplotlib
    import plotly
    print('✅ Matplotlib & Plotly')

    from duckduckgo_search import DDGS
    print('✅ DuckDuckGo Search')

    import pyttsx3
    print('✅ Text-to-Speech')

    from PIL import Image
    print('✅ Pillow')

    print('')
    print('🎉 All dependencies verified!')

except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}📋 Your comprehensive platform includes:${NC}"
echo ""
echo "  💻 Code Execution (Python interpreter)"
echo "  💰 Financial Data (stocks, crypto, charts)"
echo "  🔍 Web Search (AI-synthesized answers)"
echo "  📊 Data Formatting (beautiful tables)"
echo "  🎤 Voice (speech-to-text & text-to-speech)"
echo "  📁 File Analysis (CSV, Excel, JSON, images)"
echo "  🧠 Advanced Reasoning (LangChain/LangGraph)"
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo ""
echo "  1. Start the server:"
echo "     ${GREEN}./scripts/orchestrate.sh --start${NC}"
echo ""
echo "  2. Open the UI:"
echo "     ${GREEN}open http://localhost:7006${NC}"
echo ""
echo "  3. Try it out:"
echo "     • Ask: \"Calculate compound interest on $10k at 5% for 10 years with a chart\""
echo "     • Ask: \"Show me Tesla stock for the last 10 months\""
echo "     • Ask: \"What's the weather in Paris?\""
echo ""
echo -e "${BLUE}============================================================================${NC}"
