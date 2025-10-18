"""
Streamlit Control Panel for MLX Omni Server.
Provides UI for chat testing, tool calling, and server monitoring.
MLX Omni Server delivers 99% function calling accuracy on Apple Silicon.
"""

import streamlit as st
import requests
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from server.tools.web_search import TOOL_DEFINITIONS, execute_tool
from server.tools.enhanced_web_search import ENHANCED_TOOL_DEFINITIONS, execute_enhanced_tool
from server.tools.financial_data import FINANCIAL_TOOL_DEFINITIONS, execute_financial_tool
from server.tools.table_formatter import TABLE_FORMATTER_TOOL_DEFINITIONS, execute_table_formatter_tool
from server.tools.response_formatter import format_response, clean_latex_artifacts
from server.tools.voice import VOICE_TOOL_DEFINITIONS, execute_voice_tool, speech_to_text, text_to_speech
from server.tools.rag import RAG_TOOL_DEFINITIONS, execute_rag_tool, get_rag_manager
from server.tools.registry import REGISTRY
from server.model_manager import model_manager
import base64
import tempfile

# Load environment
load_dotenv()

# Configuration
API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:7007/v1")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "7007"))
API_URL = f"http://{API_HOST}:{API_PORT}/v1"

# Page config
st.set_page_config(
    page_title="MLX Omni Server Control Panel",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-healthy {
        background-color: #d4edda;
        color: #155724;
    }
    .status-unhealthy {
        background-color: #f8d7da;
        color: #721c24;
    }
    .model-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Helper Functions
# ============================================================================

def check_server_health():
    """Check if the MLX Omni Server is running."""
    try:
        # Try standard OpenAI /v1/models endpoint
        response = requests.get(f"{API_URL}/models", timeout=2)
        if response.status_code == 200:
            data = response.json()
            # Check if there's at least one model
            models = data.get("data", [])
            if models:
                return True, {
                    "model_loaded": True,
                    "current_model": models[0]["id"]
                }
            return True, {"model_loaded": False, "current_model": "None"}
        return False, None
    except:
        return False, None


def get_available_models():
    """Get list of available models from API."""
    try:
        response = requests.get(f"{API_URL}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        return []
    except Exception as e:
        st.error(f"Failed to fetch models: {e}")
        return []


# Note: MLX Omni Server manages models through CLI arguments
# Model loading/unloading is done via restart with different --model parameter


def send_chat_completion(messages, model=None, temperature=0.7, max_tokens=512,
                        top_p=0.95, tools=None, stream=False):
    """Send a chat completion request."""

    # Add intelligent system prompt when tools are available
    enhanced_messages = messages.copy()
    if tools:
        # Check if there's already a system message
        has_system = any(msg.get("role") == "system" for msg in enhanced_messages)

        if not has_system:
            # Add system message to guide tool usage
            system_prompt = """You are a helpful AI assistant. You have access to various tools, but you should ONLY use them when the user's question genuinely requires external information or capabilities.

**When to use tools:**
- Web Search: Only when asked about current events, news, real-time information, or facts you don't know
- Financial Tools: Only when asked about specific stock prices, crypto prices, or market data
- Voice Tools: Only when user provides audio or asks for audio output

**When NOT to use tools:**
- Simple greetings (Hello, Hi, How are you)
- General knowledge questions you can answer directly
- Casual conversation
- Math calculations you can solve
- Coding questions
- Explanations of concepts

**Be conservative:** If you can answer directly without tools, do so. Tools should be a last resort for information you genuinely don't have."""

            enhanced_messages.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": model or os.getenv("DEFAULT_MODEL"),
        "messages": enhanced_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "stream": stream
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        response = requests.post(
            f"{API_URL}/chat/completions",
            json=payload,
            timeout=120,
            stream=stream
        )

        if stream:
            return response
        else:
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}


def stream_response(response):
    """Generator to yield streaming response chunks."""
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                if data == '[DONE]':
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        yield delta['content']
                except:
                    pass


# ============================================================================
# Main UI
# ============================================================================

# Header
st.markdown('<div class="main-header">🚀 MLX Omni Server Control Panel</div>', unsafe_allow_html=True)
st.caption("99% Function Calling Accuracy • Apple Silicon Optimized • LangChain Ready")

# Check server status
is_healthy, health_data = check_server_health()

if is_healthy:
    status_html = '<span class="status-badge status-healthy">✓ Server Online</span>'
    model_loaded = health_data.get("model_loaded", False)
    current_model = health_data.get("current_model", "None")
else:
    status_html = '<span class="status-badge status-unhealthy">✗ Server Offline</span>'
    model_loaded = False
    current_model = "None"

st.markdown(status_html, unsafe_allow_html=True)

if not is_healthy:
    st.error(f"Cannot connect to API server at {API_URL}. Please start the server with `./scripts/orchestrate.sh --start`")
    st.stop()


# ============================================================================
# Sidebar - Model Management
# ============================================================================

with st.sidebar:
    st.header("📦 Model Information")

    # Current model info
    if model_loaded:
        st.success(f"**Active Model:**\n\n`{current_model}`")
    else:
        st.warning("**No model loaded**")

    st.divider()

    # Available models
    available_models = get_available_models()

    if available_models:
        st.subheader("Available Models")
        for model in available_models:
            if model == current_model:
                st.info(f"✓ {model} (active)")
            else:
                st.text(f"  {model}")
    else:
        st.warning("No models available")

    st.divider()

    # Model switching instructions
    with st.expander("🔄 How to Change Models"):
        st.markdown("""
        To switch to a different model:

        1. Update `.env` file:
           ```bash
           DEFAULT_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit
           ```

        2. Restart the server:
           ```bash
           ./scripts/orchestrate.sh --restart
           ```

        Or use the command line:
        ```bash
        mlx-omni-server --model mlx-community/Qwen2.5-7B-Instruct-4bit
        ```
        """)

    st.divider()

    # Logs
    st.subheader("📋 Recent Logs")
    log_dir = Path(os.getenv("LOG_DIR", "./logs"))
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        if log_files:
            latest_log = log_files[0]
            try:
                with open(latest_log, "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:]  # Last 10 lines
                    st.text_area("Logs", "".join(recent_lines), height=200, disabled=True)
            except:
                st.info("Could not read log file")
        else:
            st.info("No log files found")
    else:
        st.info("Log directory not found")


# ============================================================================
# Main Panel - Tabs
# ============================================================================

tab1, tab2, tab3 = st.tabs(["💬 Chat", "🛠️ Tools", "⚙️ Settings"])

# ============================================================================
# Tab 1: Chat Interface
# ============================================================================

with tab1:
    st.header("Chat with Model")

    if not model_loaded:
        st.warning("⚠️ Please load a model first using the sidebar")
    else:
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Enable tools with mode selection
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        with col1:
            enable_web_search = st.toggle("🌐 Enable Web Search", value=False,
                                           help="Allow the model to search the web for current information")
        with col2:
            enable_financial = st.toggle("💰 Real-time Finance", value=False,
                                         help="Real-time stock/crypto prices (accurate!)")
        with col3:
            enable_rag = st.toggle("🧠 RAG (NEW!)", value=False,
                                   help="Document & YouTube knowledge base search")
        with col4:
            enable_voice = st.toggle("🎤 Voice Input", value=False,
                                     help="Record audio or enable text-to-speech")
        with col5:
            enable_streaming = st.toggle("⚡ Live Streaming", value=True,
                                         help="See responses being typed in real-time (like ChatGPT)")
        with col6:
            if enable_web_search:
                search_mode = st.selectbox(
                    "Search Mode",
                    ["Enhanced", "Basic"],
                    help="Enhanced: AI-processed\nBasic: Raw results"
                )
                use_enhanced = search_mode == "Enhanced"
            else:
                use_enhanced = False

        # RAG Knowledge Base Management (if enabled)
        if enable_rag:
            st.divider()
            st.subheader("🧠 Knowledge Base Management")

            rag_col1, rag_col2 = st.columns(2)

            with rag_col1:
                st.markdown("**📄 Ingest Documents**")
                uploaded_file = st.file_uploader("Upload PDF, TXT, or MD file", type=['pdf', 'txt', 'md'])
                if uploaded_file:
                    if st.button("📥 Ingest File"):
                        with st.spinner("Processing document..."):
                            # Save to temp file
                            temp_path = f"/tmp/{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Ingest
                            result = execute_rag_tool("ingest_document", {"file_path": temp_path})
                            result_data = json.loads(result) if isinstance(result, str) else result

                            if result_data.get("success"):
                                st.success(f"✅ {result_data.get('message')}")
                            else:
                                st.error(f"❌ {result_data.get('error')}")

                st.markdown("**🎥 Ingest YouTube Video**")
                youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
                if youtube_url and st.button("📥 Ingest YouTube"):
                    with st.spinner("Extracting transcript..."):
                        result = execute_rag_tool("ingest_youtube", {"youtube_url": youtube_url})
                        result_data = json.loads(result) if isinstance(result, str) else result

                        if result_data.get("success"):
                            st.success(f"✅ {result_data.get('message')}")
                        else:
                            st.error(f"❌ {result_data.get('error')}")

            with rag_col2:
                st.markdown("**📊 Knowledge Base Stats**")
                if st.button("🔄 Refresh Stats"):
                    result = execute_rag_tool("get_knowledge_base_stats", {})
                    result_data = json.loads(result) if isinstance(result, str) else result

                    if "error" not in result_data:
                        st.info(f"""
                        **Collection:** {result_data.get('collection_name', 'N/A')}
                        **Documents:** {result_data.get('document_count', 0)}
                        **Directory:** {result_data.get('persist_directory', 'N/A')}
                        """)
                    else:
                        st.error(result_data.get('error'))

                st.markdown("**🗑️ Clear Knowledge Base**")
                if st.button("⚠️ Clear All Documents", type="secondary"):
                    if st.button("✅ Confirm Clear"):
                        result = execute_rag_tool("clear_knowledge_base", {})
                        result_data = json.loads(result) if isinstance(result, str) else result

                        if result_data.get("success"):
                            st.success("✅ Knowledge base cleared")
                        else:
                            st.error(result_data.get("error"))

            st.divider()

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message.get("content"):
                    st.markdown(message["content"])
                elif message.get("tool_calls"):
                    st.caption("🔧 Using tools...")
                    for tool_call in message["tool_calls"]:
                        st.code(f"{tool_call['function']['name']}({tool_call['function']['arguments']})", language="python")

        # Voice input (if enabled)
        prompt = None
        if enable_voice:
            st.divider()
            voice_col1, voice_col2 = st.columns([3, 1])
            with voice_col1:
                audio_value = st.audio_input("🎤 Record your message")
            with voice_col2:
                st.caption("📝 Or type below")

            if audio_value is not None:
                with st.spinner("🎧 Transcribing audio..."):
                    try:
                        # Read audio file
                        audio_bytes = audio_value.read()
                        # Encode to base64
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                        # Transcribe
                        result_json = speech_to_text(audio_base64)
                        result = json.loads(result_json)

                        if result.get("status") == "success":
                            prompt = result.get("text")
                            st.success(f"✅ Transcribed: *{prompt}*")
                        else:
                            st.error(f"❌ Transcription failed: {result.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error processing audio: {e}")

        # Chat input (text)
        if not prompt:
            prompt = st.chat_input("Type your message...")

        if prompt:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response with tool support
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Select tool definitions based on enabled features
                    selected_tools = []

                    if enable_web_search:
                        selected_tools.extend(ENHANCED_TOOL_DEFINITIONS if use_enhanced else TOOL_DEFINITIONS)

                    if enable_financial:
                        selected_tools.extend(FINANCIAL_TOOL_DEFINITIONS)

                    if enable_rag:
                        selected_tools.extend(RAG_TOOL_DEFINITIONS)

                    if enable_voice:
                        selected_tools.extend(VOICE_TOOL_DEFINITIONS)

                    # Always include table formatter for beautiful data display
                    selected_tools.extend(TABLE_FORMATTER_TOOL_DEFINITIONS)

                    # Use None if no tools selected
                    selected_tools = selected_tools if selected_tools else None

                    # First request with tools
                    response = send_chat_completion(
                        messages=st.session_state.messages,
                        model=current_model,
                        tools=selected_tools
                    )

                    if "error" in response:
                        st.error(f"Error: {response['error']}")
                    else:
                        message = response["choices"][0]["message"]

                        # Check if model wants to use tools
                        if message.get("tool_calls"):
                            # Show appropriate status based on tool type
                            tool_name = message["tool_calls"][0]["function"]["name"]

                            if tool_name in ['get_stock_price', 'get_crypto_price']:
                                with st.status("💰 Fetching real-time financial data...", expanded=True) as status:
                                    st.write(f"📊 Querying {tool_name}...")
                            elif use_enhanced:
                                with st.status("🔍 Searching and processing web results...", expanded=True) as status:
                                    st.write("🌐 Searching the web...")
                            else:
                                with st.status("🔍 Searching the web...", expanded=True) as status:
                                    st.write("📡 Fetching data...")

                            # Add assistant's tool call message to history
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": message["tool_calls"]
                            })

                            # Execute each tool call
                            for tool_call in message["tool_calls"]:
                                tool_name = tool_call["function"]["name"]
                                tool_args = json.loads(tool_call["function"]["arguments"])

                                # Execute tool based on type
                                if tool_name in ['get_stock_price', 'get_crypto_price', 'get_stock_history']:
                                    tool_result = execute_financial_tool(tool_name, tool_args)
                                elif tool_name == 'format_table':
                                    tool_result = execute_table_formatter_tool(tool_name, tool_args)
                                elif tool_name in ['speech_to_text', 'text_to_speech']:
                                    tool_result = execute_voice_tool(tool_name, tool_args)
                                elif tool_name in ['ingest_document', 'ingest_youtube', 'query_knowledge_base', 'clear_knowledge_base', 'get_knowledge_base_stats']:
                                    tool_result = execute_rag_tool(tool_name, tool_args)
                                elif use_enhanced:
                                    tool_result = execute_enhanced_tool(tool_name, tool_args)
                                else:
                                    tool_result = execute_tool(tool_name, tool_args)

                                # For enhanced mode, financial tools, or table formatter - show the answer directly
                                is_financial = tool_name in ['get_stock_price', 'get_crypto_price', 'get_stock_history']
                                is_table_formatter = tool_name == 'format_table'

                                if use_enhanced or is_financial or is_table_formatter:
                                    try:
                                        result_data = json.loads(tool_result)
                                        if "answer" in result_data:
                                            # Clean and format the answer before display
                                            cleaned_answer = clean_latex_artifacts(result_data['answer'])

                                            # Display answer with better formatting
                                            if is_table_formatter and result_data.get("status") == "success":
                                                # Table formatter - show with special formatting
                                                st.success(f"📊 Formatted {result_data.get('table_type', 'Table').title()} ({result_data.get('row_count', 0)} rows)")
                                                st.markdown(cleaned_answer)
                                            elif is_financial and result_data.get("status") == "success":
                                                # Check if this is historical data or current price
                                                if tool_name == 'get_stock_history':
                                                    # Historical data with interactive chart
                                                    st.success(f"📈 Historical Stock Data - {result_data.get('symbol', '')} ({result_data.get('period', '')})")

                                                    # Display interactive Plotly chart if available
                                                    if result_data.get('chart_json'):
                                                        import plotly.graph_objects as go
                                                        import json as json_module

                                                        # Parse and display Plotly chart
                                                        chart_json = json_module.loads(result_data['chart_json'])
                                                        fig = go.Figure(chart_json)

                                                        # Display with full interactivity
                                                        st.plotly_chart(fig, use_container_width=True, config={
                                                            'displayModeBar': True,
                                                            'displaylogo': False,
                                                            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                                                        })

                                                    # Display markdown answer (includes table)
                                                    st.markdown(cleaned_answer)

                                                    # Show summary metrics
                                                    with st.expander("📊 Summary Statistics", expanded=True):
                                                        col1, col2, col3 = st.columns(3)

                                                        with col1:
                                                            st.metric(
                                                                "Period Change",
                                                                f"${result_data.get('change', 0):.2f}",
                                                                f"{result_data.get('change_percent', 0):.2f}%"
                                                            )

                                                        with col2:
                                                            st.metric("Highest", f"${result_data.get('high', 0):.2f}")

                                                        with col3:
                                                            st.metric("Lowest", f"${result_data.get('low', 0):.2f}")

                                                        st.divider()
                                                        st.caption(f"📅 Data Points: {result_data.get('data_points', 0)}")
                                                        st.caption(f"🔗 Source: {result_data.get('source', 'N/A')}")
                                                else:
                                                    # Current price - show with metrics
                                                    st.success("✅ Real-time Financial Data")
                                                    st.markdown(cleaned_answer)

                                                    # Show detailed metrics in expander
                                                    with st.expander("📊 Detailed Metrics", expanded=False):
                                                        col1, col2, col3 = st.columns(3)

                                                        with col1:
                                                            if "price" in result_data:
                                                                st.metric(
                                                                    "Current Price",
                                                                    f"${result_data.get('price')}",
                                                                    f"{result_data.get('change')} ({result_data.get('change_percent')}%)"
                                                                )

                                                        with col2:
                                                            if "previous_close" in result_data:
                                                                st.metric("Previous Close", f"${result_data.get('previous_close')}")

                                                        with col3:
                                                            if "exchange" in result_data:
                                                                st.metric("Exchange", result_data.get('exchange', 'N/A'))

                                                        st.divider()
                                                        st.caption(f"📅 Updated: {result_data.get('timestamp', 'N/A')}")
                                                        st.caption(f"🔗 Source: {result_data.get('source', 'N/A')}")
                                            else:
                                                # Web search or other - show normally
                                                st.markdown(cleaned_answer)

                                            # Show sources for web search
                                            if result_data.get("sources"):
                                                with st.expander("📚 Sources"):
                                                    for source in result_data.get("sources", []):
                                                        st.markdown(f"- [{source.get('title')}]({source.get('url')})")

                                            # For enhanced mode, send simplified confirmation to model
                                            # This prevents the model from repeating the answer
                                            simplified_result = json.dumps({
                                                "status": "success",
                                                "message": f"Retrieved information successfully. Answer has been provided to the user."
                                            })
                                            tool_result = simplified_result
                                    except:
                                        pass

                                # Add tool result to messages
                                st.session_state.messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.get("id", "default"),
                                    "name": tool_name,
                                    "content": tool_result
                                })

                            # Get final response from model with tool results
                            # In enhanced mode, financial tools, or table formatter - we've already shown the answer
                            skip_final_call = use_enhanced or any(
                                tc["function"]["name"] in ['get_stock_price', 'get_crypto_price', 'get_stock_history', 'format_table']
                                for tc in message.get("tool_calls", [])
                            )

                            if not skip_final_call:
                                with st.spinner("Processing results..."):
                                    final_response = send_chat_completion(
                                        messages=st.session_state.messages,
                                        model=current_model,
                                        tools=selected_tools
                                    )

                                    if "error" in final_response:
                                        st.error(f"Error: {final_response['error']}")
                                    else:
                                        final_message_obj = final_response["choices"][0]["message"]

                                        # Check if message has content (not another tool call)
                                        if final_message_obj.get("content"):
                                            final_message = final_message_obj["content"]
                                            # Clean and format the response
                                            cleaned_message = clean_latex_artifacts(final_message)
                                            st.markdown(cleaned_message)
                                            st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": cleaned_message
                                            })

                                            # Show token usage
                                            usage = final_response.get("usage", {})
                                            st.caption(f"Tokens: {usage.get('total_tokens', 'N/A')} (prompt: {usage.get('prompt_tokens', 'N/A')}, completion: {usage.get('completion_tokens', 'N/A')})")
                                        else:
                                            # Model returned another tool call or empty response
                                            st.warning("⚠️ The model tried to call tools again. Please try rephrasing your question or disable tools for this query.")
                                            st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": "I encountered an issue processing your request. Please try again or disable tool usage."
                                            })
                            else:
                                # In enhanced mode, add a simple completion message
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": "I've retrieved and displayed the information for you."
                                })
                        else:
                            # Regular response without tool calls
                            # Check if streaming is enabled
                            if enable_streaming and not message.get("tool_calls"):
                                # Use streaming for real-time response
                                stream_response_obj = send_chat_completion(
                                    messages=st.session_state.messages,
                                    model=current_model,
                                    tools=selected_tools,
                                    stream=True
                                )

                                # Stream the response in real-time
                                full_response = st.write_stream(stream_response(stream_response_obj))
                                cleaned_message = clean_latex_artifacts(full_response)

                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": cleaned_message
                                })
                            else:
                                # Non-streaming response
                                assistant_message = message["content"]
                                # Clean and format the response
                                cleaned_message = clean_latex_artifacts(assistant_message)
                                st.markdown(cleaned_message)
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": cleaned_message
                                })

                                # Show token usage
                                usage = response.get("usage", {})
                                st.caption(f"Tokens: {usage.get('total_tokens', 'N/A')} (prompt: {usage.get('prompt_tokens', 'N/A')}, completion: {usage.get('completion_tokens', 'N/A')})")

                            # TTS playback option (if voice enabled)
                            if enable_voice and len(cleaned_message) > 0:
                                if st.button("🔊 Play Response", key=f"tts_{len(st.session_state.messages)}"):
                                    with st.spinner("🎤 Generating speech..."):
                                        try:
                                            tts_result = text_to_speech(cleaned_message)
                                            tts_data = json.loads(tts_result)
                                            if tts_data.get("status") == "success":
                                                # Decode base64 audio
                                                audio_bytes = base64.b64decode(tts_data.get("audio_base64"))
                                                # Play audio
                                                st.audio(audio_bytes, format='audio/wav')
                                            else:
                                                st.error(f"TTS failed: {tts_data.get('error')}")
                                        except Exception as e:
                                            st.error(f"Error generating speech: {e}")

        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()


