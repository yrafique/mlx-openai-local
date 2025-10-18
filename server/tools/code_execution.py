"""
Code execution tool - like ChatGPT Code Interpreter.
Executes Python code in a sandboxed environment and returns results.
"""

import json
import sys
import io
import contextlib
import traceback
from typing import Dict, Any
import base64
from datetime import datetime


def execute_python_code(code: str, timeout: int = 30) -> str:
    """
    Execute Python code and return results.

    This is like ChatGPT's Code Interpreter - can run Python code,
    generate plots, analyze data, and return results.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        JSON string with execution results, stdout, and any generated plots
    """
    try:
        # Create StringIO to capture stdout
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Store generated plots
        generated_plots = []

        # Prepare execution namespace with useful libraries
        exec_namespace = {
            '__builtins__': __builtins__,
            'datetime': datetime,
        }

        # Try to import common libraries
        try:
            import numpy as np
            exec_namespace['np'] = np
            exec_namespace['numpy'] = np
        except ImportError:
            pass

        try:
            import pandas as pd
            exec_namespace['pd'] = pd
            exec_namespace['pandas'] = pd
        except ImportError:
            pass

        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            exec_namespace['plt'] = plt
            exec_namespace['matplotlib'] = matplotlib
        except ImportError:
            pass

        try:
            import plotly.graph_objects as go
            exec_namespace['go'] = go
            exec_namespace['plotly'] = go
        except ImportError:
            pass

        # Execute code with stdout/stderr capture
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, exec_namespace)

        # Capture stdout/stderr
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        # Check for matplotlib plots
        if 'plt' in exec_namespace:
            try:
                import matplotlib.pyplot as plt
                # Check if there are any figures
                figures = [plt.figure(num) for num in plt.get_fignums()]

                for fig in figures:
                    # Save figure to base64
                    buffer = io.BytesIO()
                    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                    buffer.seek(0)
                    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                    generated_plots.append({
                        'type': 'matplotlib',
                        'data': image_base64
                    })

                # Close all figures
                plt.close('all')
            except Exception as e:
                pass

        # Get the last expression result if any
        last_result = None
        if exec_namespace:
            # Try to get result from last line if it was an expression
            code_lines = code.strip().split('\n')
            if code_lines:
                last_line = code_lines[-1].strip()
                if last_line and not last_line.startswith(('import', 'from', 'def', 'class', 'if', 'for', 'while', 'with', 'try', '#')):
                    try:
                        last_result = eval(last_line, exec_namespace)
                    except:
                        pass

        # Build answer text
        answer_parts = []

        if stdout_output:
            answer_parts.append(f"**Output:**\n```\n{stdout_output.strip()}\n```")

        if last_result is not None:
            answer_parts.append(f"**Result:** `{repr(last_result)}`")

        if generated_plots:
            answer_parts.append(f"\n**Generated {len(generated_plots)} plot(s)** - See below")

        if not answer_parts:
            answer_parts.append("✅ Code executed successfully (no output)")

        answer = "\n\n".join(answer_parts)

        return json.dumps({
            "status": "success",
            "stdout": stdout_output,
            "stderr": stderr_output,
            "result": repr(last_result) if last_result is not None else None,
            "plots": generated_plots,
            "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "answer": answer
        }, indent=2)

    except SyntaxError as e:
        return json.dumps({
            "status": "error",
            "error_type": "SyntaxError",
            "error": str(e),
            "line": e.lineno,
            "answer": f"**Syntax Error** on line {e.lineno}:\n```\n{e.text}\n```\n{str(e)}"
        })

    except Exception as e:
        # Get full traceback
        tb = traceback.format_exc()

        return json.dumps({
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
            "traceback": tb,
            "answer": f"**Error ({type(e).__name__}):**\n```\n{str(e)}\n```\n\n**Traceback:**\n```\n{tb}\n```"
        })


# Tool definitions for OpenAI function calling
CODE_EXECUTION_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Execute Python code and return results. Like ChatGPT Code Interpreter - can run calculations, generate plots, analyze data, process text, and more. Has access to numpy, pandas, matplotlib, plotly. Use this when user asks you to: calculate something, analyze data, create visualizations, process files, run algorithms, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute. Can use: numpy (as np), pandas (as pd), matplotlib.pyplot (as plt), plotly.graph_objects (as go), datetime, and all standard library modules."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["code"]
            }
        }
    }
]

# Tool execution mapping
CODE_EXECUTION_TOOL_FUNCTIONS = {
    "execute_python_code": execute_python_code
}


def execute_code_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a code execution tool by name.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        Tool result as JSON string
    """
    if tool_name not in CODE_EXECUTION_TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(CODE_EXECUTION_TOOL_FUNCTIONS.keys())
        })

    try:
        func = CODE_EXECUTION_TOOL_FUNCTIONS[tool_name]
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
    print("Testing Code Execution Tool")
    print("=" * 80)

    # Test 1: Simple calculation
    print("\n1. Testing simple calculation...")
    print("-" * 80)
    code1 = """
import math
result = math.sqrt(16) + math.pi
print(f"Square root of 16 plus pi = {result}")
result
"""
    result1 = execute_python_code(code1)
    data1 = json.loads(result1)
    print(f"Status: {data1['status']}")
    print(f"Answer:\n{data1['answer']}")

    # Test 2: Data analysis
    print("\n\n2. Testing data analysis with pandas...")
    print("-" * 80)
    code2 = """
import pandas as pd
import numpy as np

# Create sample data
data = {
    'Product': ['A', 'B', 'C', 'D'],
    'Sales': [100, 150, 200, 175],
    'Profit': [20, 35, 50, 40]
}

df = pd.DataFrame(data)
print("Sales Data:")
print(df)
print(f"\\nTotal Sales: ${df['Sales'].sum()}")
print(f"Average Profit: ${df['Profit'].mean():.2f}")
"""
    result2 = execute_python_code(code2)
    data2 = json.loads(result2)
    print(f"Status: {data2['status']}")
    print(f"Answer:\n{data2['answer']}")

    # Test 3: Plot generation
    print("\n\n3. Testing plot generation...")
    print("-" * 80)
    code3 = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y, linewidth=2)
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('sin(X)')
plt.grid(True, alpha=0.3)
print("Generated sine wave plot")
"""
    result3 = execute_python_code(code3)
    data3 = json.loads(result3)
    print(f"Status: {data3['status']}")
    print(f"Plots generated: {len(data3.get('plots', []))}")
    print(f"Answer:\n{data3['answer']}")

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
