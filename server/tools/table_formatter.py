"""
Table formatting tool for creating beautiful markdown tables.
Can be called by the LLM to format structured data.
"""

import json
from typing import Dict, Any, List


def format_table(data: str, table_type: str = "auto") -> str:
    """
    Format data into a beautiful markdown table.

    Args:
        data: JSON string containing table data as list of dictionaries
        table_type: Type of table ("auto", "countries", "comparison", "financial")

    Returns:
        JSON string with formatted table in markdown

    Example data format:
    [
        {"country": "Singapore", "income": "$100k-$150k", "expenses": "$30k-$40k"},
        {"country": "Dubai", "income": "$90k-$130k", "expenses": "$25k-$35k"}
    ]
    """
    try:
        # Parse input data
        table_data = json.loads(data)

        if not isinstance(table_data, list) or not table_data:
            return json.dumps({
                "status": "error",
                "error": "Data must be a non-empty list of dictionaries",
                "answer": "I couldn't format the table. Please provide data as a list of dictionaries."
            })

        # Auto-detect table type
        if table_type == "auto":
            first_row = table_data[0]
            if "country" in str(first_row).lower():
                table_type = "countries"
            elif "income" in str(first_row).lower() or "salary" in str(first_row).lower():
                table_type = "financial"
            else:
                table_type = "comparison"

        # Format based on type
        if table_type == "countries":
            formatted_table = _format_country_table(table_data)
        elif table_type == "financial":
            formatted_table = _format_financial_table(table_data)
        else:
            formatted_table = _format_generic_table(table_data)

        return json.dumps({
            "status": "success",
            "table_type": table_type,
            "row_count": len(table_data),
            "answer": formatted_table
        }, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid JSON: {str(e)}",
            "answer": "The data provided is not valid JSON. Please ensure it's properly formatted."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "answer": f"Error formatting table: {str(e)}"
        })


def _format_country_table(countries: List[Dict[str, Any]]) -> str:
    """Format country comparison table with emojis and colors."""
    table = "## 🌍 Country Comparison\n\n"
    table += "| 🏆 Rank | 🌍 Country | 💰 Annual Income (USD) | 💸 Annual Expenses (USD) | 💵 Annual Savings (USD) | 🎉 Lifestyle | ✨ Why |\n"
    table += "|:-------:|:----------|:----------------------|:-------------------------|:------------------------|:------------|:-------|\n"

    for i, country in enumerate(countries, 1):
        rank = country.get("rank", i)
        name = country.get("country", country.get("name", "Unknown"))
        income = country.get("income", country.get("salary", "N/A"))
        expenses = country.get("expenses", country.get("cost", "N/A"))
        savings = country.get("savings", _calculate_savings(income, expenses))
        lifestyle = country.get("lifestyle", country.get("fun_score", "⭐⭐⭐"))
        why = country.get("why", country.get("reason", "N/A"))

        # Truncate "why" if too long
        if len(str(why)) > 80:
            why = str(why)[:77] + "..."

        table += f"| **{rank}** | **{name}** | {income} | {expenses} | {savings} | {lifestyle} | {why} |\n"

    # Add detailed breakdown
    table += "\n\n### 📊 Detailed Analysis\n\n"
    for i, country in enumerate(countries, 1):
        name = country.get("country", country.get("name", "Unknown"))
        income = country.get("income", "N/A")
        expenses = country.get("expenses", "N/A")
        savings = country.get("savings", _calculate_savings(income, expenses))
        why = country.get("why", country.get("reason", "N/A"))
        details = country.get("details", country.get("description", ""))

        table += f"#### {i}. {name}\n\n"
        table += f"- 💰 **Income Range:** {income}\n"
        table += f"- 💸 **Annual Expenses:** {expenses}\n"
        table += f"- 💵 **Potential Savings:** {savings}\n"
        table += f"- ✨ **Why:** {why}\n"

        if details:
            table += f"\n{details}\n"

        table += "\n"

    return table


