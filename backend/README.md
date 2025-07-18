# AI Test Manager Backend

FastAPI backend with PostgreSQL database for AI Test Manager application.

## Setup

### Prerequisites
- Python 3.8+
- Docker and Docker Compose (recommended)
- OR PostgreSQL database + pip/pipenv (for local development)

### Quick Start

#### Option 1: Complete Fresh Setup (Recommended)

```bash
cd backend
./clean_start.sh
```

This script will:
- Stop all containers and clean volumes completely
- Start PostgreSQL fresh
- Create all database tables from models (no migrations needed)
- Load sample data
- Start FastAPI server

#### Option 2: Manual Setup

1. Install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Start database only:
```bash
./refresh_db.sh
```

3. Start API server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 2: Full Docker Development Environment

Run everything in Docker (backend + database):
```bash
docker-compose -f docker-compose.dev.yml up --build
```

#### Option 3: Local PostgreSQL Installation

1. Install PostgreSQL locally and create database:
```bash
createdb testmanager_db
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env file with your database credentials
```

5. Run migrations:
```bash
alembic upgrade head
```

## Database Access

### PgAdmin (when using Docker)
- URL: http://localhost:5050
- Email: admin@testmanager.com
- Password: admin123

### Database Connection Details
- Host: localhost
- Port: 5432
- Database: testmanager_db
- Username: testmanager_user
- Password: testmanager_password

## Sample Data

To populate the database with sample data for testing:

```bash
python sample_data.py
```

This will create:
- 2 sample users (admin, tester1)
- 2 sample projects (E-commerce, Mobile App)
- 5 sample test cases

## Available Scripts

### Backend Scripts (run from `backend/` directory)

```bash
# Complete fresh start (removes all data, creates fresh DB + starts API)
./clean_start.sh         # Recommended for clean slate

# Refresh database only (no API server)
./refresh_db.sh          # Creates tables + loads sample data

# Traditional startup with migrations
./start.sh              # Uses Alembic migrations
./stop.sh               # Stop containers
```

### Root Directory Scripts (run from project root)

```bash
# Start backend API from root directory
./run_backend.sh                        # Start API server
./run_backend.sh python sample_data.py  # Run backend commands
```

## Docker Commands

### Manual Docker Commands
```bash
# Start only PostgreSQL
docker-compose up -d postgres

# Start all services (PostgreSQL + PgAdmin)
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres

# Complete cleanup (removes volumes)
docker-compose down
docker volume prune -f
```

The API will be available at:
- Main API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## API Endpoints

### Users
- `POST /api/v1/users/` - Create new user
- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Projects
- `POST /api/v1/projects/` - Create new project
- `GET /api/v1/projects/` - Get all projects
- `GET /api/v1/projects/{project_id}` - Get project by ID with statistics
- `PUT /api/v1/projects/{project_id}` - Update project
- `DELETE /api/v1/projects/{project_id}` - Delete project

### Test Cases
- `POST /api/v1/test-cases/` - Create new test case
- `GET /api/v1/test-cases/` - Get all test cases (supports filtering by project_id and status)
- `GET /api/v1/test-cases/{test_case_id}` - Get test case by ID
- `PUT /api/v1/test-cases/{test_case_id}` - Update test case
- `PATCH /api/v1/test-cases/{test_case_id}/status` - Update test case status
- `DELETE /api/v1/test-cases/{test_case_id}` - Delete test case

### Health Check
- `GET /health` - Check API and database health

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── users.py
│   │   └── api.py
│   ├── crud/
│   │   └── user.py
│   ├── models/
│   │   ├── base.py
│   │   └── user.py
│   ├── schemas/
│   │   └── user.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── alembic/
├── requirements.txt
└── README.md
``` 