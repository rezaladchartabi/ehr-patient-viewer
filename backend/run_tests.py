#!/usr/bin/env python3
"""
Test runner script for the EHR backend application.
This script sets up the test environment and runs all tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_test_environment():
    """Setup test environment variables"""
    os.environ["PYTEST_RUNNING"] = "true"
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    os.environ["TESTING"] = "true"
    
    # Set test-specific configuration
    os.environ["DB_PATH"] = ":memory:"  # Use in-memory database for tests
    os.environ["CACHE_TTL"] = "0.1"  # Very short TTL for tests
    os.environ["RATE_LIMIT_WINDOW"] = "1"  # Short window for tests
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests

def run_tests(test_path=None, coverage=True, verbose=False, markers=None):
    """Run the test suite"""
    setup_test_environment()
    
    # Build pytest command
    cmd = ["python3", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("test_main_updated.py")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    if verbose:
        cmd.append("-v")
    
    if markers:
        cmd.extend(["-m", markers])
    
    # Add additional options
    cmd.extend([
        "--tb=short",
        "--disable-warnings",
        "--strict-markers"
    ])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("=" * 60)
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print("❌ Tests failed!")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    setup_test_environment()
    
    cmd = [
        "python3", "-m", "pytest", 
        f"test_main_updated.py::{test_name}",
        "-v", "--tb=short"
    ]
    
    print(f"Running specific test: {test_name}")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print("=" * 60)
        print("✅ Test passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print("❌ Test failed!")
        return False

def run_frontend_tests():
    """Run frontend tests"""
    print("Running frontend tests...")
    print("=" * 60)
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = ["npm", "test", "--", "--watchAll=false", "--coverage"]
    
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print("=" * 60)
        print("✅ Frontend tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print("❌ Frontend tests failed!")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run EHR application tests")
    parser.add_argument(
        "--test", 
        help="Run a specific test (e.g., TestCacheSystem::test_cache_basic_operations)"
    )
    parser.add_argument(
        "--no-coverage", 
        action="store_true", 
        help="Run tests without coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--markers", "-m", 
        help="Run tests with specific markers (e.g., 'unit' or 'integration')"
    )
    parser.add_argument(
        "--frontend", 
        action="store_true", 
        help="Run frontend tests instead of backend tests"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run both backend and frontend tests"
    )
    
    args = parser.parse_args()
    
    if args.frontend:
        success = run_frontend_tests()
    elif args.all:
        print("Running all tests (backend + frontend)")
        print("=" * 60)
        
        # Run backend tests
        backend_success = run_tests(
            coverage=not args.no_coverage,
            verbose=args.verbose,
            markers=args.markers
        )
        
        print("\n" + "=" * 60)
        print("Backend tests completed. Running frontend tests...")
        print("=" * 60)
        
        # Run frontend tests
        frontend_success = run_frontend_tests()
        
        success = backend_success and frontend_success
    elif args.test:
        success = run_specific_test(args.test)
    else:
        success = run_tests(
            coverage=not args.no_coverage,
            verbose=args.verbose,
            markers=args.markers
        )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
