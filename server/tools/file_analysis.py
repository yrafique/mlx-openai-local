"""
File analysis tool - Upload and analyze files.
Supports CSV, Excel, JSON, text files, images, PDFs, and more.
"""

import json
import base64
from typing import Dict, Any
from datetime import datetime
import io


def analyze_file(file_base64: str, filename: str, analysis_type: str = "auto") -> str:
    """
    Analyze uploaded file and extract information.

    Supports:
    - CSV/Excel: Data analysis, statistics, visualizations
    - JSON: Parse and analyze structure
    - Text: Extract text, analyze content
    - Images: Describe (if vision model available)
    - PDF: Extract text
    - Code files: Analyze code structure

    Args:
        file_base64: Base64 encoded file content
        filename: Original filename (used to detect file type)
        analysis_type: Type of analysis ("auto", "data", "text", "code", "image")

    Returns:
        JSON string with file analysis results
    """
    try:
        # Decode file
        file_data = base64.b64decode(file_base64)

        # Determine file type from extension
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''

        # Auto-detect analysis type if not specified
        if analysis_type == "auto":
            if file_ext in ['csv', 'xlsx', 'xls']:
                analysis_type = "data"
            elif file_ext in ['json', 'jsonl']:
                analysis_type = "json"
            elif file_ext in ['txt', 'md', 'log']:
                analysis_type = "text"
            elif file_ext in ['py', 'js', 'java', 'cpp', 'c', 'go', 'rs']:
                analysis_type = "code"
            elif file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
                analysis_type = "image"
            elif file_ext == 'pdf':
                analysis_type = "pdf"
            else:
                analysis_type = "text"

        # Route to appropriate analyzer
        if analysis_type == "data":
            return _analyze_data_file(file_data, filename, file_ext)
        elif analysis_type == "json":
            return _analyze_json_file(file_data, filename)
        elif analysis_type == "text" or analysis_type == "code":
            return _analyze_text_file(file_data, filename, file_ext)
        elif analysis_type == "pdf":
            return _analyze_pdf_file(file_data, filename)
        elif analysis_type == "image":
            return _analyze_image_file(file_data, filename)
        else:
            return json.dumps({
                "status": "error",
                "error": "Unsupported analysis type",
                "answer": f"Unsupported analysis type: {analysis_type}"
            })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "answer": f"Error analyzing file: {str(e)}"
        })


def _analyze_data_file(file_data: bytes, filename: str, file_ext: str) -> str:
    """Analyze CSV or Excel files."""
    try:
        import pandas as pd

        # Load data
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(file_data))
        elif file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(file_data))
        else:
            return json.dumps({"status": "error", "error": "Unsupported data format"})

        # Analyze data
        analysis = {
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head(5).to_dict(orient='records')
        }

        # Get basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe().to_dict()
            analysis["statistics"] = stats

        # Build answer
        answer = f"## 📊 File Analysis: {filename}\n\n"
        answer += f"**Shape:** {analysis['rows']} rows × {analysis['columns']} columns\n\n"
        answer += f"**Columns:** {', '.join(analysis['column_names'])}\n\n"

        if analysis['statistics']:
            answer += f"**Numeric Summary:**\n"
            answer += "| Column | Mean | Std | Min | Max |\n"
            answer += "|--------|------|-----|-----|-----|\n"
            for col, stats in list(analysis['statistics'].items())[:5]:
                answer += f"| {col} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} |\n"

        answer += f"\n**Sample Data (first 5 rows):**\n"
        answer += "| " + " | ".join(analysis['column_names']) + " |\n"
        answer += "|" + "|".join(["---" for _ in analysis['column_names']]) + "|\n"
        for row in analysis['sample_data'][:5]:
            answer += "| " + " | ".join([str(row.get(col, ''))[:20] for col in analysis['column_names']]) + " |\n"

        return json.dumps({
            "status": "success",
            "file_type": "data",
            "analysis": analysis,
            "answer": answer
        }, indent=2)

    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "pandas not available",
            "answer": "Data file analysis requires pandas. Install with: `pip install pandas openpyxl`"
        })


