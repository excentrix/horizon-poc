# backend/src/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class FactsResponse(BaseModel):
    profile: dict
    tasks: list
    sessions: list

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    # TODO: Add auth dependency
):
    """Stream chat responses with fact extraction"""
    
    async def generate_response():
        # Mock streaming response for now
        response_text = f"Thanks for your message: {request.message}. I'm here to help you learn!"
        
        # Simulate streaming
        for i, char in enumerate(response_text):
            if i % 5 == 0:  # Send chunks of 5 chars
                await asyncio.sleep(0.1)
            
            yield f"data: {json.dumps({'type': 'token', 'data': char})}\n\n"
        
        # Send facts update
        facts = {
            "type": "facts",
            "data": {
                "patch": {"last_interaction": "chat"}
            }
        }
        yield f"data: {json.dumps(facts)}\n\n"
        
        # End stream
        yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/facts")
async def get_facts(
    # TODO: Add auth dependency
):
    """Get user profile, tasks, and session summaries"""
    return FactsResponse(
        profile={"name": "Test User", "degree": "Computer Science"},
        tasks=[{"id": "1", "title": "Complete Python basics", "done": False}],
        sessions=[{"id": "1", "summary": "Discussed career goals"}]
    )

@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    # TODO: Add auth dependency
):
    """Upload and parse resume"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # TODO: Implement PDF parsing with PyMuPDF
    return {"message": "Resume uploaded successfully", "extracted": {}}