# backend/src/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form , Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import asyncio
from uuid import UUID
import uuid
import sentry_sdk
from sqlalchemy.orm import Session  # Import Session from SQLAlchemy

# Enable or disable Sentry error tracking
sentry_enabled = False  # Set to True if Sentry is configured

from models.core import DatabaseService, get_session, User, ChatSession, Task, engine
from chains.horizon_chat import HorizonChatChain

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_email: str  # Temporary until auth is implemented

class CreateSessionRequest(BaseModel):
    user_email: str
    title: Optional[str] = "New Conversation"

class FactsResponse(BaseModel):
    profile: Dict[str, Any]
    tasks: List[Dict[str, Any]]
    sessions: List[Dict[str, Any]]

# Initialize chat chain
chat_chain = HorizonChatChain()

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Stream chat responses with real-time fact extraction and task creation."""
    
    try:
        # Get or create user
        user = DatabaseService.get_user_by_email(request.user_email)
        if not user:
            user = DatabaseService.create_user(request.user_email)
        
        # Get or create session
        session = None
        if request.session_id:
            try:
                session_uuid = UUID(request.session_id)
                # TODO: Implement session retrieval and validation
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        if not session:
            session = DatabaseService.create_chat_session(user.id)
        
        # Store user message
        user_message = DatabaseService.add_message(
            session.id, 
            request.message, 
            is_user=True
        )
        
        # Build user context
        user_context = {
            "name": user.name,
            "email": user.email,
            "degree": user.degree,
            "year": user.year,
            "goal": user.goal,
            "biggest_worry": user.biggest_worry,
            "fav_subject": user.fav_subject,
            "skills": json.loads(user.skills) if user.skills else [],
            "gpa": user.gpa
        }
        
        async def generate_response():
            ai_response_content = ""
            
            try:
                async for chunk in chat_chain.chat_stream(
                    request.message,
                    user_context=user_context,
                    conversation_history=[]  # TODO: Implement history retrieval
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Collect AI response content
                    if chunk.get("type") == "token":
                        ai_response_content += chunk.get("data", "")
                    
                    # Handle fact updates
                    elif chunk.get("type") == "facts_update":
                        facts = chunk.get("data", {})
                        facts = {k: v for k, v in facts.items() if v is not None}
                        if facts:
                            try:
                                DatabaseService.update_user_profile(user.id, **facts)
                            except Exception as e:
                                print(f"Failed to update user profile: {e}")
                                # Continue processing, don't fail the entire stream
                    
                    # Handle task creation
                    elif chunk.get("type") == "task_created":
                        task_data = chunk.get("data", {})
                        try:
                            DatabaseService.create_task(
                                user.id,
                                title=task_data.get("title", "Untitled Task"),
                                description=task_data.get("description"),
                                created_by_ai=True
                            )
                        except Exception as e:
                            print(f"Failed to create task: {e}")
                            # Continue processing
                    
                    await asyncio.sleep(0.01)
                
                # Store AI response
                if ai_response_content.strip():
                    try:
                        DatabaseService.add_message(
                            session.id,
                            ai_response_content,
                            is_user=False,
                            # meta={"session_id": str(session.id)}
                        )
                    except Exception as e:
                        print(f"Failed to store AI message: {e}")
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'stream_end', 'session_id': str(session.id)})}\n\n"
                
            except Exception as e:
                print(f"Stream generation error: {e}")
                # Log to Sentry if available
                if sentry_enabled:
                    sentry_sdk.capture_exception(e)
                
                error_response = {
                    "type": "error",
                    "data": {
                        "message": "I apologize, but I encountered an error while processing your message. Please try again.",
                        "error_code": "STREAM_ERROR"
                    }
                }
                yield f"data: {json.dumps(error_response)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected chat endpoint error: {e}")
        if sentry_enabled:
            sentry_sdk.capture_exception(e)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred while processing your chat request.",
                "error_code": "CHAT_ERROR"
            }
        )

@router.post("/chat/session")
async def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    user = DatabaseService.get_user_by_email(request.user_email)
    if not user:
        user = DatabaseService.create_user(request.user_email)
    
    session = DatabaseService.create_chat_session(user.id, request.title)
    
    return {
        "session_id": str(session.id),
        "title": session.title,
        "created_at": session.created_at.isoformat()
    }

@router.get("/facts")
async def get_user_facts(user_email: str = Query(..., description="User email address")):
    """Get user profile, tasks, and session summaries."""
    try:
        user = DatabaseService.get_user_by_email(user_email)
        if not user:
            # Return empty data for new users
            return FactsResponse(profile={}, tasks=[], sessions=[])
        
        # Build profile
        profile = {
            "name": user.name,
            "email": user.email,
            "degree": user.degree,
            "year": user.year,
            "goal": user.goal,
            "biggest_worry": user.biggest_worry,
            "fav_subject": user.fav_subject,
            "skills": json.loads(user.skills) if user.skills else [],
            "gpa": user.gpa,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        
        # Get tasks using the new method
        tasks = []
        try:
            user_tasks = DatabaseService.get_user_tasks(user.id, limit=10)
            tasks = [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_by_ai": task.created_by_ai,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in user_tasks
            ]
        except Exception as e:
            print(f"Error fetching tasks: {e}")
        
        # Get sessions using the new method
        sessions = []
        try:
            user_sessions = DatabaseService.get_user_sessions(user.id, limit=5)
            sessions = [
                {
                    "id": str(sess.id),
                    "title": sess.title,
                    "summary": sess.summary or f"{sess.created_at.strftime('%b %d')}",
                    "created_at": sess.created_at.isoformat(),
                    "updated_at": sess.updated_at.isoformat()
                }
                for sess in user_sessions
            ]
        except Exception as e:
            print(f"Error fetching sessions: {e}")
        
        return FactsResponse(
            profile=profile,
            tasks=tasks,
            sessions=sessions
        )
        
    except Exception as e:
        print(f"Facts API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user facts: {str(e)}"
        )

@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_email: str = Form(...)
):
    """Upload and parse resume for profile extraction."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # TODO: Implement PDF parsing with PyMuPDF
        # For now, return mock data
        extracted_data = {
            "skills": ["Python", "Machine Learning", "Data Analysis"],
            "degree": "Computer Science",
            "gpa": 8.5,
            "experience": ["Internship at Tech Corp", "Project Lead at University"]
        }
        
        # Update user profile
        user = DatabaseService.get_user_by_email(user_email)
        if user:
            DatabaseService.update_user_profile(
                user.id,
                skills=json.dumps(extracted_data["skills"]),
                degree=extracted_data["degree"],
                gpa=extracted_data["gpa"]
            )
        
        return {
            "message": "Resume uploaded and parsed successfully",
            "extracted_data": extracted_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume processing error: {str(e)}"
        )