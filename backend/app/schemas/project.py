from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    environment: str = "development"
    playwright_project_path: Optional[str] = None


class ProjectCreate(ProjectBase):
    created_by: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    playwright_project_path: Optional[str] = None
    updated_by: Optional[str] = None


class ProjectInDB(ProjectBase):
    id: UUID  # Changed from str to UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    last_run_by: Optional[str] = None
    last_run: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Project(ProjectInDB):
    pass


class ProjectWithDetails(Project):
    test_cases_count: Optional[int] = 0
    fixtures_count: Optional[int] = 0
    last_test_result: Optional[str] = None 