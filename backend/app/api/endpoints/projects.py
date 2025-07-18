from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from ...database import get_db
from ...schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectWithDetails
from ...schemas.project_setting import ProjectSetting, ProjectSettingCreate, ProjectSettingUpdate
from ...schemas.release import Release, ReleaseCreate, ReleaseUpdate, ReleaseSummary, ReleaseTestCase, ReleaseTestCaseCreate
from ...crud import project as crud_project, project_setting as crud_setting, release as crud_release

router = APIRouter()


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create new project"""
    return crud_project.create_project(db=db, project=project, created_by=project.created_by or "system")


@router.get("/", response_model=List[Project])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all projects"""
    projects = crud_project.get_projects(db, skip=skip, limit=limit)
    return projects


@router.get("/with-stats", response_model=List[Dict])
def read_projects_with_stats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all projects with statistics in one call"""
    from ...crud import test_result as crud_result
    
    projects = crud_project.get_projects(db, skip=skip, limit=limit)
    projects_with_stats = []
    
    for project in projects:
        # Get project statistics
        project_stats = crud_project.get_project_stats(db, str(project.id))
        test_stats = crud_result.get_project_test_stats(db, str(project.id))
        
        # Convert project to dict and add stats
        project_dict = {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "environment": project.environment,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "created_by": project.created_by,
            "updated_by": project.updated_by,
            "last_run": project.last_run.isoformat() if project.last_run else None,
            "last_run_by": project.last_run_by,
            # Add statistics
            "test_cases_count": project_stats["test_cases_count"],
            "fixtures_count": project_stats["fixtures_count"],
            "success_rate": test_stats["success_rate"],
            "total_runs": test_stats["total_runs"],
            "avg_execution_time": test_stats["avg_execution_time"]
        }
        
        projects_with_stats.append(project_dict)
    
    return projects_with_stats


@router.get("/{project_id}", response_model=ProjectWithDetails)
def read_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project by ID with statistics"""
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project statistics
    stats = crud_project.get_project_stats(db, project_id)
    
    # Convert to dict and add stats
    project_dict = {
        **db_project.__dict__,
        "test_cases_count": stats["test_cases_count"],
        "fixtures_count": stats["fixtures_count"]
    }
    
    return ProjectWithDetails(**project_dict)


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update project"""
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return crud_project.update_project(db=db, project_id=project_id, project=project)


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Delete project"""
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    crud_project.delete_project(db=db, project_id=project_id)
    return {"message": "Project deleted successfully"}


# ============ PROJECT SETTINGS NESTED ROUTES ============

