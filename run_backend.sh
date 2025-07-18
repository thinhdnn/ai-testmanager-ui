#!/bin/bash

# Script to run backend from root directory
echo "🔧 Running backend from root directory..."

# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Run uvicorn with provided arguments or default
if [ $# -eq 0 ]; then
    echo "🚀 Starting FastAPI with default settings..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "🚀 Running: $@"
    "$@"
fi 