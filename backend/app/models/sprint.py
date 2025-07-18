from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Sprint(BaseModel):
    __tablename__ = "sprints"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="active")
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="sprints")


class Release(BaseModel):
    __tablename__ = "releases"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="planning")
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="releases")
    test_cases = relationship("ReleaseTestCase", back_populates="release", cascade="all, delete-orphan")


class ReleaseTestCase(BaseModel):
    __tablename__ = "release_test_cases"
    
    release_id = Column(UUID(as_uuid=True), ForeignKey("releases.id"), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    version = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    release = relationship("Release", back_populates="test_cases")
    test_case = relationship("TestCase", back_populates="release_test_cases")
    
    __table_args__ = (
        UniqueConstraint('release_id', 'test_case_id', name='uix_release_test_case'),
    ) 