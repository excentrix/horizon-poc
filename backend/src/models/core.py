# backend/src/models/core.py (fix ID generation for NextAuth compatibility)
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
    create_engine,
    Session,
    select,
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
)
from datetime import datetime, UTC
from typing import Optional, List
import os
import json

from dotenv import load_dotenv

load_dotenv()

from .enhanced_models import *


# NextAuth tables with proper ID generation
class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: str = Field(primary_key=True)  # NextAuth will handle ID generation
    userId: str = Field(foreign_key="users.id", index=True)
    type: str
    provider: str
    providerAccountId: str = Field(index=True)
    refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    access_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    expires_at: Optional[int] = Field(default=None)
    token_type: Optional[str] = Field(default=None)
    scope: Optional[str] = Field(default=None)
    id_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    session_state: Optional[str] = Field(default=None)


class NextAuthSession(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True)  # NextAuth will handle ID generation
    sessionToken: str = Field(unique=True, index=True)
    userId: str = Field(foreign_key="users.id", index=True)
    expires: datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)  # NextAuth will handle ID generation
    name: Optional[str] = Field(default=None)
    email: str = Field(unique=True, index=True)
    emailVerified: Optional[datetime] = Field(default=None)
    image: Optional[str] = Field(default=None)

    # Horizon-specific fields
    degree: Optional[str] = Field(default=None)
    year: Optional[int] = Field(default=None)
    goal: Optional[str] = Field(default=None)
    biggest_worry: Optional[str] = Field(default=None)
    fav_subject: Optional[str] = Field(default=None)
    skills: Optional[str] = Field(default=None)
    gpa: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships to our custom tables
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")


class VerificationToken(SQLModel, table=True):
    __tablename__ = "verification_tokens"

    identifier: str = Field(primary_key=True)
    token: str = Field(primary_key=True, unique=True, index=True)
    expires: datetime


