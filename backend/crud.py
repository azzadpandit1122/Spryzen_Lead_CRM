from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import date, time, datetime
from typing import Optional, List
from backend.models import User, Lead, Reminder, AuditLog, ScannerConfig
from backend.schemas import UserCreate, UserUpdate, LeadCreate, LeadUpdate, ReminderCreate, ReminderUpdate, ScannerConfigCreate
from backend.auth_utils import get_password_hash

# Audit log helper
def log_activity(db: Session, action: str, user_id: Optional[int], details: str):
    db_log = AuditLog(action=action, user_id=user_id, details=details, timestamp=datetime.utcnow())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate, creator_id: Optional[int] = None):
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        password_hash=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log_activity(db, "CREATE_USER", creator_id, f"Created user {user.username} with role {user.role}")
    return db_user

def update_user(db: Session, user_id: int, user_data: UserUpdate, updater_id: Optional[int] = None):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_dict = user_data.dict(exclude_unset=True)
    if "password" in update_dict and update_dict["password"]:
        db_user.password_hash = get_password_hash(update_dict.pop("password"))
        
    for key, value in update_dict.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    log_activity(db, "UPDATE_USER", updater_id, f"Updated user profile for {db_user.username}")
    return db_user

def delete_user(db: Session, user_id: int, deleter_id: Optional[int] = None):
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    username = db_user.username
    db.delete(db_user)
    db.commit()
    log_activity(db, "DELETE_USER", deleter_id, f"Deleted user account {username}")
    return True

# Lead CRUD
def get_lead(db: Session, lead_id: int):
    return db.query(Lead).filter(Lead.id == lead_id).first()

def get_leads(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    keyword: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    assigned_to_id: Optional[int] = None,
    claimed_by_id: Optional[int] = None
):
    query = db.query(Lead)
    
    if source:
        query = query.filter(Lead.source == source)
    if status:
        query = query.filter(Lead.status == status)
    if priority:
        query = query.filter(Lead.priority == priority)
    if assigned_to_id:
        query = query.filter(Lead.assigned_to_id == assigned_to_id)
    if claimed_by_id:
        query = query.filter(Lead.claimed_by_id == claimed_by_id)
    if date_from:
        query = query.filter(Lead.collection_date >= date_from)
    if date_to:
        query = query.filter(Lead.collection_date <= date_to)
    if keyword:
        # Search in project name and description
        search_filter = or_(
            Lead.project_name.ilike(f"%{keyword}%"),
            Lead.project_description.ilike(f"%{keyword}%"),
            Lead.location.ilike(f"%{keyword}%")
        )
        query = query.filter(search_filter)
        
    return query.order_by(Lead.collection_date.desc(), Lead.collection_time.desc()).offset(skip).limit(limit).all()

def create_lead(db: Session, lead: LeadCreate, creator_id: Optional[int] = None):
    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    log_activity(db, "CREATE_LEAD", creator_id, f"Created/Collected lead: '{lead.project_name}' from {lead.source}")
    return db_lead

def update_lead(db: Session, lead_id: int, lead_data: LeadUpdate, updater_id: Optional[int] = None):
    db_lead = get_lead(db, lead_id)
    if not db_lead:
        return None
    
    details = []
    for key, value in lead_data.dict(exclude_unset=True).items():
        old_val = getattr(db_lead, key)
        if old_val != value:
            details.append(f"{key}: {old_val} -> {value}")
        setattr(db_lead, key, value)
        
    db.commit()
    db.refresh(db_lead)
    
    if details:
        log_activity(db, "UPDATE_LEAD", updater_id, f"Updated lead '{db_lead.project_name}' (ID: {db_lead.id}). Changes: {', '.join(details)}")
    return db_lead

def delete_lead(db: Session, lead_id: int, deleter_id: Optional[int] = None):
    db_lead = get_lead(db, lead_id)
    if not db_lead:
        return False
    project_name = db_lead.project_name
    db.delete(db_lead)
    db.commit()
    log_activity(db, "DELETE_LEAD", deleter_id, f"Deleted lead '{project_name}' (ID: {lead_id})")
    return True

# Reminder CRUD
def get_reminder(db: Session, reminder_id: int):
    return db.query(Reminder).filter(Reminder.id == reminder_id).first()

def get_reminders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    assigned_user_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    is_completed: Optional[bool] = None
):
    query = db.query(Reminder)
    if assigned_user_id:
        query = query.filter(Reminder.assigned_user_id == assigned_user_id)
    if lead_id:
        query = query.filter(Reminder.lead_id == lead_id)
    if is_completed is not None:
        query = query.filter(Reminder.is_completed == is_completed)
        
    return query.order_by(Reminder.date.asc(), Reminder.time.asc()).offset(skip).limit(limit).all()

def create_reminder(db: Session, reminder: ReminderCreate, creator_id: Optional[int] = None):
    db_reminder = Reminder(**reminder.dict())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    log_activity(db, "CREATE_REMINDER", creator_id, f"Created reminder (ID: {db_reminder.id}) for Lead ID {reminder.lead_id}")
    return db_reminder

def update_reminder(db: Session, reminder_id: int, reminder_data: ReminderUpdate, updater_id: Optional[int] = None):
    db_reminder = get_reminder(db, reminder_id)
    if not db_reminder:
        return None
    
    for key, value in reminder_data.dict(exclude_unset=True).items():
        setattr(db_reminder, key, value)
        
    db.commit()
    db.refresh(db_reminder)
    log_activity(db, "UPDATE_REMINDER", updater_id, f"Updated reminder (ID: {db_reminder.id}). Status is_completed: {db_reminder.is_completed}")
    return db_reminder

def delete_reminder(db: Session, reminder_id: int, deleter_id: Optional[int] = None):
    db_reminder = get_reminder(db, reminder_id)
    if not db_reminder:
        return False
    db.delete(db_reminder)
    db.commit()
    log_activity(db, "DELETE_REMINDER", deleter_id, f"Deleted reminder (ID: {reminder_id})")
    return True

# Audit Log
def get_audit_logs(db: Session, limit: int = 50):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

# Scanner Config CRUD
def get_scanner_config(db: Session):
    config = db.query(ScannerConfig).first()
    if not config:
        # Create a default configuration
        config = ScannerConfig(
            keywords="Web Development,Mobile App Development,AI Development,SEO Services,Digital Marketing",
            sources="LinkedIn,Instagram,X (Twitter),Google Maps,Upwork,Reddit,Wellfound,GitHub",
            schedule_interval="daily",
            active=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def update_scanner_config(db: Session, config_data: ScannerConfigCreate, updater_id: Optional[int] = None):
    config = get_scanner_config(db)
    config.keywords = config_data.keywords
    config.sources = config_data.sources
    config.schedule_interval = config_data.schedule_interval
    config.active = config_data.active
    db.commit()
    db.refresh(config)
    log_activity(db, "UPDATE_SCANNER_CONFIG", updater_id, "Updated project scanner configuration settings")
    return config
