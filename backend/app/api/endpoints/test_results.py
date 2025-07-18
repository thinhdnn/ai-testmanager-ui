from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime

from ...database import get_db
from ...schemas.test_result import TestResultHistory, TestCaseExecution
from ...crud import test_result as crud_result

router = APIRouter()


# ============ VIEW TEST RESULTS (READ-ONLY) ============

@router.get("/", response_model=List[TestResultHistory])
def get_test_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get all test results"""
    results = crud_result.get_test_results(db, skip=skip, limit=limit)
    return results


@router.get("/{result_id}", response_model=TestResultHistory)
def get_test_result(
    result_id: str,
    db: Session = Depends(get_db)
):
    """Get test result by ID"""
    result = crud_result.get_test_result(db, result_id=result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@router.get("/{result_id}/executions", response_model=List[TestCaseExecution])
def get_result_executions(
    result_id: str,
    db: Session = Depends(get_db)
):
    """Get all test case executions for a test result"""
    # Check if result exists
    result = crud_result.get_test_result(db, result_id=result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    executions = crud_result.get_executions_by_result(db, result_id=result_id)
    return executions


# ============ PROJECT TEST RESULTS ============

@router.get("/projects/{project_id}/results", response_model=List[TestResultHistory])
def get_project_test_results(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get test results for a project"""
    results = crud_result.get_test_results_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return results


@router.get("/projects/{project_id}/results/latest", response_model=TestResultHistory)
def get_latest_project_result(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get latest test result for a project"""
    result = crud_result.get_latest_test_result(db, project_id=project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No test results found for this project")
    return result


@router.get("/projects/{project_id}/stats", response_model=Dict)
def get_project_test_statistics(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get test execution statistics for a project"""
    stats = crud_result.get_project_test_stats(db, project_id=project_id)
    return stats


# ============ TEST CASE EXECUTION HISTORY ============

@router.get("/test-cases/{test_case_id}/executions", response_model=List[TestCaseExecution])
def get_test_case_execution_history(
    test_case_id: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get execution history for a test case"""
    executions = crud_result.get_executions_by_test_case(db, test_case_id=test_case_id, limit=limit)
    return executions


@router.get("/test-cases/{test_case_id}/stats", response_model=Dict)
def get_test_case_execution_statistics(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get execution statistics for a test case"""
    stats = crud_result.get_test_case_execution_stats(db, test_case_id=test_case_id)
    return stats


# ============ TEST EXECUTION TRIGGERS ============

@router.post("/projects/{project_id}/run")
async def trigger_project_test_run(
    project_id: str,
    test_name: str = Query(None, description="Optional custom name for this test run"),
    db: Session = Depends(get_db)
):
    """Trigger test run for a project (will run playwright and save results)"""
    # TODO: Implement actual playwright test execution
    # This would:
    # 1. Get project settings (browser, timeout, etc.)
    # 2. Run playwright tests via subprocess
    # 3. Parse results and create TestResultHistory + TestCaseExecution records
    # 4. Return the test result ID
    
    return {
        "message": "Test run triggered successfully",
        "project_id": project_id,
        "test_name": test_name or f"Test Run {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "status": "queued",
        "note": "Playwright execution will be implemented here"
    }


@router.post("/test-cases/{test_case_id}/run")
async def trigger_single_test_case_run(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Trigger test run for a single test case"""
    # TODO: Implement single test case execution
    return {
        "message": "Single test case run triggered",
        "test_case_id": test_case_id,
        "status": "queued",
        "note": "Single test execution will be implemented here"
    }


# ============ ANALYTICS ============

@router.get("/analytics/recent-runs")
def get_recent_test_runs(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get recent test runs analytics"""
    recent_results = crud_result.get_test_results(db, skip=0, limit=50)
    
    # Convert recent_results to serializable dicts
    recent_results_serializable = []
    for result in recent_results[:10]:
        recent_results_serializable.append({
            "id": str(result.id),
            "name": result.name,
            "success": result.success,
            "status": result.status,
            "execution_time": result.execution_time,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "browser": result.browser,
            "project_id": str(result.project_id)
        })
    
    analytics = {
        "total_runs": len(recent_results),
        "successful_runs": sum(1 for r in recent_results if r.success),
        "failed_runs": sum(1 for r in recent_results if not r.success),
        "recent_results": recent_results_serializable  # Use serializable dicts instead of raw models
    }
    
    return analytics 