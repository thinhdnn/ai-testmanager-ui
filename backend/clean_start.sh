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

# Clean up Playwright projects folder
echo "🎭 Cleaning Playwright projects..."
if [ -d "../playwright_projects" ]; then
    # Count projects before cleanup
    project_count=$(find ../playwright_projects -maxdepth 1 -type d ! -path ../playwright_projects | wc -l)
    if [ "$project_count" -gt 0 ]; then
        echo "   🗑️  Removing $project_count Playwright projects..."
        find ../playwright_projects -maxdepth 1 -type d ! -path ../playwright_projects -exec rm -rf {} +
        # Verify cleanup
        remaining_count=$(find ../playwright_projects -maxdepth 1 -type d ! -path ../playwright_projects | wc -l)
        if [ "$remaining_count" -eq 0 ]; then
            echo "   ✅ Playwright projects folder cleaned ($project_count projects removed)"
        else
            echo "   ⚠️  Some projects may remain ($remaining_count left)"
        fi
    else
        echo "   ℹ️  No Playwright projects to clean"
    fi
else
    echo "   ℹ️  Playwright projects folder doesn't exist"
fi

# Start database and cloudbeaver fresh
echo "🐘 Starting fresh PostgreSQL and CloudBeaver..."
docker-compose up -d postgres cloudbeaver

# Wait longer for database
echo "⏳ Waiting for database (30 seconds)..."
sleep 30

# Ensure uv is available and manage venv/dependencies with uv
echo "🧰 Ensuring uv is available..."
if ! command -v uv >/dev/null 2>&1; then
    echo "⬇️ Installing uv (standalone)..."
    if command -v curl >/dev/null 2>&1; then
       curl -LsSf https://astral.sh/uv/install.sh | sh|| {
            echo "❌ Failed to install uv via installer"; exit 1; }
        # Ensure common user bin dirs are on PATH for this session
        export PATH="$HOME/.local/bin:$HOME/Library/Python/3.12/bin:$PATH"
    else
        echo "❌ curl is required to install uv automatically. Please install curl and rerun."; exit 1
    fi
fi

# Prefer active venv; otherwise use .venv managed by uv
echo "🧰 Ensuring Python virtual environment..."
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Using active virtual environment: $VIRTUAL_ENV"
elif [ -d ".venv" ]; then
    echo "🐍 Activating local .venv..."
    source .venv/bin/activate || { echo "❌ Failed to activate .venv"; exit 1; }
else
    echo "📦 Creating .venv with uv..."
    uv venv .venv || { echo "❌ Failed to create .venv with uv"; exit 1; }
    echo "🐍 Activating newly created .venv..."
    source .venv/bin/activate || { echo "❌ Failed to activate .venv"; exit 1; }
fi

echo "📥 Installing backend dependencies with uv..."
uv pip install -r requirements.txt || { echo "❌ Failed to install requirements with uv"; exit 1; }

# Create tables
echo "🏗️  Creating tables from models..."
uv run -- python -c "
from app.database import get_engine, Base
from app.models import *
print('Creating all tables...')
Base.metadata.create_all(bind=get_engine())
print('✅ Tables created successfully!')
"

# Load sample data
echo "📊 Loading sample data..."
uv run -- python sample_data.py

# Start the FastAPI application
echo "🚀 Starting FastAPI application..."
uv run -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Clean fresh setup complete!"
echo "🌐 API Documentation: http://localhost:8000/docs"
echo "🐘 CloudBeaver: http://localhost:8978"
echo "🎭 Playwright projects: Clean slate ready for new projects" 