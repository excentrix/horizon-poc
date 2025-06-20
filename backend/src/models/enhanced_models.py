# backend/src/models/enhanced_models.py
from sqlmodel import SQLModel, Field, Relationship, Column, String, DateTime, Text, Float
from pgvector.sqlalchemy import Vector
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid

def generate_id() -> str:
    return str(uuid.uuid4())

class ConversationMemory(SQLModel, table=True):
    __tablename__ = "conversation_memories"
    
    id: str = Field(default_factory=generate_id, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    session_id: Optional[str] = Field(foreign_key="chat_sessions.id", index=True)
    memory_type: str = Field(index=True)  # facts, preferences, patterns, goals
    content: str = Field(sa_column=Column(Text))
    meta: Optional[str] = Field(sa_column=Column(Text))  # JSON metadata
    embedding: Optional[List[float]] = Field(sa_column=Column(Vector(1536)))
    confidence: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SessionSummary(SQLModel, table=True):
    __tablename__ = "session_summaries"
    
    id: str = Field(default_factory=generate_id, primary_key=True)
    session_id: str = Field(foreign_key="chat_sessions.id", unique=True, index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    summary: str = Field(sa_column=Column(Text))
    key_topics: str = Field(sa_column=Column(Text))  # JSON array
    facts_extracted: str = Field(sa_column=Column(Text))  # JSON object
    emotional_tone: Optional[str] = None
    learning_progress: Optional[str] = Field(sa_column=Column(Text))  # JSON object
    message_count: int = Field(default=0)
    duration_minutes: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessingJob(SQLModel, table=True):
    __tablename__ = "processing_jobs"
    
    id: str = Field(default_factory=generate_id, primary_key=True)
    job_type: str = Field(index=True)  # session_analysis, fact_extraction, memory_consolidation
    status: str = Field(default="pending", index=True)  # pending, processing, completed, failed
    session_id: Optional[str] = Field(foreign_key="chat_sessions.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    input_data: Optional[str] = Field(sa_column=Column(Text))  # JSON input
    result_data: Optional[str] = Field(sa_column=Column(Text))  # JSON result
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced User model (add to existing User class)
class EnhancedUserProfile(SQLModel):
    # Conversation preferences
    conversation_style: Optional[str] = None  # formal, casual, technical, friendly
    response_length_preference: Optional[str] = None  # short, medium, detailed
    learning_style: Optional[str] = None  # visual, auditory, kinesthetic, reading
    
    # Memory metadata
    last_memory_update: Optional[datetime] = None
    memory_version: int = Field(default=1)
    total_conversations: int = Field(default=0)
    
    # AI interaction patterns
    preferred_topics: Optional[str] = None  # JSON array
    conversation_patterns: Optional[str] = None  # JSON object
    engagement_level: Optional[str] = None  # high, medium, low