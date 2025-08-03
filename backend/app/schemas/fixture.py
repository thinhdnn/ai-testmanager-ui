from typing import Optional, List, Union
from pydantic import BaseModel, validator
from datetime import datetime
from uuid import UUID


class FixtureBase(BaseModel):
    name: str
    project_id: Union[str, UUID]
    type: Optional[str] = "data"  # data, config, mock
    status: Optional[str] = "draft"  # active, inactive, draft
    environment: Optional[str] = "all"  # all, development, staging, production
    playwright_script: Optional[str] = None

    @validator('project_id')
    def convert_project_id_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v


class FixtureCreate(FixtureBase):
    created_by: Optional[str] = None


class FixtureUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    environment: Optional[str] = None
    playwright_script: Optional[str] = None
    updated_by: Optional[str] = None


class Fixture(FixtureBase):
    id: Union[str, UUID]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    author_name: Optional[str] = None

    @validator('id')
    def convert_id_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v

    class Config:
        from_attributes = True 