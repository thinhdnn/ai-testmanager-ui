from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Fixture(BaseModel):
    __tablename__ = "fixtures"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    playwright_script = Column(Text, nullable=True)
    type = Column(String, default="extend")  # extend or inline
    filename = Column(String, nullable=True)
    export_name = Column(String, nullable=True)
    fixture_file_path = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="fixtures")
    steps = relationship("Step", back_populates="fixture", cascade="all, delete-orphan")
    versions = relationship("FixtureVersion", back_populates="fixture", cascade="all, delete-orphan") 