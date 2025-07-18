from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    permissions = relationship("PermissionAssignment", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan") 