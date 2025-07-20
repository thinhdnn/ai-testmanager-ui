import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from tests.conftest import get_test_app


class TestTestCases:
    """Test cases for test case endpoints"""

    @pytest.mark.asyncio
    async def test_create_test_case(self, async_client, auth_headers, test_project):
        """Test creating a new test case"""
        headers = auth_headers
        project = test_project
        
        test_case_data = {
            "name": "New Test Case",
            "project_id": str(project.id),
            "status": "active",
            "is_manual": False
        }
        response = await async_client.post("/api/v1/test-cases/", json=test_case_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == test_case_data["name"]
        assert data["project_id"] == test_case_data["project_id"]
        assert data["status"] == test_case_data["status"]
        assert data["is_manual"] == test_case_data["is_manual"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_test_case_unauthorized(self, async_client, test_project):
        """Test creating test case without authentication (API hiện tại không yêu cầu xác thực)"""
        test_case_data = {
            "project_id": str(test_project.id),
            "name": "Unauthorized Test Case",
            "status": "pending",
            "order": 1,
            "version": "1.0.0",
            "is_manual": False
        }
        response = await async_client.post("/api/v1/test-cases/", json=test_case_data)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_get_test_cases(self, async_client, auth_headers, test_project, test_test_case):
        """Test getting all test cases"""
        headers = auth_headers
        
        response = await async_client.get("/api/v1/test-cases/", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Check that we have at least one test case
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_test_cases_by_project(self, async_client, auth_headers, test_project, test_test_case):
        """Test getting test cases by project"""
        headers = auth_headers
        project = test_project
        
        response = await async_client.get(f"/api/v1/test-cases/?project_id={project.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # All test cases should belong to the specified project
        for test_case in data:
            assert test_case["project_id"] == str(project.id)

    @pytest.mark.asyncio
    async def test_get_test_case_by_id(self, async_client, auth_headers, test_project, test_test_case):
        """Test getting a specific test case by ID"""
        headers = auth_headers
        test_case = test_test_case
        
        response = await async_client.get(f"/api/v1/test-cases/{test_case.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_case.id)
        assert data["name"] == test_case.name
        assert data["project_id"] == str(test_case.project_id)

    @pytest.mark.asyncio
    async def test_get_test_case_not_found(self, async_client, auth_headers):
        """Test getting a test case that doesn't exist"""
        headers = auth_headers
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        response = await async_client.get(f"/api/v1/test-cases/{non_existent_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_test_case(self, async_client, auth_headers, test_project, test_test_case):
        """Test updating a test case"""
        headers = auth_headers
        test_case = test_test_case
        
        update_data = {
            "name": "Updated Test Case",
            "status": "inactive",
            "is_manual": True
        }
        response = await async_client.put(f"/api/v1/test-cases/{test_case.id}", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["status"] == update_data["status"]
        assert data["is_manual"] == update_data["is_manual"]

    @pytest.mark.asyncio
    async def test_update_test_case_not_found(self, async_client, auth_headers):
        """Test updating a test case that doesn't exist"""
        headers = auth_headers
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        update_data = {
            "name": "Updated Test Case",
            "status": "inactive"
        }
        response = await async_client.put(f"/api/v1/test-cases/{non_existent_id}", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_test_case(self, async_client, auth_headers, test_project, test_test_case):
        """Test deleting a test case"""
        headers = auth_headers
        test_case = test_test_case
        
        response = await async_client.delete(f"/api/v1/test-cases/{test_case.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Test case deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_test_case_not_found(self, async_client, auth_headers):
        """Test deleting a test case that doesn't exist"""
        headers = auth_headers
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        response = await async_client.delete(f"/api/v1/test-cases/{non_existent_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_test_case_invalid_project(self, async_client):
        """Test creating test case with invalid project ID (UUID hợp lệ nhưng không tồn tại)"""
        import uuid
        invalid_project_id = str(uuid.uuid4())
        test_case_data = {
            "project_id": invalid_project_id,
            "name": "Invalid Project Test Case",
            "status": "pending",
            "order": 1,
            "version": "1.0.0",
            "is_manual": False
        }
        response = await async_client.post("/api/v1/test-cases/", json=test_case_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_test_case_invalid_data(self, async_client, auth_headers, test_project):
        """Test creating test case with invalid data"""
        headers = auth_headers
        project = test_project
        
        # Missing required fields
        invalid_data = {
            "project_id": str(project.id)
        }
        response = await async_client.post("/api/v1/test-cases/", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_test_cases_pagination(self, async_client, auth_headers, test_test_case):
        """Test test cases pagination"""
        headers = auth_headers
        
        response = await async_client.get("/api/v1/test-cases/?skip=0&limit=5", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5  # Should respect limit

    @pytest.mark.asyncio
    async def test_get_test_cases_filter_by_status(self, async_client, auth_headers, test_test_case):
        """Test filtering test cases by status"""
        headers = auth_headers
        
        response = await async_client.get("/api/v1/test-cases/?status=active", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Check that all returned test cases have active status
        for test_case in data:
            assert test_case["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_test_cases_filter_by_status_pending(self, async_client, auth_headers, test_test_case):
        """Test filtering test cases by status pending"""
        headers = auth_headers
        
        response = await async_client.get("/api/v1/test-cases/?status=pending", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Check that all returned test cases have pending status
        for test_case in data:
            assert test_case["status"] == "pending" 