from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Tag(BaseModel):
    __tablename__ = "tags"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    value = Column(String, nullable=False)
    label = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="tags")
    
    __table_args__ = (
        UniqueConstraint('project_id', 'value', name='uix_project_tag_value'),
    ) 