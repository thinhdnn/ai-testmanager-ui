from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base


class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 