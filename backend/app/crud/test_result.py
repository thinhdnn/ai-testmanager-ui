from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from ..models.test_result import TestResultHistory, TestCaseExecution
from ..models.user import User
from ..schemas.test_result import (
    TestResultHistoryCreate, 
    TestResultHistoryUpdate,
    TestCaseExecutionCreate,
    TestCaseExecutionUpdate
)


# ============ TEST RESULT HISTORY CRUD ============

def get_test_result(db: Session, result_id: str) -> Optional[TestResultHistory]:
    return db.query(TestResultHistory).filter(TestResultHistory.id == result_id).first()


def get_test_results(db: Session, skip: int = 0, limit: int = 100) -> List[TestResultHistory]:
    return db.query(TestResultHistory).offset(skip).limit(limit).all()


def get_test_results_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 50) -> List[TestResultHistory]:
    results = db.query(TestResultHistory).filter(
        TestResultHistory.project_id == project_id
    ).order_by(TestResultHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    # Populate author_name for each result
    for result in results:
        if result.created_by:
            try:
                user = db.query(User).filter(User.id == UUID(result.created_by)).first()
                result.author_name = user.username if user else None
            except ValueError:
                result.author_name = None
    
    return results


def get_latest_test_result(db: Session, project_id: str) -> Optional[TestResultHistory]:
    return db.query(TestResultHistory).filter(
        TestResultHistory.project_id == project_id
    ).order_by(TestResultHistory.created_at.desc()).first()


def create_test_result(db: Session, test_result: TestResultHistoryCreate) -> TestResultHistory:
    db_result = TestResultHistory(
        project_id=test_result.project_id,
        name=test_result.name,
        test_result_file_name=test_result.test_result_file_name,
        success=test_result.success,
        status=test_result.status,
        execution_time=test_result.execution_time,
        output=test_result.output,
        error_message=test_result.error_message,
        result_data=test_result.result_data,
        browser=test_result.browser,
        video_url=test_result.video_url,
        created_by=test_result.created_by,
        last_run_by=test_result.last_run_by
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def update_test_result(db: Session, result_id: str, test_result: TestResultHistoryUpdate) -> Optional[TestResultHistory]:
    db_result = get_test_result(db, result_id)
    if db_result:
        update_data = test_result.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_result, field, value)
        
        db.commit()
        db.refresh(db_result)
    return db_result


def delete_test_result(db: Session, result_id: str) -> bool:
    db_result = get_test_result(db, result_id)
    if db_result:
        db.delete(db_result)
        db.commit()
        return True
    return False


# ============ TEST CASE EXECUTION CRUD ============

def get_test_case_execution(db: Session, execution_id: str) -> Optional[TestCaseExecution]:
    return db.query(TestCaseExecution).filter(TestCaseExecution.id == execution_id).first()


def get_executions_by_result(db: Session, result_id: str) -> List[TestCaseExecution]:
    return db.query(TestCaseExecution).filter(
        TestCaseExecution.test_result_id == result_id
    ).order_by(TestCaseExecution.start_time).all()


def get_executions_by_test_case(db: Session, test_case_id: str, limit: int = 20) -> List[TestCaseExecution]:
    return db.query(TestCaseExecution).filter(
        TestCaseExecution.test_case_id == test_case_id
    ).order_by(TestCaseExecution.created_at.desc()).limit(limit).all()


def get_project_test_executions(db: Session, project_id: str, skip: int = 0, limit: int = 50) -> List[TestCaseExecution]:
    """Get test case executions for a project"""
    from sqlalchemy.orm import joinedload
    
    return db.query(TestCaseExecution).options(
        joinedload(TestCaseExecution.test_result),
        joinedload(TestCaseExecution.test_case)
    ).join(
        TestResultHistory, TestCaseExecution.test_result_id == TestResultHistory.id
    ).filter(
        TestResultHistory.project_id == project_id
    ).order_by(TestCaseExecution.created_at.desc()).offset(skip).limit(limit).all()


def create_test_case_execution(db: Session, execution: TestCaseExecutionCreate) -> TestCaseExecution:
    db_execution = TestCaseExecution(
        test_result_id=execution.test_result_id,
        test_case_id=execution.test_case_id,
        status=execution.status,
        duration=execution.duration,
        error_message=execution.error_message,
        output=execution.output,
        start_time=execution.start_time,
        end_time=execution.end_time,
        retries=execution.retries
    )
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    return db_execution


def update_test_case_execution(db: Session, execution_id: str, execution: TestCaseExecutionUpdate) -> Optional[TestCaseExecution]:
    db_execution = get_test_case_execution(db, execution_id)
    if db_execution:
        update_data = execution.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_execution, field, value)
        
        db.commit()
        db.refresh(db_execution)
    return db_execution


def delete_test_case_execution(db: Session, execution_id: str) -> bool:
    db_execution = get_test_case_execution(db, execution_id)
    if db_execution:
        db.delete(db_execution)
        db.commit()
        return True
    return False


# ============ STATISTICS AND ANALYTICS ============

def get_project_test_stats(db: Session, project_id: str) -> dict:
    """Get test execution statistics for a project"""
    # Get latest test result
    latest_result = get_latest_test_result(db, project_id)
    
    if not latest_result:
        return {
            "total_runs": 0,
            "latest_result": None,
            "success_rate": 0.0,
            "avg_execution_time": 0
        }
    
    # Count total runs
    total_runs = db.query(TestResultHistory).filter(
        TestResultHistory.project_id == project_id
    ).count()
    
    # Calculate success rate (last 10 runs)
    recent_results = db.query(TestResultHistory).filter(
        TestResultHistory.project_id == project_id
    ).order_by(TestResultHistory.created_at.desc()).limit(10).all()
    
    successful_runs = sum(1 for result in recent_results if result.success)
    success_rate = (successful_runs / len(recent_results)) * 100 if recent_results else 0
    
    # Average execution time (last 10 runs)
    execution_times = [r.execution_time for r in recent_results if r.execution_time]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    
    # Convert latest_result to dict for serialization
    latest_result_dict = None
    if latest_result:
        latest_result_dict = {
            "id": str(latest_result.id),
            "name": latest_result.name,
            "success": latest_result.success,
            "status": latest_result.status,
            "execution_time": latest_result.execution_time,
            "created_at": latest_result.created_at.isoformat() if latest_result.created_at else None,
            "browser": latest_result.browser
        }
    
    return {
        "total_runs": total_runs,
        "latest_result": latest_result_dict,  # Use serializable dict instead of raw model
        "success_rate": round(success_rate, 2),
        "avg_execution_time": round(avg_execution_time, 2)
    }


def get_test_case_execution_stats(db: Session, test_case_id: str) -> dict:
    """Get execution statistics for a specific test case"""
    executions = get_executions_by_test_case(db, test_case_id, limit=50)
    
    if not executions:
        return {
            "total_executions": 0,
            "success_rate": 0.0,
            "avg_duration": 0,
            "last_status": None
        }
    
    total_executions = len(executions)
    successful_executions = sum(1 for ex in executions if ex.status == "passed")
    success_rate = (successful_executions / total_executions) * 100
    
    durations = [ex.duration for ex in executions if ex.duration]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "total_executions": total_executions,
        "success_rate": round(success_rate, 2),
        "avg_duration": round(avg_duration, 2),
        "last_status": executions[0].status if executions else None
    } 