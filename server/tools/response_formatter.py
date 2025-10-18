"""
Response formatter for cleaning and beautifying LLM outputs.
Handles table formatting, markdown cleanup, and LaTeX artifact removal.
"""

import re
import pandas as pd
from typing import Dict, Any, List, Optional


def clean_latex_artifacts(text: str) -> str:
    """
    Remove common LaTeX/math formatting artifacts from text.

    Examples:
        "USD)**:" -> "USD):"
        "USD)∗∗:" -> "USD):"
        "$\\$" -> "$"
    """
    # Remove LaTeX bold markers
    text = re.sub(r'\*\*([^*]+)\)\*\*:', r'**\1):**', text)

    # Fix broken bold markdown
    text = re.sub(r'∗∗', '**', text)

    # Fix currency symbols
    text = re.sub(r'\$\\?\\?\$', '$', text)

    # Fix broken line breaks
    text = re.sub(r'([a-z])([A-Z])', r'\1\n\n\2', text)

    # Remove Unicode artifacts
    text = re.sub(r'\\u[0-9a-fA-F]{4}', '', text)

    return text


def extract_table_data(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Try to extract structured data from text that should be a table.

    Returns:
        List of dictionaries representing table rows, or None if no table detected
    """
    # Look for patterns like "Country: X, Income: Y, Expenses: Z"
    # This is a simple heuristic - can be expanded

    lines = text.split('\n')
    table_data = []

    for line in lines:
        if ':' in line and ',' in line:
            # Potential table row
            row = {}
            parts = line.split(',')
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    row[key.strip()] = value.strip()
            if row:
                table_data.append(row)

    return table_data if table_data else None


def format_as_markdown_table(data: List[Dict[str, Any]]) -> str:
    """
    Convert list of dictionaries to a beautiful markdown table.

    Args:
        data: List of dictionaries with consistent keys

    Returns:
        Formatted markdown table string
    """
    if not data:
        return ""

    # Get headers from first row
    headers = list(data[0].keys())

    # Build header row
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---" for _ in headers]) + " |"

    # Build data rows
    data_rows = []
    for row in data:
        values = [str(row.get(h, "N/A")) for h in headers]
        data_rows.append("| " + " | ".join(values) + " |")

    # Combine
    table = "\n".join([header_row, separator_row] + data_rows)

    return table


def create_country_comparison_table(countries: List[Dict[str, Any]]) -> str:
    """
    Create a beautiful comparison table for countries.

    Expected format:
    [
        {
            "rank": 1,
            "country": "Singapore",
            "income": "$100,000 - $150,000",
            "expenses": "$30,000 - $40,000",
            "savings": "$60,000 - $110,000",
            "fun_score": "⭐⭐⭐⭐⭐",
            "why": "Tech hub, low taxes..."
        },
        ...
    ]
    """
    if not countries:
        return ""

    # Create header
    table = "| 🏆 Rank | 🌍 Country | 💰 Annual Income (USD) | 💸 Annual Expenses (USD) | 💵 Annual Savings (USD) | 🎉 Fun Score | ✨ Why This Country |\n"
    table += "|---------|-----------|----------------------|--------------------------|------------------------|-------------|--------------------|\n"

    # Add rows
    for country in countries:
        rank = country.get("rank", "?")
        country_name = country.get("country", "Unknown")
        income = country.get("income", "N/A")
        expenses = country.get("expenses", "N/A")
        savings = country.get("savings", "N/A")
        fun_score = country.get("fun_score", "⭐⭐⭐")
        why = country.get("why", "N/A")

        # Truncate "why" if too long
        if len(why) > 60:
            why = why[:57] + "..."

        table += f"| {rank} | **{country_name}** | {income} | {expenses} | {savings} | {fun_score} | {why} |\n"

    return table


def format_response(text: str, response_type: str = "auto") -> str:
    """
    Main formatter - cleans and beautifies LLM responses.

    Args:
        text: Raw LLM output
        response_type: "auto", "table", "text", "code"

    Returns:
        Cleaned and formatted text
    """
    # Step 1: Clean LaTeX artifacts
    cleaned = clean_latex_artifacts(text)

    # Step 2: Detect response type if auto
    if response_type == "auto":
        if "country" in text.lower() and ("income" in text.lower() or "salary" in text.lower()):
            response_type = "country_table"
        elif "|" in text or "table" in text.lower():
            response_type = "table"
        else:
            response_type = "text"

    # Step 3: Format based on type
    if response_type == "country_table":
        # Try to extract structured data and format as table
        # For now, just clean and return
        # TODO: Implement smart parsing
        return cleaned
    elif response_type == "table":
        return cleaned
    else:
        return cleaned


# Export main function
__all__ = ["format_response", "clean_latex_artifacts", "create_country_comparison_table"]


# Example usage
if __name__ == "__main__":
    # Test with broken output
    broken_text = """
    Canada
    **Income (USD)**∗∗:Approximately80,000 - $100,000
    **Expenses (USD)∗∗:Approximately18,000 - $22,000
    Reasons: High standard of living
    """

    print("=== Original (Broken) ===")
    print(broken_text)
    print("\n=== Cleaned ===")
    print(format_response(broken_text))

    # Test with country data
    print("\n\n=== Country Comparison Table ===")
    countries = [
        {
            "rank": 1,
            "country": "Singapore",
            "income": "$100,000 - $150,000",
            "expenses": "$30,000 - $40,000",
            "savings": "$60,000 - $110,000",
            "fun_score": "⭐⭐⭐⭐⭐",
            "why": "Tech hub, low taxes, excellent infrastructure, vibrant nightlife, safe"
        },
        {
            "rank": 2,
            "country": "Dubai (UAE)",
            "income": "$90,000 - $130,000",
            "expenses": "$25,000 - $35,000",
            "savings": "$55,000 - $105,000",
            "fun_score": "⭐⭐⭐⭐⭐",
            "why": "Zero income tax, luxury lifestyle, beach life, growing tech scene"
        },
        {
            "rank": 3,
            "country": "Portugal",
            "income": "$60,000 - $80,000",
            "expenses": "$20,000 - $25,000",
            "savings": "$35,000 - $60,000",
            "fun_score": "⭐⭐⭐⭐⭐",
            "why": "Affordable, great weather, beaches, vibrant culture, tech visas"
        },
        {
            "rank": 4,
            "country": "Netherlands",
            "income": "$80,000 - $110,000",
            "expenses": "$28,000 - $35,000",
            "savings": "$45,000 - $82,000",
            "fun_score": "⭐⭐⭐⭐",
            "why": "Strong tech scene, work-life balance, English-friendly, bike culture"
        },
        {
            "rank": 5,
            "country": "Canada (Toronto/Vancouver)",
            "income": "$85,000 - $120,000",
            "expenses": "$30,000 - $40,000",
            "savings": "$45,000 - $90,000",
            "fun_score": "⭐⭐⭐⭐",
            "why": "Strong economy, diverse cities, good quality of life, nature access"
        }
    ]

    table = create_country_comparison_table(countries)
    print(table)

    print("\n\n=== Detailed Breakdown ===")
    for i, country in enumerate(countries, 1):
        print(f"\n**{i}. {country['country']}** {country['fun_score']}")
        print(f"   💰 Income: {country['income']}")
        print(f"   💸 Expenses: {country['expenses']}")
        print(f"   💵 Savings: {country['savings']}")
        print(f"   ✨ Why: {country['why']}")
