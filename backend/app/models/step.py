from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Step(BaseModel):
    __tablename__ = "steps"
    
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=True)
    action = Column(String, nullable=False)
    data = Column(Text, nullable=True)
    expected = Column(Text, nullable=True)
    playwright_script = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    disabled = Column(Boolean, default=False)
    referenced_fixture_id = Column(UUID(as_uuid=True), ForeignKey("fixtures.id"), nullable=True)  # Fixture to call in this step
    referenced_fixture_type = Column(String, nullable=True)  # Type of referenced fixture: "extend" or "inline"
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="steps")
    referenced_fixture = relationship("Fixture", foreign_keys=[referenced_fixture_id]) 