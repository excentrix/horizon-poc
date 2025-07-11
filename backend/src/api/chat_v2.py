# backend/src/api/chat_v2.py (update error handling)
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json
import asyncio
from datetime import datetime
import os

from models.core import DatabaseService, User, ChatSession
from auth.dependencies import get_current_user
from agents.mentor_agent import MentorAgent

router = APIRouter(prefix="/api/v2", tags=["chat-v2"])

class ChatRequestV2(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None

# Initialize mentor agent with error handling
try:
    mentor_agent = MentorAgent()
    print("✅ MentorAgent v2 initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize MentorAgent: {e}")
    mentor_agent = None

@router.post("/chat/stream")
async def enhanced_chat_stream(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Enhanced chat stream with agent-based processing and memory integration."""
    
    if mentor_agent is None:
        raise HTTPException(
            status_code=500, 
            detail="Enhanced chat system is not available. Please check configuration."
        )
    
    try:
        # Parse request
        body = await request.body()
        request_data = json.loads(body.decode())
        chat_request = ChatRequestV2(**request_data)
        
        print(f"🚀 Enhanced chat request from {current_user.email}")
        
        # Get or create session
        session = None
        if chat_request.session_id:
            user_sessions = DatabaseService.get_user_sessions(current_user.id, limit=100)
            session = next((s for s in user_sessions if s.id == chat_request.session_id), None)
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        
        if not session:
            session = DatabaseService.create_chat_session(current_user.id)
            print(f"✅ Created new session: {session.id}")
        
        # Store user message
        try:
            user_message = DatabaseService.add_message(
                session.id,
                chat_request.message,
                is_user=True
            )
        except Exception as e:
            print(f"⚠️ Failed to store user message: {e}")
            # Continue without storing
        
        # Build user context
        user_context = {
            "user_id": current_user.id,
            "session_id": session.id,
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
        
        print(f"👤 User context prepared for {current_user.name or current_user.email}")
        
        async def generate_response():
            ai_response_content = ""
            
            try:
                # Stream response from mentor agent
                async for chunk in mentor_agent.chat_stream(
                    chat_request.message,
                    user_context
                ):
                    if chunk.get("type") == "token":
                        ai_response_content += chunk.get("data", "")
                    
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.01)
                
                # Store AI response
                if ai_response_content.strip():
                    try:
                        ai_message = DatabaseService.add_message(
                            session.id,
                            ai_response_content,
                            is_user=False,
                            metadata={"agent": "mentor_v2", "version": "enhanced"}
                        )
                        print(f"✅ Stored enhanced AI response: {len(ai_response_content)} chars")
                    except Exception as e:
                        print(f"⚠️ Failed to store AI response: {e}")
                
                # Send completion signal
                completion_data = {
                    "type": "stream_end",
                    "session_id": str(session.id),
                    "version": "v2_enhanced",
                    "response_length": len(ai_response_content)
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
            except Exception as e:
                print(f"❌ Enhanced stream error: {e}")
                error_response = {
                    "type": "error",
                    "data": {
                        "message": "I encountered an error while processing your message. Please try again.",
                        "error_code": "ENHANCED_STREAM_ERROR",
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
        
    except Exception as e:
        print(f"❌ Enhanced chat endpoint error: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Enhanced chat processing failed",
                "error_code": "CHAT_V2_ERROR",
                "details": str(e) if os.getenv("ENV") == "development" else None
            }
        )

@router.get("/memory/summary")
async def get_memory_summary(current_user: User = Depends(get_current_user)):
    """Get user's memory summary."""
    if mentor_agent is None or not mentor_agent.mem0_memory.enabled:
        return {
            "total_memories": 0,
            "memory_system": "disabled",
            "message": "Memory system is not available"
        }
    
    try:
        summary = await mentor_agent.mem0_memory.get_user_memories(current_user.id)
        return {
            "total_memories": len(summary),
            "memories": summary,
            "memory_system": "mem0",
            "user_id": current_user.id
        }
    except Exception as e:
        print(f"❌ Memory summary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory summary")

@router.post("/test")
async def test_enhanced_system(current_user: User = Depends(get_current_user)):
    """Test endpoint for the enhanced system."""
    if mentor_agent is None:
        return {
            "status": "error",
            "message": "Enhanced system failed to initialize",
            "user": current_user.email
        }
    
    # Test the process method
    try:
        test_result = await mentor_agent.process({
            "message": "Testing the enhanced system",
            "user_context": {"user_id": current_user.id},
            "type": "standard"
        })
        
        return {
            "status": "success",
            "message": "Enhanced system is working perfectly!",
            "user": current_user.email,
            "agent": "mentor_agent_v2",
            "memory": "mem0" if mentor_agent.mem0_memory.enabled else "basic",
            "version": "enhanced",
            "test_result": {
                "process_status": test_result["status"],
                "response_length": test_result.get("metadata", {}).get("response_length", 0),
                "processing_time": test_result.get("metadata", {}).get("processing_time_seconds", 0)
            }
        }
    except Exception as e:
        return {
            "status": "partial",
            "message": "Enhanced system initialized but test failed",
            "user": current_user.email,
            "error": str(e)
        }