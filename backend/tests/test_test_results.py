import pytest
from fastapi import status
import uuid

@pytest.mark.asyncio
class TestTestResults:
    """Test test results endpoints (read-only)"""

    async def test_get_test_results(self, async_client):
        """Test getting all test results"""
        response = await async_client.get("/api/v1/test-results/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_test_result_by_id_not_found(self, async_client):
        """Test getting a non-existent test result by ID (UUID hợp lệ nhưng không tồn tại)"""
        non_existent_id = str(uuid.uuid4())
        response = await async_client.get(f"/api/v1/test-results/{non_existent_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_project_test_results(self, async_client, test_project):
        """Test getting test results by project"""
        response = await async_client.get(f"/api/v1/test-results/projects/{test_project.id}/results")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_latest_project_result_not_found(self, async_client):
        """Test getting latest test result for a non-existent project"""
        non_existent_project_id = str(uuid.uuid4())
        response = await async_client.get(f"/api/v1/test-results/projects/{non_existent_project_id}/results/latest")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_project_test_statistics(self, async_client, test_project):
        """Test getting test execution statistics for a project"""
        response = await async_client.get(f"/api/v1/test-results/projects/{test_project.id}/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "avg_execution_time" in data
        assert "latest_result" in data
        assert "success_rate" in data
        assert "total_runs" in data

    async def test_get_test_case_execution_history(self, async_client, test_test_case):
        """Test getting execution history for a test case"""
        response = await async_client.get(f"/api/v1/test-results/test-cases/{test_test_case.id}/executions")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_test_case_execution_statistics(self, async_client, test_test_case):
        """Test getting execution statistics for a test case"""
        response = await async_client.get(f"/api/v1/test-results/test-cases/{test_test_case.id}/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_recent_test_runs_analytics(self, async_client):
        """Test getting recent test runs analytics"""
        response = await async_client.get("/api/v1/test-results/analytics/recent-runs")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "total_runs" in data
        assert "successful_runs" in data
        assert "failed_runs" in data
        assert "recent_results" in data 