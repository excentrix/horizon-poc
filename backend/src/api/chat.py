# backend/src/api/chat.py (update with better error handling)
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Dict, Any
import json
import asyncio
import traceback
import os
from datetime import datetime

from models.core import DatabaseService, get_session, User, ChatSession, Task, Session, engine
from chains.horizon_chat import HorizonChatChain
from auth.dependencies import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")

    class Config:
        schema_extra = {
            "example": {
                "message": "Hello, can you help me with my studies?",
                "session_id": None
            }
        }

class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field("New Conversation", description="Session title")

class FactsResponse(BaseModel):
    profile: Dict[str, Any]
    tasks: List[Dict[str, Any]]
    sessions: List[Dict[str, Any]]

# Initialize chat chain
try:
    chat_chain = HorizonChatChain()
    print("✅ Chat chain initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize chat chain: {e}")
    chat_chain = None

@router.post("/chat/stream")
async def chat_stream_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Stream chat responses with real-time fact extraction and task creation."""
    
    try:
        # Get raw request body for debugging
        body = await request.body()
        print(f"📝 Raw request body: {body.decode()}")
        
        # Parse JSON manually with better error handling
        try:
            request_data = json.loads(body.decode())
            print(f"📋 Parsed request data: {request_data}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid JSON in request body: {str(e)}"
            )
        
        # Validate request data
        try:
            chat_request = ChatRequest(**request_data)
            print(f"✅ Valid chat request: {chat_request}")
        except ValidationError as e:
            print(f"❌ Validation error: {e}")
            raise HTTPException(
                status_code=422, 
                detail={
                    "message": "Invalid request data",
                    "errors": e.errors()
                }
            )
        
        # Check if chat chain is available
        if chat_chain is None:
            raise HTTPException(
                status_code=500,
                detail="Chat service is not available. Please check Azure OpenAI configuration."
            )
        
        print(f"👤 Current user: {current_user.email} (ID: {current_user.id})")
        
        # Get or create session
        session = None
        if chat_request.session_id:
            print(f"🔍 Looking for session: {chat_request.session_id}")
            # Validate session belongs to current user
            user_sessions = DatabaseService.get_user_sessions(current_user.id, limit=100)
            session = next((s for s in user_sessions if s.id == chat_request.session_id), None)
            
            if not session:
                print(f"❌ Session not found: {chat_request.session_id}")
                raise HTTPException(status_code=404, detail="Session not found")
            else:
                print(f"✅ Found session: {session.title}")
        
        if not session:
            print("📝 Creating new session")
            session = DatabaseService.create_chat_session(current_user.id)
            print(f"✅ Created session: {session.id}")
        
        # Store user message
        print(f"💬 Storing user message: {chat_request.message[:50]}...")
        try:
            user_message = DatabaseService.add_message(
                session.id, 
                chat_request.message, 
                is_user=True
            )
            print(f"✅ Stored user message: {user_message.id}")
        except Exception as e:
            print(f"❌ Failed to store user message: {e}")
            # Continue without storing for now
        
        # Build user context
        user_context = {
            "name": current_user.name,
            "email": current_user.email,
            "degree": current_user.degree,
            "year": current_user.year,
            "goal": current_user.goal,
            "biggest_worry": current_user.biggest_worry,
            "fav_subject": current_user.fav_subject,
            "skills": json.loads(current_user.skills) if current_user.skills else [],
            "gpa": current_user.gpa
        }
        print(f"👤 User context prepared: {user_context}")
        
        async def generate_response():
            ai_response_content = ""
            
            try:
                print("🤖 Starting AI response generation...")
                
                async for chunk in chat_chain.chat_stream(
                    chat_request.message,
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
                                DatabaseService.update_user_profile(current_user.id, **facts)
                                print(f"✅ Updated user profile with facts: {list(facts.keys())}")
                            except Exception as e:
                                print(f"❌ Failed to update user profile: {e}")
                    
                    # Handle task creation
                    elif chunk.get("type") == "task_created":
                        task_data = chunk.get("data", {})
                        try:
                            task = DatabaseService.create_task(
                                current_user.id,
                                title=task_data.get("title", "Untitled Task"),
                                description=task_data.get("description"),
                                created_by_ai=True
                            )
                            print(f"✅ Created task: {task.title}")
                        except Exception as e:
                            print(f"❌ Failed to create task: {e}")
                    
                    await asyncio.sleep(0.01)
                
                # Store AI response
                if ai_response_content.strip():
                    try:
                        ai_message = DatabaseService.add_message(
                            session.id,
                            ai_response_content,
                            is_user=False,
                            metadata={"session_id": str(session.id)}
                        )
                        print(f"✅ Stored AI response: {ai_message.id}")
                    except Exception as e:
                        print(f"❌ Failed to store AI message: {e}")
                
                # Send completion signal
                completion_data = {
                    'type': 'stream_end', 
                    'session_id': str(session.id),
                    'message_count': len(ai_response_content)
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                print("✅ Stream completed successfully")
                
            except Exception as e:
                print(f"❌ Stream generation error: {e}")
                print(f"🔍 Traceback: {traceback.format_exc()}")
                
                error_response = {
                    "type": "error",
                    "data": {
                        "message": "I apologize, but I encountered an error while processing your message. Please try again.",
                        "error_code": "STREAM_ERROR",
                        "details": str(e) if os.getenv("ENV") == "development" else None
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
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"❌ Unexpected chat endpoint error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred while processing your chat request.",
                "error_code": "CHAT_ERROR",
                "details": str(e) if os.getenv("ENV") == "development" else None
            }
        )

# Add a simple test endpoint
@router.post("/chat/test")
async def test_chat_endpoint(
    message: str = "Hello",
    current_user: User = Depends(get_current_user)
):
    """Test endpoint to verify authentication and basic functionality."""
    return {
        "message": f"Hello {current_user.name or current_user.email}!",
        "user_id": current_user.id,
        "received_message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

# Rest of the endpoints remain the same...
@router.post("/chat/session")
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session."""
    try:
        session = DatabaseService.create_chat_session(current_user.id, request.title)
        
        return {
            "session_id": str(session.id),
            "title": session.title,
            "created_at": session.created_at.isoformat()
        }
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.get("/facts")
async def get_user_facts(current_user: User = Depends(get_current_user)):
    """Get user profile, tasks, and session summaries."""
    try:
        # Build profile
        profile = {
            "name": current_user.name,
            "email": current_user.email,
            "degree": current_user.degree,
            "year": current_user.year,
            "goal": current_user.goal,
            "biggest_worry": current_user.biggest_worry,
            "fav_subject": current_user.fav_subject,
            "skills": json.loads(current_user.skills) if current_user.skills else [],
            "gpa": current_user.gpa,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
        
        # Get tasks
        tasks = []
        try:
            user_tasks = DatabaseService.get_user_tasks(current_user.id, limit=10)
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
            print(f"❌ Error fetching tasks: {e}")
        
        # Get sessions
        sessions = []
        try:
            user_sessions = DatabaseService.get_user_sessions(current_user.id, limit=5)
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
            print(f"❌ Error fetching sessions: {e}")
        
        return FactsResponse(
            profile=profile,
            tasks=tasks,
            sessions=sessions
        )
        
    except Exception as e:
        print(f"❌ Facts API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user facts: {str(e)}"
        )