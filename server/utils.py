"""
Utility functions for MLX OpenAI server.
Includes streaming helpers, logging setup, tokenization, and more.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging() -> logging.Logger:
    """
    Configure logging with rotation to LOG_DIR.
    Returns the configured logger instance.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = Path(os.getenv("LOG_DIR", "./logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("mlx-openai-server")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level, logging.INFO))
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


# ============================================================================
# ID Generation
# ============================================================================

def generate_id(prefix: str = "chatcmpl") -> str:
    """Generate OpenAI-style IDs."""
    return f"{prefix}-{uuid.uuid4().hex[:24]}"


# ============================================================================
# Streaming Helpers
# ============================================================================

async def stream_json_response(data: Dict[str, Any]) -> str:
    """
    Format a chunk for Server-Sent Events (SSE).
    Returns: "data: {json}\n\n"
    """
    return f"data: {json.dumps(data)}\n\n"


async def stream_done_signal() -> str:
    """Send the [DONE] signal for SSE streams."""
    return "data: [DONE]\n\n"


# ============================================================================
# Token Counting (Approximation)
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (avg 4 chars per token).
    For accurate counts, use the model's tokenizer.
    """
    return max(1, len(text) // 4)


def count_tokens_in_messages(messages: List[Dict[str, Any]]) -> int:
    """
    Estimate total tokens in a message list.
    """
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if content:
            total += estimate_tokens(content)
        # Account for role and structure overhead
        total += 4
    return total


# ============================================================================
# Chat Template Formatting
# ============================================================================

def format_chat_prompt(messages: List[Dict[str, Any]], model_name: str = "") -> str:
    """
    Convert messages array into a single prompt string.
    Uses a basic template; can be extended for model-specific formats.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model_name: Optional model identifier for custom templates

    Returns:
        Formatted prompt string
    """
    # Simple template for TinyLlama / general instruction models
    prompt_parts = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            prompt_parts.append(f"<|system|>\n{content}")
        elif role == "user":
            prompt_parts.append(f"<|user|>\n{content}")
        elif role == "assistant":
            prompt_parts.append(f"<|assistant|>\n{content}")
        elif role == "tool":
            # Tool results are injected as special user messages
            tool_call_id = msg.get("tool_call_id", "unknown")
            prompt_parts.append(f"<|user|>\n[Tool Result {tool_call_id}]\n{content}")

    # Add final assistant prompt
    prompt_parts.append("<|assistant|>")

    return "\n".join(prompt_parts)


def format_qwen_prompt(messages: List[Dict[str, Any]]) -> str:
    """
    Qwen-specific chat template.
    Format: <|im_start|>role\ncontent<|im_end|>
    """
    prompt_parts = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")

    # Add assistant start
    prompt_parts.append("<|im_start|>assistant\n")

    return "\n".join(prompt_parts)


def get_chat_formatter(model_name: str):
    """
    Return the appropriate chat formatter function based on model name.
    """
    model_lower = model_name.lower()

    if "qwen" in model_lower:
        return format_qwen_prompt
    else:
        return format_chat_prompt


# ============================================================================
# Configuration Helpers
# ============================================================================

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    """
    return {
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("API_PORT", "7007")),
        "ui_port": int(os.getenv("UI_PORT", "7006")),
        "default_model": os.getenv("DEFAULT_MODEL", "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx"),
        "allowed_models": os.getenv("ALLOWED_MODELS", "").split(","),
        "model_cache_dir": os.getenv("MODEL_CACHE_DIR", "./models"),
        "hf_token": os.getenv("HF_TOKEN", None),
        "max_tokens": int(os.getenv("MAX_TOKENS", "512")),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "top_p": float(os.getenv("TOP_P", "0.95")),
    }


# ============================================================================
# Error Response Helper
# ============================================================================

def create_error_response(message: str, error_type: str = "invalid_request_error",
                         code: str = None, param: str = None) -> Dict[str, Any]:
    """
    Create an OpenAI-style error response.
    """
    return {
        "error": {
            "message": message,
            "type": error_type,
            "code": code,
            "param": param
        }
    }


# ============================================================================
# Model Name Parsing
# ============================================================================

def parse_model_id(model_id: str) -> Dict[str, str]:
    """
    Parse a Hugging Face model ID into components.

    Example: "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx"
    Returns: {"org": "mlx-community", "name": "TinyLlama-1.1B-Chat-v1.0-mlx"}
    """
    parts = model_id.split("/")
    if len(parts) == 2:
        return {"org": parts[0], "name": parts[1]}
    else:
        return {"org": "", "name": model_id}


# ============================================================================
# Tool Calling Helpers
# ============================================================================

def extract_tool_call_from_text(text: str, available_tools: List[str]) -> Dict[str, Any]:
    """
    Simple heuristic to detect tool calls in generated text.
    Looks for patterns like: TOOL: tool_name(arg1="value", arg2=123)

    Returns: {"name": str, "arguments": dict} or None
    """
    import re

    # Pattern: TOOL: function_name(json_args)
    pattern = r'TOOL:\s*(\w+)\((.*?)\)'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        function_name = match.group(1)
        args_str = match.group(2)

        # Only recognize known tools
        if function_name not in available_tools:
            return None

        # Try to parse arguments (simple key=value parser)
        try:
            import json
            # Attempt JSON parse
            args_dict = json.loads(args_str) if args_str else {}
        except:
            # Fallback to simple parsing
            args_dict = {}
            if args_str:
                # Simple key="value" parsing
                pairs = re.findall(r'(\w+)=(["\'])(.*?)\2', args_str)
                for key, _, value in pairs:
                    args_dict[key] = value

        return {
            "name": function_name,
            "arguments": json.dumps(args_dict)
        }

    return None


logger.info("Utils module initialized")
