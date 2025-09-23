from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from fastapi_users import schemas
from uuid import UUID


class UserRead(schemas.BaseUser):
    username: str
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    username: str


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str 