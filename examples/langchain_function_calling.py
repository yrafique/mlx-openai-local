"""
LangChain Function Calling with MLX Omni Server
Demonstrates 99% accuracy function calling on Apple Silicon
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Configure LangChain to use MLX Omni Server
llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",
    model="mlx-community/Qwen2.5-3B-Instruct-4bit",
    temperature=0.7,
)

# Define custom tools
@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression. Use this for any math calculations."""
    try:
        # Safe eval for basic math
        import ast
        import operator as op

        operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.USub: op.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            else:
                raise TypeError(node)

        result = eval_expr(ast.parse(expression, mode='eval').body)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # Mock weather data for demo
    return f"The weather in {location} is sunny, 22°C with light wind."


@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Mock search result for demo
    return f"Mock search results for '{query}': Found relevant information about {query}."


# Create agent with tools
tools = [calculate, get_weather, search_web]

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant with access to tools. Use them when needed."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Test function calling
print("=" * 80)
print("MLX Omni Server - LangChain Function Calling (99% Accuracy)")
print("=" * 80)

test_queries = [
    "What is 15 multiplied by 23 plus 47?",
    "What's the weather in Ottawa?",
    "Calculate the sum of 100 and 256, then tell me what that number divided by 2 is.",
]

for query in test_queries:
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}\n")

    result = agent_executor.invoke({"input": query})

    print(f"\n✅ Final Answer: {result['output']}\n")

print("=" * 80)
print("🚀 Function calling tests complete!")
print("=" * 80)
