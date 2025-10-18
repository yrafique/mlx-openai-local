"""
LangChain Streaming with MLX Omni Server
Demonstrates real-time streaming responses from local MLX model
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Load environment variables
load_dotenv()

# Configure LangChain to use MLX Omni Server with streaming
llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",
    model="mlx-community/Qwen2.5-3B-Instruct-4bit",
    temperature=0.7,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
)

print("=" * 80)
print("MLX Omni Server - Streaming Response Demo")
print("=" * 80)
print()

# Test streaming
query = "Write a short poem about Apple Silicon and machine learning"

print(f"Query: {query}\n")
print("Streaming response:\n")
print("-" * 80)

response = llm.invoke(query)

print()
print("-" * 80)
print(f"\n✅ Streaming complete!\n")
print("=" * 80)