# ============================================================================
# Tab 2: Tool Testing
# ============================================================================

with tab2:
    st.header("Function/Tool Calling")
    st.success("🚀 MLX Omni Server delivers 99% function calling accuracy!")

    if not model_loaded:
        st.warning("⚠️ Please load a model first")
    else:
        st.info("Test OpenAI-compatible function calling with custom tools")

        # Tool selection
        enable_calculator = st.checkbox("Enable Calculator", value=True)
        enable_search = st.checkbox("Enable Web Search", value=False)

        tools = []
        if enable_calculator:
            tools.append({
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Evaluate a mathematical expression",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to evaluate"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            })

        if enable_search:
            tools.append({
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            })

        # Test prompt
        test_prompt = st.text_area(
            "Test Prompt",
            value="Calculate 15 * 23 + 47",
            help="Try: 'Calculate sqrt(144)' or 'Search for Python tutorials'"
        )

        if st.button("🧪 Test Tool Call"):
            with st.spinner("Processing..."):
                response = send_chat_completion(
                    messages=[{"role": "user", "content": test_prompt}],
                    model=current_model,
                    tools=tools if tools else None
                )

                if "error" in response:
                    st.error(f"Error: {response['error']}")
                else:
                    st.success("Response received!")
                    st.json(response)


# ============================================================================
# Tab 3: Settings
# ============================================================================

