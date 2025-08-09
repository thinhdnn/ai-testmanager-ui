from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...schemas.fixture import Fixture, FixtureCreate, FixtureUpdate
from ...crud import fixture as crud_fixture
from ...models.versioning import FixtureVersion
from ...auth import current_active_user
from ...models.user import User

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
def create_fixture(
    fixture: FixtureCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create new fixture with auto-versioning"""
    # Set created_by from current user
    fixture.created_by = str(current_user.id)
    
    # Create fixture
    db_fixture = crud_fixture.create_fixture(db=db, fixture=fixture)
    
    # Auto-create first version
    _create_version(db, db_fixture, "1.0.0")
    
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


@router.put("/{fixture_id}", response_model=Fixture)
def update_fixture(
    fixture_id: str,
    fixture: FixtureUpdate,
    auto_version: bool = Query(True, description="Auto-create version on update"),
    db: Session = Depends(get_db)
):
    """Update fixture with optional auto-versioning"""
    db_fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Create version before update if requested
    if auto_version:
        _create_version(db, db_fixture)
    
    # Update fixture  
    updated_fixture = crud_fixture.update_fixture(db=db, fixture_id=fixture_id, fixture=fixture)
    
    return updated_fixture


@router.delete("/{fixture_id}")
def delete_fixture(
    fixture_id: str,
    db: Session = Depends(get_db)
):
    """Delete fixture"""
    db_fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    crud_fixture.delete_fixture(db=db, fixture_id=fixture_id)
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
    """Get steps for a specific version of a fixture"""
    # Check if fixture exists
    fixture = crud_fixture.get_fixture(db, fixture_id=fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # For now, return current steps since fixture versions don't store steps separately
    # In the future, you might want to store steps with versions
    from ...models.step import Step
    steps = db.query(Step).filter(
        Step.fixture_id == fixture_id
    ).order_by(Step.order).all()
    
    return [
        {
            "id": str(step.id),
            "fixture_id": str(step.fixture_id),
            "action": step.action,
            "data": step.data,
            "expected": step.expected,
            "playwright_script": step.playwright_script,
            "order": step.order,
            "disabled": step.disabled,
            "created_at": step.created_at,
            "updated_at": step.updated_at
        }
        for step in steps
    ]


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