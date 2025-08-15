from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from ...database import get_db
from ...schemas.test_case import TestCase, TestCaseCreate, TestCaseUpdate, TestCaseFixtureCreate, TestCaseFixtureUpdate
from ...crud import test_case as crud_test_case
from ...models.versioning import TestCaseVersion, StepVersion
from ...auth import current_active_user
from ...models.user import User
from ...services.playwright_test_case import generate_test_script, save_test_script, list_test_scripts

logger = logging.getLogger(__name__)

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
    db.refresh(db_version)
    
    # Copy current steps to StepVersion table
    from ...models.step import Step
    current_steps = db.query(Step).filter(
        Step.test_case_id == test_case.id
    ).order_by(Step.order).all()
    
    for step in current_steps:
        step_version = StepVersion(
            test_case_version_id=db_version.id,
            action=step.action,
            data=step.data,
            expected=step.expected,
            playwright_code=step.playwright_script,
            selector=step.selector if hasattr(step, 'selector') else None,
            order=step.order,
            disabled=step.disabled,
            created_by=step.created_by
        )
        db.add(step_version)
    
    db.commit()
    return db_version


@router.post("/", response_model=TestCase, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """Create new test case with auto-versioning and auto-script generation"""
    # Create test case
    db_test_case = crud_test_case.create_test_case(db=db, test_case=test_case)
    
    # Auto-create first version
    _create_version(db, db_test_case, "1.0.0")
    
    # Auto-generate test script if project exists
    if db_test_case.project_id:
        try:
            await crud_test_case.regenerate_test_case_script(db, str(db_test_case.id))
            logger.info(f"Auto-generated test script for new test case: {db_test_case.id}")
        except Exception as e:
            # Log error but don't fail the test case creation
            logger.warning(f"Failed to auto-generate test script for test case {db_test_case.id}: {str(e)}")
    
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
async def update_test_case(
    test_case_id: str,
    test_case: TestCaseUpdate,
    auto_version: bool = Query(True, description="Auto-create version on update"),
    db: Session = Depends(get_db)
):
    """Update test case with optional auto-versioning and auto-script regeneration"""
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Create version before update if requested
    new_version = None
    if auto_version:
        new_version = _create_version(db, db_test_case)
    
    # Update test case  
    updated_test_case = crud_test_case.update_test_case(db=db, test_case_id=test_case_id, test_case=test_case)
    
    # Update version field if new version was created
    if new_version:
        updated_test_case.version = new_version.version
        db.commit()
        db.refresh(updated_test_case)
    
    # Auto-regenerate test script if project exists
    if updated_test_case.project_id:
        try:
            await crud_test_case.regenerate_test_case_script(db, test_case_id)
            logger.info(f"Auto-regenerated test script for updated test case: {test_case_id}")
        except Exception as e:
            # Log error but don't fail the test case update
            logger.warning(f"Failed to auto-regenerate test script for test case {test_case_id}: {str(e)}")
    
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
            "description": version.description,
            "playwright_script": version.playwright_script,
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
    
    # Update current test case with version data (only fields that exist in TestCaseVersion)
    test_case.name = db_version.name
    test_case.playwright_script = db_version.playwright_script
    test_case.version = version  # Update current version
    
    # Delete current steps
    from ...models.step import Step
    db.query(Step).filter(Step.test_case_id == test_case_id).delete()
    
    # Restore steps from version
    step_versions = db.query(StepVersion).filter(
        StepVersion.test_case_version_id == db_version.id
    ).order_by(StepVersion.order).all()
    
    for step_version in step_versions:
        new_step = Step(
            test_case_id=test_case_id,
            action=step_version.action,
            data=step_version.data,
            expected=step_version.expected,
            playwright_script=step_version.playwright_code,
            order=step_version.order,
            disabled=step_version.disabled,
            created_by=step_version.created_by
        )
        db.add(new_step)
    
    db.commit()
    db.refresh(test_case)

    # Lấy version mới nhất sau khi restore
    latest_version = (
        db.query(TestCaseVersion)
        .filter(TestCaseVersion.test_case_id == test_case_id)
        .order_by(TestCaseVersion.created_at.desc())
        .first()
    )
    if latest_version:
        test_case.version = latest_version.version
        db.commit()
        db.refresh(test_case)

    return test_case


@router.post("/{test_case_id}/versions/create", response_model=dict)
def create_test_case_version(
    test_case_id: str,
    reason: str = Query(..., description="Reason for creating version"),
    db: Session = Depends(get_db)
):
    """Create a new version of test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Create version
    version = _create_version(db, test_case)
    
    # Update test case version field
    test_case.version = version.version
    db.commit()
    db.refresh(test_case)
    
    return {
        "message": "Version created successfully",
        "version": version.version,
        "reason": reason,
        "created_at": version.created_at
    }


@router.get("/{test_case_id}/versions/{version}/steps", response_model=List[dict])
def get_test_case_version_steps(
    test_case_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get steps for a specific version of a test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Get the specific version
    db_version = db.query(TestCaseVersion).filter(
        TestCaseVersion.test_case_id == test_case_id,
        TestCaseVersion.version == version
    ).first()
    
    if not db_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for test case"
        )
    
    # Get step versions for this test case version
    step_versions = db.query(StepVersion).filter(
        StepVersion.test_case_version_id == db_version.id
    ).order_by(StepVersion.order).all()
    
    return [
        {
            "id": str(step.id),
            "action": step.action,
            "data": step.data,
            "expected": step.expected,
            "playwright_script": step.playwright_code,
            "order": step.order,
            "disabled": step.disabled,
            "created_at": step.created_at,
            "updated_at": step.updated_at
        }
        for step in step_versions
    ]


@router.post("/{test_case_id}/versions/{version}/copy-steps", response_model=dict)
def copy_current_steps_to_version(
    test_case_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Copy current steps to a specific version"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Get the specific version
    db_version = db.query(TestCaseVersion).filter(
        TestCaseVersion.test_case_id == test_case_id,
        TestCaseVersion.version == version
    ).first()
    
    if not db_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for test case"
        )
    
    # Delete existing step versions for this version
    db.query(StepVersion).filter(
        StepVersion.test_case_version_id == db_version.id
    ).delete()
    
    # Copy current steps to StepVersion table
    from ...models.step import Step
    current_steps = db.query(Step).filter(
        Step.test_case_id == test_case.id
    ).order_by(Step.order).all()
    
    for step in current_steps:
        step_version = StepVersion(
            test_case_version_id=db_version.id,
            action=step.action,
            data=step.data,
            expected=step.expected,
            playwright_code=step.playwright_script,
            selector=step.selector if hasattr(step, 'selector') else None,
            order=step.order,
            disabled=step.disabled,
            created_by=step.created_by
        )
        db.add(step_version)
    
    db.commit()
    
    return {
        "message": f"Copied {len(current_steps)} steps to version {version}",
        "steps_count": len(current_steps)
    }


# Test Case Fixture endpoints
@router.post("/{test_case_id}/fixtures", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_fixture_to_test_case(
    test_case_id: str,
    fixture_data: TestCaseFixtureCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Add a fixture to a test case"""
    try:
        result = crud_test_case.add_fixture_to_test_case(
            db, test_case_id, fixture_data, str(current_user.id)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{test_case_id}/fixtures/{fixture_id}")
def remove_fixture_from_test_case(
    test_case_id: str,
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Remove a fixture from a test case"""
    success = crud_test_case.remove_fixture_from_test_case(db, test_case_id, fixture_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fixture not found in test case")
    return {"message": "Fixture removed from test case"}


@router.get("/{test_case_id}/fixtures", response_model=List[dict])
def get_test_case_fixtures(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get all fixtures associated with a test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    fixtures = crud_test_case.get_test_case_fixtures(db, test_case_id)
    return fixtures


@router.patch("/{test_case_id}/fixtures/{fixture_id}/order")
def update_fixture_order(
    test_case_id: str,
    fixture_id: str,
    new_order: int = Query(..., description="New order for the fixture"),
    db: Session = Depends(get_db)
):
    """Update the order of a fixture in a test case"""
    success = crud_test_case.update_test_case_fixture_order(db, test_case_id, fixture_id, new_order)
    if not success:
        raise HTTPException(status_code=404, detail="Fixture not found in test case")
    return {"message": "Fixture order updated"}


@router.patch("/{test_case_id}/fixtures/reorder")
def reorder_test_case_fixtures(
    test_case_id: str,
    fixture_orders: List[dict],
    db: Session = Depends(get_db)
):
    """Reorder all fixtures for a test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    success = crud_test_case.reorder_test_case_fixtures(db, test_case_id, fixture_orders)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder fixtures")
    return {"message": "Fixtures reordered successfully"}


@router.get("/{test_case_id}/fixtures/{fixture_id}/steps", response_model=List[dict])
def get_test_case_fixture_steps(
    test_case_id: str,
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get steps for a specific fixture in a test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Check if fixture is associated with test case
    fixtures = crud_test_case.get_test_case_fixtures(db, test_case_id)
    fixture_exists = any(f["fixture_id"] == fixture_id for f in fixtures)
    if not fixture_exists:
        raise HTTPException(status_code=404, detail="Fixture not found in test case")
    
    # Get fixture steps
    from ...models.step import Step
    steps = db.query(Step).filter(
        Step.fixture_id == fixture_id
    ).order_by(Step.order).all()
    
    return [
        {
            "id": str(step.id),
            "fixture_id": str(step.fixture_id),
            "action": step.action,
            "data": step.data,
            "expected": step.expected,
            "playwright_script": step.playwright_script,
            "order": step.order,
            "disabled": step.disabled,
            "created_at": step.created_at,
            "updated_at": step.updated_at
        }
        for step in steps
    ]


# ============ PLAYWRIGHT TEST SCRIPT GENERATION ENDPOINTS ============

@router.post("/{test_case_id}/generate-script", response_model=dict)
def generate_test_case_script(
    test_case_id: str,
    project_name: Optional[str] = Query(None, description="Target Playwright project name"),
    db: Session = Depends(get_db)
):
    """Generate Playwright test script from test case"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Generate test script
    result = generate_test_script(db, test_case_id, project_name)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate test script: {result.get('error', 'Unknown error')}"
        )
    
    return {
        "success": True,
        "message": "Test script generated successfully",
        "filename": result['filename'],
        "test_case_name": result['test_case_name'],
        "content": result['content'],
        "template_context": result['template_context']
    }


@router.post("/{test_case_id}/generate-and-save", response_model=dict)
def generate_and_save_test_case_script(
    test_case_id: str,
    project_name: str = Query(..., description="Target Playwright project name"),
    db: Session = Depends(get_db)
):
    """Generate and save Playwright test script to project"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Generate test script
    result = generate_test_script(db, test_case_id, project_name)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate test script: {result.get('error', 'Unknown error')}"
        )
    
    # Save to project
    save_result = save_test_script(project_name, result)
    
    if not save_result.get('success'):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save test script: {save_result.get('error', 'Unknown error')}"
        )
    
    return {
        "success": True,
        "message": "Test script generated and saved successfully",
        "filename": result['filename'],
        "file_path": save_result['file_path'],
        "project_name": project_name,
        "test_case_name": result['test_case_name']
    }


@router.get("/scripts/{project_name}", response_model=List[dict])
def list_project_test_scripts(
    project_name: str,
    db: Session = Depends(get_db)
):
    """List all test scripts in a Playwright project"""
    scripts = list_test_scripts(project_name)
    return scripts


@router.get("/{test_case_id}/preview-script", response_model=dict)
def preview_test_case_script(
    test_case_id: str,
    project_name: Optional[str] = Query(None, description="Target Playwright project name"),
    db: Session = Depends(get_db)
):
    """Preview generated Playwright test script without saving"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Generate test script
    result = generate_test_script(db, test_case_id, project_name)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate test script: {result.get('error', 'Unknown error')}"
        )
    
    return {
        "success": True,
        "preview": True,
        "filename": result['filename'],
        "test_case_name": result['test_case_name'],
        "content": result['content'],
        "template_context": result['template_context'],
        "project_name": project_name or "default"
    }


@router.post("/bulk-generate-scripts", response_model=dict)
def bulk_generate_test_scripts(
    test_case_ids: List[str],
    project_name: str = Query(..., description="Target Playwright project name"),
    save_to_project: bool = Query(True, description="Whether to save scripts to project"),
    db: Session = Depends(get_db)
):
    """Generate Playwright test scripts for multiple test cases"""
    results = []
    errors = []
    
    for test_case_id in test_case_ids:
        try:
            # Check if test case exists
            test_case = crud_test_case.get_test_case(db, test_case_id)
            if not test_case:
                errors.append({
                    "test_case_id": test_case_id,
                    "error": "Test case not found"
                })
                continue
            
            # Generate test script
            result = generate_test_script(db, test_case_id, project_name)
            
            if not result.get('success'):
                errors.append({
                    "test_case_id": test_case_id,
                    "error": result.get('error', 'Unknown error')
                })
                continue
            
            # Save to project if requested
            if save_to_project:
                save_result = save_test_script(project_name, result)
                if not save_result.get('success'):
                    errors.append({
                        "test_case_id": test_case_id,
                        "error": f"Failed to save: {save_result.get('error', 'Unknown error')}"
                    })
                    continue
                
                results.append({
                    "test_case_id": test_case_id,
                    "filename": result['filename'],
                    "file_path": save_result['file_path'],
                    "test_case_name": result['test_case_name']
                })
            else:
                results.append({
                    "test_case_id": test_case_id,
                    "filename": result['filename'],
                    "test_case_name": result['test_case_name'],
                    "content": result['content']
                })
                
        except Exception as e:
            errors.append({
                "test_case_id": test_case_id,
                "error": str(e)
            })
    
    return {
        "success": True,
        "message": f"Processed {len(test_case_ids)} test cases",
        "results": results,
        "errors": errors,
        "summary": {
            "total": len(test_case_ids),
            "successful": len(results),
            "failed": len(errors),
            "project_name": project_name,
            "saved_to_project": save_to_project
        }
    }


 