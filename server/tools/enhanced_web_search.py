"""
Enhanced web search tool that processes and synthesizes results.
This tool searches the web AND provides a final processed answer,
similar to Claude's web search functionality.
"""

from duckduckgo_search import DDGS
import json
import requests
import os
import time
import logging
from typing import Dict, Any, List

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _call_local_llm(prompt: str, max_tokens: int = 500) -> str:
    """
    Call the local MLX LLM to process information.

    Args:
        prompt: The prompt to send to the LLM
        max_tokens: Maximum tokens in response

    Returns:
        LLM response as string
    """
    api_url = os.getenv("OPENAI_API_BASE", "http://localhost:7007/v1")
    model = os.getenv("DEFAULT_MODEL", "mlx-community/Qwen2.5-3B-Instruct-4bit")

    try:
        response = requests.post(
            f"{api_url}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,  # Lower temp for factual responses
                "max_tokens": max_tokens
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error calling LLM: {response.text}"
    except Exception as e:
        return f"Error calling LLM: {str(e)}"


def search_web_enhanced(query: str, max_results: int = 5) -> str:
    """
    Search the web AND process results to provide a synthesized answer.

    This function:
    1. Searches DuckDuckGo for the query
    2. Gathers the top results
    3. Uses the local LLM to process and synthesize the information
    4. Returns a coherent, final answer

    Args:
        query: Search query string
        max_results: Maximum number of results to fetch (default: 5)

    Returns:
        Synthesized answer based on web search results
    """
    # Ensure max_results is an integer (in case it comes from JSON as string)
    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 5

    try:
        # Step 1: Search the web with retry logic
        results = []
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Web search attempt {attempt + 1}/{max_retries} for query: {query}")
                ddgs = DDGS()
                results = list(ddgs.text(query, max_results=max_results))

                if results:
                    logger.info(f"Found {len(results)} results for query: {query}")
                    break
                else:
                    logger.warning(f"No results on attempt {attempt + 1} for query: {query}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
            except Exception as search_error:
                logger.error(f"Search error on attempt {attempt + 1}: {str(search_error)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

        if not results:
            logger.error(f"No results found after {max_retries} attempts for query: {query}")
            return json.dumps({
                "status": "no_results",
                "query": query,
                "answer": f"No web results found for: {query}. DuckDuckGo may be rate limiting or experiencing issues. Try rephrasing your query or try again in a moment.",
                "suggestion": "Try making your query more specific or try again in 30 seconds."
            })

        # Step 2: Format search results for processing
        search_context = f"Web search results for query: '{query}'\n\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            snippet = result.get("body", "")
            url = result.get("href", "")
            search_context += f"{i}. **{title}**\n"
            search_context += f"   {snippet}\n"
            search_context += f"   Source: {url}\n\n"

        # Step 3: Create prompt for LLM to synthesize results
        synthesis_prompt = f"""Based on the following web search results, provide a comprehensive and accurate answer to the user's query.

Query: {query}

{search_context}

Instructions:
- Synthesize information from multiple sources
- Provide specific facts, numbers, and details when available
- Be concise but informative
- Cite sources when mentioning specific information
- If results are conflicting, mention different perspectives
- Focus on answering the user's actual question

Answer:"""

        # Step 4: Use local LLM to process and synthesize
        synthesized_answer = _call_local_llm(synthesis_prompt, max_tokens=500)

        # Step 5: Return structured response
        return json.dumps({
            "status": "success",
            "query": query,
            "answer": synthesized_answer,
            "sources_count": len(results),
            "sources": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", "")
                } for r in results[:3]  # Include top 3 sources
            ]
        }, indent=2)

    except Exception as e:
        logger.exception(f"Fatal error in web search for query: {query}")
        error_message = str(e)

        # Provide helpful error messages for common issues
        if "rate" in error_message.lower() or "limit" in error_message.lower():
            helpful_msg = "DuckDuckGo is rate limiting requests. Please wait 30 seconds and try again."
        elif "timeout" in error_message.lower():
            helpful_msg = "Search timed out. Please check your internet connection and try again."
        elif "connection" in error_message.lower():
            helpful_msg = "Cannot connect to search service. Please check your internet connection."
        else:
            helpful_msg = f"Search failed: {error_message}"

        return json.dumps({
            "status": "error",
            "query": query,
            "error": error_message,
            "answer": helpful_msg,
            "suggestion": "Try rephrasing your query or try again in a moment."
        })


def get_weather_enhanced(location: str) -> str:
    """
    Get current weather with synthesized, processed answer.

    This function:
    1. Searches for current weather information
    2. Processes multiple sources
    3. Synthesizes a clear, concise answer
    4. Returns current conditions

    Args:
        location: City name or location

    Returns:
        Synthesized weather information
    """
    try:
        # Step 1: Try multiple search strategies for better results
        queries = [
            f"{location} weather temperature humidity wind conditions",
            f"current weather {location} celsius fahrenheit",
            f"{location} temperature now feels like"
        ]

        all_results = []
        ddgs = DDGS()

        # Try each query and collect results
        for query in queries:
            try:
                results = list(ddgs.text(query, max_results=3))
                all_results.extend(results)
                if len(all_results) >= 5:
                    break
            except:
                continue

        # Use the collected results
        results = all_results[:10]  # Use up to 10 results for better coverage

        if not results:
            return json.dumps({
                "status": "no_results",
                "location": location,
                "answer": f"Could not find current weather for {location}"
            })

        # Step 2: Filter and format weather-specific results
        weather_context = f"Current weather information for {location}:\n\n"
        relevant_results = []

        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("href", "")

            # Prioritize results with weather indicators
            if any(keyword in body.lower() for keyword in
                   ["°", "temperature", "feels like", "humidity", "wind", "conditions"]):
                relevant_results.append(result)
                weather_context += f"{len(relevant_results)}. **{title}**\n"
                weather_context += f"   {body}\n"
                weather_context += f"   Source: {url}\n\n"

        # Use all results if no specific weather data found
        if not relevant_results:
            relevant_results = results
            for i, result in enumerate(results, 1):
                weather_context += f"{i}. **{result.get('title', '')}**\n"
                weather_context += f"   {result.get('body', '')}\n\n"

        # Step 3: Create weather-specific synthesis prompt
        synthesis_prompt = f"""Based on the following weather search results, extract and summarize the current weather for {location}.

{weather_context}

IMPORTANT Instructions:
1. Look carefully through ALL the text snippets for temperature, conditions, humidity, wind
2. Extract ANY numbers you find with ° or °C or °F or temperature mentions
3. Look for words like: sunny, cloudy, partly cloudy, clear, rain, snow, etc.
4. Look for "feels like", humidity %, wind speed (km/h or mph)
5. If you find actual data, present it clearly
6. If the snippets only have links/titles without data, say: "The search found weather sites for {location}. Please visit: [list the main weather site URLs]"
7. Be honest - if there's no actual temperature data in the snippets, say so
8. Keep response concise (2-4 sentences)

Current weather for {location}:"""

        # Step 4: Synthesize weather answer
        weather_answer = _call_local_llm(synthesis_prompt, max_tokens=300)

        # Step 5: Return structured response
        return json.dumps({
            "status": "success",
            "location": location,
            "answer": weather_answer,
            "sources_count": len(relevant_results),
            "sources": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", "")
                } for r in relevant_results[:2]  # Top 2 sources
            ]
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "location": location,
            "error": str(e),
            "answer": f"Weather search failed: {str(e)}"
        })


