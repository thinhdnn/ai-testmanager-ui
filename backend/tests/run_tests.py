#!/usr/bin/env python3
"""
Script to run all API tests for AI Test Manager
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests(test_type="all", verbose=False):
    """
    Run API tests
    
    Args:
        test_type (str): Type of tests to run ('all', 'auth', 'projects', 'test_cases', 'fixtures', 'test_results', 'integration')
        verbose (bool): Run tests in verbose mode
    """
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add coverage if available
    try:
        import coverage
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
    except ImportError:
        print("Coverage not available, running without coverage")
    
    # Add specific test files based on type
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "auth":
        cmd.append("tests/test_auth.py")
    elif test_type == "projects":
        cmd.append("tests/test_projects.py")
    elif test_type == "test_cases":
        cmd.append("tests/test_test_cases.py")
    elif test_type == "fixtures":
        cmd.append("tests/test_fixtures.py")
    elif test_type == "test_results":
        cmd.append("tests/test_test_results.py")
    elif test_type == "integration":
        cmd.append("tests/test_integration.py")
    else:
        print(f"Unknown test type: {test_type}")
        print("Available types: all, auth, projects, test_cases, fixtures, test_results, integration")
        return False
    
    # Add additional pytest options
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings"  # Disable warnings
    ])
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def run_specific_test(test_file, test_name=None):
    """
    Run a specific test
    
    Args:
        test_file (str): Test file path
        test_name (str): Specific test name (optional)
    """
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    cmd = ["python", "-m", "pytest", "-v"]
    
    if test_name:
        cmd.append(f"{test_file}::{test_name}")
    else:
        cmd.append(test_file)
    
    print(f"Running specific test: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running test: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run API tests for AI Test Manager")
    parser.add_argument(
        "--type", 
        choices=["all", "auth", "projects", "test_cases", "fixtures", "test_results", "integration"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    parser.add_argument(
        "--test",
        help="Run specific test name (use with --file)"
    )
    
    args = parser.parse_args()
    
    if args.file:
        success = run_specific_test(args.file, args.test)
    else:
        success = run_tests(args.type, args.verbose)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 