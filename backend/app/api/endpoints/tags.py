from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.tag import Tag as TagModel
from ...schemas.tag import Tag as TagSchema

router = APIRouter()

@router.get("/", response_model=List[TagSchema])
def get_global_tags(db: Session = Depends(get_db)):
    """Get all global tags (project_id=None)"""
    tags = db.query(TagModel).filter(TagModel.project_id == None).all()
    return tags 