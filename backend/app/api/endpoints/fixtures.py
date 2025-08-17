from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pathlib import Path
import logging

from ...database import get_db
from ...schemas.fixture import Fixture, FixtureCreate, FixtureUpdate
from ...crud import fixture as crud_fixture
from ...models.versioning import FixtureVersion
from ...auth import current_active_user
from ...models.user import User
from ...services.playwright_fixture import fixture_generator

logger = logging.getLogger(__name__)

router = APIRouter()


def _create_version(db: Session, fixture, version: str = None):
    """Helper function to create a version of fixture"""
    if not version:
        # Auto-generate version based on existing versions
        existing_versions = db.query(FixtureVersion).filter(
            FixtureVersion.fixture_id == fixture.id
        ).count()
        version = f"1.{existing_versions}.0"
    
    db_version = FixtureVersion(
        fixture_id=fixture.id,
        version=version,
        name=fixture.name,
        playwright_script=fixture.playwright_script
    )
    
    db.add(db_version)
    db.commit()
    return db_version


@router.post("/", response_model=Fixture, status_code=status.HTTP_201_CREATED)
async def create_fixture(
    fixture: FixtureCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create new fixture with auto-versioning and local file generation"""
    # Set created_by from current user
    fixture.created_by = str(current_user.id)
    
    # Create fixture (now async to handle file generation)
    db_fixture = await crud_fixture.create_fixture(db=db, fixture=fixture)
    
    # Auto-create first version
    _create_version(db, db_fixture, "1.0.0")
    
    # Auto-regenerate fixtures/index.ts for the project
    if db_fixture.project_id:
        from ...services.playwright_project import regenerate_fixtures_index_for_project
        try:
            await regenerate_fixtures_index_for_project(db, str(db_fixture.project_id))
            logger.info(f"Auto-regenerated fixtures/index.ts for project after creating fixture: {db_fixture.id}")
        except Exception as e:
            # Log error but don't fail the fixture creation
            logger.warning(f"Failed to regenerate fixtures/index.ts after creating fixture {db_fixture.id}: {str(e)}")
    
    return db_fixture


@router.get("/", response_model=List[Fixture])
def read_fixtures(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """Get fixtures with optional filters"""
    if project_id:
        fixtures = crud_fixture.get_fixtures_by_project(
            db, project_id=project_id, skip=skip, limit=limit
        )
    else:
        fixtures = crud_fixture.get_fixtures(db, skip=skip, limit=limit)
    
    return fixtures


@router.get("/{fixture_id}", response_model=Fixture)
def read_fixture(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get fixture by ID"""
    db_fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return db_fixture


@router.get("/{fixture_id}/detail")
def read_fixture_detail(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get fixture detail with test cases information"""
    fixture_detail = crud_fixture.get_fixture_detail(db, fixture_id=fixture_id)
    if fixture_detail is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return fixture_detail


@router.put("/{fixture_id}", response_model=Fixture)
async def update_fixture(
    fixture_id: str,
    fixture: FixtureUpdate,
    auto_version: bool = Query(True, description="Auto-create version on update"),
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Update fixture with optional auto-versioning and index regeneration"""
    db_fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Create version before update if requested
    if auto_version:
        _create_version(db, db_fixture)
    
    # Update fixture with updated_by field
    updated_fixture = crud_fixture.update_fixture(
        db=db, 
        fixture_id=fixture_id, 
        fixture=fixture,
        updated_by=str(current_user.id)
    )
    
    # Auto-regenerate fixtures/index.ts for the project
    if updated_fixture.project_id:
        from ...services.playwright_project import regenerate_fixtures_index_for_project
        try:
            await regenerate_fixtures_index_for_project(db, str(updated_fixture.project_id))
            logger.info(f"Auto-regenerated fixtures/index.ts for project after updating fixture: {fixture_id}")
        except Exception as e:
            # Log error but don't fail the fixture update
            logger.warning(f"Failed to regenerate fixtures/index.ts after updating fixture {fixture_id}: {str(e)}")
    
    return updated_fixture


@router.delete("/{fixture_id}")
async def delete_fixture(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Delete fixture and regenerate index"""
    db_fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Store project_id before deletion
    project_id = db_fixture.project_id
    
    crud_fixture.delete_fixture(db=db, fixture_id=fixture_id)
    
    # Auto-regenerate fixtures/index.ts for the project
    if project_id:
        from ...services.playwright_project import regenerate_fixtures_index_for_project
        try:
            await regenerate_fixtures_index_for_project(db, str(project_id))
            logger.info(f"Auto-regenerated fixtures/index.ts for project after deleting fixture: {fixture_id}")
        except Exception as e:
            # Log error but don't fail the fixture deletion
            logger.warning(f"Failed to regenerate fixtures/index.ts after deleting fixture {fixture_id}: {str(e)}")
    
    return {"message": "Fixture deleted successfully"}


# ============ VERSIONING ENDPOINTS ============

@router.get("/{fixture_id}/versions", response_model=List[dict])
def get_fixture_versions(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get all versions of a fixture"""
    # Check if fixture exists
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Get all versions
    versions = db.query(FixtureVersion).filter(
        FixtureVersion.fixture_id == fixture_id
    ).order_by(FixtureVersion.created_at.desc()).all()
    
    return [
        {
            "id": str(version.id),
            "version": version.version,
            "name": version.name,
            "playwright_script": version.playwright_script,
            "created_at": version.created_at,
            "updated_at": version.updated_at
        }
        for version in versions
    ]


@router.get("/{fixture_id}/versions/{version}", response_model=dict)
def get_fixture_version(
    fixture_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get a specific version of a fixture"""
    db_version = db.query(FixtureVersion).filter(
        FixtureVersion.fixture_id == fixture_id,
        FixtureVersion.version == version
    ).first()
    
    if not db_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for fixture"
        )
    
    return {
        "id": str(db_version.id),
        "version": db_version.version,
        "fixture_id": str(fixture_id),
        "name": db_version.name,
        "playwright_script": db_version.playwright_script,
        "created_at": db_version.created_at,
        "updated_at": db_version.updated_at
    }


@router.post("/{fixture_id}/versions/{version}/restore", response_model=Fixture)
def restore_fixture_version(
    fixture_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Restore a fixture to a specific version"""
    # Get the version to restore
    db_version = db.query(FixtureVersion).filter(
        FixtureVersion.fixture_id == fixture_id,
        FixtureVersion.version == version
    ).first()
    
    if not db_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for fixture"
        )
    
    # Get current fixture
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Create version of current state before restore
    _create_version(db, fixture)
    
    # Update current fixture with version data
    fixture.name = db_version.name
    fixture.playwright_script = db_version.playwright_script
    
    db.commit()
    db.refresh(fixture)
    
    return fixture


@router.post("/{fixture_id}/versions/create", response_model=dict)
def create_fixture_version(
    fixture_id: str,
    reason: str = Query(..., description="Reason for version creation"),
    db: Session = Depends(get_db)
):
    """Create a new version of a fixture"""
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Create new version
    version = _create_version(db, fixture)
    
    return {
        "id": str(version.id),
        "version": version.version,
        "name": version.name,
        "created_at": version.created_at,
        "reason": reason
    }


@router.get("/{fixture_id}/versions/{version}/steps", response_model=List[dict])
def get_fixture_version_steps(
    fixture_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get all steps of a specific fixture version"""
    # Get fixture version
    fixture_version = crud_fixture.get_fixture_version(db, fixture_id=fixture_id, version=version)
    if not fixture_version:
        raise HTTPException(status_code=404, detail="Fixture version not found")
    
    # Get steps that reference this fixture
    steps = db.query(Step).filter(
        Step.referenced_fixture_id == fixture_id
    ).order_by(Step.order).all()
    
    # Convert to dict format
    steps_data = []
    for step in steps:
        steps_data.append({
            "id": str(step.id),
            "action": step.action,
            "data": step.data,
            "expected": step.expected,
            "playwright_script": step.playwright_script,
            "order": step.order,
            "disabled": step.disabled,
            "referenced_fixture_id": str(step.referenced_fixture_id),
            "created_at": step.created_at,
            "updated_at": step.updated_at
        })
    
    return steps_data


@router.patch("/{fixture_id}/status")
def update_fixture_status(
    fixture_id: str,
    status: str = Query(..., description="New status"),
    db: Session = Depends(get_db)
):
    """Update fixture status"""
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Update status
    fixture.status = status
    db.commit()
    db.refresh(fixture)
    
    return fixture


# ============ FIXTURE FILE MANAGEMENT ============

@router.get("/{fixture_id}/file-info")
def get_fixture_file_info(
    fixture_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    """Get fixture file information"""
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    return {
        "fixture_id": str(fixture.id),
        "filename": fixture.filename,
        "export_name": fixture.export_name,
        "fixture_file_path": fixture.fixture_file_path,
        "file_exists": bool(fixture.fixture_file_path and Path(fixture.fixture_file_path).exists()) if fixture.fixture_file_path else False
    }


@router.post("/{fixture_id}/regenerate-file")
async def regenerate_fixture_file(
    fixture_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    """Regenerate fixture file from current database content"""
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Get project information
    from ...models.project import Project
    project = db.query(Project).filter(Project.id == fixture.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Generate fixture file
        fixture_result = fixture_generator.generate_fixture(
            name=fixture.name,
            fixture_type=fixture.type,
            content=fixture.playwright_script or "// Add your fixture code here",
            description=f"Fixture for {project.name}"
        )
        
        if not fixture_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate fixture: {fixture_result.get('error')}"
            )
        
        # Save to local project
        save_result = fixture_generator.save_fixture_to_project(
            project_name=project.name,
            fixture_result=fixture_result
        )
        
        if not save_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save fixture file: {save_result.get('error')}"
            )
        
        # Update database with new file information
        fixture.filename = fixture_result['filename']
        fixture.export_name = fixture_result['export_name']
        fixture.fixture_file_path = save_result['file_path']
        
        db.commit()
        db.refresh(fixture)
        
        return {
            "message": "Fixture file regenerated successfully",
            "file_path": save_result['file_path'],
            "filename": fixture_result['filename'],
            "export_name": fixture_result['export_name']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating fixture file: {str(e)}"
        )


@router.get("/project/{project_id}/files")
def list_project_fixture_files(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    """List all fixture files in a project's local directory"""
    # Get project information
    from ...models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # List fixtures from local project
        local_fixtures = fixture_generator.list_project_fixtures(project.name)
        
        # Get database fixtures for comparison
        db_fixtures = crud_fixture.get_fixtures_by_project(db, project_id=project_id)
        
        # Create mapping for comparison
        db_fixture_map = {f.export_name: f for f in db_fixtures if f.export_name}
        
        result = []
        for local_fixture in local_fixtures:
            db_fixture = db_fixture_map.get(local_fixture['export_name'])
            result.append({
                **local_fixture,
                "in_database": bool(db_fixture),
                "database_id": str(db_fixture.id) if db_fixture else None,
                "sync_status": "synced" if db_fixture and db_fixture.fixture_file_path == local_fixture['file_path'] else "out_of_sync"
            })
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "fixtures": result,
            "total_files": len(result),
            "synced_count": len([f for f in result if f['sync_status'] == 'synced'])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing project fixture files: {str(e)}"
        )


# ============ FIXTURE STEPS ENDPOINTS ============

@router.get("/{fixture_id}/steps", response_model=List[dict])
def get_fixture_steps(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Get steps that belong to this fixture (fixture's own steps)"""
    from ...crud import step as crud_step
    
    # Check if fixture exists
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Get fixture's own steps (not steps that reference this fixture)
    steps = crud_step.get_fixture_steps(db, fixture_id=fixture_id)
    
    # Convert to dict format for response
    steps_data = []
    for step in steps:
        steps_data.append({
            "id": str(step.id),
            "action": step.action,
            "data": step.data,
            "expected": step.expected,
            "playwright_script": step.playwright_script,
            "order": step.order,
            "disabled": step.disabled,
            "referenced_fixture_id": str(step.referenced_fixture_id) if step.referenced_fixture_id else None,
            "referenced_fixture_name": getattr(step, 'referenced_fixture_name', None),
            "created_at": step.created_at,
            "updated_at": step.updated_at,
            "created_by": step.created_by,
            "updated_by": step.updated_by
        })
    
    return steps_data