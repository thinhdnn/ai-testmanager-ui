from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class ProjectSetting(BaseModel):
    __tablename__ = "project_settings"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="settings")
    
    __table_args__ = (
        UniqueConstraint('project_id', 'key', name='uix_project_key'),
    ) 