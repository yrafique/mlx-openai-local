"""
Calculator tool for safe mathematical expression evaluation.
Uses asteval for safe evaluation without arbitrary code execution.
"""

from asteval import Interpreter
from typing import Dict, Any


# Tool schema in OpenAI format
CALCULATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression safely. Supports basic arithmetic (+, -, *, /), exponents (**), and common functions (sqrt, sin, cos, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', '3**2')"
                }
            },
            "required": ["expression"]
        }
    }
}


def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression as string

    Returns:
        Dict with result or error
    """
    try:
        # Create safe interpreter
        aeval = Interpreter()

        # Evaluate expression
        result = aeval(expression)

        if aeval.error:
            return {
                "success": False,
                "error": f"Evaluation error: {aeval.error[0].get_error()}"
            }

        return {
            "success": True,
            "result": result,
            "expression": expression
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Calculation failed: {str(e)}"
        }


# Export for testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        "2 + 2",
        "sqrt(16)",
        "3**2 + 4**2",
        "sin(0)",
        "log(10)",
        "invalid syntax!!"
    ]

    for expr in test_cases:
        result = calculate(expr)
        print(f"{expr} = {result}")
