from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProjectSettingBase(BaseModel):
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Setting value")


class ProjectSettingCreate(ProjectSettingBase):
    project_id: UUID = Field(..., description="Project ID")
    created_by: Optional[str] = None


class ProjectSettingUpdate(BaseModel):
    value: Optional[str] = None
    updated_by: Optional[str] = None


class ProjectSetting(ProjectSettingBase):
    id: UUID
    project_id: UUID
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSettingBulk(BaseModel):
    """Schema for bulk setting operations"""
    settings: list[ProjectSettingCreate] = Field(..., description="List of settings to create/update")


class ProjectSettingsByCategory(BaseModel):
    """Schema for grouped settings response"""
    category: str
    settings: dict[str, str] = Field(..., description="Key-value pairs for the category") 