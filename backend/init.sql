-- Initialize database for AI Test Manager
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional schemas if needed
-- CREATE SCHEMA IF NOT EXISTS test_management;

-- You can add initial data here
-- INSERT INTO table_name (column1, column2) VALUES ('value1', 'value2');

-- Example: Create a test user (this will be created by your FastAPI app)
-- This is just for reference 