with tab3:
    st.header("Generation Settings")

    st.subheader("Model Parameters")

    col1, col2 = st.columns(2)

    with col1:
        temperature = st.slider(
            "Temperature (τ)",
            min_value=0.0,
            max_value=2.0,
            value=float(os.getenv("TEMPERATURE", "0.7")),
            step=0.1,
            help="""**Temperature** controls randomness via softmax temperature scaling.

**How it works:**
- Modifies probability distribution: P(token) = exp(logit/τ) / Σ exp(logit_i/τ)
- τ → 0: Argmax selection (deterministic, greedy decoding)
- τ = 1.0: Unmodified probabilities (standard sampling)
- τ > 1.0: Flattened distribution (increased entropy, more random)

**Recommended values:**
- 0.0: Deterministic, reproducible outputs (code, facts)
- 0.3-0.5: Focused, factual responses
- 0.7-0.9: Balanced creativity and coherence
- 1.0-1.5: Creative writing, brainstorming
- 1.5-2.0: Highly random, experimental outputs"""
        )

        max_tokens = st.number_input(
            "Max Tokens (n)",
            min_value=1,
            max_value=32768,
            value=int(os.getenv("MAX_TOKENS", "512")),
            step=256,
            help="""**Max Tokens** limits the maximum sequence length of the generated response.

**Technical details:**
- Tokenization: Text is encoded into subword units (BPE/WordPiece)
- Approximation: 1 token ≈ 0.75 words (English)
- Includes: Both prompt tokens + completion tokens count toward context window

**Token-to-word estimates:**
- 100 tokens ≈ 75 words (~1-2 sentences)
- 512 tokens ≈ 384 words (~1 paragraph)
- 2,048 tokens ≈ 1,536 words (~1 page)
- 10,000 tokens ≈ 7,500 words (~15 pages)
- 32,768 tokens ≈ 24,576 words (~50 pages)

**Recommendations:**
- Short answers: 256-512 tokens
- Standard responses: 512-2,048 tokens
- Long-form content: 2,048-10,000 tokens
- Maximum generation: 10,000-32,768 tokens"""
        )

    with col2:
        top_p = st.slider(
            "Top-p / Nucleus Sampling (p)",
            min_value=0.0,
            max_value=1.0,
            value=float(os.getenv("TOP_P", "0.95")),
            step=0.05,
            help="""**Top-p (nucleus sampling)** dynamically truncates the token distribution.

**Algorithm:**
1. Sort tokens by probability: P(t₁) ≥ P(t₂) ≥ ... ≥ P(tₙ)
2. Compute cumulative sum until Σ P(tᵢ) ≥ p
3. Sample only from this "nucleus" set
4. Renormalize probabilities over selected tokens

**Behavior:**
- p = 1.0: Consider all tokens (no truncation)
- p = 0.95: Top 95% probability mass (standard, balanced)
- p = 0.9: Top 90% probability mass (more focused)
- p = 0.5: Top 50% probability mass (deterministic-like)
- p = 0.1: Very restrictive (near-greedy)

**Interaction with temperature:**
- Temperature=0 → Top-p has no effect (argmax always selected)
- Temperature>0 → Top-p filters tail probabilities before sampling
- Use both: Temperature shapes distribution, Top-p truncates long tail

**Recommended combinations:**
- Deterministic: temp=0, top_p=1.0
- Balanced: temp=0.7, top_p=0.9
- Creative: temp=0.9, top_p=0.95
- Focused: temp=0.5, top_p=0.8"""
        )

    # Store in session state
    st.session_state.temperature = temperature
    st.session_state.max_tokens = max_tokens
    st.session_state.top_p = top_p

    st.divider()

    # ========================================================================
    # Parameter Reference Guide
    # ========================================================================

    st.subheader("📚 Parameter Reference Guide")

    with st.expander("🎯 Quick Reference: Common Use Cases", expanded=False):
        st.markdown("""
        ### Code Generation & Technical Writing
        ```
        Temperature: 0.0-0.3
        Top-p: 0.8-1.0
        Max Tokens: 2048-4096
        ```
        **Why:** Deterministic output, precise syntax, reproducible results

        ---

        ### Factual Q&A & Documentation
        ```
        Temperature: 0.3-0.5
        Top-p: 0.9
        Max Tokens: 512-2048
        ```
        **Why:** Focused responses, minimal hallucination, consistent answers

        ---

        ### General Chat & Assistance
        ```
        Temperature: 0.7-0.8
        Top-p: 0.9-0.95
        Max Tokens: 1024-2048
        ```
        **Why:** Balanced creativity and coherence, natural conversation

        ---

        ### Creative Writing & Brainstorming
        ```
        Temperature: 0.9-1.2
        Top-p: 0.95-1.0
        Max Tokens: 2048-8192
        ```
        **Why:** Diverse ideas, unexpected connections, varied vocabulary

        ---

        ### Long-form Content Generation
        ```
        Temperature: 0.7-0.9
        Top-p: 0.9
        Max Tokens: 10000-32768
        ```
        **Why:** Extended coherence, detailed explanations, complete articles
        """)

    with st.expander("🔬 Mathematical Formulation", expanded=False):
        st.markdown("""
        ### Softmax Temperature Scaling

        Given logits **z** from the model's final layer:

        $$P(token_i | z, \\tau) = \\frac{e^{z_i / \\tau}}{\\sum_{j=1}^{V} e^{z_j / \\tau}}$$

        Where:
        - **τ** (tau) = temperature parameter
        - **V** = vocabulary size (~50,000+ tokens)
        - **z<sub>i</sub>** = logit (raw score) for token i

        **Effect on entropy:**
        - τ → 0: Entropy → 0 (deterministic)
        - τ = 1: Standard softmax (model's learned distribution)
        - τ → ∞: Entropy → log(V) (uniform distribution)

        ---

        ### Nucleus Sampling (Top-p)

        **Step 1:** Sort vocabulary by probability
        $$P(t_1) \\geq P(t_2) \\geq ... \\geq P(t_V)$$

        **Step 2:** Find minimum set **V<sub>p</sub>** where:
        $$\\sum_{t \\in V_p} P(t) \\geq p$$

        **Step 3:** Sample from renormalized distribution:
        $$P'(t) = \\begin{cases}
        \\frac{P(t)}{\\sum_{t' \\in V_p} P(t')} & \\text{if } t \\in V_p \\\\
        0 & \\text{otherwise}
        \\end{cases}$$

        **Dynamic truncation:** Nucleus size varies per token (adaptive)

        ---

        ### Alternative Methods (Not Implemented)

        **Top-k Sampling:** Fixed k tokens (inflexible)
        $$V_k = \\{t_1, t_2, ..., t_k\\}$$

        **Beam Search:** Maintains top-k sequences (deterministic)
        """)

    with st.expander("⚡ Performance Considerations", expanded=False):
        st.markdown("""
        ### Inference Speed vs Quality

        | Parameter | Speed Impact | Quality Impact |
        |-----------|-------------|----------------|
        | **Max Tokens** | Linear O(n) | Longer context |
        | **Temperature** | Negligible | Distribution shape |
        | **Top-p** | Small (~5%) | Tail truncation |

        ### Memory Usage

        **Formula:** Memory ≈ max_tokens × model_size × precision

        For **3B parameter model (4-bit quantized)**:
        - 512 tokens: ~200 MB additional
        - 2,048 tokens: ~800 MB additional
        - 10,000 tokens: ~4 GB additional
        - 32,768 tokens: ~13 GB additional

        ### Latency Estimates (M2 MacBook Pro)

        **3B model (Qwen2.5/Llama-3.2):**
        - First token: 500-1000ms (prompt processing)
        - Subsequent: 50-100ms per token (~10-20 tokens/sec)
        - 512 tokens: ~30-50 seconds
        - 2,048 tokens: ~2-3 minutes

        **8B model (Llama-3.1):**
        - First token: 1-2 seconds
        - Subsequent: 150-200ms per token (~5-7 tokens/sec)
        - 512 tokens: ~1.5-2 minutes
        """)

    st.divider()

    st.subheader("Server Information")
    st.info(f"""
    **API Endpoint:** {API_URL}

    **Environment:**
    - API Port: {API_PORT}
    - UI Port: {os.getenv("UI_PORT", "7006")}
    - Model Cache: {os.getenv("MODEL_CACHE_DIR", "./models")}
    - Default Model: {os.getenv("DEFAULT_MODEL", "N/A")}
    """)


# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("MLX Omni Server Control Panel v2.0 | Powered by Apple MLX | 99% Function Calling Accuracy")
