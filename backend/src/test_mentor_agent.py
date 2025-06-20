# backend/test_mentor_agent.py (create this test file)
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.mentor_agent import MentorAgent

async def test_mentor_agent():
    """Test the enhanced MentorAgent with both process and streaming methods."""
    
    print("🧪 Testing Enhanced MentorAgent...")
    
    # Initialize agent
    mentor = MentorAgent()
    
    # Test data
    user_context = {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "name": "Test Student",
        "degree": "Computer Science",
        "year": "3rd",
        "goal": "Get a software engineering internship",
        "biggest_worry": "Not having enough practical experience",
        "skills": ["Python", "JavaScript", "React"]
    }
    
    # Test 1: Process method (batch processing)
    print("\n1️⃣ Testing process method...")
    
    process_result = await mentor.process({
        "message": "I'm struggling with system design concepts for interviews",
        "user_context": user_context,
        "type": "standard"
    })
    
    print(f"Process result status: {process_result['status']}")
    print(f"Response length: {process_result.get('metadata', {}).get('response_length', 0)} chars")
    print(f"Memories used: {process_result.get('memories_used', 0)}")
    
    # Test 2: Streaming method
    print("\n2️⃣ Testing streaming method...")
    
    response_chunks = []
    async for chunk in mentor.chat_stream(
        "Can you help me prepare for technical interviews?",
        user_context
    ):
        response_chunks.append(chunk)
        if chunk.get("type") == "token":
            print(".", end="", flush=True)
    
    print(f"\nStreaming completed: {len(response_chunks)} chunks")
    
    # Test 3: Analysis method
    print("\n3️⃣ Testing analysis method...")
    
    analysis_result = await mentor.analyze_conversation(
        "I just finished my data structures course and feel confident about trees and graphs",
        user_context
    )
    
    print(f"Analysis status: {analysis_result['status']}")
    print(f"Fact extraction available: {'extracted_facts' in analysis_result}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_mentor_agent())