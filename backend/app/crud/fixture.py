from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from ..models.fixture import Fixture
from ..models.user import User
from ..schemas.fixture import FixtureCreate, FixtureUpdate
from ..services.playwright_fixture import fixture_generator

logger = logging.getLogger(__name__)


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


async def create_fixture(db: Session, fixture: FixtureCreate) -> Fixture:
    from ..models.project import Project
    from fastapi import HTTPException
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == fixture.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"Creating fixture with created_by: {fixture.created_by}")
    
    # Create database fixture first
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
    
    # Generate and save fixture file to local project
    try:
        # Generate fixture file using the template
        fixture_result = fixture_generator.generate_fixture(
            name=fixture.name,
            fixture_type=fixture.type,
            content=fixture.playwright_script or "// Add your fixture code here",
            description=f"Fixture for {project.name}"
        )
        
        if fixture_result['success']:
            # Save to local project
            save_result = fixture_generator.save_fixture_to_project(
                project_name=project.name,
                fixture_result=fixture_result
            )
            
            if save_result['success']:
                # Update database with file information
                db_fixture.filename = fixture_result['filename']
                db_fixture.export_name = fixture_result['export_name']
                db_fixture.fixture_file_path = save_result['file_path']
                
                db.commit()
                db.refresh(db_fixture)
                
                logger.info(f"Successfully created fixture file: {save_result['file_path']}")
            else:
                logger.warning(f"Failed to save fixture file: {save_result.get('error')}")
        else:
            logger.warning(f"Failed to generate fixture file: {fixture_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error creating fixture file: {str(e)}")
        # Don't fail the database creation if file generation fails
    
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


async def regenerate_fixture_with_steps(db: Session, fixture_id: str) -> bool:
    """Regenerate fixture file including all steps"""
    from ..models.project import Project
    from ..crud.step import get_steps_by_fixture
    
    # Get fixture
    fixture = get_fixture(db, fixture_id)
    if not fixture:
        return False
    
    # Get project
    project = db.query(Project).filter(Project.id == fixture.project_id).first()
    if not project:
        return False
    
    # Get steps
    steps = get_steps_by_fixture(db, fixture_id)
    
    # Convert steps to dict format for template
    steps_data = []
    for step in steps:
        steps_data.append({
            'order': step.order,
            'action': step.action,
            'playwright_script': step.playwright_script,
            'expected': step.expected,
            'data': step.data
        })
    
    # Sort steps by order
    steps_data.sort(key=lambda x: x['order'])
    
    try:
        # Generate fixture file with steps
        fixture_result = fixture_generator.generate_fixture(
            name=fixture.name,
            fixture_type=fixture.type,
            content=fixture.playwright_script or "// Add your fixture code here",
            description=f"Fixture for {project.name}",
            steps=steps_data
        )
        
        if fixture_result['success']:
            # Save to local project
            save_result = fixture_generator.save_fixture_to_project(
                project_name=project.name,
                fixture_result=fixture_result
            )
            
            if save_result['success']:
                # Update database with file information
                fixture.filename = fixture_result['filename']
                fixture.export_name = fixture_result['export_name']
                fixture.fixture_file_path = save_result['file_path']
                
                db.commit()
                db.refresh(fixture)
                
                logger.info(f"Successfully regenerated fixture file with steps: {save_result['file_path']}")
                return True
            else:
                logger.warning(f"Failed to save fixture file: {save_result.get('error')}")
        else:
            logger.warning(f"Failed to generate fixture file: {fixture_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error regenerating fixture file: {str(e)}")
    
    return False 