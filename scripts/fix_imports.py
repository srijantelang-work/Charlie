#!/usr/bin/env python3
"""
Import resolution fix script for Charlie AI Assistant Backend
This script helps resolve import issues in VS Code and other IDEs
"""

import json
import os
from pathlib import Path


def create_vscode_settings():
    """Create VS Code settings to help with import resolution"""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    # Settings for Python path and linting
    settings = {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe" if os.name == 'nt' else "./venv/bin/python",
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": False,
        "python.linting.flake8Enabled": True,
        "python.formatting.provider": "black",
        "python.analysis.autoImportCompletions": True,
        "python.analysis.typeCheckingMode": "basic",
        "python.analysis.autoSearchPaths": True,
        "python.analysis.extraPaths": ["./app"],
        "files.associations": {
            "*.py": "python"
        }
    }
    
    settings_file = vscode_dir / "settings.json"
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)
    
    print(f"✅ Created VS Code settings: {settings_file}")


def create_python_path():
    """Create .pythonpath file for better import resolution"""
    pythonpath_content = """app
app/core
app/api
app/services
app/models
"""
    
    with open(".pythonpath", 'w') as f:
        f.write(pythonpath_content)
    
    print("✅ Created .pythonpath file")


def create_pyproject_tool_config():
    """Add tool configurations to pyproject.toml if missing"""
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return
    
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    # Check if mypy config exists
    if "[tool.mypy]" not in content:
        mypy_config = """
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
"""
        content += mypy_config
        print("✅ Added mypy configuration")
    
    # Check if pylint config exists
    if "[tool.pylint]" not in content:
        pylint_config = """
[tool.pylint.messages_control]
disable = ["C0114", "C0116", "R0903", "W0613"]

[tool.pylint.format]
max-line-length = "88"
"""
        content += pylint_config
        print("✅ Added pylint configuration")
    
    with open(pyproject_path, 'w') as f:
        f.write(content)


def check_dependencies():
    """Check if critical dependencies are available"""
    critical_deps = [
        "fastapi",
        "uvicorn", 
        "slowapi",
        "pydantic",
        "supabase"
    ]
    
    missing_deps = []
    
    for dep in critical_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} is available")
        except ImportError:
            missing_deps.append(dep)
            print(f"❌ {dep} is missing")
    
    if missing_deps:
        print(f"\n📦 Missing dependencies: {', '.join(missing_deps)}")
        print("Run: python scripts/install_dependencies.py")
        return False
    
    print("\n🎉 All critical dependencies are available!")
    return True


def main():
    """Main function to fix import issues"""
    print("🔧 Charlie AI Assistant - Import Fix Utility")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Create VS Code settings
    create_vscode_settings()
    
    # Create Python path file
    create_python_path()
    
    # Update pyproject.toml
    create_pyproject_tool_config()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 50)
    print("📋 Import Resolution Checklist:")
    print("1. ✅ VS Code settings created")
    print("2. ✅ Python path configuration added")
    print("3. ✅ Tool configurations updated")
    print(f"4. {'✅' if deps_ok else '❌'} Dependencies {'available' if deps_ok else 'missing'}")
    
    if not deps_ok:
        print("\n⚠️  Some dependencies are missing. Please run:")
        print("   python scripts/install_dependencies.py")
    
    print("\n🚀 Next steps to resolve import issues:")
    print("1. Restart VS Code completely")
    print("2. Open the project folder in VS Code")
    print("3. Select the correct Python interpreter (Ctrl/Cmd + Shift + P → 'Python: Select Interpreter')")
    print("4. If using virtual environment, select the venv Python executable")
    print("5. Reload the window (Ctrl/Cmd + Shift + P → 'Developer: Reload Window')")
    
    print("\n💡 If issues persist:")
    print("- Clear Python cache: find . -name '__pycache__' -type d -exec rm -rf {} +")
    print("- Reinstall dependencies: python scripts/install_dependencies.py")
    print("- Check Python interpreter path in VS Code status bar")


if __name__ == "__main__":
    main() 