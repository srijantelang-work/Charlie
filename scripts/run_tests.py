#!/usr/bin/env python3
"""
Test runner script for Charlie AI Assistant Backend
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    success = result.returncode == 0
    print(f"{'✅' if success else '❌'} {description} {'passed' if success else 'failed'}")
    return success


def main():
    """Run all tests and code quality checks"""
    print("🧪 Running Charlie AI Assistant Backend Tests")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    all_passed = True
    
    # Run unit tests
    if not run_command("poetry run pytest tests/ -v --tb=short", "Unit tests"):
        all_passed = False
    
    # Run code formatting check
    if not run_command("poetry run black --check app/ tests/", "Code formatting (Black)"):
        all_passed = False
    
    # Run import sorting check
    if not run_command("poetry run isort --check-only app/ tests/", "Import sorting (isort)"):
        all_passed = False
    
    # Run linting
    if not run_command("poetry run flake8 app/ tests/", "Code linting (flake8)"):
        all_passed = False
    
    # Run type checking
    if not run_command("poetry run mypy app/", "Type checking (mypy)"):
        all_passed = False
    
    # Run test coverage
    if not run_command("poetry run pytest tests/ --cov=app --cov-report=term-missing", "Test coverage"):
        all_passed = False
    
    print(f"\n{'🎉' if all_passed else '❌'} All checks {'passed' if all_passed else 'failed'}")
    
    if not all_passed:
        print("\n📝 To fix formatting issues, run:")
        print("  poetry run black app/ tests/")
        print("  poetry run isort app/ tests/")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main() 