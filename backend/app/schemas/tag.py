from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class Tag(BaseModel):
    id: UUID
    value: str
    label: Optional[str]
    project_id: Optional[UUID]

    class Config:
        orm_mode = True 