from typing import Optional, Union, List
from pydantic import BaseModel, validator, ConfigDict
from datetime import datetime
from uuid import UUID


class PageBase(BaseModel):
    project_id: Union[str, UUID]
    name: str

    @validator('project_id')
    def convert_project_id_to_str(cls, v):
        # Normalize UUID to string for consistent downstream handling
        return str(v) if isinstance(v, UUID) else v


class PageCreate(PageBase):
    created_by: Optional[str] = None


class PageUpdate(BaseModel):
    name: Optional[str] = None
    updated_by: Optional[str] = None


class Page(PageBase):
    id: Union[str, UUID]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    author_name: Optional[str] = None

    @validator('id')
    def convert_id_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v

    model_config = ConfigDict(from_attributes=True)


class PageLocatorBase(BaseModel):
    page_id: Union[str, UUID]
    locator_key: str
    locator_value: str

    @validator('page_id')
    def convert_page_id_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v


class PageLocatorCreate(PageLocatorBase):
    created_by: Optional[str] = None


class PageLocatorUpdate(BaseModel):
    locator_key: Optional[str] = None
    locator_value: Optional[str] = None
    updated_by: Optional[str] = None


class PageLocator(PageLocatorBase):
    id: Union[str, UUID]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    author_name: Optional[str] = None

    @validator('id')
    def convert_id_to_str_locator(cls, v):
        return str(v) if isinstance(v, UUID) else v

    model_config = ConfigDict(from_attributes=True)


