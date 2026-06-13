from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend import crud, schemas, auth_utils
from backend.models import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("", response_model=List[schemas.UserOut])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_utils.require_manager_or_admin),
    db: Session = Depends(get_db)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.post("", response_model=schemas.UserOut)
def create_user(
    user: schemas.UserCreate,
    current_user: User = Depends(auth_utils.require_admin),
    db: Session = Depends(get_db)
):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_email = crud.get_user_by_email(db, email=user.email)
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    return crud.create_user(db=db, user=user, creator_id=current_user.id)

@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # Non-admins can only update their own profile
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    # Non-admins cannot update their own role
    if current_user.role != "admin" and user_data.role is not None and user_data.role != current_user.role:
        raise HTTPException(status_code=403, detail="Non-admins cannot modify user roles")
        
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    updated = crud.update_user(db=db, user_id=user_id, user_data=user_data, updater_id=current_user.id)
    return updated

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(auth_utils.require_admin),
    db: Session = Depends(get_db)
):
    # Cannot delete yourself
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
        
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    crud.delete_user(db=db, user_id=user_id, deleter_id=current_user.id)
    return {"detail": "User deleted successfully"}
