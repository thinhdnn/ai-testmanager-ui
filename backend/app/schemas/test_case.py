from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TestCaseBase(BaseModel):
    name: str
    project_id: Union[str, UUID]
    order: Optional[int] = None
    status: Optional[str] = "pending"
    version: Optional[str] = None
    is_manual: Optional[bool] = False
    tags: Optional[Union[str, List[str]]] = None
    test_file_path: Optional[str] = None
    playwright_script: Optional[str] = None
    created_by: Optional[str] = None

    @validator('project_id')
    def convert_project_id_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v

    @validator('tags')
    def convert_tags_to_list(cls, v):
        if isinstance(v, str):
            return v.split(',') if v else []
        return v or []


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None
    version: Optional[str] = None
    is_manual: Optional[bool] = None
    tags: Optional[List[str]] = None
    test_file_path: Optional[str] = None
    playwright_script: Optional[str] = None
    updated_by: Optional[str] = None


class TestCase(TestCaseBase):
    id: Union[str, UUID]
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    last_run: Optional[datetime] = None
    last_run_by: Optional[str] = None
    author_name: Optional[str] = None

    @validator('id')
    def convert_id_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v

    class Config:
        from_attributes = True 