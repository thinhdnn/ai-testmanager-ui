from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from pathlib import Path

from ..models.fixture import Fixture
from ..models.user import User
from ..schemas.fixture import FixtureCreate, FixtureUpdate
from ..services.playwright_fixture import fixture_generator

logger = logging.getLogger(__name__)


def _read_fixture_file_content(fixture_file_path: str) -> Optional[str]:
    """
    Read fixture file content from filesystem
    
    Args:
        fixture_file_path: Path to fixture file (can be absolute or relative)
        
    Returns:
        File content as string, or None if file not found/readable
    """
    try:
        if not fixture_file_path:
            return None
            
        file_path = Path(fixture_file_path)
        
        # If it's a relative path, make it absolute by joining with project root
        if not file_path.is_absolute():
            # Get project root (assuming we're in backend/app/crud)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up to project root
            playwright_projects_dir = project_root / "playwright_projects"
            
            # Try to find the file in playwright_projects directory
            # fixture_file_path might be like "fixtures/loginAsAdmin.fixture.ts"
            for project_dir in playwright_projects_dir.glob("*"):
                if project_dir.is_dir():
                    potential_file = project_dir / fixture_file_path
                    if potential_file.exists():
                        file_path = potential_file
                        break
            else:
                # If not found in any project, try as relative to project root
                file_path = project_root / fixture_file_path
        
        # Read file content
        if file_path.exists() and file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Successfully read fixture file content: {file_path}")
            return content
        else:
            logger.warning(f"Fixture file not found: {file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error reading fixture file {fixture_file_path}: {str(e)}")
        return None


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
    
    # Set default values for fields that may not exist in the database
    if fixture:
        if not hasattr(fixture, 'status') or fixture.status is None:
            fixture.status = "draft"
        if not hasattr(fixture, 'environment') or fixture.environment is None:
            fixture.environment = "all"
    
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
        
        # Set default values for fields that may not exist in the database
        if not hasattr(fixture, 'status') or fixture.status is None:
            fixture.status = "draft"
        if not hasattr(fixture, 'environment') or fixture.environment is None:
            fixture.environment = "all"
    
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
            
            # Set default values for fields that may not exist in the database
            if not hasattr(fixture, 'status') or fixture.status is None:
                fixture.status = "draft"
            if not hasattr(fixture, 'environment') or fixture.environment is None:
                fixture.environment = "all"
        
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
    
    # Set optional fields if they exist in the model
    if hasattr(db_fixture, 'status'):
        db_fixture.status = fixture.status
    if hasattr(db_fixture, 'environment'):
        db_fixture.environment = fixture.environment
    
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
                # Update database with file information if fields exist
                if hasattr(db_fixture, 'filename'):
                    db_fixture.filename = fixture_result['filename']
                if hasattr(db_fixture, 'export_name'):
                    db_fixture.export_name = fixture_result['export_name']
                if hasattr(db_fixture, 'fixture_file_path'):
                    db_fixture.fixture_file_path = save_result['file_path']
                
                # Read the generated file content and save to playwright_script
                file_content = _read_fixture_file_content(save_result['file_path'])
                if file_content:
                    db_fixture.playwright_script = file_content
                    logger.info(f"Successfully read and saved fixture file content to database")
                else:
                    logger.warning(f"Could not read fixture file content from: {save_result['file_path']}")
                
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


