from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID

from ..models.test_case import TestCase
from ..models.fixture import Fixture
from ..models.step import Step
from ..schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseFixtureCreate, TestCaseFixtureUpdate
from ..models.test_case import test_case_fixtures


def create_test_case(db: Session, test_case: TestCaseCreate) -> TestCase:
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


def get_test_case(db: Session, test_case_id: str) -> Optional[TestCase]:
    return db.query(TestCase).filter(TestCase.id == test_case_id).first()


def get_test_cases(db: Session, skip: int = 0, limit: int = 100) -> List[TestCase]:
    return db.query(TestCase).offset(skip).limit(limit).all()


def get_test_cases_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 100) -> List[TestCase]:
    return db.query(TestCase).filter(TestCase.project_id == project_id).offset(skip).limit(limit).all()


def get_test_cases_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[TestCase]:
    return db.query(TestCase).filter(TestCase.status == status).offset(skip).limit(limit).all()


def update_test_case(db: Session, test_case_id: str, test_case: TestCaseUpdate) -> Optional[TestCase]:
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        update_data = test_case.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_test_case, field, value)
        db.commit()
        db.refresh(db_test_case)
    return db_test_case


def delete_test_case(db: Session, test_case_id: str) -> bool:
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        db.delete(db_test_case)
        db.commit()
        return True
    return False


# Test Case Fixture CRUD operations
def add_fixture_to_test_case(db: Session, test_case_id: str, fixture_data: TestCaseFixtureCreate, created_by: str = None) -> dict:
    """Add a fixture to a test case"""
    # Check if test case exists
    test_case = get_test_case(db, test_case_id)
    if not test_case:
        raise ValueError("Test case not found")
    
    # Check if fixture exists
    fixture = db.query(Fixture).filter(Fixture.id == fixture_data.fixture_id).first()
    if not fixture:
        raise ValueError("Fixture not found")
    
    # Check if fixture is already associated with test case
    existing = db.query(test_case_fixtures).filter(
        and_(
            test_case_fixtures.c.test_case_id == test_case_id,
            test_case_fixtures.c.fixture_id == fixture_data.fixture_id
        )
    ).first()
    
    if existing:
        raise ValueError("Fixture is already associated with this test case")
    
    # Get max order for this test case
    max_order = db.query(test_case_fixtures.c.order).filter(
        test_case_fixtures.c.test_case_id == test_case_id
    ).order_by(test_case_fixtures.c.order.desc()).first()
    
    order = (max_order[0] if max_order else 0) + 1
    
    # Insert the association
    db.execute(
        test_case_fixtures.insert().values(
            test_case_id=test_case_id,
            fixture_id=fixture_data.fixture_id,
            order=order,
            created_by=created_by
        )
    )
    db.commit()
    
    return {
        "test_case_id": test_case_id,
        "fixture_id": str(fixture_data.fixture_id),
        "order": order
    }


def remove_fixture_from_test_case(db: Session, test_case_id: str, fixture_id: str) -> bool:
    """Remove a fixture from a test case"""
    result = db.execute(
        test_case_fixtures.delete().where(
            and_(
                test_case_fixtures.c.test_case_id == test_case_id,
                test_case_fixtures.c.fixture_id == fixture_id
            )
        )
    )
    db.commit()
    return result.rowcount > 0


def get_test_case_fixtures(db: Session, test_case_id: str) -> List[dict]:
    """Get all fixtures associated with a test case"""
    fixtures = db.query(
        test_case_fixtures.c.fixture_id,
        test_case_fixtures.c.order,
        test_case_fixtures.c.created_at,
        test_case_fixtures.c.created_by,
        Fixture.name,
        Fixture.type,
        Fixture.playwright_script
    ).join(
        Fixture, test_case_fixtures.c.fixture_id == Fixture.id
    ).filter(
        test_case_fixtures.c.test_case_id == test_case_id
    ).order_by(test_case_fixtures.c.order).all()
    
    return [
        {
            "fixture_id": str(fixture.fixture_id),
            "order": fixture.order,
            "created_at": fixture.created_at,
            "created_by": fixture.created_by,
            "name": fixture.name,
            "type": fixture.type,
            "playwright_script": fixture.playwright_script
        }
        for fixture in fixtures
    ]


def update_test_case_fixture_order(db: Session, test_case_id: str, fixture_id: str, new_order: int) -> bool:
    """Update the order of a fixture in a test case"""
    result = db.execute(
        test_case_fixtures.update().where(
            and_(
                test_case_fixtures.c.test_case_id == test_case_id,
                test_case_fixtures.c.fixture_id == fixture_id
            )
        ).values(order=new_order)
    )
    db.commit()
    return result.rowcount > 0


def reorder_test_case_fixtures(db: Session, test_case_id: str, fixture_orders: List[dict]) -> bool:
    """Reorder all fixtures for a test case"""
    for fixture_order in fixture_orders:
        db.execute(
            test_case_fixtures.update().where(
                and_(
                    test_case_fixtures.c.test_case_id == test_case_id,
                    test_case_fixtures.c.fixture_id == fixture_order["fixture_id"]
                )
            ).values(order=fixture_order["order"])
        )
    db.commit()
    return True 