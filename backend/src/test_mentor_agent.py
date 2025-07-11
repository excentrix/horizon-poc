# # backend/test_fixed_system.py
# import asyncio
# import sys
# import os

# sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# async def test_fixed_system():
#     print("🧪 Testing Fixed System...")
    
#     # Test memory system
#     try:
#         from memory.mem0_manager import mem0_manager
#         print(f"Mem0 Status: {'Enabled' if mem0_manager.enabled else 'Disabled'}")
        
#         if mem0_manager.enabled:
#             summary = await mem0_manager.get_user_memory_summary("test_user")
#             print(f"✅ Memory system working: {summary}")
#         else:
#             print("🔄 Using fallback memory system")
#     except Exception as e:
#         print(f"❌ Memory test failed: {e}")
    
#     # Test agent
#     try:
#         from agents.mentor_agent import MentorAgent
#         mentor = MentorAgent()
        
#         result = await mentor.process({
#             "message": "Test the fixed system",
#             "user_context": {"user_id": "test", "name": "Test User"}
#         })
        
#         print(f"✅ Agent working: {result['status']}")
        
#     except Exception as e:
#         print(f"❌ Agent test failed: {e}")
    
#     print("🎉 System test completed!")

# if __name__ == "__main__":
#     asyncio.run(test_fixed_system())

# backend/test_fixed_system.py
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_fixed_system():
    """Test the fixed system components."""
    
    print("🧪 Testing Fixed System Components...")
    
    # Test 1: Memory Manager
    print("\n1️⃣ Testing Mem0 Manager...")
    try:
        from memory.mem0_manager import mem0_manager
        
        if mem0_manager.enabled:
            # Test memory search
            memories = await mem0_manager.search_relevant_memories(
                user_id="test_user",
                query="Hello test",
                limit=3
            )
            print(f"✅ Memory search working: Found {len(memories)} memories")
            
            # Test memory addition
            memory_id = await mem0_manager.add_conversation_memory(
                user_id="test_user",
                messages=[{"content": "Test message", "is_user": True}],
                metadata={"test": True}
            )
            print(f"✅ Memory addition working: {memory_id}")
            
        else:
            print("⚠️ Mem0 disabled - check configuration")
            
    except Exception as e:
        print(f"❌ Memory Manager test failed: {e}")
    
    # Test 2: MentorAgent
    print("\n2️⃣ Testing MentorAgent...")
    try:
        from agents.mentor_agent import MentorAgent
        
        mentor = MentorAgent()
        
        # Test process method
        result = await mentor.process({
            "message": "Test the fixed system",
            "user_context": {
                "user_id": "test_user",
                "name": "Test Student",
                "degree": "Computer Science"
            },
            "type": "standard"
        })
        
        print(f"✅ MentorAgent process: {result['status']}")
        if result['status'] == 'success':
            print(f"   Response length: {len(result.get('response', ''))}")
            print(f"   Memories used: {result.get('memories_used', 0)}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ MentorAgent test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Datetime handling
    print("\n3️⃣ Testing Datetime Handling...")
    try:
        # Test timezone-aware datetime
        now_utc = datetime.now(timezone.utc)
        iso_string = now_utc.isoformat()
        print(f"✅ Timezone-aware datetime working: {iso_string}")
        
    except Exception as e:
        print(f"❌ Datetime test failed: {e}")
    
    # Test 4: Qdrant connection
    print("\n4️⃣ Testing Qdrant Connection...")
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print(f"✅ Qdrant connection working: {len(collections.collections)} collections")
        
        # Check if our collection exists with correct dimensions
        for collection in collections.collections:
            if collection.name == "horizon_memories":
                info = client.get_collection("horizon_memories")
                vector_size = info.config.params.vectors.size
                print(f"✅ Collection 'horizon_memories' found with {vector_size} dimensions")
                break
        else:
            print("⚠️ Collection 'horizon_memories' not found - will be created on first use")
            
    except Exception as e:
        print(f"❌ Qdrant test failed: {e}")
    
    print("\n🎉 System tests completed!")

if __name__ == "__main__":
    asyncio.run(test_fixed_system())