def _format_financial_table(data: List[Dict[str, Any]]) -> str:
    """Format financial data table."""
    table = "## 💰 Financial Comparison\n\n"

    # Get headers from first row
    headers = list(data[0].keys())

    # Add emoji headers
    emoji_map = {
        "country": "🌍",
        "income": "💰",
        "salary": "💰",
        "expenses": "💸",
        "cost": "💸",
        "savings": "💵",
        "tax": "📊",
        "lifestyle": "🎉"
    }

    header_row = "|"
    separator_row = "|"
    for header in headers:
        emoji = emoji_map.get(header.lower(), "📌")
        header_row += f" {emoji} {header.title()} |"
        separator_row += ":----------|"

    table += header_row + "\n" + separator_row + "\n"

    # Add data rows
    for row in data:
        table += "|"
        for header in headers:
            value = row.get(header, "N/A")
            table += f" {value} |"
        table += "\n"

    return table


def _format_generic_table(data: List[Dict[str, Any]]) -> str:
    """Format generic table from data with improved styling."""
    if not data:
        return "No data to display"

    # Get headers from first row
    headers = list(data[0].keys())

    # Add a title if appropriate
    table = ""

    # Detect what kind of data this is
    sample_keys = " ".join(headers).lower()
    if "language" in sample_keys or "framework" in sample_keys:
        table += "## 📊 Comparison Table\n\n"
    elif "population" in sample_keys:
        table += "## 🌍 Population Data\n\n"
    else:
        table += "## 📋 Data Summary\n\n"

    # Build header row with better formatting
    formatted_headers = []
    for h in headers:
        # Convert snake_case to Title Case
        formatted = h.replace("_", " ").title()
        formatted_headers.append(formatted)

    header_row = "| " + " | ".join(formatted_headers) + " |"
    separator_row = "|" + "|".join([" :---: " for _ in headers]) + "|"  # Center align

    # Build data rows with bold first column
    rows = []
    for i, row_data in enumerate(data):
        values = []
        for j, h in enumerate(headers):
            value = str(row_data.get(h, "N/A"))
            # Bold the first column for emphasis
            if j == 0:
                value = f"**{value}**"
            values.append(value)
        rows.append("| " + " | ".join(values) + " |")

    table += "\n".join([header_row, separator_row] + rows)

    # Add summary
    table += f"\n\n*Total rows: {len(data)}*"

    return table


def _calculate_savings(income: str, expenses: str) -> str:
    """Calculate savings from income and expenses strings."""
    try:
        # Extract numbers from strings like "$100,000 - $150,000"
        import re

        income_match = re.findall(r'\$?([\d,]+)', str(income))
        expenses_match = re.findall(r'\$?([\d,]+)', str(expenses))

        if income_match and expenses_match:
            # Get min/max income
            income_nums = [int(x.replace(',', '')) for x in income_match]
            expenses_nums = [int(x.replace(',', '')) for x in expenses_match]

            min_savings = min(income_nums) - max(expenses_nums)
            max_savings = max(income_nums) - min(expenses_nums)

            return f"${min_savings:,} - ${max_savings:,}"
    except:
        pass

    return "N/A"


# Tool definitions for OpenAI function calling
TABLE_FORMATTER_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "format_table",
            "description": "Format data into a beautiful markdown table. Use this when you need to display structured data in a table format. Especially useful for country comparisons, financial data, or any tabular data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "JSON string containing table data as a list of dictionaries. Each dictionary represents a row. Example: '[{\"country\": \"Singapore\", \"income\": \"$100k-$150k\"}]'"
                    },
                    "table_type": {
                        "type": "string",
                        "enum": ["auto", "countries", "comparison", "financial"],
                        "description": "Type of table to format. 'auto' will detect automatically."
                    }
                },
                "required": ["data"]
            }
        }
    }
]

