from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


# Association table for test case and fixture relationship
test_case_fixtures = Table(
    'test_case_fixtures',
    BaseModel.metadata,
    Column('test_case_id', UUID(as_uuid=True), ForeignKey('test_cases.id'), primary_key=True),
    Column('fixture_id', UUID(as_uuid=True), ForeignKey('fixtures.id'), primary_key=True),
    Column('order', Integer, default=0),  # Order of fixture execution
    Column('created_at', DateTime(timezone=True), server_default='now()'),
    Column('created_by', String, nullable=True)
)


class TestCase(BaseModel):
    __tablename__ = "test_cases"
    
    order = Column(Integer, default=0)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")
    version = Column(String, default="1.0.0")
    is_manual = Column(Boolean, default=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    last_run_by = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    test_file_path = Column(String, nullable=True)
    playwright_script = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="test_cases")
    versions = relationship("TestCaseVersion", back_populates="test_case", cascade="all, delete-orphan")
    steps = relationship("Step", back_populates="test_case", cascade="all, delete-orphan")
    executions = relationship("TestCaseExecution", back_populates="test_case", cascade="all, delete-orphan")
    release_test_cases = relationship("ReleaseTestCase", back_populates="test_case", cascade="all, delete-orphan")
    # New relationship for fixtures
    fixtures = relationship("Fixture", secondary=test_case_fixtures, back_populates="test_cases") 