# Our custom Horizon tables (with default ID generation)
def generate_id() -> str:
    """Generate a string ID for our custom tables."""
    import uuid

    return str(uuid.uuid4())


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: str = Field(default_factory=generate_id, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str = Field(default="New Conversation")
    summary: Optional[str] = Field(default=None)
    context: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: str = Field(default_factory=generate_id, primary_key=True)
    session_id: str = Field(foreign_key="chat_sessions.id")
    content: str
    is_user: bool = Field(default=True)
    meta: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: ChatSession = Relationship(back_populates="messages")


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: str = Field(default_factory=generate_id, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str
    description: Optional[str] = Field(default=None)
    due_date: Optional[datetime] = Field(default=None)
    priority: str = Field(default="medium")
    status: str = Field(default="pending")
    tags: Optional[str] = Field(default=None)
    created_by_ai: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    user: User = Relationship(back_populates="tasks")


class FactExtraction(SQLModel, table=True):
    __tablename__ = "fact_extractions"

    id: str = Field(default_factory=generate_id, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    session_id: str = Field(foreign_key="chat_sessions.id")
    facts: str
    confidence: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Database setup
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL or NEON_DATABASE_URL must be set")

engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("ENV") == "development" else False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)


def create_db_and_tables():
    """Create all database tables."""
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        print("📋 NextAuth tables: users, accounts, sessions, verification_tokens")
        print(
            "📋 Horizon tables: chat_sessions, chat_messages, tasks, fact_extractions"
        )
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


def get_session():
    with Session(engine) as session:
        yield session


# DatabaseService remains the same...
class DatabaseService:
    @staticmethod
    def create_user(email: str, name: str = None, image: str = None) -> User:
        """Create a new user or return existing user."""
        with Session(engine) as session:
            try:
                existing_user = session.exec(
                    select(User).where(User.email == email)
                ).first()
                if existing_user:
                    return existing_user

                # Generate ID manually for our database service
                import uuid

                user = User(id=str(uuid.uuid4()), email=email, name=name, image=image)
                session.add(user)
                session.commit()
                session.refresh(user)
                return user
            except Exception as e:
                session.rollback()
                print(f"Error creating user: {e}")
                raise

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email address."""
        with Session(engine) as session:
            try:
                return session.exec(select(User).where(User.email == email)).first()
            except Exception as e:
                print(f"Error getting user by email: {e}")
                return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        with Session(engine) as session:
            try:
                return session.get(User, user_id)
            except Exception as e:
                print(f"Error getting user by ID: {e}")
                return None

    @staticmethod
    def update_user_profile(user_id: str, **kwargs) -> Optional[User]:
        """Update user profile with given fields."""
        with Session(engine) as session:
            try:
                user = session.get(User, user_id)
                if user:
                    for key, value in kwargs.items():
                        if hasattr(user, key) and value is not None:
                            setattr(user, key, value)
                    user.updated_at = datetime.now(UTC)
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    return user
                return None
            except Exception as e:
                session.rollback()
                print(f"Error updating user profile: {e}")
                return None

    @staticmethod
    def create_chat_session(
        user_id: str, title: str = "New Conversation"
    ) -> ChatSession:
        with Session(engine) as session:
            try:
                chat_session = ChatSession(user_id=user_id, title=title)
                session.add(chat_session)
                session.commit()
                session.refresh(chat_session)
                return chat_session
            except Exception as e:
                session.rollback()
                print(f"Error creating chat session: {e}")
                raise

    @staticmethod
    def add_message(
        session_id: str, content: str, is_user: bool, metadata: dict = None
    ) -> ChatMessage:
        with Session(engine) as session:
            try:
                message = ChatMessage(
                    session_id=session_id,
                    content=content,
                    is_user=is_user,
                    meta=json.dumps(metadata) if metadata else None,
                )
                session.add(message)
                session.commit()
                session.refresh(message)
                return message
            except Exception as e:
                session.rollback()
                print(f"Error adding message: {e}")
                raise

    @staticmethod
    def create_task(
        user_id: str,
        title: str,
        description: str = None,
        due_date: datetime = None,
        created_by_ai: bool = False,
    ) -> Task:
        with Session(engine) as session:
            try:
                task = Task(
                    user_id=user_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    created_by_ai=created_by_ai,
                )
                session.add(task)
                session.commit()
                session.refresh(task)
                return task
            except Exception as e:
                session.rollback()
                print(f"Error creating task: {e}")
                raise

    @staticmethod
    def get_user_tasks(user_id: str, limit: int = 10) -> List[Task]:
        with Session(engine) as session:
            try:
                return session.exec(
                    select(Task)
                    .where(Task.user_id == user_id)
                    .order_by(Task.created_at.desc())
                    .limit(limit)
                ).all()
            except Exception as e:
                print(f"Error getting user tasks: {e}")
                return []

    @staticmethod
    def get_user_sessions(user_id: str, limit: int = 5) -> List[ChatSession]:
        with Session(engine) as session:
            try:
                return session.exec(
                    select(ChatSession)
                    .where(ChatSession.user_id == user_id)
                    .order_by(ChatSession.updated_at.desc())
                    .limit(limit)
                ).all()
            except Exception as e:
                print(f"Error getting user sessions: {e}")
                return []

    @staticmethod
    def get_session_messages(session_id: str) -> List[ChatMessage]:
        """Get all messages for a session."""
        with Session(engine) as session:
            messages = session.exec(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
            ).all()
            return list(messages)

    @staticmethod
    def get_conversation_memory(memory_id: str) -> Optional[ConversationMemory]:
        """Get a specific conversation memory."""
        with Session(engine) as session:
            memory = session.get(ConversationMemory, memory_id)
            return memory

    @staticmethod
    def create_processing_job(job: ProcessingJob) -> ProcessingJob:
        """Create a new processing job."""
        with Session(engine) as session:
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    @staticmethod
    def complete_processing_job(job_id: str, result_data: Dict[str, Any]) -> bool:
        """Mark a processing job as completed."""
        with Session(engine) as session:
            job = session.get(ProcessingJob, job_id)
            if job:
                job.status = "completed"
                job.completed_at = datetime.now(UTC)
                job.result_data = json.dumps(result_data)
                session.commit()
                return True
            return False

    @staticmethod
    def fail_processing_job(job_id: str, error_message: str) -> bool:
        """Mark a processing job as failed."""
        with Session(engine) as session:
            job = session.get(ProcessingJob, job_id)
            if job:
                job.status = "failed"
                job.completed_at = datetime.now(UTC)
                job.error_message = error_message
                session.commit()
                return True
            return False

    @staticmethod
    def create_session_summary(
        session_id: str,
        user_id: str,
        summary: str,
        facts_extracted: Dict[str, Any],
        memory_id: str = None,
    ) -> SessionSummary:
        """Create a session summary record."""
        with Session(engine) as session_db:
            summary_record = SessionSummary(
                session_id=session_id,
                user_id=user_id,
                summary=summary,
                facts_extracted=json.dumps(facts_extracted),
                key_topics=json.dumps([]),  # Could be enhanced
                emotional_tone="neutral",
            )
            session_db.add(summary_record)
            session_db.commit()
            session_db.refresh(summary_record)
            return summary_record

    @staticmethod
    def update_user_profile(user_id: str, **updates) -> bool:
        """Update user profile with new information."""
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user:
                for field, value in updates.items():
                    if hasattr(user, field):
                        setattr(user, field, value)
                session.commit()
                return True
            return False

    @staticmethod
    def get_active_users_since(cutoff_date: datetime) -> List[User]:
        """Get users who have been active since the cutoff date."""
        with Session(engine) as session:
            # Get users who have chat sessions since cutoff
            active_user_ids = session.exec(
                select(ChatSession.user_id)
                .where(ChatSession.created_at > cutoff_date)
                .distinct()
            ).all()

            if not active_user_ids:
                return []

            users = session.exec(select(User).where(User.id.in_(active_user_ids))).all()

            return list(users)
