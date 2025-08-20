from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...schemas.step import Step, StepCreate, StepUpdate, StepReorder
from ...crud import step as crud_step
from ...models.versioning import StepVersion
from ...models.user import User
from ...auth import current_active_user

router = APIRouter()


def _create_version(db: Session, step, version: str = None):
    """Helper function to create a version of step"""
    # For now, we'll skip step versioning as it's more complex
    # Step versions are managed through test case and fixture versions
    pass


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
async def create_test_case_step(
    test_case_id: str,
    step: StepCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create new step for a test case"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== CREATE TEST CASE STEP DEBUG START ===")
    logger.info(f"Creating test case step:")
    logger.info(f"  - test_case_id: {test_case_id}")
    logger.info(f"  - step.referenced_fixture_id: {step.referenced_fixture_id}")
    logger.info(f"  - step.action: {step.action}")
    logger.info(f"  - current_user.id: {current_user.id}")
    
    # Override test_case_id from URL and set created_by
    step_data = step.model_dump()
    step_data['test_case_id'] = test_case_id
    step_data['created_by'] = str(current_user.id)
    # Allow referenced_fixture_id to be set - test cases can have steps that reference fixtures
    
    logger.info(f"Modified step data:")
    logger.info(f"  - test_case_id: {step_data['test_case_id']}")
    logger.info(f"  - referenced_fixture_id: {step_data['referenced_fixture_id']}")
    logger.info(f"  - created_by: {step_data['created_by']}")
    
    new_step = StepCreate(**step_data)
    created_step = crud_step.create_step(db, new_step)
    
    logger.info(f"Step created successfully:")
    logger.info(f"  - step.id: {created_step.id}")
    logger.info(f"  - step.test_case_id: {created_step.test_case_id}")
    logger.info(f"  - step.referenced_fixture_id: {created_step.referenced_fixture_id}")
    
    # Auto-regenerate test case file with new step
    from ...crud.test_case import regenerate_test_case_script
    try:
        logger.info("Starting test case file regeneration...")
        await regenerate_test_case_script(db, str(created_step.test_case_id))
        logger.info("Test case file regeneration completed")
    except Exception as e:
        # Log error but don't fail the step creation
        logger.warning(f"Failed to regenerate test case file after adding step: {str(e)}")
    
    logger.info(f"=== CREATE TEST CASE STEP DEBUG END ===")
    return created_step


# ============ NESTED ROUTES FOR FIXTURES ============

