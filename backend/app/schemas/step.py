from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class StepBase(BaseModel):
    action: str
    data: Optional[str] = None
    expected: Optional[str] = None
    playwright_script: Optional[str] = None
    order: int
    disabled: bool = False
    test_case_id: Optional[UUID] = None
    fixture_id: Optional[UUID] = None


class StepCreate(StepBase):
    created_by: Optional[str] = None


class StepUpdate(BaseModel):
    action: Optional[str] = None
    data: Optional[str] = None
    expected: Optional[str] = None
    playwright_script: Optional[str] = None
    order: Optional[int] = None
    disabled: Optional[bool] = None
    test_case_id: Optional[UUID] = None
    fixture_id: Optional[UUID] = None
    updated_by: Optional[str] = None


class StepInDB(StepBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class Step(StepInDB):
    pass 