def get_current_info(topic: str) -> str:
    """
    Get current information on any topic with AI-processed synthesis.

    This is a general-purpose function that searches and synthesizes
    information on any topic, providing a clear, processed answer.

    Args:
        topic: Any topic or question to search for

    Returns:
        Synthesized answer with sources
    """
    return search_web_enhanced(topic, max_results=5)


# Enhanced tool definitions for OpenAI function calling
ENHANCED_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web_enhanced",
            "description": "Search the web and get a processed, synthesized answer (like Claude). This tool searches DuckDuckGo, processes multiple sources, and returns a clear, coherent answer to your question. Use this when you need up-to-date information, current events, or any real-time data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question to look up"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to process (1-10, default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_enhanced",
            "description": "Get current weather with a synthesized, easy-to-read answer. Returns current conditions, temperature, feels like, and more for any location.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_info",
            "description": "Get current information on any topic with AI-processed answer. Use this for general queries about current events, latest news, or any topic requiring recent information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic or question to search for"
                    }
                },
                "required": ["topic"]
            }
        }
    }
]

# Enhanced tool execution mapping
ENHANCED_TOOL_FUNCTIONS = {
    "search_web_enhanced": search_web_enhanced,
    "get_weather_enhanced": get_weather_enhanced,
    "get_current_info": get_current_info
}


def execute_enhanced_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute an enhanced tool by name with given arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool

    Returns:
        Tool execution result as string (JSON formatted)
    """
    if tool_name not in ENHANCED_TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(ENHANCED_TOOL_FUNCTIONS.keys())
        })

    try:
        func = ENHANCED_TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return json.dumps({
            "status": "error",
            "tool": tool_name,
            "error": str(e),
            "answer": f"Tool execution failed: {str(e)}"
        })


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Enhanced Web Search Tool")
    print("=" * 60)

    # Test 1: Weather search
    print("\n1. Testing weather search (Ottawa)...")
    print("-" * 60)
    result = get_weather_enhanced("Ottawa")
    data = json.loads(result)
    print(f"Status: {data.get('status')}")
    print(f"\nAnswer:\n{data.get('answer')}")
    if data.get('sources'):
        print(f"\nSources ({data.get('sources_count')}):")
        for source in data.get('sources', []):
            print(f"  - {source.get('title')}")

    # Test 2: General web search
    print("\n" + "=" * 60)
    print("2. Testing general web search (Python tutorials)...")
    print("-" * 60)
    result = search_web_enhanced("latest Python tutorials", max_results=3)
    data = json.loads(result)
    print(f"Status: {data.get('status')}")
    print(f"\nAnswer:\n{data.get('answer')}")
    if data.get('sources'):
        print(f"\nSources ({data.get('sources_count')}):")
        for source in data.get('sources', []):
            print(f"  - {source.get('title')}")

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