@router.get("/{project_id}/settings", response_model=List[ProjectSetting])
def get_project_settings(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get all settings for a project"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    settings = crud_setting.get_settings_by_project(db, project_id=project_id)
    return settings


@router.get("/{project_id}/settings/dict", response_model=Dict[str, str])
def get_project_settings_dict(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project settings as key-value dictionary"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return crud_setting.get_settings_as_dict(db, project_id=project_id)


@router.post("/{project_id}/settings", response_model=ProjectSetting, status_code=status.HTTP_201_CREATED)
def create_project_setting(
    project_id: str,
    setting: ProjectSettingCreate,
    db: Session = Depends(get_db)
):
    """Create setting for a project"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Override project_id from URL
    setting_data = setting.dict()
    setting_data['project_id'] = project_id
    
    new_setting = ProjectSettingCreate(**setting_data)
    
    # Check if setting already exists
    existing = crud_setting.get_setting_by_key(db, project_id, setting.key)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Setting '{setting.key}' already exists for this project"
        )
    
    return crud_setting.create_project_setting(db=db, setting=new_setting)


@router.get("/{project_id}/settings/{key}", response_model=ProjectSetting)
def get_project_setting_by_key(
    project_id: str,
    key: str,
    db: Session = Depends(get_db)
):
    """Get specific setting by key"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    setting = crud_setting.get_setting_by_key(db, project_id=project_id, key=key)
    if setting is None:
        raise HTTPException(
            status_code=404,
            detail=f"Setting '{key}' not found for this project"
        )
    return setting


@router.put("/{project_id}/settings/{key}", response_model=ProjectSetting)
def upsert_project_setting(
    project_id: str,
    key: str,
    value: str,
    updated_by: str = None,
    db: Session = Depends(get_db)
):
    """Create or update a specific setting"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    setting = crud_setting.upsert_setting(
        db=db,
        project_id=project_id,
        key=key,
        value=value,
        updated_by=updated_by
    )
    return setting


@router.delete("/{project_id}/settings/{key}")
def delete_project_setting_by_key(
    project_id: str,
    key: str,
    db: Session = Depends(get_db)
):
    """Delete specific setting by key"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    setting = crud_setting.get_setting_by_key(db, project_id=project_id, key=key)
    if setting is None:
        raise HTTPException(
            status_code=404,
            detail=f"Setting '{key}' not found for this project"
        )
    
    crud_setting.delete_project_setting(db, setting_id=str(setting.id))
    return {"message": f"Setting '{key}' deleted successfully"}


# ============ PROJECT RELEASES NESTED ROUTES ============

@router.get("/{project_id}/releases", response_model=List[ReleaseSummary])
def get_project_releases(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get all releases for a project with statistics"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    releases_summary = crud_release.get_project_releases_summary(db, project_id=project_id)
    return releases_summary


@router.post("/{project_id}/releases", response_model=Release, status_code=status.HTTP_201_CREATED)
def create_project_release(
    project_id: str,
    release: ReleaseCreate,
    db: Session = Depends(get_db)
):
    """Create release for a project"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Override project_id from URL
    release_data = release.dict()
    release_data['project_id'] = project_id
    
    new_release = ReleaseCreate(**release_data)
    
    # Check if version already exists
    existing = crud_release.get_release_by_version(db, project_id, release.version)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Release version '{release.version}' already exists for this project"
        )
    
    return crud_release.create_release(db=db, release=new_release)


@router.get("/{project_id}/releases/{release_id}", response_model=Release)
def get_project_release(
    project_id: str,
    release_id: str,
    db: Session = Depends(get_db)
):
    """Get specific release"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    release = crud_release.get_release(db, release_id=release_id)
    if release is None or release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    return release


@router.put("/{project_id}/releases/{release_id}", response_model=Release)
def update_project_release(
    project_id: str,
    release_id: str,
    release: ReleaseUpdate,
    db: Session = Depends(get_db)
):
    """Update project release"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_release = crud_release.get_release(db, release_id=release_id)
    if db_release is None or db_release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    updated_release = crud_release.update_release(db=db, release_id=release_id, release=release)
    return updated_release


@router.delete("/{project_id}/releases/{release_id}")
def delete_project_release(
    project_id: str,
    release_id: str,
    db: Session = Depends(get_db)
):
    """Delete project release"""
    # Check if project exists
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_release = crud_release.get_release(db, release_id=release_id)
    if db_release is None or db_release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    crud_release.delete_release(db=db, release_id=release_id)
    return {"message": "Release deleted successfully"}


# ============ RELEASE TEST CASES MANAGEMENT ============

@router.get("/{project_id}/releases/{release_id}/test-cases", response_model=List[dict])
def get_release_test_cases(
    project_id: str,
    release_id: str,
    db: Session = Depends(get_db)
):
    """Get test cases in a release"""
    # Check if project and release exist
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    release = crud_release.get_release(db, release_id=release_id)
    if release is None or release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    test_cases = crud_release.get_release_test_cases_with_details(db, release_id=release_id)
    return test_cases


@router.post("/{project_id}/releases/{release_id}/test-cases", response_model=ReleaseTestCase, status_code=status.HTTP_201_CREATED)
def add_test_case_to_release(
    project_id: str,
    release_id: str,
    release_test_case: ReleaseTestCaseCreate,
    db: Session = Depends(get_db)
):
    """Add test case to release"""
    # Check if project and release exist
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    release = crud_release.get_release(db, release_id=release_id)
    if release is None or release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    # Override release_id from URL
    rtc_data = release_test_case.dict()
    rtc_data['release_id'] = release_id
    
    new_rtc = ReleaseTestCaseCreate(**rtc_data)
    
    return crud_release.add_test_case_to_release(db=db, release_test_case=new_rtc)


@router.delete("/{project_id}/releases/{release_id}/test-cases/{test_case_id}")
def remove_test_case_from_release(
    project_id: str,
    release_id: str,
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Remove test case from release"""
    # Check if project and release exist
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    release = crud_release.get_release(db, release_id=release_id)
    if release is None or release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    success = crud_release.remove_test_case_from_release(db, release_id=release_id, test_case_id=test_case_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test case not found in this release")
    
    return {"message": "Test case removed from release successfully"}


@router.post("/{project_id}/releases/{release_id}/test-cases/bulk")
def bulk_add_test_cases_to_release(
    project_id: str,
    release_id: str,
    test_case_ids: List[str],
    version: str = "1.0.0",
    created_by: str = None,
    db: Session = Depends(get_db)
):
    """Bulk add test cases to release"""
    # Check if project and release exist
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    release = crud_release.get_release(db, release_id=release_id)
    if release is None or release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    results = crud_release.bulk_add_test_cases_to_release(
        db=db,
        release_id=release_id,
        test_case_ids=test_case_ids,
        version=version,
        created_by=created_by
    )
    
    return {"message": f"Added {len(results)} test cases to release", "added_count": len(results)}


@router.get("/{project_id}/releases/{release_id}/stats", response_model=Dict)
def get_release_statistics(
    project_id: str,
    release_id: str,
    db: Session = Depends(get_db)
):
    """Get release statistics"""
    # Check if project and release exist
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    release = crud_release.get_release(db, release_id=release_id)
    if release is None or release.project_id != project_id:
        raise HTTPException(status_code=404, detail="Release not found for this project")
    
    stats = crud_release.get_release_stats(db, release_id=release_id)
    return stats 