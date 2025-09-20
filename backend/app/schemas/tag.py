from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing import Optional
from uuid import UUID

class Tag(BaseModel):
    id: UUID
    value: str
    label: Optional[str]
    project_id: Optional[UUID]

    # Pydantic v2: allow loading from ORM objects
    model_config = ConfigDict(from_attributes=True)