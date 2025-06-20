# backend/src/models/core.py
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
import os
import json

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[int] = None
    goal: Optional[str] = None
    biggest_worry: Optional[str] = None
    fav_subject: Optional[str] = None
    skills: Optional[str] = None  # JSON string for now
    gpa: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    sessions: List["ChatSession"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str = Field(default="New Conversation")
    summary: Optional[str] = None
    context: Optional[str] = None  # JSON string for conversation context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.id")
    content: str
    is_user: bool = Field(default=True)
    meta: Optional[str] = None  # JSON for storing AI reasoning, facts extracted, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session: ChatSession = Relationship(back_populates="messages")

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium")  # low, medium, high, urgent
    status: str = Field(default="pending")  # pending, in_progress, completed, cancelled
    tags: Optional[str] = None  # JSON array of tags
    created_by_ai: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Relationships  
    user: User = Relationship(back_populates="tasks")

class FactExtraction(SQLModel, table=True):
    __tablename__ = "fact_extractions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    session_id: UUID = Field(foreign_key="chat_sessions.id")
    facts: str  # JSON string of extracted facts
    confidence: float = Field(default=0.0)  # AI confidence in extraction
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Database connection with Neon
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True if os.getenv("ENV") == "development" else False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Database service functions
class DatabaseService:
    @staticmethod
    def create_user(email: str, name: str = None) -> User:
        with Session(engine) as session:
            # Check if user already exists
            existing_user = session.exec(select(User).where(User.email == email)).first()
            if existing_user:
                return existing_user
                
            user = User(email=email, name=name)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        with Session(engine) as session:
            return session.exec(select(User).where(User.email == email)).first()
    
    @staticmethod
    def update_user_profile(user_id: UUID, **kwargs) -> Optional[User]:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                user.updated_at = datetime.utcnow()
                session.add(user)
                session.commit()
                session.refresh(user)
                return user
            return None
    
    @staticmethod
    def create_chat_session(user_id: UUID, title: str = "New Conversation") -> ChatSession:
        with Session(engine) as session:
            chat_session = ChatSession(user_id=user_id, title=title)
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            return chat_session
    
    @staticmethod
    def add_message(session_id: UUID, content: str, is_user: bool, metadata: dict = None) -> ChatMessage:
        with Session(engine) as session:
            message = ChatMessage(
                session_id=session_id,
                content=content,
                is_user=is_user,
                metadata=json.dumps(metadata) if metadata else None
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message
    
    @staticmethod
    def create_task(user_id: UUID, title: str, description: str = None, due_date: datetime = None, created_by_ai: bool = False) -> Task:
        with Session(engine) as session:
            task = Task(
                user_id=user_id,
                title=title,
                description=description,
                due_date=due_date,
                created_by_ai=created_by_ai
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        
    @staticmethod
    def create_task(user_id: UUID, title: str, description: str = None, due_date: datetime = None, created_by_ai: bool = False) -> Task:
        with Session(engine) as session:
            task = Task(
                user_id=user_id,
                title=title,
                description=description,
                due_date=due_date,
                created_by_ai=created_by_ai
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
    
    @staticmethod
    def get_user_tasks(user_id: UUID, limit: int = 10) -> List[Task]:
        with Session(engine) as session:
            return session.exec(
                select(Task)
                .where(Task.user_id == user_id)
                .order_by(Task.created_at.desc())
                .limit(limit)
            ).all()
    
    @staticmethod
    def get_user_sessions(user_id: UUID, limit: int = 5) -> List[ChatSession]:
        with Session(engine) as session:
            return session.exec(
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
            ).all()