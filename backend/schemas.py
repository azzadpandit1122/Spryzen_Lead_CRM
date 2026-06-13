from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date, time

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "sales_executive"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Lead schemas
class LeadBase(BaseModel):
    project_name: str
    project_description: Optional[str] = None
    source: str
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[EmailStr] = None
    website: Optional[str] = None
    location: Optional[str] = None
    collection_date: date
    collection_time: time
    status: str = "New Lead"
    priority: str = "Normal Opportunity"
    source_link: Optional[str] = None
    trust_score: Optional[int] = 85
    trust_factors: Optional[str] = None
    lead_source_detail: Optional[str] = None
    trust_source: Optional[str] = None
    authenticity_level: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    source: Optional[str] = None
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[EmailStr] = None
    website: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    claimed_by_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None
    source_link: Optional[str] = None
    trust_score: Optional[int] = None
    trust_factors: Optional[str] = None
    lead_source_detail: Optional[str] = None
    trust_source: Optional[str] = None
    authenticity_level: Optional[str] = None

class LeadOut(LeadBase):
    id: int
    claimed_by_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    notes: str
    created_at: datetime
    claimed_by: Optional[UserOut] = None
    assigned_to: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Reminder schemas
class ReminderBase(BaseModel):
    lead_id: int
    date: date
    time: time
    note: str
    assigned_user_id: int
    is_completed: bool = False

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[time] = None
    note: Optional[str] = None
    assigned_user_id: Optional[int] = None
    is_completed: Optional[bool] = None

class ReminderOut(ReminderBase):
    id: int
    created_at: datetime
    lead: Optional[LeadBase] = None
    assigned_user: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Audit log schemas
class AuditLogOut(BaseModel):
    id: int
    action: str
    user_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Scanner schemas
class ScannerConfigBase(BaseModel):
    keywords: str
    sources: str
    schedule_interval: str = "daily"
    active: bool = True

class ScannerConfigCreate(ScannerConfigBase):
    pass

class ScannerConfigOut(ScannerConfigBase):
    id: int
    last_run: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScanTriggerRequest(BaseModel):
    keywords: List[str]
    sources: List[str]
    date_filter: str = "Today"  # Today, Last 7 Days, Last 15 Days, Last 30 Days, Custom Date Range
    time_filter: str = "Last 24 Hours"  # Last 1 Hour, Last 6 Hours, Last 12 Hours, Last 24 Hours, Custom Time Range
    location: Optional[str] = "any"
    search_engine: Optional[str] = "Google"
    target_count: Optional[int] = 5
    country: Optional[str] = "Any"
