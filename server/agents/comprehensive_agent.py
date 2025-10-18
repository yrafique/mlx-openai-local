"""
Comprehensive AI Agent using LangChain and LangGraph.
Provides ChatGPT-level capabilities with advanced orchestration.
"""

from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.checkpoint.sqlite import SqliteSaver
import json
import os

# Import our custom tools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.code_execution import execute_python_code
from tools.financial_data import get_stock_price, get_crypto_price, get_stock_history
from tools.enhanced_web_search import search_web_enhanced, get_weather_enhanced
from tools.file_analysis import analyze_file
from tools.table_formatter import format_table
from prompts.system_prompt import get_system_prompt


# Agent State
class AgentState(TypedDict):
    """State of the agent"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_action: str


# Define LangChain tools from our existing functions
@tool
def execute_code(code: str, timeout: int = 30) -> str:
    """
    Execute Python code and return results. Can run calculations, generate plots,
    analyze data, and more. Has access to numpy, pandas, matplotlib, plotly.
    """
    return execute_python_code(code, timeout)


@tool
def get_stock_data(symbol: str) -> str:
    """
    Get current real-time stock price. Use for accurate financial data.
    Works for US stocks and ETFs like AAPL, TSLA, QQQ, SPY, etc.
    """
    return get_stock_price(symbol)


@tool
def get_crypto_data(symbol: str) -> str:
    """
    Get current cryptocurrency price in USD.
    Works for BTC, ETH, DOGE, and other major cryptocurrencies.
    """
    return get_crypto_price(symbol)


@tool
def get_historical_stock_data(symbol: str, period: str = "10mo", interval: str = "1mo") -> str:
    """
    Get historical stock price data with interactive chart.
    Period options: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10mo
    Interval options: 1d, 1wk, 1mo
    """
    return get_stock_history(symbol, period, interval)


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web and get AI-synthesized answers. Use for current information,
    recent news, or facts you're unsure about. Returns processed, relevant information.
    """
    return search_web_enhanced(query, max_results)


@tool
def get_weather(location: str) -> str:
    """
    Get current weather for a location. Returns temperature, conditions, and forecast.
    """
    return get_weather_enhanced(location)


@tool
def analyze_data_file(file_base64: str, filename: str, analysis_type: str = "auto") -> str:
    """
    Analyze uploaded files (CSV, Excel, JSON, text, code, images).
    Returns statistics, summaries, and insights.
    """
    return analyze_file(file_base64, filename, analysis_type)


@tool
def create_table(data: str, table_type: str = "auto") -> str:
    """
    Format data into beautiful markdown tables. Data should be JSON string
    containing list of dictionaries representing table rows.
    """
    return format_table(data, table_type)


# Create tool list for LangChain
LANGCHAIN_TOOLS = [
    execute_code,
    get_stock_data,
    get_crypto_data,
    get_historical_stock_data,
    search_web,
    get_weather,
    analyze_data_file,
    create_table
]


class ComprehensiveAgent:
    """
    Comprehensive AI Agent with ChatGPT-level capabilities.

    Uses LangGraph for orchestration, LangChain for tools,
    and provides advanced reasoning, code execution, web search,
    financial data, file analysis, and more.
    """

    def __init__(self, model_name: str = None, mode: str = "advanced"):
        """
        Initialize the comprehensive agent.

        Args:
            model_name: Model to use (defaults to env variable)
            mode: System prompt mode ("advanced", "reasoning", "code")
        """
        # Initialize LLM
        api_base = os.getenv("OPENAI_API_BASE", "http://localhost:7007/v1")
        self.model_name = model_name or os.getenv("DEFAULT_MODEL", "mlx-community/Llama-3.2-3B-Instruct-4bit")

        # Create LangChain LLM
        self.llm = ChatOpenAI(
            base_url=api_base,
            api_key="local-demo-key",
            model=self.model_name,
            temperature=0.7
        )

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(LANGCHAIN_TOOLS)

        # Create tool executor
        self.tool_executor = ToolExecutor(LANGCHAIN_TOOLS)

        # Get system prompt
        self.system_prompt = get_system_prompt(mode)

        # Create graph
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("action", self._execute_tools)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "action",
                "end": END
            }
        )

        # Add edge from action back to agent
        workflow.add_edge("action", "agent")

        # Compile graph
        return workflow.compile()

    def _call_model(self, state: AgentState) -> dict:
        """Call the LLM with current state."""
        messages = state["messages"]

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + list(messages)

        # Call LLM
        response = self.llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def _execute_tools(self, state: AgentState) -> dict:
        """Execute tools requested by the model."""
        messages = state["messages"]
        last_message = messages[-1]

        # Extract tool calls
        tool_results = []

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                # Execute tool
                action = ToolInvocation(
                    tool=tool_call["name"],
                    tool_input=tool_call["args"]
                )

                result = self.tool_executor.invoke(action)

                # Create tool message
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
                tool_results.append(tool_message)

        return {"messages": tool_results}

    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If there are tool calls, continue
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        # Otherwise, end
        return "end"

    def run(self, user_input: str, chat_history: list = None) -> dict:
        """
        Run the agent on user input.

        Args:
            user_input: User's message
            chat_history: Previous conversation messages

        Returns:
            dict with response, tool_calls, and full history
        """
        # Build messages
        messages = []

        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Add current user message
        messages.append(HumanMessage(content=user_input))

        # Run graph
        result = self.graph.invoke({"messages": messages})

        # Extract final response
        final_message = result["messages"][-1]

        # Parse response
        response_data = {
            "response": final_message.content if hasattr(final_message, "content") else str(final_message),
            "tool_calls": [],
            "messages": result["messages"]
        }

        # Extract tool calls from history
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    response_data["tool_calls"].append({
                        "name": tc["name"],
                        "args": tc["args"]
                    })

        return response_data

    def stream(self, user_input: str, chat_history: list = None):
        """
        Stream the agent response.

        Args:
            user_input: User's message
            chat_history: Previous conversation messages

        Yields:
            Response chunks as they're generated
        """
        # Build messages
        messages = []

        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))

        # Stream graph execution
        for event in self.graph.stream({"messages": messages}):
            for key, value in event.items():
                if key == "agent":
                    # Agent generated a response
                    if value["messages"]:
                        msg = value["messages"][-1]
                        if hasattr(msg, "content"):
                            yield {
                                "type": "message",
                                "content": msg.content
                            }
                elif key == "action":
                    # Tool was executed
                    if value["messages"]:
                        for msg in value["messages"]:
                            yield {
                                "type": "tool_result",
                                "content": msg.content
                            }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("Comprehensive AI Agent - LangChain/LangGraph")
    print("=" * 80)

    # Create agent
    agent = ComprehensiveAgent(mode="advanced")

    # Test 1: Simple calculation
    print("\n1. Testing code execution...")
    print("-" * 80)
    result1 = agent.run("Calculate the sum of squares from 1 to 100")
    print(f"Response: {result1['response']}")
    print(f"Tools used: {len(result1['tool_calls'])}")

    # Test 2: Financial data
    print("\n2. Testing financial data...")
    print("-" * 80)
    result2 = agent.run("What is the current price of Tesla stock?")
    print(f"Response: {result2['response'][:200]}...")
    print(f"Tools used: {len(result2['tool_calls'])}")

    print("\n" + "=" * 80)
    print("✅ LangChain/LangGraph Agent Ready!")
    print("=" * 80)
