#!/usr/bin/env python3
"""
Basic test for daemon framework without external dependencies.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that we can import the basic modules."""
    try:
        # Test basic Python imports first
        import logging
        import threading
        import signal
        print("✓ Basic Python modules imported successfully")
        
        # Test our modules (but skip the ones that need external deps)
        print("Testing daemon framework structure...")
        
        # Check if files exist
        src_dir = Path(__file__).parent / "src" / "efis_macos"
        required_files = [
            "__init__.py",
            "daemon.py", 
            "config.py",
            "logging_config.py",
            "service_manager.py"
        ]
        
        for file in required_files:
            file_path = src_dir / file
            if file_path.exists():
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} missing")
                return False
        
        # Check config files
        config_dir = Path(__file__).parent / "config"
        config_files = [
            "macos-config.yaml",
            "com.efis-data-manager.daemon.plist"
        ]
        
        for file in config_files:
            file_path = config_dir / file
            if file_path.exists():
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} missing")
                return False
        
        print("✓ All daemon framework files are present")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    try:
        # Test that we can at least load the modules syntactically
        print("Testing module syntax...")
        
        # We can't actually import due to missing deps, but we can check syntax
        import ast
        
        src_dir = Path(__file__).parent / "src" / "efis_macos"
        
        for py_file in src_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r') as f:
                    source = f.read()
                ast.parse(source)
                print(f"✓ {py_file.name} syntax is valid")
            except SyntaxError as e:
                print(f"✗ {py_file.name} has syntax error: {e}")
                return False
        
        print("✓ All Python files have valid syntax")
        return True
        
    except Exception as e:
        print(f"✗ Syntax test failed: {e}")
        return False

def main():
    """Run basic tests."""
    print("EFIS Data Manager - macOS Daemon Framework Test")
    print("=" * 50)
    
    success = True
    
    if not test_imports():
        success = False
    
    print()
    
    if not test_basic_functionality():
        success = False
    
    print()
    
    if success:
        print("✓ All basic tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip3 install -r requirements.txt")
        print("2. Test daemon: python3 daemon_manager.py create-config")
        print("3. Install service: python3 daemon_manager.py install")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())