def update_fixture(db: Session, fixture_id: str, fixture: FixtureUpdate, updated_by: str = None) -> Optional[Fixture]:
    db_fixture = get_fixture(db, fixture_id)
    if db_fixture:
        update_data = fixture.dict(exclude_unset=True)
        
        # Set updated_by if provided and the field exists
        if updated_by and hasattr(db_fixture, 'updated_by'):
            db_fixture.updated_by = updated_by
        
        # Update other fields that exist
        for field, value in update_data.items():
            if hasattr(db_fixture, field):
                setattr(db_fixture, field, value)
        
        # Update fixture file if playwright_script changed
        if 'playwright_script' in update_data and db_fixture.project_id:
            try:
                from ..models.project import Project
                project = db.query(Project).filter(Project.id == db_fixture.project_id).first()
                if project:
                    # Regenerate fixture file
                    fixture_result = fixture_generator.generate_fixture(
                        name=db_fixture.name,
                        fixture_type=db_fixture.type,
                        content=db_fixture.playwright_script or "// Add your fixture code here",
                        description=f"Fixture for {project.name}"
                    )
                    
                    if fixture_result['success']:
                        # Save to local project
                        save_result = fixture_generator.save_fixture_to_project(
                            project_name=project.name,
                            fixture_result=fixture_result
                        )
                        
                        if save_result['success']:
                            # Update database with file information if fields exist
                            if hasattr(db_fixture, 'filename'):
                                db_fixture.filename = fixture_result['filename']
                            if hasattr(db_fixture, 'export_name'):
                                db_fixture.export_name = fixture_result['export_name']
                            if hasattr(db_fixture, 'fixture_file_path'):
                                db_fixture.fixture_file_path = save_result['file_path']
                            
                            # Read the updated file content and save to playwright_script
                            file_content = _read_fixture_file_content(save_result['file_path'])
                            if file_content:
                                db_fixture.playwright_script = file_content
                                logger.info(f"Successfully read and updated fixture file content in database")
                            else:
                                logger.warning(f"Could not read updated fixture file content from: {save_result['file_path']}")
                            
                            logger.info(f"Successfully updated fixture file: {save_result['file_path']}")
                        else:
                            logger.warning(f"Failed to save updated fixture file: {save_result.get('error')}")
                    else:
                        logger.warning(f"Failed to generate updated fixture file: {fixture_result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Error updating fixture file: {str(e)}")
                # Don't fail the database update if file generation fails
        
        db.commit()
        db.refresh(db_fixture)
    return db_fixture


