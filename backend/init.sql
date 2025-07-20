-- Initialize database for AI Test Manager
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional schemas if needed
-- CREATE SCHEMA IF NOT EXISTS test_management;

-- Note: Superuser will be created automatically by Alembic migration
-- Migration: 0fb64c3d0480_add_superuser.py
-- Superuser credentials:
-- Email: admin@testmanager.com
-- Username: admin
-- Password: admin123

-- You can add other initial data here
-- INSERT INTO table_name (column1, column2) VALUES ('value1', 'value2'); 