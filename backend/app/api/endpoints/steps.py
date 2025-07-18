from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...schemas.step import Step, StepCreate, StepUpdate
from ...crud import step as crud_step
from ...models.versioning import StepVersion

router = APIRouter()


def _create_version(db: Session, step, version: str = None):
    """Helper function to create a version of step"""
    # For now, we'll skip step versioning as it's more complex
    # Step versions are managed through test case and fixture versions
    pass


# ============ BASIC STEP CRUD ============

@router.post("/", response_model=Step, status_code=status.HTTP_201_CREATED)
def create_step(
    step: StepCreate,
    db: Session = Depends(get_db)
):
    """Create new step"""
    # Create step
    db_step = crud_step.create_step(db=db, step=step)
    
    return db_step


@router.get("/{step_id}", response_model=Step)
def read_step(
    step_id: str,
    db: Session = Depends(get_db)
):
    """Get step by ID"""
    db_step = crud_step.get_step(db, step_id=step_id)
    if db_step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    return db_step


@router.put("/{step_id}", response_model=Step)
def update_step(
    step_id: str,
    step: StepUpdate,
    db: Session = Depends(get_db)
):
    """Update step"""
    db_step = crud_step.get_step(db, step_id=step_id)
    if db_step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Update step  
    updated_step = crud_step.update_step(db=db, step_id=step_id, step=step)
    
    return updated_step


@router.delete("/{step_id}")
def delete_step(
    step_id: str,
    db: Session = Depends(get_db)
):
    """Delete step"""
    db_step = crud_step.get_step(db, step_id=step_id)
    if db_step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    
    crud_step.delete_step(db=db, step_id=step_id)
    return {"message": "Step deleted successfully"}


# ============ NESTED ROUTES FOR TEST CASES ============

@router.get("/test-cases/{test_case_id}/steps", response_model=List[Step])
def get_test_case_steps(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get all steps of a test case"""
    steps = crud_step.get_steps_by_test_case(db, test_case_id=test_case_id)
    return steps


@router.post("/test-cases/{test_case_id}/steps", response_model=Step, status_code=status.HTTP_201_CREATED)
def create_test_case_step(
    test_case_id: str,
    step: StepCreate,
    db: Session = Depends(get_db)
):
    """Create new step for a test case"""
    # Override test_case_id from URL
    step_data = step.dict()
    step_data['test_case_id'] = test_case_id
    step_data['fixture_id'] = None  # Ensure it's not for fixture
    
    new_step = StepCreate(**step_data)
    return create_step(new_step, db)


# ============ NESTED ROUTES FOR FIXTURES ============

@router.get("/fixtures/{fixture_id}/steps", response_model=List[Step])
def get_fixture_steps(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get all steps of a fixture"""
    steps = crud_step.get_steps_by_fixture(db, fixture_id=fixture_id)
    return steps


@router.post("/fixtures/{fixture_id}/steps", response_model=Step, status_code=status.HTTP_201_CREATED)
def create_fixture_step(
    fixture_id: str,
    step: StepCreate,
    db: Session = Depends(get_db)
):
    """Create new step for a fixture"""
    # Override fixture_id from URL
    step_data = step.dict()
    step_data['fixture_id'] = fixture_id
    step_data['test_case_id'] = None  # Ensure it's not for test case
    
    new_step = StepCreate(**step_data)
    return create_step(new_step, db)


# ============ STEP VERSIONING ============
# Note: Step versioning is managed through TestCase and Fixture versions
# Individual step versioning is complex and may not be needed for most use cases


# ============ REORDER STEPS ============

@router.patch("/test-cases/{test_case_id}/steps/reorder")
def reorder_test_case_steps(
    test_case_id: str,
    step_orders: List[dict],  # [{"step_id": "uuid", "order": 1}, ...]
    db: Session = Depends(get_db)
):
    """Reorder steps in a test case"""
    for item in step_orders:
        step = crud_step.get_step(db, step_id=item["step_id"])
        if step and step.test_case_id == test_case_id:
            step.order = item["order"]
    
    db.commit()
    return {"message": "Steps reordered successfully"}


@router.patch("/fixtures/{fixture_id}/steps/reorder")
def reorder_fixture_steps(
    fixture_id: str,
    step_orders: List[dict],  # [{"step_id": "uuid", "order": 1}, ...]
    db: Session = Depends(get_db)
):
    """Reorder steps in a fixture"""
    for item in step_orders:
        step = crud_step.get_step(db, step_id=item["step_id"])
        if step and step.fixture_id == fixture_id:
            step.order = item["order"]
    
    db.commit()
    return {"message": "Steps reordered successfully"} 