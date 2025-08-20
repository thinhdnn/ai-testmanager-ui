from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
import logging
from pathlib import Path

from ..models.test_case import TestCase
from ..models.fixture import Fixture
from ..models.step import Step
from ..schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseFixtureCreate, TestCaseFixtureUpdate
from ..models.test_case import test_case_fixtures

logger = logging.getLogger(__name__)


def _read_test_case_file_content(test_file_path: str) -> Optional[str]:
    """
    Read test case file content from filesystem
    
    Args:
        test_file_path: Path to test case file (can be absolute or relative)
        
    Returns:
        File content as string, or None if file not found/readable
    """
    try:
        if not test_file_path:
            return None
            
        file_path = Path(test_file_path)
        
        # If it's a relative path, make it absolute by joining with project root
        if not file_path.is_absolute():
            # Get project root (assuming we're in backend/app/crud)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up to project root
            playwright_projects_dir = project_root / "playwright_projects"
            
            # Try to find the file in playwright_projects directory
            # test_file_path might be like "tests/loginTest.spec.ts"
            for project_dir in playwright_projects_dir.glob("*"):
                if project_dir.is_dir():
                    potential_file = project_dir / test_file_path
                    if potential_file.exists():
                        file_path = potential_file
                        break
            else:
                # If not found in any project, try as relative to project root
                file_path = project_root / test_file_path
        
        # Read file content
        if file_path.exists() and file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Successfully read test case file content: {file_path}")
            return content
        else:
            logger.warning(f"Test case file not found: {file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error reading test case file {test_file_path}: {str(e)}")
        return None


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
        
        # Read the generated file content and save to playwright_script
        file_content = _read_test_case_file_content(save_result.get('file_path'))
        if file_content and test_case:
            test_case.playwright_script = file_content
            logger.info(f"Successfully read and saved test case file content to database")
        else:
            logger.warning(f"Could not read test case file content from: {save_result.get('file_path')}")
        
        # Commit the updated test_file_path if it was updated
        if save_result.get('renamed') and test_case:
            try:
                db.commit()
                logger.info(f"Updated test case {test_case_id} with new file path: {save_result.get('file_path')}")
            except Exception as e:
                logger.warning(f"Failed to commit test case file path update: {str(e)}")
        
        logger.info(f"Successfully regenerated test script for test case {test_case_id}: {save_result.get('file_path')}")
        return True
        
    except Exception as e:
        logger.error(f"Error regenerating test script for test case {test_case_id}: {str(e)}")
        return False


async def create_test_case(db: Session, test_case: TestCaseCreate, created_by: str = None) -> TestCase:
    test_case_data = test_case.model_dump()
    if created_by:
        test_case_data['created_by'] = created_by
    db_test_case = TestCase(**test_case_data)
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    
    # Generate test case file and read content
    try:
        # Get project name
        from ..models.project import Project
        project = db.query(Project).filter(Project.id == db_test_case.project_id).first()
        if project:
            project_name = project.name
            
            # Import here to avoid circular imports
            from ..services.playwright_test_case import test_case_generator
            
            # Generate test case file
            test_result = test_case_generator.generate_test_case(
                db=db,
                test_case_id=str(db_test_case.id),
                project_name=project_name
            )
            
            if test_result.get('success'):
                # Save test case file to project
                save_result = test_case_generator.save_test_case_to_project(
                    project_name=project_name,
                    test_result=test_result,
                    test_case_db=db_test_case
                )
                
                if save_result.get('success'):
                    # Read the generated file content and save to playwright_script
                    file_content = _read_test_case_file_content(save_result.get('file_path'))
                    if file_content:
                        db_test_case.playwright_script = file_content
                        logger.info(f"Successfully read and saved test case file content to database")
                    else:
                        logger.warning(f"Could not read test case file content from: {save_result.get('file_path')}")
                    
                    db.commit()
                    db.refresh(db_test_case)
                    
                    logger.info(f"Successfully created test case file: {save_result.get('file_path')}")
                else:
                    logger.warning(f"Failed to save test case file: {save_result.get('error')}")
            else:
                logger.warning(f"Failed to generate test case file: {test_result.get('error')}")
        else:
            logger.warning(f"Project not found for test case: {db_test_case.id}")
            
    except Exception as e:
        logger.error(f"Error creating test case file: {str(e)}")
        # Don't fail the database creation if file generation fails
    
    return db_test_case


def get_test_case(db: Session, test_case_id: str) -> Optional[TestCase]:
    return db.query(TestCase).filter(TestCase.id == test_case_id).first()


def get_test_cases(db: Session, skip: int = 0, limit: int = 100) -> List[TestCase]:
    return db.query(TestCase).offset(skip).limit(limit).all()


def get_test_cases_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 100) -> List[TestCase]:
    return db.query(TestCase).filter(TestCase.project_id == project_id).offset(skip).limit(limit).all()


def get_test_cases_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[TestCase]:
    return db.query(TestCase).filter(TestCase.status == status).offset(skip).limit(limit).all()


async def update_test_case(db: Session, test_case_id: str, test_case: TestCaseUpdate, updated_by: str = None) -> Optional[TestCase]:
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        update_data = test_case.dict(exclude_unset=True)
        
        # Add updated_by if provided
        if updated_by:
            update_data['updated_by'] = updated_by
        
        # Check if we need to regenerate test file (if certain fields changed)
        should_regenerate = any(field in update_data for field in ['name', 'description', 'playwright_script', 'is_manual'])
        
        for field, value in update_data.items():
            setattr(db_test_case, field, value)
        
        # Regenerate test case file if needed
        if should_regenerate:
            try:
                # Get project name
                from ..models.project import Project
                project = db.query(Project).filter(Project.id == db_test_case.project_id).first()
                if project:
                    project_name = project.name
                    
                    # Import here to avoid circular imports
                    from ..services.playwright_test_case import test_case_generator
                    
                    # Generate test case file
                    test_result = test_case_generator.generate_test_case(
                        db=db,
                        test_case_id=str(db_test_case.id),
                        project_name=project_name
                    )
                    
                    if test_result.get('success'):
                        # Save test case file to project
                        save_result = test_case_generator.save_test_case_to_project(
                            project_name=project_name,
                            test_result=test_result,
                            test_case_db=db_test_case
                        )
                        
                        if save_result.get('success'):
                            # Read the updated file content and save to playwright_script
                            file_content = _read_test_case_file_content(save_result.get('file_path'))
                            if file_content:
                                db_test_case.playwright_script = file_content
                                logger.info(f"Successfully read and updated test case file content in database")
                            else:
                                logger.warning(f"Could not read updated test case file content from: {save_result.get('file_path')}")
                            
                            logger.info(f"Successfully updated test case file: {save_result.get('file_path')}")
                        else:
                            logger.warning(f"Failed to save updated test case file: {save_result.get('error')}")
                    else:
                        logger.warning(f"Failed to generate updated test case file: {test_result.get('error')}")
                else:
                    logger.warning(f"Project not found for test case: {test_case_id}")
                    
            except Exception as e:
                logger.error(f"Error updating test case file: {str(e)}")
                # Don't fail the database update if file generation fails
        
        db.commit()
        db.refresh(db_test_case)
    return db_test_case


def update_test_case_status(db: Session, test_case_id: str, status: str, last_run_by: str = None) -> Optional[TestCase]:
    """Update test case status and last_run_by fields"""
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        db_test_case.status = status
        if last_run_by:
            db_test_case.last_run_by = last_run_by
        db.commit()
        db.refresh(db_test_case)
        return db_test_case
    return None


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