def _analyze_json_file(file_data: bytes, filename: str) -> str:
    """Analyze JSON files."""
    try:
        data = json.loads(file_data.decode('utf-8'))

        analysis = {
            "filename": filename,
            "type": type(data).__name__,
            "size": len(file_data)
        }

        if isinstance(data, dict):
            analysis["keys"] = list(data.keys())[:20]
            analysis["key_count"] = len(data.keys())
        elif isinstance(data, list):
            analysis["length"] = len(data)
            if len(data) > 0:
                analysis["first_item_type"] = type(data[0]).__name__

        answer = f"## 📄 JSON Analysis: {filename}\n\n"
        answer += f"**Type:** {analysis['type']}\n"
        answer += f"**Size:** {analysis['size']:,} bytes\n\n"

        if 'keys' in analysis:
            answer += f"**Keys ({analysis['key_count']}):** {', '.join(analysis['keys'])}\n"
        elif 'length' in analysis:
            answer += f"**Array Length:** {analysis['length']}\n"

        answer += f"\n**Preview:**\n```json\n{json.dumps(data, indent=2)[:500]}...\n```"

        return json.dumps({
            "status": "success",
            "file_type": "json",
            "data": data,
            "analysis": analysis,
            "answer": answer
        })

    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid JSON: {str(e)}",
            "answer": f"File is not valid JSON: {str(e)}"
        })


def _analyze_text_file(file_data: bytes, filename: str, file_ext: str) -> str:
    """Analyze text or code files."""
    try:
        text = file_data.decode('utf-8')
        lines = text.split('\n')

        analysis = {
            "filename": filename,
            "file_type": file_ext,
            "size": len(file_data),
            "characters": len(text),
            "lines": len(lines),
            "words": len(text.split())
        }

        # Code-specific analysis
        if file_ext in ['py', 'js', 'java', 'cpp', 'c', 'go', 'rs']:
            analysis["code_language"] = file_ext
            analysis["blank_lines"] = sum(1 for line in lines if not line.strip())
            analysis["comment_lines"] = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('//'))

        answer = f"## 📝 File Analysis: {filename}\n\n"
        answer += f"**Type:** {analysis['file_type']}\n"
        answer += f"**Size:** {analysis['size']:,} bytes\n"
        answer += f"**Lines:** {analysis['lines']:,}\n"
        answer += f"**Words:** {analysis['words']:,}\n"
        answer += f"**Characters:** {analysis['characters']:,}\n\n"

        answer += f"**Preview:**\n```{file_ext}\n{text[:1000]}...\n```"

        return json.dumps({
            "status": "success",
            "file_type": "text",
            "content": text,
            "analysis": analysis,
            "answer": answer
        })

    except UnicodeDecodeError:
        return json.dumps({
            "status": "error",
            "error": "Cannot decode file as text",
            "answer": "File appears to be binary and cannot be analyzed as text"
        })


def _analyze_pdf_file(file_data: bytes, filename: str) -> str:
    """Analyze PDF files."""
    return json.dumps({
        "status": "info",
        "message": "PDF analysis requires additional libraries",
        "answer": "PDF analysis coming soon! Requires PyPDF2 or similar library."
    })


def _analyze_image_file(file_data: bytes, filename: str) -> str:
    """Analyze image files."""
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(file_data))

        analysis = {
            "filename": filename,
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height
        }

        answer = f"## 🖼️ Image Analysis: {filename}\n\n"
        answer += f"**Format:** {analysis['format']}\n"
        answer += f"**Size:** {analysis['width']} × {analysis['height']} pixels\n"
        answer += f"**Mode:** {analysis['mode']}\n\n"
        answer += "*Image preview available below*"

        return json.dumps({
            "status": "success",
            "file_type": "image",
            "analysis": analysis,
            "answer": answer
        })

    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "PIL not available",
            "answer": "Image analysis requires Pillow. Install with: `pip install Pillow`"
        })


# Tool definitions
FILE_ANALYSIS_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_file",
            "description": "Analyze uploaded file (CSV, Excel, JSON, text, code, images). Extracts data, provides statistics, and summarizes content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_base64": {
                        "type": "string",
                        "description": "Base64 encoded file content"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename (used to detect file type)"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["auto", "data", "text", "code", "json", "image", "pdf"],
                        "description": "Type of analysis to perform",
                        "default": "auto"
                    }
                },
                "required": ["file_base64", "filename"]
            }
        }
    }
]

# Tool execution mapping
FILE_ANALYSIS_TOOL_FUNCTIONS = {
    "analyze_file": analyze_file
}


def execute_file_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute file analysis tool."""
    if tool_name not in FILE_ANALYSIS_TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}"
        })

    try:
        func = FILE_ANALYSIS_TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


if __name__ == "__main__":
    print("File Analysis Tool - Ready!")
    print("Supports: CSV, Excel, JSON, text, code, images")