@router.get("/fixtures/{fixture_id}/steps", response_model=List[Step])
def get_fixture_steps(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get all steps that reference a fixture"""
    steps = crud_step.get_steps_by_fixture(db, fixture_id=fixture_id)
    return steps


@router.post("/fixtures/{fixture_id}/steps", response_model=Step, status_code=status.HTTP_201_CREATED)
async def create_fixture_step(
    fixture_id: str,
    step: StepCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create new step that references a fixture"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.warning(f"=== CREATE FIXTURE STEP CALLED (UNEXPECTED?) ===")
    logger.warning(f"Creating fixture step:")
    logger.warning(f"  - fixture_id: {fixture_id}")
    logger.warning(f"  - step.test_case_id: {step.test_case_id}")
    logger.warning(f"  - step.action: {step.action}")
    logger.warning(f"  - current_user.id: {current_user.id}")
    
    # Override referenced_fixture_id from URL and set created_by
    step_data = step.model_dump()
    step_data['referenced_fixture_id'] = fixture_id
    step_data['test_case_id'] = None  # Ensure it's not for test case
    step_data['created_by'] = str(current_user.id)
    
    logger.warning(f"Modified step data:")
    logger.warning(f"  - test_case_id: {step_data['test_case_id']}")
    logger.warning(f"  - referenced_fixture_id: {step_data['referenced_fixture_id']}")
    logger.warning(f"  - created_by: {step_data['created_by']}")
    
    new_step = StepCreate(**step_data)
    created_step = crud_step.create_step(db, new_step)
    
    logger.warning(f"Fixture step created successfully:")
    logger.warning(f"  - step.id: {created_step.id}")
    logger.warning(f"  - step.test_case_id: {created_step.test_case_id}")
    logger.warning(f"  - step.referenced_fixture_id: {created_step.referenced_fixture_id}")
    
    # Auto-regenerate fixture file with new step
    from ...crud.fixture import regenerate_fixture_with_steps
    try:
        logger.warning("Starting fixture file regeneration...")
        await regenerate_fixture_with_steps(db, fixture_id)
        logger.warning("Fixture file regeneration completed")
    except Exception as e:
        # Log error but don't fail the step creation
        logger.warning(f"Failed to regenerate fixture file after adding step: {str(e)}")
    
    logger.warning(f"=== CREATE FIXTURE STEP DEBUG END ===")
    return created_step


# ============ BASIC STEP CRUD ============

@router.post("/", response_model=Step, status_code=status.HTTP_201_CREATED)
def create_step(
    step: StepCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create new step"""
    try:
        # Set created_by from current user
        step_data = step.model_dump()
        step_data['created_by'] = str(current_user.id)
        step_with_user = StepCreate(**step_data)
        
        # Create step
        db_step = crud_step.create_step(db=db, step=step_with_user)
        return db_step
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
async def update_step(
    step_id: str,
    step: StepUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing step"""
    updated_step = crud_step.update_step(db, step_id=step_id, step=step)
    if not updated_step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Auto-regenerate fixture file if step belongs to a fixture
    if updated_step.referenced_fixture_id:
        from ...crud.fixture import regenerate_fixture_with_steps
        try:
            await regenerate_fixture_with_steps(db, str(updated_step.referenced_fixture_id))
        except Exception as e:
            # Log error but don't fail the step update
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to regenerate fixture file after updating step: {str(e)}")
    
    # Auto-regenerate test case file if step belongs to a test case
    if updated_step.test_case_id:
        from ...crud.test_case import regenerate_test_case_script
        try:
            await regenerate_test_case_script(db, str(updated_step.test_case_id))
        except Exception as e:
            # Log error but don't fail the step update
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to regenerate test case file after updating step: {str(e)}")
    
    return updated_step


@router.delete("/{step_id}")
async def delete_step(
    step_id: str,
    db: Session = Depends(get_db)
):
    """Delete a step"""
    db_step = crud_step.get_step(db, step_id=step_id)
    if not db_step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Store fixture_id and test_case_id before deletion for regeneration
    fixture_id = db_step.referenced_fixture_id
    test_case_id = db_step.test_case_id
    
    # Delete the step
    success = crud_step.delete_step(db, step_id=step_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete step")
    
    # Auto-regenerate fixture file if step belonged to a fixture
    if fixture_id:
        from ...crud.fixture import regenerate_fixture_with_steps
        try:
            await regenerate_fixture_with_steps(db, str(fixture_id))
        except Exception as e:
            # Log error but don't fail the step deletion
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to regenerate fixture file after deleting step: {str(e)}")
    
    # Auto-regenerate test case file if step belonged to a test case
    if test_case_id:
        from ...crud.test_case import regenerate_test_case_script
        try:
            await regenerate_test_case_script(db, str(test_case_id))
        except Exception as e:
            # Log error but don't fail the step deletion
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to regenerate test case file after deleting step: {str(e)}")
    
    return {"message": "Step deleted successfully"}


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
    if not step_to_move or str(step_to_move.referenced_fixture_id) != fixture_id:
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


@router.patch("/fixtures/{fixture_id}/steps/auto-reorder")
def auto_reorder_fixture_steps(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Auto reorder all steps in a fixture from 1 to n"""
    # Get all steps for this fixture, sorted by current order
    steps = crud_step.get_steps_by_fixture(db, fixture_id=fixture_id)
    steps.sort(key=lambda x: x.order)
    
    # Reorder from 1 to n
    for index, step in enumerate(steps, 1):
        step.order = index
    
    db.commit()
    return {"message": f"Steps auto-reordered successfully. Total steps: {len(steps)}"} 