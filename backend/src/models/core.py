# backend/src/models/core.py
from sqlmodel import SQLModel, Field, create_engine, Session
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
import os

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[int] = None
    goal: Optional[str] = None
    biggest_worry: Optional[str] = None
    fav_subject: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Session(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str
    due: datetime
    done: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/horizon")
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session