# backend/src/memory/mem0_manager.py (fix memory search response handling)
import os
from typing import Dict, List, Optional, Any
from mem0 import Memory
import json
import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

class Mem0Manager:
    def __init__(self):
        """Initialize Mem0 with correct embedding configuration."""
        try:
            # Complete Mem0 configuration with correct embedding model
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": os.getenv("QDRANT_HOST", "localhost"),
                        "port": int(os.getenv("QDRANT_PORT", 6333)),
                        # "api_key": os.getenv("QDRANT_API_KEY"),  # None for local
                        "collection_name": "horizon_memories",
                    },
                },
                "llm": {
                    "provider": "azure_openai",
                    "config": {
                        "model": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                        "temperature": 0.1,  # Low temperature for memory processing
                        "azure_kwargs": {
                            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
                        },
                    },
                },
                "embedder": {
                    "provider": "azure_openai",
                    "config": {
                        "model": "text-embedding-ada-002",
                        "azure_kwargs": {
                            "api_version": os.getenv("AZURE_EMBEDDING_API_VERSION"),
                            "azure_deployment": os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
                            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                        },
                    },
                },
            }
            
            self.memory = Memory.from_config(config)
            self.enabled = True
            self._test_connection()
            print("✅ Mem0 Manager initialized successfully with correct embeddings (1536D)")
            
        except Exception as e:
            print(f"❌ Mem0 initialization failed: {e}")
            print("🔄 Falling back to basic memory system")
            self.memory = None
            self.enabled = False
    
    def _test_connection(self):
        """Test connection with proper error handling."""
        try:
            # Test with a simple memory operation
            test_result = self.memory.add(
                "System test message for embedding compatibility", 
                user_id="system_test",
                metadata={"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
            )
            
            # Clean up test data
            if test_result and isinstance(test_result, dict) and test_result.get("id"):
                self.memory.delete(test_result["id"])
            
            print("✅ Mem0 connection and embedding test successful")
            
        except Exception as e:
            print(f"⚠️ Mem0 connection test failed: {e}")
            # Check if it's a dimension mismatch
            if "Vector dimension error" in str(e):
                print("❌ Vector dimension mismatch - need to reset Qdrant collection")
                self._reset_qdrant_collection()
            else:
                raise
    
    def _reset_qdrant_collection(self):
        """Reset Qdrant collection with correct dimensions."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # Connect to Qdrant directly
            qdrant_client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", 6333))
            )
            
            collection_name = "horizon_memories"
            
            # Delete existing collection if it exists
            try:
                qdrant_client.delete_collection(collection_name)
                print(f"🗑️ Deleted existing collection: {collection_name}")
            except:
                pass  # Collection might not exist
            
            # Create new collection with correct dimensions (1536 for text-embedding-ada-002)
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-ada-002 dimension
                    distance=Distance.COSINE
                )
            )
            
            print(f"✅ Created new Qdrant collection with 1536 dimensions")
            
        except Exception as e:
            print(f"❌ Failed to reset Qdrant collection: {e}")
            raise
    
    async def add_conversation_memory(
        self, 
        user_id: str, 
        messages: List[Dict[str, str]], 
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add conversation memory with detailed logging."""
        if not self.enabled:
            return "mem0_disabled"
        
        try:
            # Format conversation for storage
            conversation_text = ""
            for msg in messages:
                role = "User" if msg.get("is_user", True) else "Assistant"
                content = msg.get("content", "")
                conversation_text += f"{role}: {content}\n"
            
            # Enhanced metadata
            enhanced_metadata = {
                "conversation_length": len(messages),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "horizon_mentor",
                "user_id": user_id,
                **(metadata or {})
            }
            
            # Add to Mem0
            result = self.memory.add(
                conversation_text.strip(), 
                user_id=user_id,
                metadata=enhanced_metadata
            )
            
            # Parse Mem0 response correctly
            memory_ids = []
            if result and isinstance(result, dict):
                # Handle {'results': [...]} format
                if 'results' in result:
                    for item in result['results']:
                        if isinstance(item, dict) and 'id' in item:
                            memory_ids.append(item['id'])
                # Handle direct format
                elif 'id' in result:
                    memory_ids.append(result['id'])
            
            memory_id = ",".join(memory_ids) if memory_ids else "unknown"
            print(f"✅ Stored {len(memory_ids)} memory items: {memory_id}")
            return memory_id
            
        except Exception as e:
            print(f"❌ Error adding conversation memory: {e}")
            return "error"
    
    async def search_relevant_memories(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search memories with fixed parsing for Mem0 API response."""
        if not self.enabled:
            return []
        
        try:
            # Search memories
            results = self.memory.search(
                query=query, 
                user_id=user_id, 
                limit=limit
            )
            
            print(f"🔍 Raw search results: {type(results)}")
            
            formatted_results = []
            
            # Handle Mem0 API response format: {'results': [...]}
            if isinstance(results, dict) and 'results' in results:
                memory_items = results['results']
                print(f"📋 Processing {len(memory_items)} memory items from results array")
                
                for i, item in enumerate(memory_items):
                    try:
                        if isinstance(item, dict):
                            score = item.get("score", 0.8)
                            memory_content = item.get("memory", "")
                            
                            if score >= threshold and memory_content:
                                formatted_result = {
                                    "id": item.get("id", f"item_{i}"),
                                    "content": memory_content,  # This is the actual extracted fact
                                    "score": score,
                                    "metadata": item.get("metadata", {}),
                                    "created_at": item.get("created_at", ""),
                                    "updated_at": item.get("updated_at", "")
                                }
                                formatted_results.append(formatted_result)
                                print(f"✅ Added memory: '{memory_content}' (score: {score:.3f})")
                            else:
                                print(f"❌ Skipped item {i}: score {score:.3f} < {threshold} or empty content")
                    except Exception as e:
                        print(f"❌ Error processing memory item {i}: {e}")
                        continue
            
            # Fallback: Handle other response formats
            elif isinstance(results, dict):
                print("📋 Processing single dictionary (fallback)")
                score = results.get("score", 0.8)
                if score >= threshold:
                    formatted_results.append({
                        "id": results.get("id", "single_dict"),
                        "content": results.get("memory", str(results)),
                        "score": score,
                        "metadata": results.get("metadata", {}),
                        "created_at": results.get("created_at", ""),
                        "updated_at": results.get("updated_at", "")
                    })
            
            elif isinstance(results, (list, tuple)):
                print(f"📋 Processing list of {len(results)} items (fallback)")
                for i, result in enumerate(results):
                    if isinstance(result, dict):
                        score = result.get("score", 0.8)
                        if score >= threshold:
                            formatted_results.append({
                                "id": result.get("id", f"item_{i}"),
                                "content": result.get("memory", result.get("content", str(result))),
                                "score": score,
                                "metadata": result.get("metadata", {}),
                                "created_at": result.get("created_at", ""),
                                "updated_at": result.get("updated_at", "")
                            })
            
            print(f"🎯 Final results: {len(formatted_results)} relevant memories")
            for i, memory in enumerate(formatted_results):
                print(f"   {i+1}. '{memory['content']}' (score: {memory['score']:.3f})")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching memories: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_user_memory_summary(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get user memory summary with fixed parsing."""
        if not self.enabled:
            return {"total_memories": 0, "enabled": False}
        
        try:
            # Get all user memories
            memories_response = self.memory.get_all(user_id=user_id, limit=limit)
            
            memories = []
            
            # Handle {'results': [...]} format
            if isinstance(memories_response, dict) and 'results' in memories_response:
                memories = memories_response['results']
            elif isinstance(memories_response, (list, tuple)):
                memories = memories_response
            elif memories_response:
                memories = [memories_response]
            
            total_memories = len(memories)
            memory_types = {}
            recent_topics = []
            
            for memory in memories:
                try:
                    if isinstance(memory, dict):
                        metadata = memory.get("metadata", {})
                        content = memory.get("memory", memory.get("content", ""))
                        source = metadata.get("source", "unknown") if isinstance(metadata, dict) else "unknown"
                        
                        if source not in memory_types:
                            memory_types[source] = 0
                        memory_types[source] += 1
                        
                        if content and len(content) > 10:
                            recent_topics.append(content)
                            
                except Exception as e:
                    print(f"⚠️ Error processing memory in summary: {e}")
                    continue
            
            return {
                "total_memories": total_memories,
                "memory_types": memory_types,
                "recent_topics": recent_topics[:5],
                "enabled": True,
                "vector_store": "qdrant",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting memory summary: {e}")
            return {"total_memories": 0, "enabled": False, "error": str(e)}

# Global instance
mem0_manager = Mem0Manager()