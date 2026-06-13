import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="sales_executive")  # admin, sales_manager, sales_executive
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    claimed_leads = relationship("Lead", foreign_keys="[Lead.claimed_by_id]", back_populates="claimed_by")
    assigned_leads = relationship("Lead", foreign_keys="[Lead.assigned_to_id]", back_populates="assigned_to")
    reminders = relationship("Reminder", back_populates="assigned_user")
    logs = relationship("AuditLog", back_populates="user")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True, nullable=False)
    project_description = Column(Text, nullable=True)
    source = Column(String, nullable=False)  # LinkedIn, Instagram, X (Twitter), Google Maps
    contact_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email_address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    location = Column(String, nullable=True)
    collection_date = Column(Date, nullable=False)
    collection_time = Column(Time, nullable=False)
    status = Column(String, default="New Lead")  # New Lead, Contacted, Interested, Follow Up Required, Proposal Sent, Negotiation, Won, Lost, Closed
    priority = Column(String, default="Normal Opportunity")  # Best Opportunity, Better Opportunity, Normal Opportunity, Low Priority
    
    claimed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    claimed_by = relationship("User", foreign_keys=[claimed_by_id], back_populates="claimed_leads")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_leads")
    reminders = relationship("Reminder", back_populates="lead", cascade="all, delete-orphan")

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    note = Column(String, nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="reminders")
    assigned_user = relationship("User", back_populates="reminders")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="logs")

class ScannerConfig(Base):
    __tablename__ = "scanner_configs"

    id = Column(Integer, primary_key=True, index=True)
    keywords = Column(Text, nullable=False)  # Comma-separated or JSON string of keywords
    sources = Column(Text, nullable=False)   # Comma-separated list of sources
    schedule_interval = Column(String, default="daily")  # manual, hourly, daily, weekly
    active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
