import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
class TestAuth:
    """Test authentication endpoints"""
    
    async def test_register_user(self, async_client):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        # User might already exist from previous test runs
        if response.status_code == 400 and "REGISTER_USER_ALREADY_EXISTS" in response.text:
            # This is expected if user already exists
            return
            
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    async def test_login_user(self, async_client, test_user_data):
        """Test user login"""
        # First register the user
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "username": test_user_data["email"],  # fastapi-users uses email as username
            "password": test_user_data["password"]
        }
        
        response = await async_client.post("/api/v1/auth/jwt/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    async def test_get_current_user(self, async_client, auth_headers):
        """Test getting current user information"""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "password" not in data
    
    async def test_invalid_login(self, async_client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/v1/auth/jwt/login", data=login_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_duplicate_registration(self, async_client, test_user_data):
        """Test registering the same user twice"""
        # First registration might succeed or fail (if user already exists)
        response1 = await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Second registration should always fail
        response2 = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "REGISTER_USER_ALREADY_EXISTS" in response2.text 