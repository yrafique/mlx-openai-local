"""
LangChain Basic Integration with MLX Omni Server
Demonstrates simple chat completion using LangChain with local MLX model
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Configure LangChain to use MLX Omni Server
llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",  # Not used but required by API
    model="mlx-community/Qwen2.5-3B-Instruct-4bit",
    temperature=0.7,
)

# Simple chat
print("=" * 60)
print("LangChain + MLX Omni Server - Basic Chat")
print("=" * 60)

response = llm.invoke("Explain what MLX is in 2 sentences")
print(f"\nResponse: {response.content}\n")

# Multi-turn conversation
from langchain.schema import HumanMessage, AIMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful AI assistant running locally on Apple Silicon."),
    HumanMessage(content="What are the benefits of local LLM inference?"),
]

response = llm.invoke(messages)
print("=" * 60)
print("Multi-turn Conversation")
print("=" * 60)
print(f"\nAssistant: {response.content}\n")

# Continue conversation
messages.append(AIMessage(content=response.content))
messages.append(HumanMessage(content="How does MLX help with this?"))

response = llm.invoke(messages)
print(f"Assistant: {response.content}\n")

print("=" * 60)
print("✅ Basic LangChain integration working!")
print("=" * 60)
