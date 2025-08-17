from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Fixture(BaseModel):
    __tablename__ = "fixtures"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "extend" or "inline"
    # Note: These fields may not exist in the current database schema
    # They will be added via migration when possible
    status = Column(String, nullable=True, default="draft")  # active, inactive, draft
    environment = Column(String, nullable=True, default="all")  # all, development, staging, production
    playwright_script = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=1)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)  # May not exist in current schema
    filename = Column(String, nullable=True)  # May not exist in current schema
    export_name = Column(String, nullable=True)  # May not exist in current schema
    fixture_file_path = Column(String, nullable=True)  # May not exist in current schema
    
    # Relationships
    project = relationship("Project", back_populates="fixtures")
    # Many-to-many relationship with test cases through test_case_fixtures table
    test_cases = relationship("TestCase", secondary="test_case_fixtures", back_populates="fixtures")
    # Versioning relationship
    versions = relationship("FixtureVersion", back_populates="fixture", cascade="all, delete-orphan")
    # Note: Steps now reference fixtures via referenced_fixture_id, not fixture_id
    # This allows steps to reference fixtures without being "owned" by them 