# Tool execution mapping
TABLE_FORMATTER_TOOL_FUNCTIONS = {
    "format_table": format_table
}


def execute_table_formatter_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a table formatter tool by name.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        Tool result as JSON string
    """
    if tool_name not in TABLE_FORMATTER_TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(TABLE_FORMATTER_TOOL_FUNCTIONS.keys())
        })

    try:
        func = TABLE_FORMATTER_TOOL_FUNCTIONS[tool_name]
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
    print("=" * 80)
    print("Testing Table Formatter Tool")
    print("=" * 80)

    # Test data
    countries_data = [
        {
            "rank": 1,
            "country": "Singapore",
            "income": "$100,000 - $150,000",
            "expenses": "$30,000 - $40,000",
            "savings": "$60,000 - $110,000",
            "lifestyle": "⭐⭐⭐⭐⭐",
            "why": "Tech hub with low taxes, excellent infrastructure, and vibrant nightlife",
            "details": "Singapore offers tax incentives for expats, has a booming tech sector with companies like Grab and Shopee, and provides excellent quality of life with world-class amenities."
        },
        {
            "rank": 2,
            "country": "Dubai (UAE)",
            "income": "$90,000 - $130,000",
            "expenses": "$25,000 - $35,000",
            "savings": "$55,000 - $105,000",
            "lifestyle": "⭐⭐⭐⭐⭐",
            "why": "Zero income tax, luxury lifestyle, beach culture, growing tech ecosystem",
            "details": "Dubai offers zero income tax, making it extremely attractive for high earners. The city has beautiful beaches, luxury shopping, and a rapidly growing tech scene with initiatives like Dubai Internet City."
        },
        {
            "rank": 3,
            "country": "Portugal (Lisbon)",
            "income": "$60,000 - $80,000",
            "expenses": "$20,000 - $25,000",
            "savings": "$35,000 - $60,000",
            "lifestyle": "⭐⭐⭐⭐⭐",
            "why": "Affordable cost of living, great weather, beaches, vibrant culture, tech visa program",
            "details": "Portugal has become a tech hub with Lisbon's Web Summit and startup ecosystem. The cost of living is very affordable compared to income, and the D7 and tech visas make it easy for digital workers to relocate."
        },
        {
            "rank": 4,
            "country": "Netherlands (Amsterdam)",
            "income": "$80,000 - $110,000",
            "expenses": "$28,000 - $35,000",
            "savings": "$45,000 - $82,000",
            "lifestyle": "⭐⭐⭐⭐",
            "why": "Strong tech scene, excellent work-life balance, English-friendly, bike culture",
            "details": "Amsterdam has a thriving tech ecosystem with companies like Booking.com and Adyen. The 30% ruling for expats offers significant tax benefits, and the quality of life is exceptional with great infrastructure and social systems."
        },
        {
            "rank": 5,
            "country": "Canada (Toronto/Vancouver)",
            "income": "$85,000 - $120,000",
            "expenses": "$30,000 - $40,000",
            "savings": "$45,000 - $90,000",
            "lifestyle": "⭐⭐⭐⭐",
            "why": "Strong economy, diverse multicultural cities, good quality of life, access to nature",
            "details": "Canada offers excellent tech opportunities with companies like Shopify and a growing startup scene. Toronto and Vancouver are multicultural cities with great food, culture, and easy access to outdoor activities like skiing and hiking."
        }
    ]

    # Convert to JSON string
    data_json = json.dumps(countries_data)

    # Test formatting
    print("\nTesting format_table with country data...\n")
    result = format_table(data_json, "countries")
    result_data = json.loads(result)

    print(f"Status: {result_data['status']}")
    print(f"Table Type: {result_data['table_type']}")
    print(f"Rows: {result_data['row_count']}")
    print("\n" + "=" * 80)
    print("FORMATTED TABLE OUTPUT:")
    print("=" * 80)
    print(result_data['answer'])
