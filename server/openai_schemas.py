"""
OpenAI-compatible API schemas using Pydantic v2.
Implements /v1/models, /v1/chat/completions, and /v1/embeddings endpoints.
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
import time


# ============================================================================
# Tool / Function Calling Schemas
# ============================================================================

class FunctionDefinition(BaseModel):
    """OpenAI function definition schema."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """OpenAI tool definition schema."""
    type: Literal["function"] = "function"
    function: FunctionDefinition


class ToolCall(BaseModel):
    """Tool call made by the model."""
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, Any]  # {"name": str, "arguments": str (JSON)}


class FunctionCall(BaseModel):
    """Deprecated function call format (kept for compatibility)."""
    name: str
    arguments: str  # JSON string


# ============================================================================
# Chat Completion Schemas
# ============================================================================

class ChatMessage(BaseModel):
    """Single message in a chat conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """Request schema for /v1/chat/completions."""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=512, ge=1)
    stream: Optional[bool] = False
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[Union[Literal["none", "auto"], Dict[str, Any]]] = "auto"
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    """Single choice in a chat completion response."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None  # "stop", "length", "tool_calls", "content_filter"


class ChatCompletionUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response schema for /v1/chat/completions."""
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


# ============================================================================
# Streaming Schemas
# ============================================================================

class ChatCompletionStreamChoice(BaseModel):
    """Single choice in a streaming chunk."""
    index: int
    delta: Dict[str, Any]  # Can contain role, content, tool_calls
    finish_reason: Optional[str] = None


class ChatCompletionStreamChunk(BaseModel):
    """Streaming chunk for chat completions."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionStreamChoice]


# ============================================================================
# Models Endpoint Schemas
# ============================================================================

class ModelObject(BaseModel):
    """Single model object."""
    id: str
    object: Literal["model"] = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "mlx-local"
    permission: List[Any] = Field(default_factory=list)
    root: Optional[str] = None
    parent: Optional[str] = None


class ModelsResponse(BaseModel):
    """Response schema for /v1/models."""
    object: Literal["list"] = "list"
    data: List[ModelObject]


# ============================================================================
# Embeddings Schemas (Optional)
# ============================================================================

class EmbeddingRequest(BaseModel):
    """Request schema for /v1/embeddings."""
    model: str
    input: Union[str, List[str]]
    encoding_format: Optional[Literal["float", "base64"]] = "float"
    user: Optional[str] = None


class EmbeddingObject(BaseModel):
    """Single embedding object."""
    object: Literal["embedding"] = "embedding"
    embedding: List[float]
    index: int


class EmbeddingUsage(BaseModel):
    """Token usage for embeddings."""
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """Response schema for /v1/embeddings."""
    object: Literal["list"] = "list"
    data: List[EmbeddingObject]
    model: str
    usage: EmbeddingUsage


# ============================================================================
# Error Schema
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail object."""
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: ErrorDetail
