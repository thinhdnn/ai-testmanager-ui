from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...schemas.user import User, UserCreate, UserUpdate
from ...crud import user as crud_user

router = APIRouter()


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create new user"""
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    db_user = crud_user.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    return crud_user.create_user(db=db, user=user)


@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users"""
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user"""
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud_user.update_user(db=db, user_id=user_id, user=user)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete user"""
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    crud_user.delete_user(db=db, user_id=user_id)
    return {"message": "User deleted successfully"} 