from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas, auth_utils
from backend.models import User
from backend.scanner.engine import generate_leads_and_logs

router = APIRouter(prefix="/api/scanner", tags=["scanner"])

@router.get("/config", response_model=schemas.ScannerConfigOut)
def read_scanner_config(
    current_user: User = Depends(auth_utils.require_manager_or_admin),
    db: Session = Depends(get_db)
):
    return crud.get_scanner_config(db)

@router.post("/config", response_model=schemas.ScannerConfigOut)
def update_scanner_config(
    config_data: schemas.ScannerConfigCreate,
    current_user: User = Depends(auth_utils.require_admin),
    db: Session = Depends(get_db)
):
    return crud.update_scanner_config(db, config_data, updater_id=current_user.id)

@router.post("/scan")
def trigger_scan(
    request: schemas.ScanTriggerRequest,
    current_user: User = Depends(auth_utils.require_manager_or_admin),
    db: Session = Depends(get_db)
):
    # Run scanner engine simulation
    leads_to_create, logs = generate_leads_and_logs(
        db=db,
        keywords=request.keywords,
        sources=request.sources,
        date_filter=request.date_filter,
        time_filter=request.time_filter
    )
    
    created_leads = []
    # Save leads to DB
    for lead_data in leads_to_create:
        lead_schema = schemas.LeadCreate(**lead_data)
        created = crud.create_lead(db, lead_schema, creator_id=current_user.id)
        created_leads.append(created)
        
    # Update scanner config's last run timestamp
    config = crud.get_scanner_config(db)
    import datetime
    config.last_run = datetime.datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "leads_collected": len(created_leads),
        "logs": logs,
        "leads": [schemas.LeadOut.from_orm(l) for l in created_leads]
    }
