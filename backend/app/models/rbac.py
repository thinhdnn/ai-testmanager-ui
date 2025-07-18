from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Permission(BaseModel):
    __tablename__ = "permissions"
    
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    permission_assignments = relationship("PermissionAssignment", back_populates="permission", cascade="all, delete-orphan")


class Role(BaseModel):
    __tablename__ = "roles"
    
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class RolePermission(BaseModel):
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uix_role_permission'),
    )


class UserRole(BaseModel):
    __tablename__ = "user_roles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uix_user_role'),
    )


class PermissionAssignment(BaseModel):
    __tablename__ = "permission_assignments"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission", back_populates="permission_assignments")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id', 'resource_type', 'resource_id', name='uix_user_permission_resource'),
    ) 