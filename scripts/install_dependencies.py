#!/usr/bin/env python3
"""
Dependency installation script for Charlie AI Assistant Backend
This script resolves import issues by ensuring all dependencies are installed
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description, check=True):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} succeeded")
            if result.stdout:
                print(f"Output: {result.stdout}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error: {e}")
        return False


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_poetry():
    """Install Poetry if not available"""
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
        print("✅ Poetry is already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 Installing Poetry...")
        if os.name == 'nt':  # Windows
            return run_command(
                "powershell -Command \"(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -\"",
                "Installing Poetry on Windows",
                check=False
            )
        else:  # Unix/macOS
            return run_command(
                "curl -sSL https://install.python-poetry.org | python3 -",
                "Installing Poetry on Unix/macOS",
                check=False
            )


def install_with_pip():
    """Fallback: Install dependencies with pip"""
    print("\n📦 Fallback: Installing dependencies with pip...")
    
    dependencies = [
        "fastapi[all]>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "supabase>=2.0.0",
        "google-cloud-speech>=2.22.0",
        "google-cloud-texttospeech>=2.16.0",
        "google-generativeai>=0.3.0",
        "pyaudio>=0.2.11",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "celery>=5.3.0",
        "redis>=5.0.0",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "aiofiles>=23.2.1",
        "librosa>=0.10.1",
        "soundfile>=0.12.1",
        "asyncio-mqtt>=0.13.0",
        "psutil>=5.9.6",
        "slowapi>=0.1.9"
    ]
    
    for dep in dependencies:
        success = run_command(f"pip install {dep}", f"Installing {dep}", check=False)
        if not success:
            print(f"⚠️  Failed to install {dep}, continuing...")
    
    return True


def main():
    """Main dependency installation function"""
    print("🚀 Charlie AI Assistant - Dependency Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Python version check failed")
        sys.exit(1)
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Try Poetry first
    if install_poetry():
        print("\n📦 Installing dependencies with Poetry...")
        if run_command("poetry install", "Installing project dependencies", check=False):
            print("\n🎉 Dependencies installed successfully with Poetry!")
            print("\nNext steps:")
            print("1. Copy .env.example to .env and configure your API keys")
            print("2. Run: poetry run uvicorn app.main:app --reload")
            print("3. Visit: http://localhost:8000/docs")
            return
    
    # Fallback to pip
    print("\n⚠️  Poetry installation failed, trying pip...")
    install_with_pip()
    
    print("\n🎉 Dependencies installed with pip!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your API keys")
    print("2. Run: python -m uvicorn app.main:app --reload")
    print("3. Visit: http://localhost:8000/docs")
    
    print("\n📝 Note: Import errors in VS Code should be resolved after:")
    print("1. Restarting VS Code")
    print("2. Selecting the correct Python interpreter")
    print("3. Running the dependency installation")


if __name__ == "__main__":
    main() 