"""
Pytest tests for MLX OpenAI Server.
Tests chat completions, tool calling, and model switching.
"""

import pytest
import requests
import json
import os
from typing import Dict, Any

# Configuration
API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:7007/v1")
API_URL = API_BASE.rstrip("/v1")


@pytest.fixture(scope="module")
def api_url():
    """Fixture providing the API URL."""
    return API_BASE


@pytest.fixture(scope="module")
def ensure_server_running():
    """Ensure the server is running before tests."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        assert response.status_code == 200, "Server is not running"
        yield
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Cannot connect to server: {e}")


def test_health_check(ensure_server_running):
    """Test the health endpoint."""
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_list_models(api_url, ensure_server_running):
    """Test /v1/models endpoint."""
    response = requests.get(f"{api_url}/models")
    assert response.status_code == 200

    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    # Check model structure
    model = data["data"][0]
    assert "id" in model
    assert "object" in model
    assert model["object"] == "model"


def test_chat_completion_basic(api_url, ensure_server_running):
    """Test basic chat completion."""
    payload = {
        "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "max_tokens": 20,
        "temperature": 0.7
    }

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        timeout=60
    )

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert "object" in data
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert len(data["choices"]) > 0

    choice = data["choices"][0]
    assert "message" in choice
    assert "content" in choice["message"]
    assert isinstance(choice["message"]["content"], str)

    # Check usage
    assert "usage" in data
    assert "prompt_tokens" in data["usage"]
    assert "completion_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]


def test_chat_completion_with_system_message(api_url, ensure_server_running):
    """Test chat completion with system message."""
    payload = {
        "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        "max_tokens": 30,
        "temperature": 0.5
    }

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        timeout=60
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["choices"]) > 0
    assert "content" in data["choices"][0]["message"]


def test_chat_completion_with_temperature(api_url, ensure_server_running):
    """Test chat completion with different temperatures."""
    base_payload = {
        "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "max_tokens": 10
    }

    # Test low temperature
    payload_low = {**base_payload, "temperature": 0.1}
    response_low = requests.post(
        f"{api_url}/chat/completions",
        json=payload_low,
        timeout=60
    )
    assert response_low.status_code == 200

    # Test high temperature
    payload_high = {**base_payload, "temperature": 1.5}
    response_high = requests.post(
        f"{api_url}/chat/completions",
        json=payload_high,
        timeout=60
    )
    assert response_high.status_code == 200


@pytest.mark.skipif(
    not os.getenv("TEST_TOOLS", "false").lower() == "true",
    reason="Tool calling tests disabled by default (set TEST_TOOLS=true to enable)"
)
def test_tool_calling_calculator(api_url, ensure_server_running):
    """Test function calling with calculator tool."""
    payload = {
        "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
        "messages": [
            {"role": "user", "content": "Calculate 15 * 23"}
        ],
        "max_tokens": 100,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Evaluate a mathematical expression",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ],
        "tool_choice": "auto"
    }

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        timeout=120
    )

    assert response.status_code == 200
    data = response.json()

    # Check if tool was called or final answer given
    # (depends on model's ability to call tools)
    assert "choices" in data
    assert len(data["choices"]) > 0


@pytest.mark.skipif(
    not os.getenv("TEST_STREAMING", "false").lower() == "true",
    reason="Streaming tests disabled by default (set TEST_STREAMING=true to enable)"
)
def test_streaming_chat_completion(api_url, ensure_server_running):
    """Test streaming chat completion."""
    payload = {
        "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
        "messages": [
            {"role": "user", "content": "Count to 3"}
        ],
        "max_tokens": 30,
        "stream": True
    }

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        timeout=60,
        stream=True
    )

    assert response.status_code == 200

    chunks = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                data_str = line_str[6:]  # Remove "data: " prefix
                if data_str == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data_str)
                    chunks.append(chunk_data)
                except json.JSONDecodeError:
                    pass

    # Verify we got chunks
    assert len(chunks) > 0
    assert chunks[0]["object"] == "chat.completion.chunk"


def test_invalid_model(api_url, ensure_server_running):
    """Test requesting an invalid model."""
    payload = {
        "model": "invalid-model-name",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 10
    }

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        timeout=60
    )

    # Should return error (400 or 500)
    assert response.status_code in [400, 500]


def test_missing_messages(api_url, ensure_server_running):
    """Test request without messages."""
    payload = {
        "model": "mlx-community/TinyLlama-1.1B-Chat-v1.0-mlx",
        "max_tokens": 10
    }

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        timeout=60
    )

    # Should return 422 (validation error)
    assert response.status_code == 422


@pytest.mark.skipif(
    not os.getenv("TEST_MODEL_SWITCHING", "false").lower() == "true",
    reason="Model switching tests disabled (set TEST_MODEL_SWITCHING=true to enable)"
)
def test_model_switching(api_url, ensure_server_running):
    """Test switching between models (requires multiple models in ALLOWED_MODELS)."""
    # Get available models
    models_response = requests.get(f"{api_url}/models")
    models = models_response.json()["data"]

    if len(models) < 2:
        pytest.skip("Need at least 2 models for switching test")

    model1 = models[0]["id"]
    model2 = models[1]["id"]

    # Test with first model
    payload1 = {
        "model": model1,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    response1 = requests.post(f"{api_url}/chat/completions", json=payload1, timeout=120)
    assert response1.status_code == 200

    # Test with second model
    payload2 = {
        "model": model2,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    response2 = requests.post(f"{api_url}/chat/completions", json=payload2, timeout=120)
    assert response2.status_code == 200


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_chat.py -v
    pytest.main([__file__, "-v"])
