from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class TestResultHistory(BaseModel):
    __tablename__ = "test_result_history"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=True)  # Custom name for the test run
    test_result_file_name = Column(String, nullable=True)
    success = Column(Boolean, nullable=False)
    status = Column(String, nullable=False)
    execution_time = Column(Integer, nullable=True)
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    result_data = Column(Text, nullable=True)  # JSON string
    created_by = Column(String, nullable=True)
    last_run_by = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="test_results")
    test_case_executions = relationship("TestCaseExecution", back_populates="test_result", cascade="all, delete-orphan")


class TestCaseExecution(BaseModel):
    __tablename__ = "test_case_executions"
    
    test_result_id = Column(UUID(as_uuid=True), ForeignKey("test_result_history.id"), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    status = Column(String, nullable=False)
    duration = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    retries = Column(Integer, default=0)
    
    # Relationships
    test_result = relationship("TestResultHistory", back_populates="test_case_executions")
    test_case = relationship("TestCase", back_populates="executions") 