# backend/test_memory_detailed.py
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_memory_system_detailed():
    """Detailed memory system testing."""
    
    print("🧪 Detailed Memory System Testing...")
    
    from memory.mem0_manager import mem0_manager
    
    if not mem0_manager.enabled:
        print("❌ Memory system not enabled")
        return
    
    test_user_id = "detailed_test_user"
    
    # Test 1: Add a meaningful conversation
    print("\n1️⃣ Testing Memory Storage...")
    
    test_conversations = [
        {
            "messages": [
                {"content": "I'm studying Computer Science and want to work at Google", "is_user": True},
                {"content": "That's a great goal! Google values strong algorithmic thinking and system design skills. What year are you in?", "is_user": False}
            ],
            "metadata": {"session_id": "test_session_1", "topic": "career_goals"}
        },
        {
            "messages": [
                {"content": "I'm in my 3rd year and struggling with algorithms", "is_user": True},
                {"content": "Algorithms can be challenging. I recommend starting with basic sorting and searching, then moving to dynamic programming.", "is_user": False}
            ],
            "metadata": {"session_id": "test_session_2", "topic": "academic_challenges"}
        },
        {
            "messages": [
                {"content": "I also need help with system design interviews", "is_user": True},
                {"content": "System design interviews focus on scalability. Let's practice designing a chat application.", "is_user": False}
            ],
            "metadata": {"session_id": "test_session_3", "topic": "interview_prep"}
        }
    ]
    
    stored_memory_ids = []
    for i, conversation in enumerate(test_conversations):
        print(f"\n   📝 Storing conversation {i+1}...")
        memory_id = await mem0_manager.add_conversation_memory(
            user_id=test_user_id,
            messages=conversation["messages"],
            metadata=conversation["metadata"]
        )
        stored_memory_ids.append(memory_id)
        print(f"   ✅ Stored with ID: {memory_id}")
    
    # Test 2: Search for relevant memories
    print("\n2️⃣ Testing Memory Search...")
    
    search_queries = [
        "Google career advice",
        "algorithm help",
        "system design interview",
        "Computer Science studies",
        "programming challenges"
    ]
    
    for query in search_queries:
        print(f"\n   🔍 Searching: '{query}'")
        memories = await mem0_manager.search_relevant_memories(
            user_id=test_user_id,
            query=query,
            limit=3,
            threshold=0.5
        )
        print(f"   📊 Found {len(memories)} relevant memories")
        for j, memory in enumerate(memories):
            print(f"      {j+1}. Score: {memory['score']:.3f} - {memory['content'][:80]}...")
    
    # Test 3: Get memory summary
    print("\n3️⃣ Testing Memory Summary...")
    summary = await mem0_manager.get_user_memory_summary(test_user_id)
    print(f"   📊 Total memories: {summary.get('total_memories', 0)}")
    print(f"   📊 Memory types: {summary.get('memory_types', {})}")
    
    # Test 4: Test new conversation with memory context
    print("\n4️⃣ Testing Contextual Conversation...")
    
    from agents.mentor_agent import MentorAgent
    mentor = MentorAgent()
    
    # This should find relevant memories about Google and algorithms
    result = await mentor.process({
        "message": "Can you help me prepare for my Google interview?",
        "user_context": {
            "user_id": test_user_id,
            "name": "Test Student",
            "degree": "Computer Science",
            "year": "3rd year"
        },
        "type": "standard"
    })
    
    print(f"   🤖 Agent response status: {result['status']}")
    print(f"   🧠 Memories used: {result.get('memories_used', 0)}")
    if result.get('memories_used', 0) > 0:
        print("   ✅ Memory system working correctly!")
    else:
        print("   ❌ No memories were used - system not working")
    
    print(f"   💬 Response preview: {result.get('response', '')[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_memory_system_detailed())