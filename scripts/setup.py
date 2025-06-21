#!/usr/bin/env python3
"""
Setup script for Charlie AI Assistant Backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result.returncode == 0


def check_python_version():
    """Check if Python 3.11+ is available"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_poetry():
    """Check if Poetry is installed"""
    if shutil.which("poetry") is None:
        print("❌ Poetry not found. Please install Poetry first:")
        print("   curl -sSL https://install.python-poetry.org | python3 -")
        return False
    print("✅ Poetry is installed")
    return True


def check_docker():
    """Check if Docker is available"""
    if shutil.which("docker") is None:
        print("⚠️  Docker not found. Docker is optional but recommended for development")
        return False
    print("✅ Docker is available")
    return True


def setup_environment():
    """Setup the development environment"""
    print("🚀 Setting up Charlie AI Assistant Backend...")
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_poetry():
        return False
    
    check_docker()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command("poetry install"):
        print("❌ Failed to install dependencies")
        return False
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\n⚙️  Creating .env file from template...")
        shutil.copy(env_example, env_file)
        print("✅ Created .env file. Please edit it with your configuration.")
    
    # Create required directories
    print("\n📁 Creating required directories...")
    directories = [
        "logs",
        "temp",
        "uploads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")
    
    # Setup pre-commit hooks
    print("\n🔧 Setting up pre-commit hooks...")
    if run_command("poetry run pre-commit install", check=False):
        print("✅ Pre-commit hooks installed")
    else:
        print("⚠️  Failed to install pre-commit hooks (optional)")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your Supabase and Google Cloud credentials")
    print("2. Run 'poetry run uvicorn app.main:app --reload' to start the development server")
    print("3. Visit http://localhost:8000/docs to see the API documentation")
    
    return True


def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Just check prerequisites
        check_python_version()
        check_poetry()
        check_docker()
        return
    
    success = setup_environment()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 