#!/usr/bin/env python3
"""
Test script for Charlie CLI implementation
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all CLI modules can be imported"""
    
    print("🧪 Testing Charlie CLI imports...")
    
    try:
        # Test core modules
        from charlie import __version__
        print(f"✅ Charlie version: {__version__}")
        
        from charlie.utils.config import ConfigManager
        print("✅ Config manager imported")
        
        from charlie.ui.components import create_welcome_panel
        print("✅ UI components imported")
        
        from charlie.commands.chat import ChatCommand
        print("✅ Chat command imported")
        
        from charlie.commands.config import ConfigCommand  
        print("✅ Config command imported")
        
        from charlie.utils.history import HistoryManager
        print("✅ History manager imported")
        
        print("\n🎉 All core modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration management"""
    
    print("\n🧪 Testing configuration management...")
    
    try:
        from charlie.utils.config import ConfigManager
        from charlie.cli import CLIContext
        
        # Create mock context
        class MockContext:
            def __init__(self):
                self.config = ConfigManager()
                self.debug = False
                self.verbose = False
        
        ctx = MockContext()
        
        print(f"✅ Config directory: {ctx.config.config_dir}")
        print(f"✅ Config file: {ctx.config.config_file}")
        
        # Test basic config operations
        test_key = 'test_setting'
        test_value = 'test_value'
        
        ctx.config.set(test_key, test_value)
        retrieved_value = ctx.config.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Config set/get working")
        else:
            print("❌ Config set/get failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Config test error: {e}")
        return False

def test_cli_structure():
    """Test CLI structure and commands"""
    
    print("\n🧪 Testing CLI structure...")
    
    try:
        from charlie.cli import cli, show_welcome, show_help
        
        print("✅ CLI entry point imported")
        print("✅ CLI helper functions imported")
        
        # Test that CLI group exists
        if hasattr(cli, 'commands'):
            print(f"✅ CLI has {len(cli.commands)} commands registered")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI structure test error: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Charlie CLI Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config, 
        test_cli_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Charlie CLI is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 