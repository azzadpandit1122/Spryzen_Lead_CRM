from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend import crud, schemas, auth_utils
from backend.models import User

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

@router.get("", response_model=List[schemas.ReminderOut])
def read_reminders(
    skip: int = 0,
    limit: int = 100,
    assigned_user_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    is_completed: Optional[bool] = None,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    reminders = crud.get_reminders(
        db,
        skip=skip,
        limit=limit,
        assigned_user_id=assigned_user_id,
        lead_id=lead_id,
        is_completed=is_completed
    )
    return reminders

@router.post("", response_model=schemas.ReminderOut)
def create_reminder(
    reminder: schemas.ReminderCreate,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if lead exists
    db_lead = crud.get_lead(db, lead_id=reminder.lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    return crud.create_reminder(db=db, reminder=reminder, creator_id=current_user.id)

@router.put("/{reminder_id}", response_model=schemas.ReminderOut)
def update_reminder(
    reminder_id: int,
    reminder_data: schemas.ReminderUpdate,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    db_reminder = crud.get_reminder(db, reminder_id=reminder_id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    updated = crud.update_reminder(db=db, reminder_id=reminder_id, reminder_data=reminder_data, updater_id=current_user.id)
    return updated

@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    db_reminder = crud.get_reminder(db, reminder_id=reminder_id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    crud.delete_reminder(db=db, reminder_id=reminder_id, deleter_id=current_user.id)
    return {"detail": "Reminder deleted successfully"}
