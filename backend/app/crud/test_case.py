from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException

from ..models.test_case import TestCase
from ..models.user import User
from ..schemas.test_case import TestCaseCreate, TestCaseUpdate


def get_test_case(db: Session, test_case_id: str) -> Optional[TestCase]:
    return db.query(TestCase).filter(TestCase.id == test_case_id).first()


def get_test_cases(db: Session, skip: int = 0, limit: int = 100) -> List[TestCase]:
    results = (
        db.query(TestCase, User.username.label('author_name'))
        .outerjoin(User, User.id == TestCase.created_by)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    test_cases = []
    for test_case, author_name in results:
        test_case.author_name = author_name
        test_cases.append(test_case)
    
    return test_cases


def get_test_cases_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 100) -> List[TestCase]:
    from uuid import UUID
    import logging
    from fastapi import HTTPException
    logger = logging.getLogger(__name__)
    
    try:
        # Convert string to UUID
        logger.debug(f"Converting project_id string to UUID: {project_id}")
        project_uuid = UUID(project_id)
        logger.debug(f"Converted to UUID: {project_uuid}")
        
        logger.debug("Executing database query")
        # Query test cases first
        test_cases = (
            db.query(TestCase)
            .filter(TestCase.project_id == project_uuid)
            .offset(skip)
            .limit(limit)
            .all()
        )
        logger.debug(f"Query returned {len(test_cases)} results")
        
        # Then get author names in a separate query
        for test_case in test_cases:
            if test_case.created_by:
                author = db.query(User.username).filter(User.id == test_case.created_by).first()
                test_case.author_name = author[0] if author else None
            else:
                test_case.author_name = None
        
        logger.debug(f"Processed {len(test_cases)} test cases")
        return test_cases
    except ValueError as e:
        logger.error(f"Invalid UUID format: {project_id}")
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid project ID format: {project_id}")
    except Exception as e:
        logger.error(f"Error getting test cases for project {project_id}")
        logger.error(f"Error: {str(e)}")
        raise


def get_test_cases_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[TestCase]:
    results = (
        db.query(TestCase, User.username.label('author_name'))
        .outerjoin(User, User.id == TestCase.created_by)
        .filter(TestCase.status == status)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    test_cases = []
    for test_case, author_name in results:
        test_case.author_name = author_name
        test_cases.append(test_case)
    
    return test_cases


def create_test_case(db: Session, test_case: TestCaseCreate) -> TestCase:
    db_test_case = TestCase(
        name=test_case.name,
        project_id=test_case.project_id,
        order=test_case.order,
        status=test_case.status,
        version=test_case.version,
        is_manual=test_case.is_manual,
        tags=test_case.tags,
        test_file_path=test_case.test_file_path,
        playwright_script=test_case.playwright_script,
        created_by=test_case.created_by
    )
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


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


def update_test_case_status(db: Session, test_case_id: str, status: str, last_run_by: Optional[str] = None) -> Optional[TestCase]:
    """Update test case status and last run info"""
    db_test_case = get_test_case(db, test_case_id)
    if db_test_case:
        db_test_case.status = status
        if last_run_by:
            db_test_case.last_run_by = last_run_by
            from datetime import datetime
            db_test_case.last_run = datetime.utcnow()
        
        db.commit()
        db.refresh(db_test_case)
    return db_test_case 