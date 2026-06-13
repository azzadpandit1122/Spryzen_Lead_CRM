from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.database import get_db
from backend import crud, schemas, auth_utils
from backend.models import User, Lead, Reminder, AuditLog

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/dashboard")
def get_dashboard_metrics(
    current_user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # Total Leads
    total_leads = db.query(Lead).count()
    
    # Leads By Source
    leads_by_source_raw = db.query(Lead.source, func.count(Lead.id)).group_by(Lead.source).all()
    leads_by_source = {r[0]: r[1] for r in leads_by_source_raw}
    # Ensure all sources are present
    for src in ["LinkedIn", "Instagram", "X (Twitter)", "Google Maps"]:
        if src not in leads_by_source:
            leads_by_source[src] = 0
            
    # Leads By Status
    leads_by_status_raw = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    leads_by_status = {r[0]: r[1] for r in leads_by_status_raw}
    # Ensure key statuses are present
    standard_statuses = ["New Lead", "Contacted", "Interested", "Follow Up Required", "Proposal Sent", "Negotiation", "Won", "Lost", "Closed"]
    for status in standard_statuses:
        if status not in leads_by_status:
            leads_by_status[status] = 0
            
    # Conversion Rate calculation
    won_leads = leads_by_status.get("Won", 0)
    lost_leads = leads_by_status.get("Lost", 0)
    closed_leads = won_leads + lost_leads
    
    # Overall conversion rate: Won / Total Leads (or Won / Closed Leads)
    # Let's show Won / Total Leads as pipeline conversion rate, or Won / Closed if closed > 0
    pipeline_conversion_rate = round((won_leads / total_leads * 100), 1) if total_leads > 0 else 0.0
    closed_conversion_rate = round((won_leads / closed_leads * 100), 1) if closed_leads > 0 else 0.0
    
    # Leads by Date (Last 7 Days)
    today = datetime.now().date()
    leads_by_date = {}
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        leads_by_date[day_str] = 0
        
    leads_by_date_raw = db.query(Lead.collection_date, func.count(Lead.id)).filter(
        Lead.collection_date >= today - timedelta(days=6)
    ).group_by(Lead.collection_date).all()
    
    for r in leads_by_date_raw:
        day_str = r[0].strftime("%Y-%m-%d")
        if day_str in leads_by_date:
            leads_by_date[day_str] = r[1]
            
    # Sales Metrics
    # Calls Made: We can approximate this by counting leads that are "Contacted" or beyond, OR counting log events
    contacted_count = db.query(Lead).filter(Lead.status != "New Lead").count()
    
    # Follow-Ups Scheduled
    active_reminders = db.query(Reminder).filter(Reminder.is_completed == False).count()
    
    # Opportunities Won and Lost
    won_opportunities = won_leads
    lost_opportunities = lost_leads
    
    # Recent Activities (Audit Log)
    recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    serialized_logs = []
    for log in recent_logs:
        user_name = log.user.username if log.user else "System"
        serialized_logs.append({
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "username": user_name
        })
        
    return {
        "lead_metrics": {
            "total_leads": total_leads,
            "leads_by_source": leads_by_source,
            "leads_by_status": leads_by_status,
            "leads_by_date": leads_by_date,
            "pipeline_conversion_rate": pipeline_conversion_rate,
            "closed_conversion_rate": closed_conversion_rate
        },
        "sales_metrics": {
            "calls_made": contacted_count,
            "follow_ups_scheduled": active_reminders,
            "opportunities_won": won_opportunities,
            "opportunities_lost": lost_opportunities
        },
        "recent_activities": serialized_logs
    }
