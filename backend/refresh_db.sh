#!/bin/bash

# Database refresh script - only refreshes database
echo "🔄 Refreshing database..."

# Stop containers
echo "📦 Stopping containers..."
docker-compose down

# Remove database volume
echo "🗑️  Removing database volume..."
docker volume prune -f

# Start database and pgadmin
echo "🐘 Starting PostgreSQL and PgAdmin..."
docker-compose up -d postgres pgadmin

# Wait for database
echo "⏳ Waiting for database..."
sleep 20

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Create tables
echo "🏗️  Creating tables from models..."
python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('✅ Database refreshed successfully!')
"

# Load sample data
echo "📊 Loading sample data..."
python sample_data.py

echo "✅ Database refresh complete!"
echo "💡 Run 'uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload' to start API server" 