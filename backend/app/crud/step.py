from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.step import Step
from ..schemas.step import StepCreate, StepUpdate


def get_step(db: Session, step_id: str) -> Optional[Step]:
    return db.query(Step).filter(Step.id == step_id).first()


def get_steps(db: Session, skip: int = 0, limit: int = 100) -> List[Step]:
    return db.query(Step).offset(skip).limit(limit).all()


def get_steps_by_test_case(db: Session, test_case_id: str) -> List[Step]:
    return db.query(Step).filter(
        Step.test_case_id == test_case_id
    ).order_by(Step.order).all()


def get_steps_by_fixture(db: Session, fixture_id: str) -> List[Step]:
    return db.query(Step).filter(
        Step.fixture_id == fixture_id
    ).order_by(Step.order).all()


def create_step(db: Session, step: StepCreate) -> Step:
    db_step = Step(
        test_case_id=step.test_case_id,
        fixture_id=step.fixture_id,
        action=step.action,
        data=step.data,
        expected=step.expected,
        playwright_script=step.playwright_script,
        order=step.order,
        disabled=step.disabled,
        created_by=step.created_by
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


def update_step(db: Session, step_id: str, step: StepUpdate) -> Optional[Step]:
    db_step = get_step(db, step_id)
    if db_step:
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