from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Project(BaseModel):
    __tablename__ = "projects"
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String, default="development")
    playwright_project_path = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    last_run_by = Column(String, nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    fixtures = relationship("Fixture", back_populates="project", cascade="all, delete-orphan")
    test_results = relationship("TestResultHistory", back_populates="project", cascade="all, delete-orphan")

    settings = relationship("ProjectSetting", back_populates="project", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="project", cascade="all, delete-orphan")
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    releases = relationship("Release", back_populates="project", cascade="all, delete-orphan") 
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan")