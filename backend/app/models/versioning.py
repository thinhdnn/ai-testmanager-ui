from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class TestCaseVersion(BaseModel):
    __tablename__ = "test_case_versions"
    
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    version = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    playwright_script = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="versions")
    step_versions = relationship("StepVersion", back_populates="test_case_version", cascade="all, delete-orphan")


class StepVersion(BaseModel):
    __tablename__ = "step_versions"
    
    test_case_version_id = Column(UUID(as_uuid=True), ForeignKey("test_case_versions.id"), nullable=True)
    fixture_version_id = Column(UUID(as_uuid=True), ForeignKey("fixture_versions.id"), nullable=True)
    action = Column(String, nullable=False)
    data = Column(Text, nullable=True)
    expected = Column(Text, nullable=True)
    playwright_code = Column(Text, nullable=True)
    selector = Column(String, nullable=True)
    order = Column(Integer, nullable=False)
    disabled = Column(Boolean, default=False)
    created_by = Column(String, nullable=True)
    
    # Relationships
    test_case_version = relationship("TestCaseVersion", back_populates="step_versions")
    fixture_version = relationship("FixtureVersion", back_populates="step_versions")


class FixtureVersion(BaseModel):
    __tablename__ = "fixture_versions"
    
    fixture_id = Column(UUID(as_uuid=True), ForeignKey("fixtures.id"), nullable=False)
    version = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    playwright_script = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    
    # Relationships
    fixture = relationship("Fixture", back_populates="versions")
    step_versions = relationship("StepVersion", back_populates="fixture_version", cascade="all, delete-orphan") 