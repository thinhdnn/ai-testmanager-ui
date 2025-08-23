from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
from ...crud import fixture as crud_fixture

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
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create new test case with auto-versioning and auto-script generation"""
    # Create test case
    db_test_case = await crud_test_case.create_test_case(db=db, test_case=test_case, created_by=current_user.email)
    
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
    current_user: User = Depends(current_active_user),
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
    updated_test_case = await crud_test_case.update_test_case(db=db, test_case_id=test_case_id, test_case=test_case, updated_by=current_user.email)
    
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
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Update test case status"""
    db_test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    updated_test_case = crud_test_case.update_test_case_status(
        db=db, test_case_id=test_case_id, status=status, last_run_by=current_user.email
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
    """Get all steps of a test case that reference a specific fixture"""
    # Check if test case exists
    test_case = crud_test_case.get_test_case(db, test_case_id=test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Check if fixture exists
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Get steps that reference this fixture
    from ...models.step import Step
    steps = db.query(Step).filter(
        Step.test_case_id == test_case_id,
        Step.referenced_fixture_id == fixture_id
    ).order_by(Step.order).all()
    
    return [
        {
            "id": str(step.id),
            "action": step.action,
            "data": step.data,
            "expected": step.expected,
            "playwright_script": step.playwright_script,
            "order": step.order,
            "disabled": step.disabled,
            "referenced_fixture_id": str(step.referenced_fixture_id),
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


@router.post("/{test_case_id}/run", response_model=dict)
async def run_test_case_locally(
    test_case_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Run a Playwright test case locally"""
    try:
        # Parse request body
        body = await request.json()
        project_identifier = body.get("project_id") or body.get("project_name") or body.get("project_path")
        test_file_path = body.get("test_file_path")
        run_settings = body.get("settings") or {}
        
        if not project_identifier:
            raise HTTPException(status_code=400, detail="Project identifier is required (id/name/path)")
        if not test_file_path:
            raise HTTPException(status_code=400, detail="Test file path is required")
        
        # Resolve Playwright project directory path
        from ...models.project import Project
        from pathlib import Path
        from ...services.playwright_project import playwright_manager, clean_name as clean_project_folder_name
        
        project_dir_path: str | None = None
        project = None
        
        # Try by exact stored path (preferred)
        if isinstance(project_identifier, str) and project_identifier.startswith('/'):
            project_dir_path = project_identifier
        else:
            # Try DB lookup by UUID or name
            try:
                # Try UUID lookup
                project = db.query(Project).filter(Project.id == project_identifier).first()
            except Exception:
                project = None
            if not project:
                # Try by name
                project = db.query(Project).filter(Project.name == project_identifier).first()
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # If DB has stored path, use it
            if project.playwright_project_path:
                # Value is stored as folder name. Resolve via manager to absolute path.
                folder_name = project.playwright_project_path
                project_dir_path = str(playwright_manager.get_project_path(folder_name))
            else:
                # Build from cleaned name using manager base dir
                cleaned_name = clean_project_folder_name(project.name)
                project_dir_path = str(playwright_manager.get_project_path(cleaned_name))
        # Ensure we have a project instance even if identifier was an absolute path
        if project is None:
            try:
                folder_name_from_path = Path(project_dir_path).name if project_dir_path else None
                if folder_name_from_path:
                    project = db.query(Project).filter(Project.playwright_project_path == folder_name_from_path).first()
            except Exception:
                project = None
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found for provided identifier/path")

        # Ensure test case exists (used for naming)
        test_case_obj = crud_test_case.get_test_case(db, test_case_id)
        if not test_case_obj:
            raise HTTPException(status_code=404, detail="Test case not found")

        # Import the playwright service here to avoid circular imports
        from ...services.playwright_test_case import run_test_locally
        
        # Run the test locally with absolute project dir path
        result = await run_test_locally(project_dir_path, test_file_path, test_case_id, settings=run_settings)
        
        if result.get('success'):
            # Create test result history and execution records
            from ...models.test_result import TestResultHistory, TestCaseExecution
            
            # Get current user from request headers
            current_user_email = "system"
            try:
                auth_header = request.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    from ...auth import get_current_user_from_token
                    current_user = get_current_user_from_token(token, db)
                    if current_user:
                        current_user_email = current_user.email
            except:
                pass
            
            # Convert duration from ms to seconds
            raw_duration_ms = result.get('duration', 0) or 0
            duration_seconds = int(float(raw_duration_ms) / 1000)

            # Create TestResultHistory for this run
            test_result_history = TestResultHistory(
                project_id=project.id,
                name=f"Run {test_case_obj.name}",
                success=(result.get('status') == 'passed'),
                status=result.get('status', 'completed'),
                execution_time=duration_seconds,
                output=result.get('output', ''),
                error_message=result.get('error', ''),
                created_by=current_user_email,
                last_run_by=current_user_email
            )
            db.add(test_result_history)
            db.commit()
            db.refresh(test_result_history)
            
            # Create TestCaseExecution linked to this run
            # Convert numeric timestamps to timezone-aware datetimes
            from datetime import datetime, timezone
            def _to_dt(value):
                if value is None:
                    return None
                try:
                    return datetime.fromtimestamp(float(value), tz=timezone.utc)
                except Exception:
                    try:
                        # Handle ISO strings like 2025-01-01T00:00:00Z
                        s = str(value).replace('Z', '+00:00')
                        return datetime.fromisoformat(s)
                    except Exception:
                        return None
            start_time_dt = _to_dt(result.get('start_time'))
            end_time_dt = _to_dt(result.get('end_time'))

            test_execution = TestCaseExecution(
                test_result_id=test_result_history.id,
                test_case_id=test_case_id,
                status=result.get('status', 'completed'),
                duration=duration_seconds,
                error_message=result.get('error', ''),
                output=result.get('output', ''),
                start_time=start_time_dt,
                end_time=end_time_dt,
                retries=0
            )
            db.add(test_execution)
            db.commit()
            db.refresh(test_execution)
            
            return {
                "success": True,
                "message": "Test executed successfully",
                "test_result_id": str(test_result_history.id),
                "execution_id": str(test_execution.id),
                "status": result.get('status'),
                "duration": duration_seconds,
                "output": result.get('output'),
                "error": result.get('error')
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error occurred'),
                "output": result.get('output', '')
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running test case {test_case_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run test: {str(e)}"
        )

 
@router.post("/run-multiple", response_model=dict)
async def run_multiple_test_cases(
    request: Request,
    db: Session = Depends(get_db)
):
    """Run multiple test cases at once"""
    try:
        body = await request.json()
        test_case_ids = body.get("test_case_ids", [])
        project_identifier = body.get("project_id") or body.get("project_name") or body.get("project_path")
        run_settings = body.get("settings") or {}
        parallel = body.get("parallel", False)
        max_workers = body.get("max_workers", 3)
        
        if not test_case_ids:
            raise HTTPException(status_code=400, detail="test_case_ids is required")
        if not project_identifier:
            raise HTTPException(status_code=400, detail="Project identifier is required")
        
        # Resolve project directory path
        from ...models.project import Project
        from pathlib import Path
        from ...services.playwright_project import playwright_manager, clean_name as clean_project_folder_name
        
        project_dir_path: str | None = None
        project = None
        
        # Try by exact stored path (preferred)
        if isinstance(project_identifier, str) and project_identifier.startswith('/'):
            project_dir_path = project_identifier
        else:
            # Try DB lookup by UUID or name
            try:
                project = db.query(Project).filter(Project.id == project_identifier).first()
            except Exception:
                project = None
            if not project:
                project = db.query(Project).filter(Project.name == project_identifier).first()
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            if project.playwright_project_path:
                folder_name = project.playwright_project_path
                project_dir_path = str(playwright_manager.get_project_path(folder_name))
            else:
                cleaned_name = clean_project_folder_name(project.name)
                project_dir_path = str(playwright_manager.get_project_path(cleaned_name))
        
        # Get test cases
        test_cases = []
        for test_case_id in test_case_ids:
            test_case = crud_test_case.get_test_case(db, test_case_id)
            if test_case:
                test_cases.append(test_case)
        
        if not test_cases:
            raise HTTPException(status_code=404, detail="No valid test cases found")
        
        # Run tests
        results = []
        errors = []
        
        if parallel:
            # Run tests in parallel using asyncio
            import asyncio
            from ...services.playwright_test_case import run_test_locally
            
            async def run_single_test(test_case):
                try:
                    test_file_path = test_case.test_file_path
                    if not test_file_path:
                        return {
                            "test_case_id": str(test_case.id),
                            "success": False,
                            "error": "No test file path found"
                        }
                    
                    result = await run_test_locally(
                        project_dir_path, 
                        test_file_path, 
                        str(test_case.id), 
                        settings=run_settings
                    )
                    
                    # Create test result records
                    if result.get('success'):
                        await _create_test_result_records(db, project.id, test_case, result, request)
                    
                    return {
                        "test_case_id": str(test_case.id),
                        "test_case_name": test_case.name,
                        **result
                    }
                except Exception as e:
                    return {
                        "test_case_id": str(test_case.id),
                        "test_case_name": test_case.name,
                        "success": False,
                        "error": str(e)
                    }
            
            # Run with limited concurrency
            semaphore = asyncio.Semaphore(max_workers)
            async def run_with_semaphore(test_case):
                async with semaphore:
                    return await run_single_test(test_case)
            
            tasks = [run_with_semaphore(test_case) for test_case in test_cases]
            results = await asyncio.gather(*tasks)
            
        else:
            # Run tests sequentially
            from ...services.playwright_test_case import run_test_locally
            
            for test_case in test_cases:
                try:
                    test_file_path = test_case.test_file_path
                    if not test_file_path:
                        errors.append({
                            "test_case_id": str(test_case.id),
                            "test_case_name": test_case.name,
                            "error": "No test file path found"
                        })
                        continue
                    
                    result = await run_test_locally(
                        project_dir_path, 
                        test_file_path, 
                        str(test_case.id), 
                        settings=run_settings
                    )
                    
                    # Create test result records
                    if result.get('success'):
                        await _create_test_result_records(db, project.id, test_case, result, request)
                    
                    results.append({
                        "test_case_id": str(test_case.id),
                        "test_case_name": test_case.name,
                        **result
                    })
                    
                except Exception as e:
                    errors.append({
                        "test_case_id": str(test_case.id),
                        "test_case_name": test_case.name,
                        "error": str(e)
                    })
        
        # Calculate summary
        successful = len([r for r in results if r.get('success')])
        failed = len(results) - successful + len(errors)
        
        return {
            "success": True,
            "summary": {
                "total": len(test_case_ids),
                "successful": successful,
                "failed": failed,
                "errors": len(errors)
            },
            "results": results,
            "errors": errors,
            "project_name": project.name if project else "Unknown"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running multiple test cases: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run multiple test cases: {str(e)}"
        )


@router.post("/run-by-tags", response_model=dict)
async def run_test_cases_by_tags(
    request: Request,
    db: Session = Depends(get_db)
):
    """Run test cases by tags"""
    try:
        body = await request.json()
        tags = body.get("tags", [])
        project_identifier = body.get("project_id") or body.get("project_name") or body.get("project_path")
        run_settings = body.get("settings") or {}
        include_all_tags = body.get("include_all_tags", False)  # True: AND logic, False: OR logic
        
        if not tags:
            raise HTTPException(status_code=400, detail="tags is required")
        if not project_identifier:
            raise HTTPException(status_code=400, detail="Project identifier is required")
        
        # Find test cases by tags
        test_cases = []
        for tag in tags:
            # Search test cases that contain this tag
            tag_filter = f"%{tag}%"
            if include_all_tags:
                # AND logic: test case must contain ALL tags
                if not test_cases:
                    test_cases = db.query(TestCase).filter(
                        TestCase.tags.like(tag_filter)
                    ).all()
                else:
                    # Filter existing results to only include test cases with this tag
                    test_cases = [tc for tc in test_cases if tag in (tc.tags or "")]
            else:
                # OR logic: test case contains ANY of the tags
                found_cases = db.query(TestCase).filter(
                    TestCase.tags.like(tag_filter)
                ).all()
                for found_case in found_cases:
                    if found_case not in test_cases:
                        test_cases.append(found_case)
        
        if not test_cases:
            return {
                "success": True,
                "message": f"No test cases found with tags: {tags}",
                "summary": {
                    "total": 0,
                    "successful": 0,
                    "failed": 0
                },
                "results": [],
                "errors": []
            }
        
        # Get test case IDs and run them
        test_case_ids = [str(tc.id) for tc in test_cases]
        
        # Create request body for run_multiple endpoint
        run_request = Request(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/test-cases/run-multiple"
            }
        )
        
        # Call run_multiple endpoint logic
        from .test_cases import run_multiple_test_cases
        return await run_multiple_test_cases(run_request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running test cases by tags: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run test cases by tags: {str(e)}"
        )


@router.post("/projects/{project_id}/run-filtered", response_model=dict)
async def run_project_test_cases_filtered(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Run test cases in a project with filters"""
    try:
        body = await request.json()
        filters = body.get("filters", {})
        run_settings = body.get("settings") or {}
        parallel = body.get("parallel", False)
        max_workers = body.get("max_workers", 3)
        
        # Build query based on filters
        query = db.query(TestCase).filter(TestCase.project_id == project_id)
        
        # Apply filters
        if filters.get("status"):
            query = query.filter(TestCase.status == filters["status"])
        
        if filters.get("tags"):
            tags = filters["tags"]
            if isinstance(tags, list):
                for tag in tags:
                    query = query.filter(TestCase.tags.like(f"%{tag}%"))
            else:
                query = query.filter(TestCase.tags.like(f"%{tags}%"))
        
        if filters.get("is_manual") is not None:
            query = query.filter(TestCase.is_manual == filters["is_manual"])
        
        if filters.get("created_by"):
            query = query.filter(TestCase.created_by == filters["created_by"])
        
        if filters.get("version"):
            query = query.filter(TestCase.version == filters["version"])
        
        # Get filtered test cases
        test_cases = query.all()
        
        if not test_cases:
            return {
                "success": True,
                "message": "No test cases found with the specified filters",
                "summary": {
                    "total": 0,
                    "successful": 0,
                    "failed": 0
                },
                "results": [],
                "errors": []
            }
        
        # Get test case IDs and run them
        test_case_ids = [str(tc.id) for tc in test_cases]
        
        # Create request body for run_multiple endpoint
        run_request = Request(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/test-cases/run-multiple"
            }
        )
        
        # Call run_multiple endpoint logic
        from .test_cases import run_multiple_test_cases
        return await run_multiple_test_cases(run_request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running filtered test cases: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run filtered test cases: {str(e)}"
        )


async def _create_test_result_records(db: Session, project_id: str, test_case: TestCase, result: dict, request: Request):
    """Helper function to create test result records"""
    try:
        from ...models.test_result import TestResultHistory, TestCaseExecution
        
        # Get current user from request headers
        current_user_email = "system"
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                from ...auth import get_current_user_from_token
                current_user = get_current_user_from_token(token, db)
                if current_user:
                    current_user_email = current_user.email
        except:
            pass
        
        # Convert duration from ms to seconds
        raw_duration_ms = result.get('duration', 0) or 0
        duration_seconds = int(float(raw_duration_ms) / 1000)

        # Create TestResultHistory for this run
        test_result_history = TestResultHistory(
            project_id=project_id,
            name=f"Run {test_case.name}",
            success=(result.get('status') == 'passed'),
            status=result.get('status', 'completed'),
            execution_time=duration_seconds,
            output=result.get('output', ''),
            error_message=result.get('error', ''),
            created_by=current_user_email,
            last_run_by=current_user_email
        )
        db.add(test_result_history)
        db.commit()
        db.refresh(test_result_history)
        
        # Create TestCaseExecution linked to this run
        from datetime import datetime, timezone
        def _to_dt(value):
            if value is None:
                return None
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except Exception:
                try:
                    s = str(value).replace('Z', '+00:00')
                    return datetime.fromisoformat(s)
                except Exception:
                    return None
        
        start_time_dt = _to_dt(result.get('start_time'))
        end_time_dt = _to_dt(result.get('end_time'))

        test_execution = TestCaseExecution(
            test_result_id=test_result_history.id,
            test_case_id=str(test_case.id),
            status=result.get('status', 'completed'),
            duration=duration_seconds,
            error_message=result.get('error', ''),
            output=result.get('output', ''),
            start_time=start_time_dt,
            end_time=end_time_dt,
            retries=0
        )
        db.add(test_execution)
        db.commit()
        
    except Exception as e:
        logger.error(f"Error creating test result records: {str(e)}")
        # Don't fail the test execution if record creation fails
        pass

 