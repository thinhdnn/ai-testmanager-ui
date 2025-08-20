from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID
import asyncio
import logging

from ..models.project import Project
from ..models.test_case import TestCase
from ..models.fixture import Fixture
from ..schemas.project import ProjectCreate, ProjectUpdate
from ..services.playwright_project import (
    create_project as create_playwright_project,
    playwright_manager
)

logger = logging.getLogger(__name__)


async def _create_default_project_settings(db: Session, project_id: str, base_url: str = None, created_by: str = None):
    """Create default project settings for Playwright configuration"""
    from ..models.project_setting import ProjectSetting
    
    # Default Playwright configuration settings
    default_settings = {
        # Base configuration
        'BASE_URL': base_url or 'https://example.com',
        'TIMEOUT': '30000',
        'EXPECT_TIMEOUT': '10000',
        'RETRIES': '1',
        'WORKERS': '1',
        
        # Viewport settings
        'VIEWPORT_WIDTH': '1920',
        'VIEWPORT_HEIGHT': '1080',
        
        # Test execution settings
        'FULLY_PARALLEL': 'true',
        'HEADLESS_MODE': 'true',
        
        # Media settings
        'SCREENSHOT': 'off',
        'VIDEO': 'off',
    }
    
    # Create settings in database
    for key, value in default_settings.items():
        setting = ProjectSetting(
            project_id=project_id,
            key=key,
            value=value,
            created_by=created_by
        )
        db.add(setting)
    
    db.commit()
    logger.info(f"Created default project settings for project {project_id}")


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    return db.query(Project).offset(skip).limit(limit).all()


def get_projects_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
    # For now, return all projects. Later add permission filtering
    return db.query(Project).offset(skip).limit(limit).all()


async def create_project(db: Session, project: ProjectCreate, created_by: str) -> Project:
    # Create database project first
    db_project = Project(
        name=project.name,
        description=project.description,
        environment=project.environment,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Create default project settings including base_url and Playwright config
    await _create_default_project_settings(db, str(db_project.id), project.base_url, created_by)
    
    # Create local Playwright project asynchronously
    try:
        # Use project name as folder name (will be cleaned automatically)
        success, cleaned_name, error = await create_playwright_project(
            project.name, 
            force_recreate=False
        )
        
        if success:
            logger.info(f"Successfully created Playwright project '{cleaned_name}' for database project '{db_project.name}' (ID: {db_project.id})")
            
            # Store ONLY the project folder name (cleaned_name) in the database
            # Resolution to full path will be handled by the Playwright project manager
            db_project.playwright_project_path = cleaned_name
            db.commit()
            logger.info(f"Set playwright_project_path (folder name): {cleaned_name}")
            
            # Build and replace playwright.config.ts with project settings using playwright_project service
            from ..services.playwright_project import playwright_manager
            config_success = await playwright_manager.build_playwright_config(db, str(db_project.id), cleaned_name)
            if not config_success:
                logger.warning(f"Failed to build playwright config for project '{cleaned_name}'")
        else:
            logger.warning(f"Failed to create Playwright project for '{db_project.name}': {error}")
            # Don't fail the database project creation if Playwright project fails
            
    except Exception as e:
        logger.error(f"Exception while creating Playwright project for '{db_project.name}': {str(e)}")
        # Don't fail the database project creation if Playwright project fails
    
    return db_project


def update_project(db: Session, project_id: UUID, project: ProjectUpdate, updated_by: str = None) -> Optional[Project]:
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    if updated_by:
        db_project.updated_by = updated_by
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: UUID) -> bool:
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    # Store project name before deletion for Playwright cleanup
    project_name = db_project.name
    
    # Delete from database first
    db.delete(db_project)
    db.commit()
    
    # Clean up Playwright project
    try:
        success, message = playwright_manager.delete_project(project_name)
        if success:
            logger.info(f"Successfully deleted Playwright project for '{project_name}'")
        else:
            logger.warning(f"Failed to delete Playwright project for '{project_name}': {message}")
    except Exception as e:
        logger.error(f"Exception while deleting Playwright project for '{project_name}': {str(e)}")
    
    return True


def get_project_stats(db: Session, project_id: UUID) -> dict:
    # Get counts
    test_cases_count = db.query(func.count(TestCase.id)).filter(TestCase.project_id == project_id).scalar()
    fixtures_count = db.query(func.count(Fixture.id)).filter(Fixture.project_id == project_id).scalar()
    
    return {
        "test_cases_count": test_cases_count,
        "fixtures_count": fixtures_count
    } 