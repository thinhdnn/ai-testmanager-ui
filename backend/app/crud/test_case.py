from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
import logging

from ..models.test_case import TestCase
from ..models.fixture import Fixture
from ..models.step import Step
from ..schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseFixtureCreate, TestCaseFixtureUpdate
from ..models.test_case import test_case_fixtures

logger = logging.getLogger(__name__)


async def regenerate_test_case_script(db: Session, test_case_id: str, project_name: str = None) -> bool:
    """
    Regenerate test script file for a test case with all its steps.
    
    Args:
        db: Database session
        test_case_id: Test case ID
        project_name: Optional project name (will be inferred from test case if not provided)
        
    Returns:
        bool: True if regeneration successful, False otherwise
    """
    try:
        # Get test case from database
        test_case = get_test_case(db, test_case_id)
        if not test_case:
            logger.error(f"Test case not found: {test_case_id}")
            return False
        
        # Get project name if not provided
        if not project_name:
            from ..models.project import Project
            project = db.query(Project).filter(Project.id == test_case.project_id).first()
            if project:
                project_name = project.name
            else:
                logger.error(f"Project not found for test case: {test_case_id}")
                return False
        
        # Import here to avoid circular imports
        from ..services.playwright_test_case import generate_test_script, save_test_script
        
        # Generate test script
        result = generate_test_script(db, test_case_id, project_name)
        
        if not result.get('success'):
            logger.error(f"Failed to generate test script for test case {test_case_id}: {result.get('error')}")
            return False
        
        # Save test script to project
        save_result = save_test_script(project_name, result)
        
        if not save_result.get('success'):
            logger.error(f"Failed to save test script for test case {test_case_id}: {save_result.get('error')}")
            return False
        
        logger.info(f"Successfully regenerated test script for test case {test_case_id}: {save_result.get('file_path')}")
        return True
        
    except Exception as e:
        logger.error(f"Error regenerating test script for test case {test_case_id}: {str(e)}")
        return False


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