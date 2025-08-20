from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class PageLocator(BaseModel):
    __tablename__ = "page_locators"

    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    locator_key = Column(String, nullable=False)
    locator_value = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    page = relationship("Page", back_populates="locators")


