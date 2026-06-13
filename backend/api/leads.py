from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from backend.database import get_db
from backend import crud, schemas, auth_utils
from backend.models import User

router = APIRouter(prefix="/api/leads", tags=["leads"])

@router.get("", response_model=List[schemas.LeadOut])
def read_leads(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    keyword: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    assigned_to_id: Optional[int] = None,
    claimed_by_id: Optional[int] = None,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    leads = crud.get_leads(
        db,
        skip=skip,
        limit=limit,
        source=source,
        status=status,
        priority=priority,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        assigned_to_id=assigned_to_id,
        claimed_by_id=claimed_by_id
    )
    return leads

@router.get("/{lead_id}", response_model=schemas.LeadOut)
def read_lead(
    lead_id: int,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db_lead

@router.post("", response_model=schemas.LeadOut)
def create_lead(
    lead: schemas.LeadCreate,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_lead(db=db, lead=lead, creator_id=current_user.id)

@router.post("/bulk-delete")
def bulk_delete_leads(
    request: schemas.BulkDeleteRequest,
    current_user: User = Depends(auth_utils.require_manager_or_admin),
    db: Session = Depends(get_db)
):
    deleted_count = 0
    for lead_id in request.lead_ids:
        db_lead = crud.get_lead(db, lead_id=lead_id)
        if db_lead:
            crud.delete_lead(db=db, lead_id=lead_id, deleter_id=current_user.id)
            deleted_count += 1
    return {"detail": f"Successfully deleted {deleted_count} leads"}

@router.put("/{lead_id}", response_model=schemas.LeadOut)
def update_lead(
    lead_id: int,
    lead_data: schemas.LeadUpdate,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    updated_lead = crud.update_lead(db=db, lead_id=lead_id, lead_data=lead_data, updater_id=current_user.id)
    return updated_lead

@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    current_user: User = Depends(auth_utils.require_manager_or_admin),
    db: Session = Depends(get_db)
):
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    crud.delete_lead(db=db, lead_id=lead_id, deleter_id=current_user.id)
    return {"detail": "Lead deleted successfully"}

@router.post("/{lead_id}/claim", response_model=schemas.LeadOut)
def claim_lead(
    lead_id: int,
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    lead_update = schemas.LeadUpdate(claimed_by_id=current_user.id, status="Contacted")
    updated_lead = crud.update_lead(db=db, lead_id=lead_id, lead_data=lead_update, updater_id=current_user.id)
    crud.log_activity(db, "CLAIM_LEAD", current_user.id, f"Claimed lead '{db_lead.project_name}' (ID: {lead_id})")
    return updated_lead

@router.post("/{lead_id}/assign", response_model=schemas.LeadOut)
def assign_lead(
    lead_id: int,
    assignee_id: int,
    current_user: User = Depends(auth_utils.require_manager_or_admin),
    db: Session = Depends(get_db)
):
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    db_assignee = crud.get_user(db, user_id=assignee_id)
    if not db_assignee:
        raise HTTPException(status_code=404, detail="Assignee user not found")
        
    lead_update = schemas.LeadUpdate(assigned_to_id=assignee_id)
    updated_lead = crud.update_lead(db=db, lead_id=lead_id, lead_data=lead_update, updater_id=current_user.id)
    crud.log_activity(db, "ASSIGN_LEAD", current_user.id, f"Assigned lead '{db_lead.project_name}' (ID: {lead_id}) to user {db_assignee.username}")
    return updated_lead
