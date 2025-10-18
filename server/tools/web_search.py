"""
Web search tool using DuckDuckGo (no API key required).
Provides real-time web search functionality for the chat interface.
"""

from duckduckgo_search import DDGS
import json
from typing import Dict, Any


def search_web(query: str, max_results: int = 3) -> str:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 3)

    Returns:
        JSON string with search results
    """
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return json.dumps({
                "status": "success",
                "query": query,
                "results": [],
                "message": "No results found"
            })

        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append({
                "position": i,
                "title": result.get("title", ""),
                "snippet": result.get("body", ""),
                "url": result.get("href", "")
            })

        return json.dumps({
            "status": "success",
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "query": query,
            "error": str(e),
            "message": f"Search failed: {str(e)}"
        })


def get_weather(location: str) -> str:
    """
    Get current weather for a location using web search.

    Args:
        location: City name or location

    Returns:
        JSON string with weather information
    """
    try:
        # Search for weather with temperature to get more specific results
        query = f"weather temperature {location} now today"
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=5))

        if not results:
            return json.dumps({
                "status": "success",
                "location": location,
                "message": "Could not find weather information"
            })

        # Collect all weather-related information
        weather_data = []
        for result in results:
            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("href", "")

            # Filter for actual weather content (not just links to weather sites)
            if any(keyword in body.lower() for keyword in ["°", "temperature", "feels like", "humidity", "wind"]):
                weather_data.append({
                    "source": title,
                    "details": body,
                    "url": url
                })

        if weather_data:
            return json.dumps({
                "status": "success",
                "location": location,
                "current_weather": weather_data[:3],  # Top 3 most relevant results
                "message": "Current weather information found from multiple sources"
            }, indent=2)
        else:
            # Fallback to basic search results
            return json.dumps({
                "status": "success",
                "location": location,
                "search_results": [
                    {
                        "source": r.get("title", ""),
                        "details": r.get("body", ""),
                        "url": r.get("href", "")
                    } for r in results[:3]
                ],
                "message": "Weather search results (visit URLs for current data)"
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "location": location,
            "error": str(e),
            "message": f"Weather search failed: {str(e)}"
        })


# Tool definitions for OpenAI function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current information, news, facts, or any real-time data. Use this when you need up-to-date information that you don't have in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (1-10)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a specific location. Use this when users ask about weather, temperature, or conditions in a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'Ottawa', 'New York', 'London')"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Tool execution mapping
TOOL_FUNCTIONS = {
    "search_web": search_web,
    "get_weather": get_weather
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool by name with given arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool

    Returns:
        Tool execution result as string
    """
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(TOOL_FUNCTIONS.keys())
        })

    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return json.dumps({
            "status": "error",
            "tool": tool_name,
            "error": str(e),
            "message": f"Tool execution failed: {str(e)}"
        })


if __name__ == "__main__":
    # Test the web search
    print("Testing web search...")
    result = search_web("Python programming tutorials")
    print(result)

    print("\nTesting weather search...")
    result = get_weather("Ottawa")
    print(result)
