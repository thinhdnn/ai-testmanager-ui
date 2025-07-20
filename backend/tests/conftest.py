import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI

# Import app only when needed
def get_test_app():
    """Get test app instance"""
    try:
        from app.main import app
        return app
    except ImportError as e:
        pytest.skip(f"Could not import app: {e}")

def dict_to_object(data):
    """Convert dictionary to object with attributes"""
    class DataObject:
        def __init__(self, data_dict):
            for key, value in data_dict.items():
                setattr(self, key, value)
    return DataObject(data)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def async_client():
    """Create async client with fresh database for each test"""
    app = get_test_app()
    
    # Create fresh database connection for each test
    from app.database import Base
    test_url = "postgresql+asyncpg://testmanager_user:testmanager_password@localhost:5432/test_db"
    engine = create_async_engine(test_url, echo=False, poolclass=StaticPool)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Dependency override
    async def override_get_db():
        async with async_session() as session:
            yield session

    from app.database import get_async_session
    app.dependency_overrides[get_async_session] = override_get_db

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    
    try:
        yield client
    finally:
        await client.aclose()
        await engine.dispose()

@pytest.fixture
def test_user_data():
    """Test user data for authentication"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

@pytest_asyncio.fixture
async def auth_headers(async_client, test_user_data):
    """Get authentication headers for authenticated requests"""
    # First register the user
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json=test_user_data
    )
    
    if register_response.status_code != 201:
        # User might already exist, try to login
        login_data = {
            "username": test_user_data["email"],  # fastapi-users uses email as username
            "password": test_user_data["password"]
        }
        login_response = await async_client.post(
            "/api/v1/auth/jwt/login",
            data=login_data
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
    else:
        # User was created, now login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await async_client.post(
            "/api/v1/auth/jwt/login",
            data=login_data
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_project_data():
    """Test project data"""
    return {
        "name": "Test Project",
        "description": "A test project for testing",
        "status": "active"
    }

@pytest.fixture
def test_test_case_data():
    """Test test case data"""
    return {
        "name": "Test Case 1",
        "status": "pending",
        "is_manual": False
    }

@pytest_asyncio.fixture
async def test_project(async_client, auth_headers, test_project_data):
    """Create a test project"""
    headers = auth_headers
    
    response = await async_client.post("/api/v1/projects/", json=test_project_data, headers=headers)
    if response.status_code == 201:
        return dict_to_object(response.json())
    else:
        # Project might already exist, try to get it
        projects_response = await async_client.get("/api/v1/projects/", headers=headers)
        projects = projects_response.json()
        for project in projects:
            if project["name"] == test_project_data["name"]:
                return dict_to_object(project)
        raise Exception("Could not create or find test project")

@pytest_asyncio.fixture
async def test_test_case(async_client, auth_headers, test_project, test_test_case_data):
    """Create a test test case"""
    headers = auth_headers
    project = test_project
    
    test_case_data = {**test_test_case_data, "project_id": str(project.id)}
    response = await async_client.post("/api/v1/test-cases/", json=test_case_data, headers=headers)
    if response.status_code == 201:
        return dict_to_object(response.json())
    else:
        # Test case might already exist, try to get it
        test_cases_response = await async_client.get(f"/api/v1/test-cases/?project_id={project.id}", headers=headers)
        test_cases = test_cases_response.json()
        for test_case in test_cases:
            if test_case["name"] == test_test_case_data["name"]:
                return dict_to_object(test_case)
        raise Exception("Could not create or find test test case")

@pytest_asyncio.fixture
async def test_fixture(async_client, auth_headers, test_project):
    """Create a test fixture"""
    headers = auth_headers
    project = test_project
    fixture_data = {
        "name": "Test Fixture",
        "type": "inline",
        "playwright_script": "print('cleanup code')",
        "project_id": str(project.id)
    }
    response = await async_client.post("/api/v1/fixtures/", json=fixture_data, headers=headers)
    if response.status_code == 201:
        return dict_to_object(response.json())
    else:
        # Fixture might already exist, try to get it
        fixtures_response = await async_client.get(f"/api/v1/fixtures/project/{project.id}", headers=headers)
        fixtures = fixtures_response.json()
        for fixture in fixtures:
            if fixture["name"] == "Test Fixture":
                return dict_to_object(fixture)
        raise Exception("Could not create or find test fixture")

@pytest_asyncio.fixture
async def test_tag(async_client, auth_headers):
    """Create a test tag"""
    headers = auth_headers
    
    tag_data = {
        "name": "test-tag",
        "description": "A test tag"
    }
    response = await async_client.post("/api/v1/tags/", json=tag_data, headers=headers)
    if response.status_code == 201:
        return dict_to_object(response.json())
    else:
        # Tag might already exist, try to get it
        tags_response = await async_client.get("/api/v1/tags/", headers=headers)
        tags = tags_response.json()
        for tag in tags:
            if tag["name"] == tag_data["name"]:
                return dict_to_object(tag)
        raise Exception("Could not create or find test tag") 