async def regenerate_fixture_with_steps(db: Session, fixture_id: str) -> bool:
    """
    Regenerate fixture file with current steps and update playwright_script in database
    
    Args:
        db: Database session
        fixture_id: Fixture ID to regenerate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get fixture
        db_fixture = get_fixture(db, fixture_id)
        if not db_fixture:
            logger.error(f"Fixture not found: {fixture_id}")
            return False
        
        # Get project
        from ..models.project import Project
        project = db.query(Project).filter(Project.id == db_fixture.project_id).first()
        if not project:
            logger.error(f"Project not found for fixture: {fixture_id}")
            return False
        
        # Get fixture steps to include in regeneration
        from .step import get_fixture_steps
        steps = get_fixture_steps(db, fixture_id)
        
        # Build fixture content with steps
        fixture_content = db_fixture.playwright_script or "// Add your fixture code here"
        
        # If we have steps, add them as comments or code blocks
        if steps:
            fixture_content += "\n\n// Steps for this fixture:\n"
            for step in sorted(steps, key=lambda x: x.order):
                fixture_content += f"// Step {step.order}: {step.action}\n"
                if step.data:
                    fixture_content += f"//   Data: {step.data}\n"
                if step.expected:
                    fixture_content += f"//   Expected: {step.expected}\n"
                if step.playwright_script:
                    fixture_content += f"//   Script:\n//   {step.playwright_script.replace(chr(10), chr(10) + '//   ')}\n"
                fixture_content += "\n"
        
        # Generate fixture file using the template
        fixture_result = fixture_generator.generate_fixture(
            name=db_fixture.name,
            fixture_type=db_fixture.type,
            content=fixture_content,
            description=f"Fixture for {project.name} (regenerated with steps)"
        )
        
        if not fixture_result['success']:
            logger.error(f"Failed to generate fixture file: {fixture_result.get('error')}")
            return False
        
        # Save to local project
        save_result = fixture_generator.save_fixture_to_project(
            project_name=project.name,
            fixture_result=fixture_result
        )
        
        if not save_result['success']:
            logger.error(f"Failed to save fixture file: {save_result.get('error')}")
            return False
        
        # Update database with file information
        if hasattr(db_fixture, 'filename'):
            db_fixture.filename = fixture_result['filename']
        if hasattr(db_fixture, 'export_name'):
            db_fixture.export_name = fixture_result['export_name']
        if hasattr(db_fixture, 'fixture_file_path'):
            db_fixture.fixture_file_path = save_result['file_path']
        
        # Read the regenerated file content and save to playwright_script
        file_content = _read_fixture_file_content(save_result['file_path'])
        if file_content:
            db_fixture.playwright_script = file_content
            logger.info(f"Successfully regenerated fixture file and updated content in database")
        else:
            logger.warning(f"Could not read regenerated fixture file content from: {save_result['file_path']}")
        
        db.commit()
        db.refresh(db_fixture)
        
        logger.info(f"Successfully regenerated fixture file: {save_result['file_path']}")
        return True
        
    except Exception as e:
        logger.error(f"Error regenerating fixture file: {str(e)}")
        return False


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


def get_fixture_detail(db: Session, fixture_id: str) -> Optional[Dict[str, Any]]:
    """Get fixture detail with test cases information"""
    from ..models.step import Step
    from ..models.test_case import TestCase
    
    fixture = get_fixture(db, fixture_id)
    if not fixture:
        return None
    
    # Get test cases that use this fixture through steps
    test_cases_using_fixture = db.query(TestCase).join(
        Step, Step.test_case_id == TestCase.id
    ).filter(
        Step.referenced_fixture_id == fixture_id
    ).distinct().all()
    
    test_cases_count = len(test_cases_using_fixture)
    
    # Get test cases details
    test_cases_info = []
    for test_case in test_cases_using_fixture:
        test_cases_info.append({
            'id': str(test_case.id),
            'name': test_case.name,
            'status': test_case.status,
            'created_at': test_case.created_at
        })
    
    # Convert fixture to dict and add test cases info
    fixture_dict = {
        'id': str(fixture.id),
        'name': fixture.name,
        'project_id': str(fixture.project_id),
        'type': fixture.type,
        'status': fixture.status,
        'environment': fixture.environment,
        'playwright_script': fixture.playwright_script,
        'order': fixture.order,
        'created_by': fixture.created_by,
        'updated_by': fixture.updated_by,
        'filename': fixture.filename,
        'export_name': fixture.export_name,
        'fixture_file_path': fixture.fixture_file_path,
        'created_at': fixture.created_at,
        'updated_at': fixture.updated_at,
        'author_name': fixture.author_name,
        'version': fixture.version,
        'total_test_cases_used': test_cases_count,
        'test_cases': test_cases_info
    }
    
    return fixture_dict 


def get_fixture_execution_statistics(db: Session, fixture_id: str) -> Dict[str, Any]:
    """Get execution statistics for a fixture"""
    from ..models.step import Step
    from ..models.test_result import TestCaseExecution
    from ..models.test_case import TestCase
    from sqlalchemy import func
    
    # Get total test cases that use this fixture
    test_cases_using_fixture = db.query(TestCase).join(
        Step, Step.test_case_id == TestCase.id
    ).filter(
        Step.referenced_fixture_id == fixture_id
    ).distinct().count()
    
    # Get executions for test cases that use this fixture
    executions_query = db.query(TestCaseExecution).join(
        TestCase, TestCaseExecution.test_case_id == TestCase.id
    ).join(
        Step, Step.test_case_id == TestCase.id
    ).filter(
        Step.referenced_fixture_id == fixture_id
    )
    
    total_executions = executions_query.count()
    
    if total_executions == 0:
        return {
            "total_executions": 0,
            "total_test_cases_used": test_cases_using_fixture,
            "success_rate": 0,
            "avg_duration": 0,
            "last_status": "not-run"
        }
    
    # Calculate success rate
    successful_executions = executions_query.filter(
        TestCaseExecution.status == "passed"
    ).count()
    success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0
    
    # Calculate average duration
    avg_duration_result = executions_query.with_entities(
        func.avg(TestCaseExecution.duration)
    ).scalar()
    avg_duration = int(avg_duration_result) if avg_duration_result else 0
    
    # Get last execution status
    last_execution = executions_query.order_by(
        TestCaseExecution.created_at.desc()
    ).first()
    last_status = last_execution.status if last_execution else "not-run"
    
    return {
        "total_executions": total_executions,
        "total_test_cases_used": test_cases_using_fixture,
        "success_rate": round(success_rate, 2),
        "avg_duration": avg_duration,
        "last_status": last_status
    } 