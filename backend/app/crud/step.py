from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.step import Step
from ..schemas.step import StepCreate, StepUpdate


def get_step(db: Session, step_id: str) -> Optional[Step]:
    return db.query(Step).filter(Step.id == step_id).first()


def get_steps(db: Session, skip: int = 0, limit: int = 100) -> List[Step]:
    return db.query(Step).offset(skip).limit(limit).all()


def get_steps_by_test_case(db: Session, test_case_id: str) -> List[Step]:
    steps = db.query(Step).filter(
        Step.test_case_id == test_case_id
    ).order_by(Step.order).all()
    
    # Add referenced fixture names
    for step in steps:
        if step.referenced_fixture_id:
            from ..models.fixture import Fixture
            fixture = db.query(Fixture.name).filter(Fixture.id == step.referenced_fixture_id).first()
            step.referenced_fixture_name = fixture[0] if fixture else "Unknown Fixture"
    
    return steps


def get_steps_by_fixture(db: Session, fixture_id: str) -> List[Step]:
    steps = db.query(Step).filter(
        Step.fixture_id == fixture_id
    ).order_by(Step.order).all()
    
    # Add referenced fixture names
    for step in steps:
        if step.referenced_fixture_id:
            from ..models.fixture import Fixture
            fixture = db.query(Fixture.name).filter(Fixture.id == step.referenced_fixture_id).first()
            step.referenced_fixture_name = fixture[0] if fixture else "Unknown Fixture"
    
    return steps


def create_step(db: Session, step: StepCreate) -> Step:
    # Validate fixture call rules
    if step.referenced_fixture_id:
        from ..models.fixture import Fixture
        fixture = db.query(Fixture).filter(Fixture.id == step.referenced_fixture_id).first()
        if not fixture:
            raise ValueError(f"Fixture with id {step.referenced_fixture_id} not found")
        
        # Check fixture type and order validation
        if fixture.type == "extend" and step.order != 1:
            raise ValueError("Extend fixtures can only be called at step 1 (order = 1)")
        elif fixture.type == "inline" and step.order == 1:
            raise ValueError("Inline fixtures cannot be called at step 1 (order = 1)")
    
    # Auto-set action to fixture name if referenced_fixture_id is provided and action is empty
    action = step.action
    if step.referenced_fixture_id and not action:
        from ..models.fixture import Fixture
        fixture = db.query(Fixture.name).filter(Fixture.id == step.referenced_fixture_id).first()
        action = fixture[0] if fixture else "Unknown Fixture"
    
    db_step = Step(
        test_case_id=step.test_case_id,
        fixture_id=step.fixture_id,
        action=action,
        data=step.data,
        expected=step.expected,
        playwright_script=step.playwright_script,
        order=step.order,
        disabled=step.disabled,
        referenced_fixture_id=step.referenced_fixture_id,
        created_by=step.created_by
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


def update_step(db: Session, step_id: str, step: StepUpdate) -> Optional[Step]:
    db_step = get_step(db, step_id)
    if db_step:
        # Validate fixture call rules if referenced_fixture_id is being updated
        if step.referenced_fixture_id is not None:
            from ..models.fixture import Fixture
            fixture = db.query(Fixture).filter(Fixture.id == step.referenced_fixture_id).first()
            if not fixture:
                raise ValueError(f"Fixture with id {step.referenced_fixture_id} not found")
            
            # Check fixture type and order validation
            order = step.order if step.order is not None else db_step.order
            if fixture.type == "extend" and order != 1:
                raise ValueError("Extend fixtures can only be called at step 1 (order = 1)")
            elif fixture.type == "inline" and order == 1:
                raise ValueError("Inline fixtures cannot be called at step 1 (order = 1)")
        
        update_data = step.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_step, field, value)
        
        db.commit()
        db.refresh(db_step)
    return db_step


def delete_step(db: Session, step_id: str) -> bool:
    db_step = get_step(db, step_id)
    if db_step:
        db.delete(db_step)
        db.commit()
        return True
    return False


def get_max_order_for_test_case(db: Session, test_case_id: str) -> int:
    """Get the maximum order value for steps in a test case"""
    result = db.query(Step.order).filter(
        Step.test_case_id == test_case_id
    ).order_by(Step.order.desc()).first()
    return result[0] if result else 0


def get_max_order_for_fixture(db: Session, fixture_id: str) -> int:
    """Get the maximum order value for steps in a fixture"""
    result = db.query(Step.order).filter(
        Step.fixture_id == fixture_id
    ).order_by(Step.order.desc()).first()
    return result[0] if result else 0 