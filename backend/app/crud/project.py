from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID

from ..models.project import Project
from ..models.test_case import TestCase
from ..models.fixture import Fixture
from ..schemas.project import ProjectCreate, ProjectUpdate


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    return db.query(Project).offset(skip).limit(limit).all()


def get_projects_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
    # For now, return all projects. Later add permission filtering
    return db.query(Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: ProjectCreate, created_by: str) -> Project:
    db_project = Project(
        name=project.name,
        description=project.description,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(db: Session, project_id: UUID, project: ProjectUpdate) -> Optional[Project]:
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: UUID) -> bool:
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True


def get_project_stats(db: Session, project_id: UUID) -> dict:
    # Get counts
    test_cases_count = db.query(func.count(TestCase.id)).filter(TestCase.project_id == project_id).scalar()
    fixtures_count = db.query(func.count(Fixture.id)).filter(Fixture.project_id == project_id).scalar()
    
    return {
        "test_cases_count": test_cases_count,
        "fixtures_count": fixtures_count
    } 