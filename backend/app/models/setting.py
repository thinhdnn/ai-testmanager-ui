from sqlalchemy import Column, String
from .base import BaseModel


class Setting(BaseModel):
    __tablename__ = "settings"
    
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True) 