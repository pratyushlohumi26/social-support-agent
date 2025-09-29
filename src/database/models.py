"""
Database models for UAE Social Support AI System
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Application(Base):
    """Application database model"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), unique=True, index=True)
    applicant_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    support_type = Column(String(50))
    status = Column(String(50), default="submitted")
    priority = Column(String(20), default="medium")

    # UAE-specific fields
    emirates_id = Column(String(20), index=True)
    emirate = Column(String(30))
    family_size = Column(Integer)
    monthly_income = Column(Float)

    # Application data as JSON
    application_data = Column(JSON)

    # Processing results
    processing_results = Column(JSON)
    decision_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(Base):
    """Document database model"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), index=True)
    document_type = Column(String(50))
    filename = Column(String(200))
    file_path = Column(String(500))
    file_size = Column(Integer)

    # Processing results
    extraction_data = Column(JSON)
    confidence_score = Column(Float)
    validation_status = Column(String(20))

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    application_id = Column(String(50), index=True)

    # Chat data
    messages = Column(JSON)
    context = Column(JSON)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

class ProcessingLog(Base):
    """Processing log model"""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), index=True)
    agent_name = Column(String(50))
    processing_stage = Column(String(50))

    # Processing data
    input_data = Column(JSON)
    output_data = Column(JSON)
    success = Column(Boolean)
    error_message = Column(Text)
    duration_ms = Column(Integer)

    # Timestamp
    processed_at = Column(DateTime, default=datetime.utcnow)
