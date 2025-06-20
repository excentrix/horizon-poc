# backend/src/memory/memory_manager.py
from typing import Dict, List, Optional, Any
from sqlmodel import Session, select
from datetime import datetime, timedelta
import json
import numpy as np
from sentence_transformers import SentenceTransformer

from models.core import engine, User
from models.enhanced_models import ConversationMemory, SessionSummary

class MemoryManager:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Memory Manager initialized")
    
    async def store_conversation_memory(
        self,
        user_id: str,
        session_id: str,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
        confidence: float = 1.0
    ) -> str:
        """Store a piece of conversation memory with embedding."""
        try:
            # Generate embedding for semantic search
            embedding = self.embedding_model.encode(content).tolist()
            
            with Session(engine) as session:
                memory = ConversationMemory(
                    user_id=user_id,
                    session_id=session_id,
                    memory_type=memory_type,
                    content=content,
                    metadata=json.dumps(metadata) if metadata else None,
                    embedding=embedding,
                    confidence=confidence
                )
                session.add(memory)
                session.commit()
                session.refresh(memory)
                return memory.id
        except Exception as e:
            print(f"❌ Error storing conversation memory: {e}")
            return None
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        memory_types: List[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to a query using semantic search."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            with Session(engine) as session:
                # Build query
                stmt = select(ConversationMemory).where(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.is_active == True
                )
                
                if memory_types:
                    stmt = stmt.where(ConversationMemory.memory_type.in_(memory_types))
                
                memories = session.exec(stmt).all()
                
                # Calculate similarities and filter
                relevant_memories = []
                for memory in memories:
                    if memory.embedding:
                        similarity = self._cosine_similarity(query_embedding, memory.embedding)
                        if similarity >= similarity_threshold:
                            relevant_memories.append({
                                "id": memory.id,
                                "content": memory.content,
                                "memory_type": memory.memory_type,
                                "metadata": json.loads(memory.metadata) if memory.metadata else {},
                                "confidence": memory.confidence,
                                "similarity": similarity,
                                "created_at": memory.created_at
                            })
                
                # Sort by similarity and limit
                relevant_memories.sort(key=lambda x: x["similarity"], reverse=True)
                return relevant_memories[:limit]
                
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            return []
    
    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of user's stored memories."""
        try:
            with Session(engine) as session:
                memories = session.exec(
                    select(ConversationMemory).where(
                        ConversationMemory.user_id == user_id,
                        ConversationMemory.is_active == True
                    )
                ).all()
                
                # Group by memory type
                memory_summary = {}
                for memory in memories:
                    if memory.memory_type not in memory_summary:
                        memory_summary[memory.memory_type] = []
                    
                    memory_summary[memory.memory_type].append({
                        "content": memory.content,
                        "confidence": memory.confidence,
                        "created_at": memory.created_at
                    })
                
                return {
                    "total_memories": len(memories),
                    "memory_types": memory_summary,
                    "last_updated": max([m.created_at for m in memories]) if memories else None
                }
        except Exception as e:
            print(f"❌ Error getting memory summary: {e}")
            return {"total_memories": 0, "memory_types": {}, "last_updated": None}
    
    async def consolidate_session_memories(self, session_id: str, user_id: str) -> Optional[str]:
        """Consolidate memories from a session into a summary."""
        try:
            with Session(engine) as session_db:
                # Get all memories from this session
                memories = session_db.exec(
                    select(ConversationMemory).where(
                        ConversationMemory.session_id == session_id,
                        ConversationMemory.user_id == user_id
                    )
                ).all()
                
                if not memories:
                    return None
                
                # Create session summary
                key_topics = list(set([m.memory_type for m in memories]))
                facts_extracted = {}
                
                for memory in memories:
                    if memory.memory_type not in facts_extracted:
                        facts_extracted[memory.memory_type] = []
                    facts_extracted[memory.memory_type].append({
                        "content": memory.content,
                        "confidence": memory.confidence
                    })
                
                summary = SessionSummary(
                    session_id=session_id,
                    user_id=user_id,
                    summary=f"Session covered {len(key_topics)} topics with {len(memories)} insights",
                    key_topics=json.dumps(key_topics),
                    facts_extracted=json.dumps(facts_extracted),
                    message_count=len(memories),
                    emotional_tone="neutral"  # TODO: Implement emotion detection
                )
                
                session_db.add(summary)
                session_db.commit()
                session_db.refresh(summary)
                return summary.id
                
        except Exception as e:
            print(f"❌ Error consolidating session memories: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0

# Global instance
memory_manager = MemoryManager()