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
    """Enhanced streaming chat with real-time fact extraction and task creation."""
    
    try:
        # Parse request (keeping existing validation)
        body = await request.body()
        request_data = json.loads(body.decode())
        chat_request = ChatRequest(**request_data)
        
        print(f"🚀 Enhanced chat request from {current_user.email}")
        
        # Check if chat chain is available
        if chat_chain is None:
            raise HTTPException(
                status_code=500,
                detail="Chat service is not available. Please check Azure OpenAI configuration."
            )
        
        # Get or create session
        session = None
        if chat_request.session_id:
            user_sessions = DatabaseService.get_user_sessions(current_user.id, limit=100)
            session = next((s for s in user_sessions if s.id == chat_request.session_id), None)
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        
        if not session:
            session = DatabaseService.create_chat_session(current_user.id)
        
        # Store user message
        user_message = DatabaseService.add_message(
            session.id, 
            chat_request.message, 
            is_user=True
        )
        
        # Build enhanced user context
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
        
        # Get conversation history (last 10 messages)
        try:
            with Session(engine) as db_session:
                messages = db_session.exec(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session.id)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(10)
                ).all()
                
                conversation_history = [
                    {
                        "content": msg.content,
                        "is_user": msg.is_user,
                        "timestamp": msg.created_at.isoformat()
                    }
                    for msg in reversed(messages)  # Reverse to get chronological order
                ]
        except Exception as e:
            print(f"⚠️ Error fetching conversation history: {e}")
            conversation_history = []
        
        print(f"📚 Context: {len(conversation_history)} messages, profile completeness: {sum(1 for v in user_context.values() if v) / len(user_context):.1%}")
        
        async def generate_enhanced_response():
            ai_response_content = ""
            facts_updated = False
            tasks_created = []
            
            try:
                async for chunk in chat_chain.chat_stream(
                    chat_request.message,
                    user_context=user_context,
                    conversation_history=conversation_history
                ):
                    # Handle different chunk types
                    chunk_type = chunk.get("type")
                    
                    if chunk_type == "token":
                        ai_response_content += chunk.get("data", "")
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    elif chunk_type == "facts_update":
                        facts = chunk.get("data", {})
                        if facts:
                            try:
                                # Update user profile in database
                                updated_user = DatabaseService.update_user_profile(current_user.id, **facts)
                                if updated_user:
                                    facts_updated = True
                                    print(f"✅ Updated profile: {list(facts.keys())}")
                                yield f"data: {json.dumps(chunk)}\n\n"
                            except Exception as e:
                                print(f"❌ Failed to update user profile: {e}")
                    
                    elif chunk_type == "fact_discovery":
                        # Send visual feedback for fact discovery
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    elif chunk_type == "task_created":
                        task_data = chunk.get("data", {})
                        try:
                            # Create task in database
                            due_date = None
                            if task_data.get("due_date"):
                                due_date = datetime.fromisoformat(task_data["due_date"].replace('Z', '+00:00'))
                            
                            task = DatabaseService.create_task(
                                current_user.id,
                                title=task_data.get("title", "Untitled Task"),
                                description=task_data.get("description"),
                                due_date=due_date,
                                created_by_ai=True
                            )
                            tasks_created.append(task)
                            print(f"✅ Created task: {task.title}")
                            yield f"data: {json.dumps(chunk)}\n\n"
                        except Exception as e:
                            print(f"❌ Failed to create task: {e}")
                    
                    elif chunk_type in ["processing_update", "stream_complete", "error"]:
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    await asyncio.sleep(0.01)
                
                # Store AI response
                if ai_response_content.strip():
                    try:
                        ai_message = DatabaseService.add_message(
                            session.id,
                            ai_response_content,
                            is_user=False,
                            meta={
                                "session_id": str(session.id),
                                "facts_updated": facts_updated,
                                "tasks_created": len(tasks_created)
                            }
                        )
                        print(f"✅ Stored enhanced AI response")
                    except Exception as e:
                        print(f"❌ Failed to store AI message: {e}")
                
                # Send final completion signal
                completion_data = {
                    'type': 'stream_end',
                    'session_id': str(session.id),
                    'enhanced_features': {
                        'facts_updated': facts_updated,
                        'tasks_created': len(tasks_created),
                        'response_length': len(ai_response_content)
                    }
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                print("✅ Enhanced stream completed successfully")
                
            except Exception as e:
                print(f"❌ Enhanced stream generation error: {e}")
                error_response = {
                    "type": "error",
                    "data": {
                        "message": "I encountered an error while processing your message. Please try again.",
                        "error_code": "ENHANCED_STREAM_ERROR"
                    }
                }
                yield f"data: {json.dumps(error_response)}\n\n"
        
        return StreamingResponse(
            generate_enhanced_response(),
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
        raise
    except Exception as e:
        print(f"❌ Enhanced chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred while processing your enhanced chat request.",
                "error_code": "ENHANCED_CHAT_ERROR"
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