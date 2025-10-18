"""
Smart Router - Automatic tool detection and execution
Workaround for models without native function calling support
"""

import re
from typing import Dict, Any, List, Optional
from server.tools import execute_tool


class SmartRouter:
    """
    Detects when queries need tools and executes them automatically.
    """

    def __init__(self):
        self.weather_patterns = [
            r"weather.*(?:in|at|for)\s+(\w+)",
            r"what'?s?\s+the\s+weather.*(?:in|at)\s+(\w+)",
            r"temperature.*(?:in|at)\s+(\w+)",
            r"forecast.*(?:for|in)\s+(\w+)",
        ]

        self.calc_patterns = [
            r"calculate\s+(.+)",
            r"what\s+is\s+([\d\s\+\-\*\/\(\)\.]+)",
            r"compute\s+(.+)",
            r"solve\s+(.+)",
        ]

    def detect_intent(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Detect if query needs a tool.

        Returns:
            {"tool": "tool_name", "args": {...}} or None
        """
        query_lower = query.lower()

        # Weather detection
        for pattern in self.weather_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1) if match.groups() else "location"
                return {
                    "tool": "web_search",
                    "args": {
                        "query": f"weather {location} now current",
                        "num_results": 3
                    },
                    "intent": "weather"
                }

        # Calculator detection
        for pattern in self.calc_patterns:
            match = re.search(pattern, query_lower)
            if match:
                expression = match.group(1).strip()
                return {
                    "tool": "calculate",
                    "args": {
                        "expression": expression
                    },
                    "intent": "calculation"
                }

        # General search detection
        search_keywords = ["search for", "find information about", "look up"]
        for keyword in search_keywords:
            if keyword in query_lower:
                search_query = query_lower.replace(keyword, "").strip()
                return {
                    "tool": "web_search",
                    "args": {
                        "query": search_query,
                        "num_results": 3
                    },
                    "intent": "search"
                }

        return None

    def execute_if_needed(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute tool if query matches a pattern.

        Returns:
            Tool result or None if no tool needed
        """
        intent = self.detect_intent(query)

        if intent:
            tool_name = intent["tool"]
            tool_args = intent["args"]

            try:
                result = execute_tool(tool_name, tool_args)
                return {
                    "used_tool": True,
                    "tool_name": tool_name,
                    "intent": intent["intent"],
                    "result": result
                }
            except Exception as e:
                return {
                    "used_tool": True,
                    "tool_name": tool_name,
                    "error": str(e)
                }

        return None

    def format_tool_response(self, tool_result: Dict[str, Any], original_query: str) -> str:
        """
        Format tool result into a user-friendly response.
        """
        if "error" in tool_result:
            return f"I tried to help but encountered an error: {tool_result['error']}"

        tool_name = tool_result.get("tool_name")
        result = tool_result.get("result", {})

        if tool_name == "web_search":
            if result.get("success"):
                response = f"Here's what I found:\n\n"
                for item in result.get("results", []):
                    response += f"**{item['title']}**\n"
                    response += f"{item['snippet']}\n"
                    response += f"Source: {item['url']}\n\n"

                # Add note if mock
                if "note" in result:
                    response += f"\n_{result['note']}_"

                return response
            else:
                return f"Search failed: {result.get('error', 'Unknown error')}"

        elif tool_name == "calculate":
            if result.get("success"):
                return f"The answer is: **{result['result']}**\n\nCalculation: {result['expression']}"
            else:
                return f"Calculation failed: {result.get('error', 'Unknown error')}"

        return str(result)


# Global router instance
smart_router = SmartRouter()
