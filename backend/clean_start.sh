#!/bin/bash

# Clean start script - completely cleans everything and starts fresh
echo "🧹 Complete cleanup and fresh start..."

# Stop all containers
echo "🛑 Stopping all containers..."
docker-compose down

# Remove ALL volumes (not just prune)
echo "🗑️  Removing ALL database volumes..."
docker volume ls | grep postgres | awk '{print $2}' | xargs -r docker volume rm
docker volume prune -f

# Remove docker networks
echo "🌐 Cleaning networks..."
docker network prune -f

# Start database and pgadmin fresh
echo "🐘 Starting fresh PostgreSQL and PgAdmin..."
docker-compose up -d postgres pgadmin

# Wait longer for database
echo "⏳ Waiting for database (30 seconds)..."
sleep 30

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Create tables
echo "🏗️  Creating tables from models..."
python -c "
from app.database import engine, Base
from app.models import *
print('Creating all tables...')
Base.metadata.create_all(bind=engine)
print('✅ Tables created successfully!')
"

# Load sample data
echo "📊 Loading sample data..."
python sample_data.py

# Start the FastAPI application
echo "🚀 Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Clean fresh setup complete!"
echo "🌐 API Documentation: http://localhost:8000/docs"
echo "🐘 PgAdmin: http://localhost:5050" 