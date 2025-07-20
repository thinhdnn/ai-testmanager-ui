#!/bin/bash

# Test Runner Script for AI Test Manager
# Runs all tests in the tests/ directory

echo "🧪 Running all tests in tests/ directory..."
echo "=========================================="

# Check if we're in the backend directory
if [ ! -d "tests" ]; then
    echo "❌ Error: tests/ directory not found. Please run this script from the backend directory."
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "📦 pytest not found. Setting up environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "🔧 Creating virtual environment..."
        
        # Try different Python versions
        if command -v python3.10 &> /dev/null; then
            python3.10 -m venv venv
        elif command -v python3.11 &> /dev/null; then
            python3.11 -m venv venv
        elif command -v python3.12 &> /dev/null; then
            python3.12 -m venv venv
        elif command -v python3 &> /dev/null; then
            python3 -m venv venv
        else
            echo "❌ Error: No Python 3.x found. Please install Python 3.10 or later."
            exit 1
        fi
        
        echo "✅ Virtual environment created!"
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "📦 Installing dependencies from requirements-dev.txt..."
    pip install -r requirements-dev.txt
    
    # Check if installation was successful
    if ! command -v pytest &> /dev/null; then
        echo "❌ Error: Failed to install dependencies. Please check your Python environment."
        exit 1
    fi
    
    echo "✅ Dependencies installed successfully!"
    echo ""
fi

# Run all tests
echo "📁 Running tests from: $(pwd)/tests/"
echo ""

# Run pytest with all tests
pytest tests/ -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    exit 0
else
    echo ""
    echo "❌ Some tests failed!"
    exit 1
fi 