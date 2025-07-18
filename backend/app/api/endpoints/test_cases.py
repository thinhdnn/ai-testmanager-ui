from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...schemas.test_case import TestCase, TestCaseCreate, TestCaseUpdate
from ...crud import test_case as crud_test_case
from ...models.versioning import TestCaseVersion

router = APIRouter()


def _create_version(db: Session, test_case, version: str = None):
    """Helper function to create a version of test case"""
    if not version:
        # Auto-generate version based on existing versions
        existing_versions = db.query(TestCaseVersion).filter(
            TestCaseVersion.test_case_id == test_case.id
        ).count()
        version = f"1.{existing_versions}.0"
    
    db_version = TestCaseVersion(
        test_case_id=test_case.id,
        version=version,
        name=test_case.name,
        playwright_script=test_case.playwright_script,
        # Only include fields that exist in TestCaseVersion
        # description=test_case.description,  # not present in TestCase
        # status=test_case.status,  # not present in TestCaseVersion
        # is_manual=test_case.is_manual,  # not present in TestCaseVersion
        # tags=test_case.tags,  # not present in TestCaseVersion
        # order=test_case.order  # not present in TestCaseVersion
    )
    
    db.add(db_version)
    db.commit()
    return db_version


@router.post("/", response_model=TestCase, status_code=status.HTTP_201_CREATED)
def create_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """Create new test case with auto-versioning"""
    # Create test case
    db_test_case = crud_test_case.create_test_case(db=db, test_case=test_case)
    
    # Auto-create first version
    _create_version(db, db_test_case, "1.0.0")
    
    return db_test_case


@router.get("/", response_model=List[TestCase])
def read_test_cases(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get test cases with optional filters"""
    if project_id:
        test_cases = crud_test_case.get_test_cases_by_project(
            db, project_id=project_id, skip=skip, limit=limit
        )
    elif status_filter:
        test_cases = crud_test_case.get_test_cases_by_status(
            db, status=status_filter, skip=skip, limit=limit
        )
    else:
        test_cases = crud_test_case.get_test_cases(db, skip=skip, limit=limit)
    
    return test_cases


@router.get("/{test_case_id}", response_model=TestCase)
def read_test_case(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get test case by ID"""
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return db_test_case


@router.put("/{test_case_id}", response_model=TestCase)
def update_test_case(
    test_case_id: str,
    test_case: TestCaseUpdate,
    auto_version: bool = Query(True, description="Auto-create version on update"),
    db: Session = Depends(get_db)
):
    """Update test case with optional auto-versioning"""
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Create version before update if requested
    if auto_version:
        _create_version(db, db_test_case)
    
    # Update test case  
    updated_test_case = crud_test_case.update_test_case(db=db, test_case_id=test_case_id, test_case=test_case)
    
    return updated_test_case


@router.patch("/{test_case_id}/status")
def update_test_case_status(
    test_case_id: str,
    status: str,
    last_run_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update test case status"""
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    updated_test_case = crud_test_case.update_test_case_status(
        db=db, test_case_id=test_case_id, status=status, last_run_by=last_run_by
    )
    
    return {"message": "Test case status updated", "status": status}


@router.delete("/{test_case_id}")
def delete_test_case(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Delete test case"""
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    crud_test_case.delete_test_case(db=db, test_case_id=test_case_id)
    return {"message": "Test case deleted successfully"}


# ============ VERSIONING ENDPOINTS ============

@router.get("/{test_case_id}/versions", response_model=List[dict])
def get_test_case_versions(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get all versions of a test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Get all versions
    versions = db.query(TestCaseVersion).filter(
        TestCaseVersion.test_case_id == test_case_id
    ).order_by(TestCaseVersion.created_at.desc()).all()
    
    return [
        {
            "id": str(version.id),
            "version": version.version,
            "name": version.name,
            "status": version.status,
            "is_manual": version.is_manual,
            "tags": version.tags,
            "created_at": version.created_at,
            "updated_at": version.updated_at
        }
        for version in versions
    ]


@router.get("/{test_case_id}/versions/{version}", response_model=dict)
def get_test_case_version(
    test_case_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get a specific version of a test case"""
    db_version = db.query(TestCaseVersion).filter(
        TestCaseVersion.test_case_id == test_case_id,
        TestCaseVersion.version == version
    ).first()
    
    if not db_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for test case"
        )
    
    return {
        "id": str(db_version.id),
        "version": db_version.version,
        "test_case_id": str(test_case_id),
        "name": db_version.name,
        "status": db_version.status,
        "is_manual": db_version.is_manual,
        "tags": db_version.tags,
        "created_at": db_version.created_at,
        "updated_at": db_version.updated_at
    }


@router.post("/{test_case_id}/versions/{version}/restore", response_model=TestCase)
def restore_test_case_version(
    test_case_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Restore a test case to a specific version"""
    # Get the version to restore
    db_version = db.query(TestCaseVersion).filter(
        TestCaseVersion.test_case_id == test_case_id,
        TestCaseVersion.version == version
    ).first()
    
    if not db_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for test case"
        )
    
    # Get current test case
    test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Create version of current state before restore
    _create_version(db, test_case)
    
    # Update current test case with version data
    test_case.name = db_version.name
    test_case.playwright_script = db_version.playwright_script
    test_case.status = db_version.status
    test_case.is_manual = db_version.is_manual
    test_case.tags = db_version.tags
    test_case.order = db_version.order
    test_case.version = version  # Update current version
    
    db.commit()
    db.refresh(test_case)
    
    return test_case


 