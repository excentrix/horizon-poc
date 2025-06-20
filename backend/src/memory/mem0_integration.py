# backend/src/memory/mem0_integration.py
import os
from typing import Dict, List, Optional, Any
from mem0 import Memory
import json

class Mem0MemoryManager:
    def __init__(self):
        """Initialize Mem0 with configuration."""
        try:
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": "localhost",
                        "port": 6333,
                    }
                },
                "llm": {
                    "provider": "azure_openai",
                    "config": {
                        "api_key": os.getenv("AZURE_OPENAI_KEY"),
                        "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                        "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
                        "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                    }
                }
            }
            
            self.memory = Memory.from_config(config)
            self.enabled = True
            print("✅ Mem0 Memory Manager initialized successfully")
            
        except Exception as e:
            print(f"⚠️ Mem0 initialization failed, falling back to basic memory: {e}")
            self.memory = None
            self.enabled = False
    
    async def add_memory(
        self, 
        user_id: str, 
        messages: List[Dict[str, str]], 
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add conversation memory to Mem0."""
        if not self.enabled:
            return "mem0_disabled"
        
        try:
            # Format messages for Mem0
            conversation_text = "\n".join([
                f"{'User' if msg.get('is_user', True) else 'Assistant'}: {msg.get('content', '')}"
                for msg in messages
            ])
            
            # Add to Mem0
            result = self.memory.add(
                conversation_text, 
                user_id=user_id,
                metadata=metadata or {}
            )
            
            print(f"✅ Added memory to Mem0 for user {user_id}")
            return result.get("id", "unknown")
            
        except Exception as e:
            print(f"❌ Error adding memory to Mem0: {e}")
            return "error"
    
    async def search_memories(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search relevant memories using Mem0."""
        if not self.enabled:
            return []
        
        try:
            results = self.memory.search(
                query=query, 
                user_id=user_id, 
                limit=limit
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.get("id", ""),
                    "content": result.get("memory", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "created_at": result.get("created_at", "")
                })
            
            print(f"✅ Found {len(formatted_results)} memories for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching Mem0 memories: {e}")
            return []
    
    async def get_user_memories(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all memories for a user."""
        if not self.enabled:
            return []
        
        try:
            memories = self.memory.get_all(user_id=user_id, limit=limit)
            
            formatted_memories = []
            for memory in memories:
                formatted_memories.append({
                    "id": memory.get("id", ""),
                    "content": memory.get("memory", ""),
                    "metadata": memory.get("metadata", {}),
                    "created_at": memory.get("created_at", "")
                })
            
            return formatted_memories
            
        except Exception as e:
            print(f"❌ Error getting user memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        if not self.enabled:
            return False
        
        try:
            self.memory.delete(memory_id)
            print(f"✅ Deleted memory: {memory_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting memory: {e}")
            return False

# Global instance
mem0_memory_manager = Mem0MemoryManager()