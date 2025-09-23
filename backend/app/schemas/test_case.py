from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime


class TestCaseFixtureBase(BaseModel):
    fixture_id: UUID
    order: int = 0


class TestCaseFixtureCreate(TestCaseFixtureBase):
    pass


class TestCaseFixtureUpdate(BaseModel):
    order: Optional[int] = None


class TestCaseFixture(TestCaseFixtureBase):
    id: str
    test_case_id: UUID
    fixture_id: UUID
    order: int
    created_at: datetime
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TestCaseBase(BaseModel):
    name: str
    project_id: UUID
    status: Optional[str] = "pending"
    version: Optional[str] = "1.0.0"
    is_manual: Optional[bool] = False
    tags: Optional[str] = None
    test_file_path: Optional[str] = None
    playwright_script: Optional[str] = None


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    is_manual: Optional[bool] = None
    tags: Optional[str] = None
    test_file_path: Optional[str] = None
    playwright_script: Optional[str] = None


class TestCase(TestCaseBase):
    id: UUID
    order: int
    last_run: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    last_run_by: Optional[str] = None
    fixtures: List[TestCaseFixture] = []

    model_config = ConfigDict(from_attributes=True) 