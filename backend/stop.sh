#!/bin/bash

# AI Test Manager Backend Stop Script
echo "🛑 Stopping AI Test Manager Backend..."

# Stop FastAPI backend (if running)
echo "🔌 Stopping FastAPI backend..."
pkill -f "uvicorn app.main:app" 2>/dev/null || echo "FastAPI was not running"

# Stop Docker containers
echo "🐘 Stopping PostgreSQL and services..."
docker-compose down

echo "✅ All services stopped!" 