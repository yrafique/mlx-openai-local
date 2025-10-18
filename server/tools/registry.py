"""
Comprehensive Tools Registry.
Central location for all available tools and their execution.
"""

from typing import Dict, Any, List
import json

# Import all tool modules
try:
    # Try relative imports (when used as module)
    from .code_execution import CODE_EXECUTION_TOOL_DEFINITIONS, execute_code_tool
    from .financial_data import FINANCIAL_TOOL_DEFINITIONS, execute_financial_tool
    from .enhanced_web_search import ENHANCED_TOOL_DEFINITIONS, execute_enhanced_tool
    from .web_search import TOOL_DEFINITIONS as WEB_SEARCH_TOOL_DEFINITIONS, execute_tool as execute_web_search_tool
    from .table_formatter import TABLE_FORMATTER_TOOL_DEFINITIONS, execute_table_formatter_tool
    from .voice import VOICE_TOOL_DEFINITIONS, execute_voice_tool
    from .file_analysis import FILE_ANALYSIS_TOOL_DEFINITIONS, execute_file_tool
    from .rag import RAG_TOOL_DEFINITIONS, execute_rag_tool
except ImportError:
    # Fall back to absolute imports (when run directly)
    from code_execution import CODE_EXECUTION_TOOL_DEFINITIONS, execute_code_tool
    from financial_data import FINANCIAL_TOOL_DEFINITIONS, execute_financial_tool
    from enhanced_web_search import ENHANCED_TOOL_DEFINITIONS, execute_enhanced_tool
    from web_search import TOOL_DEFINITIONS as WEB_SEARCH_TOOL_DEFINITIONS, execute_tool as execute_web_search_tool
    from table_formatter import TABLE_FORMATTER_TOOL_DEFINITIONS, execute_table_formatter_tool
    from voice import VOICE_TOOL_DEFINITIONS, execute_voice_tool
    from file_analysis import FILE_ANALYSIS_TOOL_DEFINITIONS, execute_file_tool
    from rag import RAG_TOOL_DEFINITIONS, execute_rag_tool


class ToolsRegistry:
    """
    Central registry for all available tools.
    Provides easy access to tool definitions and execution.
    """

    def __init__(self):
        """Initialize the tools registry."""
        self.tool_categories = {
            "code_execution": {
                "name": "Code Execution",
                "description": "Execute Python code, run calculations, generate plots",
                "icon": "💻",
                "tools": CODE_EXECUTION_TOOL_DEFINITIONS,
                "executor": execute_code_tool
            },
            "financial": {
                "name": "Financial Data",
                "description": "Real-time stock/crypto prices, historical charts",
                "icon": "💰",
                "tools": FINANCIAL_TOOL_DEFINITIONS,
                "executor": execute_financial_tool
            },
            "web_search": {
                "name": "Web Search (Enhanced)",
                "description": "AI-powered web search with synthesis",
                "icon": "🔍",
                "tools": ENHANCED_TOOL_DEFINITIONS,
                "executor": execute_enhanced_tool
            },
            "web_search_basic": {
                "name": "Web Search (Basic)",
                "description": "Basic web search without AI processing",
                "icon": "🌐",
                "tools": WEB_SEARCH_TOOL_DEFINITIONS,
                "executor": execute_web_search_tool
            },
            "formatting": {
                "name": "Data Formatting",
                "description": "Format data into beautiful tables and visualizations",
                "icon": "📊",
                "tools": TABLE_FORMATTER_TOOL_DEFINITIONS,
                "executor": execute_table_formatter_tool
            },
            "voice": {
                "name": "Voice Capabilities",
                "description": "Speech-to-text and text-to-speech",
                "icon": "🎤",
                "tools": VOICE_TOOL_DEFINITIONS,
                "executor": execute_voice_tool
            },
            "file_analysis": {
                "name": "File Analysis",
                "description": "Analyze CSV, Excel, JSON, text, code, images",
                "icon": "📁",
                "tools": FILE_ANALYSIS_TOOL_DEFINITIONS,
                "executor": execute_file_tool
            },
            "rag": {
                "name": "Knowledge Base (RAG)",
                "description": "Ingest documents/YouTube, query knowledge base (inspired by chat-with-mlx)",
                "icon": "🧠",
                "tools": RAG_TOOL_DEFINITIONS,
                "executor": execute_rag_tool
            }
        }

    def get_all_tools(self, categories: List[str] = None) -> List[Dict]:
        """
        Get all tool definitions.

        Args:
            categories: List of category IDs to include (None = all)

        Returns:
            List of tool definitions
        """
        tools = []

        for cat_id, category in self.tool_categories.items():
            if categories is None or cat_id in categories:
                tools.extend(category["tools"])

        return tools

    def get_category_tools(self, category: str) -> List[Dict]:
        """Get tools for a specific category."""
        if category in self.tool_categories:
            return self.tool_categories[category]["tools"]
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result as JSON string
        """
        # Find which category this tool belongs to
        for category in self.tool_categories.values():
            for tool_def in category["tools"]:
                if tool_def["function"]["name"] == tool_name:
                    # Execute using category's executor
                    return category["executor"](tool_name, arguments)

        # Tool not found
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": [t["function"]["name"] for t in self.get_all_tools()]
        })

    def get_tool_info(self, tool_name: str) -> Dict:
        """Get information about a specific tool."""
        for category in self.tool_categories.values():
            for tool_def in category["tools"]:
                if tool_def["function"]["name"] == tool_name:
                    return {
                        "name": tool_name,
                        "description": tool_def["function"]["description"],
                        "parameters": tool_def["function"]["parameters"],
                        "category": category["name"]
                    }
        return None

    def list_categories(self) -> List[Dict]:
        """List all available tool categories."""
        return [
            {
                "id": cat_id,
                "name": cat["name"],
                "description": cat["description"],
                "icon": cat["icon"],
                "tool_count": len(cat["tools"])
            }
            for cat_id, cat in self.tool_categories.items()
        ]


# Global registry instance
REGISTRY = ToolsRegistry()


# Convenience functions
def get_all_tools(categories: List[str] = None) -> List[Dict]:
    """Get all available tool definitions."""
    return REGISTRY.get_all_tools(categories)


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool by name."""
    return REGISTRY.execute_tool(tool_name, arguments)


def get_tool_info(tool_name: str) -> Dict:
    """Get information about a tool."""
    return REGISTRY.get_tool_info(tool_name)


def list_categories() -> List[Dict]:
    """List all tool categories."""
    return REGISTRY.list_categories()


if __name__ == "__main__":
    print("=" * 80)
    print("Tools Registry - Comprehensive Overview")
    print("=" * 80)

    # List categories
    print("\n📦 Available Tool Categories:")
    print("-" * 80)
    for cat in list_categories():
        print(f"{cat['icon']} {cat['name']}")
        print(f"   {cat['description']}")
        print(f"   Tools: {cat['tool_count']}")
        print()

    # List all tools
    all_tools = get_all_tools()
    print(f"\n🔧 Total Tools Available: {len(all_tools)}")
    print("-" * 80)
    for tool in all_tools:
        name = tool["function"]["name"]
        desc = tool["function"]["description"][:80]
        print(f"• {name}")
        print(f"  {desc}...")
        print()

    print("=" * 80)
    print("✅ Tools Registry Ready!")
    print("=" * 80)
