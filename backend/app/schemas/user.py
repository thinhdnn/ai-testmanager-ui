from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str
    created_by: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by: Optional[str] = None


class UserInDB(UserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None 