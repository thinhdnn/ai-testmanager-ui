from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...schemas.step import Step, StepCreate, StepUpdate, StepReorder
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
    reorder_data: StepReorder,
    db: Session = Depends(get_db)
):
    """Reorder a single step in a test case"""
    step_id = reorder_data.step_id
    new_order = reorder_data.new_order
    
    # Get the step to move
    step_to_move = crud_step.get_step(db, step_id=step_id)
    if not step_to_move or str(step_to_move.test_case_id) != test_case_id:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Get all steps for this test case, sorted by current order
    all_steps = crud_step.get_steps_by_test_case(db, test_case_id=test_case_id)
    all_steps.sort(key=lambda x: x.order)
    
    # Validate new_order
    if new_order < 1 or new_order > len(all_steps):
        raise HTTPException(status_code=400, detail=f"new_order must be between 1 and {len(all_steps)}")
    
    # Check if step is already at target position
    if step_to_move.order == new_order:
        return {"message": "Step is already at target position"}
    
    # Remove the step from current position
    current_order = step_to_move.order
    
    # Shift other steps accordingly
    if new_order > current_order:
        # Moving down: shift steps between current and target up
        for step in all_steps:
            if step.id != step_id and current_order < step.order <= new_order:
                step.order -= 1
    else:
        # Moving up: shift steps between target and current down
        for step in all_steps:
            if step.id != step_id and new_order <= step.order < current_order:
                step.order += 1
    
    # Set the target step to new order
    step_to_move.order = new_order
    
    db.commit()
    return {"message": "Step reordered successfully"}


@router.patch("/test-cases/{test_case_id}/steps/auto-reorder")
def auto_reorder_test_case_steps(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Auto reorder all steps in a test case from 1 to n"""
    # Get all steps for this test case, sorted by current order
    steps = crud_step.get_steps_by_test_case(db, test_case_id=test_case_id)
    steps.sort(key=lambda x: x.order)
    
    # Reorder from 1 to n
    for index, step in enumerate(steps, 1):
        step.order = index
    
    db.commit()
    return {"message": f"Steps auto-reordered successfully. Total steps: {len(steps)}"}


@router.patch("/fixtures/{fixture_id}/steps/reorder")
def reorder_fixture_steps(
    fixture_id: str,
    reorder_data: StepReorder,
    db: Session = Depends(get_db)
):
    """Reorder a single step in a fixture"""
    step_id = reorder_data.step_id
    new_order = reorder_data.new_order
    
    # Get the step to move
    step_to_move = crud_step.get_step(db, step_id=step_id)
    if not step_to_move or str(step_to_move.fixture_id) != fixture_id:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Get all steps for this fixture, sorted by current order
    all_steps = crud_step.get_steps_by_fixture(db, fixture_id=fixture_id)
    all_steps.sort(key=lambda x: x.order)
    
    # Validate new_order
    if new_order < 1 or new_order > len(all_steps):
        raise HTTPException(status_code=400, detail=f"new_order must be between 1 and {len(all_steps)}")
    
    # Check if step is already at target position
    if step_to_move.order == new_order:
        return {"message": "Step is already at target position"}
    
    # Remove the step from current position
    current_order = step_to_move.order
    
    # Shift other steps accordingly
    if new_order > current_order:
        # Moving down: shift steps between current and target up
        for step in all_steps:
            if step.id != step_id and current_order < step.order <= new_order:
                step.order -= 1
    else:
        # Moving up: shift steps between target and current down
        for step in all_steps:
            if step.id != step_id and new_order <= step.order < current_order:
                step.order += 1
    
    # Set the target step to new order
    step_to_move.order = new_order
    
    db.commit()
    return {"message": "Step reordered successfully"} 