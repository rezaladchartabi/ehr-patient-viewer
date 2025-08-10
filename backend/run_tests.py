#!/usr/bin/env python3
"""
Test runner script for the FHIR proxy backend
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests with coverage"""
    print("🧪 Running FHIR Proxy Backend Tests")
    print("=" * 50)
    
    # Install test dependencies if needed
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("📦 Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Run tests
    print("\n🔍 Running unit tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_main.py", 
        "-v", 
        "--tb=short",
        "--color=yes"
    ], cwd=os.path.dirname(__file__))
    
    if result.returncode == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    print(f"🔍 Running test: {test_name}")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        f"test_main.py::{test_name}", 
        "-v", 
        "--tb=short",
        "--color=yes"
    ], cwd=os.path.dirname(__file__))
    
    return result.returncode == 0

def list_tests():
    """List all available tests"""
    print("📋 Available tests:")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_main.py", 
        "--collect-only", 
        "-q"
    ], cwd=os.path.dirname(__file__), capture_output=True, text=True)
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if '::' in line and 'test_' in line:
                print(f"   {line}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            list_tests()
        elif command == "run":
            if len(sys.argv) > 2:
                test_name = sys.argv[2]
                success = run_specific_test(test_name)
                sys.exit(0 if success else 1)
            else:
                success = run_tests()
                sys.exit(0 if success else 1)
        else:
            print("Usage:")
            print("  python run_tests.py list     - List all tests")
            print("  python run_tests.py run      - Run all tests")
            print("  python run_tests.py run <test_name> - Run specific test")
    else:
        success = run_tests()
        sys.exit(0 if success else 1)
