#!/bin/bash

# AI Test Manager Backend Startup Script
echo "🚀 Starting AI Test Manager Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if not installed
if [ ! -f "venv/pyvenv.cfg" ] || ! pip show fastapi > /dev/null 2>&1; then
    echo "📋 Installing dependencies..."
    pip install fastapi uvicorn sqlalchemy "pydantic[email]" pydantic-settings alembic python-multipart python-jose passlib bcrypt psycopg2-binary
fi

# Start PostgreSQL with Docker Compose
echo "🐘 Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Check if database is ready
until docker exec testmanager_postgres pg_isready -U testmanager_user -d testmanager_db > /dev/null 2>&1; do
    echo "⏳ Database not ready yet, waiting..."
    sleep 2
done

echo "✅ Database is ready!"

# Run database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

# Start FastAPI backend
echo "🌟 Starting FastAPI backend..."
echo "📊 API Documentation: http://localhost:8000/docs"
echo "🔍 PgAdmin: http://localhost:5050"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 