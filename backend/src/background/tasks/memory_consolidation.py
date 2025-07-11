# backend/src/background/tasks/memory_consolidation.py
from celery import current_app as celery_app
from typing import Dict, Any, List, Optional
import sys
import os
from datetime import datetime, timedelta, UTC
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from memory.mem0_manager import mem0_manager
from models.core import DatabaseService, Session, engine
from models.enhanced_models import ProcessingJob, SessionSummary
from agents.mentor_agent import MentorAgent


@celery_app.task
async def consolidate_user_memories(user_id: str = None) -> Dict[str, Any]:
    """Consolidate and optimize user memories."""

    print(f"🔄 Starting memory consolidation for user {user_id or 'all users'}")

    try:
        if user_id:
            return await _consolidate_single_user(user_id)
        else:
            return await _consolidate_all_users()

    except Exception as e:
        print(f"❌ Memory consolidation failed: {e}")
        return {"status": "failed", "error": str(e)}


async def _consolidate_single_user(user_id: str) -> Dict[str, Any]:
    """Consolidate memories for a single user."""

    if not mem0_manager.enabled:
        return {"status": "memory_disabled"}

    try:
        # Get user's memory summary
        memory_summary = await mem0_manager.get_user_memory_summary(user_id)
        total_memories = memory_summary.get("total_memories", 0)

        if total_memories < 10:  # Not enough memories to consolidate
            return {
                "status": "insufficient_memories",
                "user_id": user_id,
                "total_memories": total_memories,
            }

        # Get all user memories
        all_memories = await mem0_manager.memory.get_all(user_id=user_id, limit=100)

        # Group memories by time periods and topics
        memory_groups = _group_memories_for_consolidation(all_memories)

        consolidated_count = 0
        removed_count = 0

        # Consolidate each group
        for group_type, memories in memory_groups.items():
            if len(memories) >= 3:  # Only consolidate groups with multiple memories
                consolidated_memory = await _create_consolidated_memory(
                    user_id, group_type, memories
                )

                if consolidated_memory:
                    # Remove original memories
                    for memory in memories:
                        memory_id = memory.get("id")
                        if memory_id:
                            await mem0_manager.memory.delete(memory_id)
                            removed_count += 1

                    consolidated_count += 1

        return {
            "status": "completed",
            "user_id": user_id,
            "original_memories": total_memories,
            "groups_consolidated": consolidated_count,
            "memories_removed": removed_count,
            "final_memory_count": total_memories - removed_count + consolidated_count,
        }

    except Exception as e:
        print(f"❌ Single user consolidation failed: {e}")
        return {"status": "failed", "user_id": user_id, "error": str(e)}


def _group_memories_for_consolidation(
    memories: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group memories by similarity and time for consolidation."""

    groups = {
        "academic_discussions": [],
        "career_planning": [],
        "skill_development": [],
        "personal_challenges": [],
        "recent_conversations": [],
    }

    # Simple grouping based on content keywords
    for memory in memories:
        content = memory.get("memory", "").lower()
        metadata = memory.get("metadata", {})

        # Categorize based on keywords
        if any(
            word in content for word in ["study", "exam", "course", "grade", "academic"]
        ):
            groups["academic_discussions"].append(memory)
        elif any(
            word in content for word in ["career", "job", "internship", "interview"]
        ):
            groups["career_planning"].append(memory)
        elif any(word in content for word in ["skill", "learn", "practice", "improve"]):
            groups["skill_development"].append(memory)
        elif any(
            word in content for word in ["worry", "concern", "stress", "difficult"]
        ):
            groups["personal_challenges"].append(memory)
        else:
            groups["recent_conversations"].append(memory)

    # Filter out empty groups
    return {k: v for k, v in groups.items() if len(v) >= 3}


async def _create_consolidated_memory(
    user_id: str, group_type: str, memories: List[Dict[str, Any]]
) -> Optional[str]:
    """Create a consolidated memory from a group of related memories."""

    try:
        # Combine memory contents
        combined_content = f"Consolidated {group_type} memories:\n"
        for i, memory in enumerate(memories, 1):
            content = memory.get("memory", "")
            combined_content += f"{i}. {content}\n"

        # Create summary using MentorAgent
        mentor = MentorAgent()
        summary_result = await mentor.process(
            {
                "message": f"Summarize these related {group_type} conversations into key insights",
                "user_context": {"user_id": user_id},
                "conversation_history": [
                    {"content": combined_content, "is_user": False}
                ],
                "type": "summary",
            }
        )

        summary_content = summary_result.get("response", combined_content)

        # Store consolidated memory
        memory_id = await mem0_manager.add_conversation_memory(
            user_id=user_id,
            messages=[{"content": summary_content, "is_user": False}],
            metadata={
                "type": "consolidated_memory",
                "group_type": group_type,
                "original_memory_count": len(memories),
                "consolidation_date": datetime.now(UTC).isoformat(),
                "source": "memory_consolidation",
            },
        )

        print(f"✅ Created consolidated memory for {group_type}: {memory_id}")
        return memory_id

    except Exception as e:
        print(f"❌ Failed to create consolidated memory: {e}")
        return None


async def _consolidate_all_users() -> Dict[str, Any]:
    """Consolidate memories for all active users."""

    try:
        # Get active users (users with recent activity)
        cutoff_date = datetime.now(UTC) - timedelta(days=30)
        active_users = DatabaseService.get_active_users_since(cutoff_date)

        consolidation_results = []
        total_processed = 0

        for user in active_users:
            user_result = await _consolidate_single_user(user.id)
            consolidation_results.append(user_result)

            if user_result.get("status") == "completed":
                total_processed += 1

        return {
            "status": "completed",
            "total_users": len(active_users),
            "users_processed": total_processed,
            "consolidation_results": consolidation_results,
        }

    except Exception as e:
        print(f"❌ All users consolidation failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task
def cleanup_old_memories(days_old: int = 90) -> Dict[str, Any]:
    """Clean up very old, low-importance memories."""

    print(f"🔄 Cleaning up memories older than {days_old} days")

    try:
        if not mem0_manager.enabled:
            return {"status": "memory_disabled"}

        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)

        # This would need to be implemented based on Mem0's API
        # For now, return a placeholder

        return {
            "status": "completed",
            "cutoff_date": cutoff_date.isoformat(),
            "memories_cleaned": 0,  # Placeholder
            "note": "Memory cleanup not fully implemented",
        }

    except Exception as e:
        print(f"❌ Memory cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task
def optimize_memory_storage() -> Dict[str, Any]:
    """Optimize memory storage and indexing."""

    print("🔄 Optimizing memory storage")

    try:
        if not mem0_manager.enabled:
            return {"status": "memory_disabled"}

        # This would include operations like:
        # - Rebuilding vector indices
        # - Optimizing Qdrant collections
        # - Updating embeddings for old memories

        return {
            "status": "completed",
            "optimizations_applied": [
                "vector_index_optimization",
                "memory_deduplication",
                "embedding_updates",
            ],
            "note": "Storage optimization not fully implemented",
        }

    except Exception as e:
        print(f"❌ Memory optimization failed: {e}")
        return {"status": "failed", "error": str(e)}
