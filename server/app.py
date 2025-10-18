"""
FastAPI OpenAI-compatible server for MLX local inference.
Implements /v1/models, /v1/chat/completions with streaming and tool calling.
"""

import json
import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from server.openai_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
    ModelsResponse,
    ModelObject,
    ChatCompletionStreamChunk,
    ChatCompletionStreamChoice,
    ToolCall,
    ErrorResponse,
    ErrorDetail
)
from server.model_manager import model_manager
from server.utils import (
    logger,
    generate_id,
    stream_json_response,
    stream_done_signal,
    get_chat_formatter,
    count_tokens_in_messages,
    estimate_tokens,
    get_config,
    create_error_response
)
from server.tools import execute_tool, get_tool_schemas, list_available_tools


# Initialize FastAPI app
app = FastAPI(
    title="MLX OpenAI-Compatible API",
    description="Local LLM serving with MLX and OpenAI API compatibility",
    version="1.0.0"
)

# Add CORS middleware (optional, for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7006", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config = get_config()


# ============================================================================
# Startup / Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load default model on startup."""
    logger.info("Starting MLX OpenAI-compatible server...")

    # Load default model
    default_model = config["default_model"]
    if default_model:
        try:
            logger.info(f"Loading default model: {default_model}")
            await model_manager.load_model(default_model)
            logger.info(f"Default model {default_model} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load default model: {e}")
            logger.warning("Server started without a loaded model. Use /v1/models endpoint to load one.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down server...")
    await model_manager.unload_model()
    logger.info("Server shutdown complete")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    model_info = await model_manager.current_model_info()
    return {
        "status": "healthy",
        "model_loaded": model_info is not None,
        "current_model": model_info.get("model_id") if model_info else None
    }


# ============================================================================
# /v1/models - List Available Models
# ============================================================================

@app.get("/v1/models")
async def list_models() -> ModelsResponse:
    """
    List all available models (OpenAI-compatible endpoint).

    Returns:
        ModelsResponse with list of model objects
    """
    try:
        available_models = await model_manager.list_available_models()
        current_info = await model_manager.current_model_info()

        model_objects = []
        for model_id in available_models:
            model_obj = ModelObject(
                id=model_id,
                owned_by="mlx-local"
            )
            model_objects.append(model_obj)

        # Mark current model if loaded
        if current_info:
            current_id = current_info["model_id"]
            # Ensure current model is in the list
            if current_id not in available_models:
                model_objects.append(ModelObject(
                    id=current_id,
                    owned_by="mlx-local"
                ))

        return ModelsResponse(data=model_objects)

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Model Management Endpoints (Custom)
# ============================================================================

