import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
class TestProjects:
    """Test project endpoints"""
    
    async def test_create_project(self, async_client, auth_headers):
        """Test creating a new project"""
        project_data = {
            "name": "New Test Project",
            "description": "A new test project",
            "environment": "development"
        }
        
        response = await async_client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["environment"] == project_data["environment"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_project_unauthorized(self, async_client):
        """Test creating project without authentication"""
        project_data = {
            "name": "Unauthorized Project",
            "description": "This should fail",
            "environment": "test"
        }
        
        response = await async_client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_projects(self, async_client, auth_headers, test_project):
        """Test getting all projects"""
        response = await async_client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test project is in the list
        project_names = [p["name"] for p in data]
        assert "Test Project" in project_names
    
    async def test_get_projects_with_stats(self, async_client, auth_headers, test_project):
        """Test getting projects with statistics"""
        response = await async_client.get("/api/v1/projects/with-stats", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if stats are included
        project = data[0]
        assert "test_cases_count" in project
        assert "fixtures_count" in project
        assert "success_rate" in project
        assert "total_runs" in project
        assert "avg_execution_time" in project
    
    async def test_get_project_by_id(self, async_client, auth_headers, test_project):
        """Test getting a specific project by ID"""
        response = await async_client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["name"] == test_project.name
        assert data["description"] == test_project.description
        assert "test_cases_count" in data
        assert "fixtures_count" in data
    
    async def test_get_project_not_found(self, async_client, auth_headers):
        """Test getting a non-existent project"""
        response = await async_client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_update_project(self, async_client, auth_headers, test_project):
        """Test updating a project"""
        update_data = {
            "name": "Updated Test Project",
            "description": "Updated description",
            "environment": "production"
        }
        
        response = await async_client.put(f"/api/v1/projects/{test_project.id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["environment"] == update_data["environment"]
    
    async def test_update_project_not_found(self, async_client, auth_headers):
        """Test updating a non-existent project"""
        update_data = {
            "name": "Updated Project",
            "description": "Updated description"
        }
        
        response = await async_client.put("/api/v1/projects/00000000-0000-0000-0000-000000000000", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_delete_project(self, async_client, auth_headers, test_project):
        """Test deleting a project"""
        response = await async_client.delete(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Project deleted successfully"
        
        # Verify project is deleted
        get_response = await async_client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_delete_project_not_found(self, async_client, auth_headers):
        """Test deleting a non-existent project"""
        response = await async_client.delete("/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_create_project_invalid_data(self, async_client, auth_headers):
        """Test creating project with invalid data"""
        # Missing required fields
        project_data = {
            "description": "Missing name field"
        }
        
        response = await async_client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_get_projects_pagination(self, async_client, auth_headers, test_project):
        """Test projects pagination"""
        response = await async_client.get("/api/v1/projects/?skip=0&limit=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5  # Should respect limit 