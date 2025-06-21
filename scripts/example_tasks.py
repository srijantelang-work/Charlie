#!/usr/bin/env python3
"""
Example Task Scripts for Charlie
Demonstrates various automation capabilities
"""

from typing import Optional

# Example Python scripts that can be executed by the task engine

EXAMPLE_SCRIPTS = {
    "hello_world": {
        "name": "Hello World",
        "description": "Simple hello world script",
        "security_level": "low",
        "script": """
# Simple hello world script
name = TASK_PARAMETERS.get('name', 'World')
message = f"Hello, {name}!"
print(message)

# Return result
result = {
    "message": message,
    "name": name,
    "timestamp": str(datetime.now())
}
""",
        "parameters": {
            "name": "Charlie User"
        }
    },
    
    "system_info": {
        "name": "System Information",
        "description": "Get basic system information",
        "security_level": "medium",
        "script": """
import platform
import json
from datetime import datetime

# Get system information
info = {
    "platform": platform.platform(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "python_version": platform.python_version(),
    "timestamp": str(datetime.now())
}

print(json.dumps(info, indent=2))
result = info
""",
        "parameters": {}
    },
    
    "file_analyzer": {
        "name": "File Analyzer",
        "description": "Analyze files in a directory",
        "security_level": "medium",
        "script": """
import os
import json
from pathlib import Path
from datetime import datetime

# Get directory from parameters
directory = TASK_PARAMETERS.get('directory', '.')
max_files = TASK_PARAMETERS.get('max_files', 10)

# Analyze files
files_info = []
directory_path = Path(directory)

if directory_path.exists() and directory_path.is_dir():
    for i, file_path in enumerate(directory_path.iterdir()):
        if i >= max_files:
            break
            
        if file_path.is_file():
            try:
                stat = file_path.stat()
                files_info.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": str(datetime.fromtimestamp(stat.st_mtime)),
                    "extension": file_path.suffix
                })
            except Exception as e:
                files_info.append({
                    "name": file_path.name,
                    "error": str(e)
                })

result = {
    "directory": str(directory_path),
    "files_count": len(files_info),
    "files": files_info,
    "analyzed_at": str(datetime.now())
}

print(json.dumps(result, indent=2))
""",
        "parameters": {
            "directory": ".",
            "max_files": 5
        }
    },
    
    "text_processor": {
        "name": "Text Processor",
        "description": "Process and analyze text",
        "security_level": "low",
        "script": """
import json
import re
from datetime import datetime

# Get text from parameters
text = TASK_PARAMETERS.get('text', 'Hello World')
operation = TASK_PARAMETERS.get('operation', 'analyze')

result = {
    "original_text": text,
    "operation": operation,
    "timestamp": str(datetime.now())
}

if operation == "analyze":
    result.update({
        "length": len(text),
        "words": len(text.split()),
        "lines": len(text.split('\\n')),
        "characters_no_spaces": len(text.replace(' ', '')),
        "uppercase_count": sum(1 for c in text if c.isupper()),
        "lowercase_count": sum(1 for c in text if c.islower()),
        "digit_count": sum(1 for c in text if c.isdigit())
    })
elif operation == "uppercase":
    result["processed_text"] = text.upper()
elif operation == "lowercase":
    result["processed_text"] = text.lower()
elif operation == "reverse":
    result["processed_text"] = text[::-1]
elif operation == "word_count":
    words = text.split()
    word_freq = {}
    for word in words:
        word = word.lower().strip('.,!?";')
        word_freq[word] = word_freq.get(word, 0) + 1
    result["word_frequency"] = word_freq

print(json.dumps(result, indent=2))
""",
        "parameters": {
            "text": "Hello World! This is a sample text for processing.",
            "operation": "analyze"
        }
    },
    
    "math_calculator": {
        "name": "Math Calculator",
        "description": "Perform mathematical calculations",
        "security_level": "low",
        "script": """
import json
import math
from datetime import datetime

# Get calculation parameters
expression = TASK_PARAMETERS.get('expression', '2 + 2')
operation = TASK_PARAMETERS.get('operation', 'eval')

result = {
    "expression": expression,
    "operation": operation,
    "timestamp": str(datetime.now())
}

try:
    if operation == "eval":
        # Safe evaluation - only allow basic math operations
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round})
        
        # Evaluate the expression safely
        calc_result = eval(expression, {"__builtins__": {}}, allowed_names)
        result["result"] = calc_result
        result["success"] = True
        
    elif operation == "factorial":
        n = int(expression)
        if n < 0:
            raise ValueError("Factorial not defined for negative numbers")
        result["result"] = math.factorial(n)
        result["success"] = True
        
    elif operation == "fibonacci":
        n = int(expression)
        if n < 0:
            raise ValueError("Fibonacci not defined for negative numbers")
        
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        result["result"] = fibonacci(min(n, 30))  # Limit to prevent long execution
        result["success"] = True
        
except Exception as e:
    result["error"] = str(e)
    result["success"] = False

print(json.dumps(result, indent=2))
""",
        "parameters": {
            "expression": "math.sqrt(16) + math.pi",
            "operation": "eval"
        }
    }
}


def get_example_script(name: str) -> Optional[dict]:
    """Get an example script by name"""
    return EXAMPLE_SCRIPTS.get(name)


def list_example_scripts() -> list:
    """List all available example scripts"""
    return [
        {
            "name": name,
            "title": script["name"],
            "description": script["description"],
            "security_level": script["security_level"]
        }
        for name, script in EXAMPLE_SCRIPTS.items()
    ]


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        script_name = sys.argv[1]
        script = get_example_script(script_name)
        if script:
            print(f"Script: {script['name']}")
            print(f"Description: {script['description']}")
            print(f"Security Level: {script['security_level']}")
            print("\nScript Content:")
            print(script['script'])
            print("\nDefault Parameters:")
            print(json.dumps(script['parameters'], indent=2))
        else:
            print(f"Script '{script_name}' not found")
    else:
        print("Available example scripts:")
        for script in list_example_scripts():
            print(f"- {script['name']}: {script['title']} ({script['security_level']})")
            print(f"  {script['description']}")
            print() 