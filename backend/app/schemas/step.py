from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class StepBase(BaseModel):
    action: Optional[str] = None
    data: Optional[str] = None
    expected: Optional[str] = None
    playwright_script: Optional[str] = None
    order: int
    disabled: bool = False
    test_case_id: Optional[UUID] = None
    referenced_fixture_id: Optional[UUID] = None
    referenced_fixture_type: Optional[str] = None  # "extend" or "inline"

    @validator('test_case_id', 'referenced_fixture_id', pre=True)
    def empty_string_to_none(cls, v):
        """Convert empty strings to None for UUID fields"""
        if v == "":
            return None
        return v


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
    referenced_fixture_id: Optional[UUID] = None
    referenced_fixture_type: Optional[str] = None
    updated_by: Optional[str] = None

    @validator('test_case_id', 'referenced_fixture_id', pre=True)
    def empty_string_to_none(cls, v):
        """Convert empty strings to None for UUID fields"""
        if v == "":
            return None
        return v


class StepInDB(StepBase):
    id: UUID
    referenced_fixture_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class Step(StepInDB):
    pass


class StepReorder(BaseModel):
    step_id: str
    new_order: int
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate step_id is a valid UUID
        try:
            UUID(self.step_id)
        except ValueError:
            raise ValueError("step_id must be a valid UUID") 