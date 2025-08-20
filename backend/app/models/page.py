from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Page(BaseModel):
    __tablename__ = "pages"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="pages")
    locators = relationship("PageLocator", back_populates="page", cascade="all, delete-orphan")


