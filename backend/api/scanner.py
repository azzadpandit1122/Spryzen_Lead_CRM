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
    if request.stream:
        import queue
        import threading
        import json
        from fastapi.responses import StreamingResponse
        
        log_queue = queue.Queue()
        
        def log_callback(msg: str):
            log_queue.put(msg)
            
        def run_scanner():
            try:
                leads_to_create, logs = generate_leads_and_logs(
                    db=db,
                    keywords=request.keywords,
                    sources=request.sources,
                    date_filter=request.date_filter,
                    time_filter=request.time_filter,
                    location=request.location,
                    search_engine=request.search_engine,
                    target_count=request.target_count,
                    country=request.country,
                    log_callback=log_callback
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
                
                log_queue.put({
                    "success": True,
                    "leads_collected": len(created_leads),
                    "leads": [json.loads(schemas.LeadOut.from_orm(l).json()) for l in created_leads]
                })
            except Exception as e:
                log_queue.put({"success": False, "error": str(e)})
                
        thread = threading.Thread(target=run_scanner)
        thread.start()
        
        def event_generator():
            while True:
                try:
                    item = log_queue.get(timeout=30.0)
                    if isinstance(item, dict):
                        yield json.dumps(item) + "\n"
                        break
                    else:
                        yield json.dumps({"log": item}) + "\n"
                except queue.Empty:
                    yield json.dumps({"log": "[INFO] Keep-alive handshake active..."}) + "\n"
                    
        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
        
    else:
        # Run scanner engine simulation synchronously (backward compatible)
        leads_to_create, logs = generate_leads_and_logs(
            db=db,
            keywords=request.keywords,
            sources=request.sources,
            date_filter=request.date_filter,
            time_filter=request.time_filter,
            location=request.location,
            search_engine=request.search_engine,
            target_count=request.target_count,
            country=request.country
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