@app.post("/v1/models/load")
async def load_model_endpoint(request: Dict[str, Any]):
    """
    Load a specific model.

    Body: {"model": "model_id"}
    """
    try:
        model_id = request.get("model")
        if not model_id:
            raise HTTPException(status_code=400, detail="Missing 'model' field")

        # Check if model is allowed
        allowed = await model_manager.list_available_models()
        if model_id not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Model {model_id} not in ALLOWED_MODELS. Available: {allowed}"
            )

        result = await model_manager.load_model(model_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/models/unload")
async def unload_model_endpoint():
    """Unload the currently loaded model."""
    try:
        await model_manager.unload_model()
        return {"status": "success", "message": "Model unloaded"}
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/models/update")
async def update_model_endpoint(request: Dict[str, Any]):
    """
    Update a model from Hugging Face.

    Body: {"model": "model_id"}
    """
    try:
        model_id = request.get("model")
        if not model_id:
            raise HTTPException(status_code=400, detail="Missing 'model' field")

        result_path = await model_manager.update_model(model_id)
        return {
            "status": "success",
            "message": f"Model {model_id} updated",
            "path": str(result_path)
        }

    except Exception as e:
        logger.error(f"Error updating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# /v1/chat/completions - Main Chat Endpoint
# ============================================================================

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create a chat completion (OpenAI-compatible endpoint).

    Supports:
    - Streaming (stream=true)
    - Tool calling (tools, tool_choice)
    - Temperature, top_p, max_tokens
    """
    try:
        # Ensure a model is loaded
        current_info = await model_manager.current_model_info()
        if not current_info:
            # Try to load the requested model or default
            model_to_load = request.model or config["default_model"]
            logger.info(f"No model loaded, attempting to load {model_to_load}")
            await model_manager.load_model(model_to_load)
            current_info = await model_manager.current_model_info()

        current_model_id = current_info["model_id"]

        # If request specifies a different model, switch
        if request.model and request.model != current_model_id:
            allowed = await model_manager.list_available_models()
            if request.model not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model {request.model} not allowed. Available: {allowed}"
                )
            logger.info(f"Switching model from {current_model_id} to {request.model}")
            await model_manager.load_model(request.model)
            current_model_id = request.model

        # Handle streaming vs non-streaming
        if request.stream:
            return StreamingResponse(
                stream_chat_completion(request, current_model_id),
                media_type="text/event-stream"
            )
        else:
            return await non_streaming_chat_completion(request, current_model_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def non_streaming_chat_completion(
    request: ChatCompletionRequest,
    model_id: str
) -> ChatCompletionResponse:
    """
    Generate a non-streaming chat completion.

    Handles tool calling if tools are provided.
    """
    messages = [msg.model_dump() for msg in request.messages]
    tools = request.tools
    max_iterations = 3  # Max tool calling iterations

    # Tool calling loop
    for iteration in range(max_iterations):
        # Format prompt
        formatter = get_chat_formatter(model_id)
        prompt = formatter(messages)

        # Generate completion
        result = await model_manager.generate_completion(
            prompt=prompt,
            max_tokens=request.max_tokens or config["max_tokens"],
            temperature=request.temperature or config["temperature"],
            top_p=request.top_p or config["top_p"]
        )

        generated_text = result["text"]
        prompt_tokens = result["prompt_tokens"]
        completion_tokens = result["completion_tokens"]

        # Check for tool calls in the response
        tool_calls_detected = []
        if tools and request.tool_choice != "none":
            # Parse for tool calls (simplified heuristic)
            tool_call = await detect_tool_call(generated_text, tools)
            if tool_call:
                tool_calls_detected.append(tool_call)

        # If no tool calls, return final response
        if not tool_calls_detected:
            # Final response
            response_message = ChatMessage(
                role="assistant",
                content=generated_text
            )

            choice = ChatCompletionChoice(
                index=0,
                message=response_message,
                finish_reason="stop"
            )

            usage = ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )

            return ChatCompletionResponse(
                id=generate_id("chatcmpl"),
                model=model_id,
                choices=[choice],
                usage=usage
            )

        # Execute tool calls
        logger.info(f"Detected {len(tool_calls_detected)} tool call(s)")

        # Add assistant message with tool calls
        assistant_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [tc.model_dump() for tc in tool_calls_detected]
        }
        messages.append(assistant_message)

        # Execute each tool and add results
        for tool_call in tool_calls_detected:
            tool_name = tool_call.function["name"]
            tool_args_str = tool_call.function["arguments"]

            try:
                tool_args = json.loads(tool_args_str)
            except:
                tool_args = {}

            logger.info(f"Executing tool: {tool_name} with args {tool_args}")

            tool_result = execute_tool(tool_name, tool_args)

            # Add tool result message
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            }
            messages.append(tool_message)

        # Continue loop to generate final answer with tool results

    # If we exhausted iterations, return last response
    logger.warning("Max tool call iterations reached")
    response_message = ChatMessage(
        role="assistant",
        content="Maximum tool calling iterations reached."
    )

    choice = ChatCompletionChoice(
        index=0,
        message=response_message,
        finish_reason="length"
    )

    usage = ChatCompletionUsage(
        prompt_tokens=count_tokens_in_messages(messages),
        completion_tokens=0,
        total_tokens=count_tokens_in_messages(messages)
    )

    return ChatCompletionResponse(
        id=generate_id("chatcmpl"),
        model=model_id,
        choices=[choice],
        usage=usage
    )


async def stream_chat_completion(request: ChatCompletionRequest, model_id: str):
    """
    Generate a streaming chat completion.

    Yields Server-Sent Events (SSE) chunks.
    """
    try:
        messages = [msg.model_dump() for msg in request.messages]

        # Format prompt
        formatter = get_chat_formatter(model_id)
        prompt = formatter(messages)

        # Generate streaming response
        chunk_id = generate_id("chatcmpl")

        # Send initial chunk
        initial_chunk = ChatCompletionStreamChunk(
            id=chunk_id,
            model=model_id,
            choices=[ChatCompletionStreamChoice(
                index=0,
                delta={"role": "assistant"},
                finish_reason=None
            )]
        )
        yield await stream_json_response(initial_chunk.model_dump())

        # Stream tokens (simplified - MLX doesn't support true streaming yet)
        result = await model_manager.generate_completion(
            prompt=prompt,
            max_tokens=request.max_tokens or config["max_tokens"],
            temperature=request.temperature or config["temperature"],
            top_p=request.top_p or config["top_p"]
        )

        generated_text = result["text"]

        # Split into words and stream
        words = generated_text.split()
        for word in words:
            chunk = ChatCompletionStreamChunk(
                id=chunk_id,
                model=model_id,
                choices=[ChatCompletionStreamChoice(
                    index=0,
                    delta={"content": word + " "},
                    finish_reason=None
                )]
            )
            yield await stream_json_response(chunk.model_dump())

        # Send final chunk
        final_chunk = ChatCompletionStreamChunk(
            id=chunk_id,
            model=model_id,
            choices=[ChatCompletionStreamChoice(
                index=0,
                delta={},
                finish_reason="stop"
            )]
        )
        yield await stream_json_response(final_chunk.model_dump())

        # Send done signal
        yield await stream_done_signal()

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_chunk = create_error_response(str(e))
        yield await stream_json_response(error_chunk)


async def detect_tool_call(text: str, tools: List) -> ToolCall:
    """
    Detect tool calls in generated text (simplified heuristic).

    In production, use a more robust parser or fine-tuned model.

    Returns:
        ToolCall object if detected, None otherwise
    """
    if not tools:
        return None

    # Extract tool names
    tool_names = [tool.function.name for tool in tools]

    # Simple pattern matching
    import re

    # Look for: TOOL: function_name(args) or function_name: {...}
    for tool_name in tool_names:
        # Pattern 1: TOOL: name(...)
        pattern1 = rf'TOOL:\s*{tool_name}\((.*?)\)'
        match = re.search(pattern1, text, re.IGNORECASE)

        if match:
            args_str = match.group(1)
            try:
                args_dict = json.loads(args_str)
            except:
                args_dict = {}

            return ToolCall(
                id=generate_id("call"),
                type="function",
                function={
                    "name": tool_name,
                    "arguments": json.dumps(args_dict)
                }
            )

        # Pattern 2: function_name: {...}
        pattern2 = rf'{tool_name}:\s*(\{{.*?\}})'
        match = re.search(pattern2, text, re.IGNORECASE | re.DOTALL)

        if match:
            args_str = match.group(1)
            return ToolCall(
                id=generate_id("call"),
                type="function",
                function={
                    "name": tool_name,
                    "arguments": args_str
                }
            )

    return None


# ============================================================================
# /v1/embeddings - Optional Endpoint
# ============================================================================

@app.post("/v1/embeddings")
async def create_embeddings(request: Dict[str, Any]):
    """
    Embeddings endpoint (not implemented for most LLMs).

    Returns 501 Not Implemented.
    """
    raise HTTPException(
        status_code=501,
        detail="Embeddings not supported. Use a dedicated embedding model."
    )


# ============================================================================
# Main Entry Point (for direct execution)
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server.app:app",
        host=config["api_host"],
        port=config["api_port"],
        log_level="info"
    )
