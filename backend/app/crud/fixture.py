from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from ..models.fixture import Fixture
from ..models.user import User
from ..schemas.fixture import FixtureCreate, FixtureUpdate


def get_fixture(db: Session, fixture_id: str) -> Optional[Fixture]:
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    
    # Get author name if fixture exists
    if fixture and fixture.created_by:
        author = db.query(User.username).filter(User.id == fixture.created_by).first()
        fixture.author_name = author[0] if author else None
    elif fixture:
        fixture.author_name = None
    
    # Get current version if fixture exists
    if fixture:
        from ..models.versioning import FixtureVersion
        latest_version = db.query(FixtureVersion).filter(
            FixtureVersion.fixture_id == fixture.id
        ).order_by(FixtureVersion.created_at.desc()).first()
        
        if latest_version:
            fixture.version = latest_version.version
        else:
            fixture.version = "1.0.0"  # Default version if no versions exist
    
    return fixture


def get_fixtures(db: Session, skip: int = 0, limit: int = 100) -> List[Fixture]:
    fixtures = (
        db.query(Fixture)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Get author names in a separate query
    for fixture in fixtures:
        if fixture.created_by:
            author = db.query(User.username).filter(User.id == fixture.created_by).first()
            fixture.author_name = author[0] if author else None
        else:
            fixture.author_name = None
    
    return fixtures


def get_fixtures_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 100) -> List[Fixture]:
    import logging
    from fastapi import HTTPException
    logger = logging.getLogger(__name__)
    
    try:
        # Convert string to UUID
        
        logger.debug("Executing database query")
        # Query fixtures first
        fixtures = (
            db.query(Fixture)
            .filter(Fixture.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        logger.debug(f"Query returned {len(fixtures)} results")
        
        # Then get author names in a separate query
        for fixture in fixtures:
            if fixture.created_by:
                author = db.query(User.username).filter(User.id == fixture.created_by).first()
                fixture.author_name = author[0] if author else None
            else:
                fixture.author_name = None
        
        logger.debug(f"Processed {len(fixtures)} fixtures")
        return fixtures
    except ValueError as e:
        logger.error(f"Invalid UUID format: {project_id}")
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid project ID format: {project_id}")
    except Exception as e:
        logger.error(f"Error getting fixtures for project {project_id}")
        logger.error(f"Error: {str(e)}")
        raise


def create_fixture(db: Session, fixture: FixtureCreate) -> Fixture:
    import logging
    logger = logging.getLogger(__name__)
    
    from ..models.project import Project
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == fixture.project_id).first()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"Creating fixture with created_by: {fixture.created_by}")
    
    db_fixture = Fixture(
        name=fixture.name,
        project_id=fixture.project_id,
        type=fixture.type,
        playwright_script=fixture.playwright_script,
        created_by=fixture.created_by
    )
    db.add(db_fixture)
    db.commit()
    db.refresh(db_fixture)
    return db_fixture


def update_fixture(db: Session, fixture_id: str, fixture: FixtureUpdate) -> Optional[Fixture]:
    db_fixture = get_fixture(db, fixture_id)
    if db_fixture:
        update_data = fixture.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_fixture, field, value)
        
        db.commit()
        db.refresh(db_fixture)
    return db_fixture


def delete_fixture(db: Session, fixture_id: str) -> bool:
    db_fixture = get_fixture(db, fixture_id)
    if db_fixture:
        db.delete(db_fixture)
        db.commit()
        return True
    return False 