import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
class TestAPIBasic:
    """Basic API tests"""
    
    async def test_api_docs_available(self, async_client):
        """Test if API documentation is available"""
        response = await async_client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    async def test_openapi_schema(self, async_client):
        """Test OpenAPI schema endpoint"""
        response = await async_client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify it's valid JSON with required fields
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    async def test_api_root(self, async_client):
        """Test API root endpoint"""
        response = await async_client.get("/")
        # Should return 200 or 404 depending on if root endpoint exists
        assert response.status_code in [200, 404]
    
    async def test_health_check(self, async_client):
        """Test health check endpoint if exists"""
        response = await async_client.get("/health")
        # Should return 200 or 404 depending on if health endpoint exists
        assert response.status_code in [200, 404]
    
    async def test_nonexistent_endpoint(self, async_client):
        """Test that nonexistent endpoints return 404"""
        response = await async_client.get("/nonexistent-endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_api_info(self, async_client):
        """Test API info from OpenAPI schema"""
        response = await async_client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        info = data.get("info", {})
        
        # Check if API has basic info
        assert "title" in info or "version" in info
    
    async def test_api_paths(self, async_client):
        """Test that API has some endpoints defined"""
        response = await async_client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        paths = data.get("paths", {})
        
        # Print available paths for debugging
        print("Available API paths:")
        for path in sorted(paths.keys()):
            print(f"  {path}")
        
        # Should have at least some endpoints
        assert len(paths) > 0 