# backend/src/background/tasks/fact_extraction.py
from celery import current_app as celery_app
from typing import Dict, Any, List
import sys
import os
from datetime import datetime, UTC
import json
from sqlalchemy import select

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.mentor_agent import MentorAgent
from models.core import DatabaseService, Session, engine
from models.enhanced_models import ProcessingJob, ConversationMemory
from memory.mem0_manager import mem0_manager


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3, "countdown": 60})
async def extract_facts_from_conversation(
    self, conversation_id: str, user_id: str
) -> Dict[str, Any]:
    """Extract facts from a specific conversation."""

    job_id = self.request.id
    print(
        f"🔄 Starting fact extraction job {job_id} for conversation {conversation_id}"
    )

    try:
        # Create processing job record
        with Session(engine) as session:
            job = ProcessingJob(
                id=job_id,
                job_type="fact_extraction",
                status="processing",
                user_id=user_id,
                input_data=json.dumps({"conversation_id": conversation_id}),
                started_at=datetime.now(UTC),
            )
            session.add(job)
            session.commit()

        # Get conversation data
        conversation = DatabaseService.get_conversation_memory(conversation_id)
        if not conversation:
            return {
                "status": "conversation_not_found",
                "conversation_id": conversation_id,
            }

        # Get user context
        user = DatabaseService.get_user_by_id(user_id)
        user_context = {
            "user_id": user_id,
            "name": user.name,
            "degree": user.degree,
            "year": user.year,
            "goal": user.goal,
            "biggest_worry": user.biggest_worry,
            "skills": json.loads(user.skills) if user.skills else [],
        }

        # Initialize mentor agent for fact extraction
        mentor = MentorAgent()

        # Perform fact extraction
        extraction_result = await mentor.process(
            {
                "message": conversation.content,
                "user_context": user_context,
                "type": "analysis",
            }
        )

        # Process extracted facts
        extracted_facts = extraction_result.get("extracted_facts", {})
        facts_count = extraction_result.get("fact_count", 0)

        # Store high-confidence facts
        stored_facts = []
        if facts_count > 0:
            for fact in extracted_facts.get("facts", []):
                confidence = fact.get("confidence", 0)
                if confidence >= 0.8:  # High confidence threshold
                    # Store individual fact as memory
                    fact_memory_id = await mem0_manager.add_conversation_memory(
                        user_id=user_id,
                        messages=[
                            {
                                "content": f"Fact: {fact.get('field', '')} = {fact.get('value', '')}",
                                "is_user": False,
                            }
                        ],
                        metadata={
                            "fact_type": fact.get("category", "unknown"),
                            "confidence": confidence,
                            "source": "fact_extraction",
                            "original_conversation_id": conversation_id,
                            "extraction_job_id": job_id,
                        },
                    )
                    stored_facts.append(
                        {
                            "field": fact.get("field"),
                            "value": fact.get("value"),
                            "confidence": confidence,
                            "memory_id": fact_memory_id,
                        }
                    )

        # Complete the job
        with Session(engine) as session:
            job = session.get(ProcessingJob, job_id)
            if job:
                job.status = "completed"
                job.completed_at = datetime.now(UTC)
                job.result_data = json.dumps(
                    {
                        "facts_extracted": facts_count,
                        "high_confidence_facts": len(stored_facts),
                        "stored_facts": stored_facts,
                    }
                )
                session.commit()

        result = {
            "status": "completed",
            "conversation_id": conversation_id,
            "facts_extracted": facts_count,
            "high_confidence_facts": len(stored_facts),
            "stored_facts": stored_facts,
        }

        print(f"✅ Fact extraction completed: {result}")
        return result

    except Exception as e:
        print(f"❌ Fact extraction failed: {e}")

        # Mark job as failed
        with Session(engine) as session:
            job = session.get(ProcessingJob, job_id)
            if job:
                job.status = "failed"
                job.completed_at = datetime.now(UTC)
                job.error_message = str(e)
                session.commit()

        # Retry if not max retries
        if self.request.retries < 3:
            print(f"🔄 Retrying fact extraction (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))

        return {
            "status": "failed",
            "conversation_id": conversation_id,
            "error": str(e),
            "retries": self.request.retries,
        }


@celery_app.task
def batch_extract_facts(user_id: str, limit: int = 10) -> Dict[str, Any]:
    """Batch extract facts from recent conversations for a user."""

    print(f"🔄 Starting batch fact extraction for user {user_id}")

    try:
        # Get recent conversations without fact extraction
        with Session(engine) as session:
            recent_conversations = session.exec(
                select(ConversationMemory)
                .where(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.memory_type == "conversation",
                )
                .order_by(ConversationMemory.created_at.desc())
                .limit(limit)
            ).all()

        extraction_jobs = []
        for conversation in recent_conversations:
            # Start individual extraction job
            job = extract_facts_from_conversation.delay(conversation.id, user_id)
            extraction_jobs.append(
                {"conversation_id": conversation.id, "job_id": job.id}
            )

        return {
            "status": "started",
            "user_id": user_id,
            "conversations_queued": len(extraction_jobs),
            "extraction_jobs": extraction_jobs,
        }

    except Exception as e:
        print(f"❌ Batch fact extraction failed: {e}")
        return {"status": "failed", "user_id": user_id, "error": str(e)}


@celery_app.task
async def update_user_profile_from_facts(user_id: str) -> Dict[str, Any]:
    """Update user profile based on extracted facts."""

    print(f"🔄 Updating user profile from facts for user {user_id}")

    try:
        # Get high-confidence facts from memory
        if not mem0_manager.enabled:
            return {"status": "memory_disabled"}

        # Search for fact-type memories
        fact_memories = await mem0_manager.search_relevant_memories(
            user_id=user_id, query="Fact:", limit=50, threshold=0.9
        )

        # Process facts into profile updates
        profile_updates = {}
        confidence_scores = {}

        for memory in fact_memories:
            metadata = memory.get("metadata", {})
            if metadata.get("source") == "fact_extraction":
                content = memory.get("content", "")
                confidence = metadata.get("confidence", 0)

                # Parse fact content (simplified)
                if " = " in content:
                    try:
                        field, value = content.split(" = ", 1)
                        field = field.replace("Fact: ", "").strip()

                        # Only update if higher confidence than existing
                        if (
                            field not in confidence_scores
                            or confidence > confidence_scores[field]
                        ):
                            profile_updates[field] = value
                            confidence_scores[field] = confidence
                    except:
                        continue

        # Update user profile
        updated_fields = 0
        if profile_updates:
            # Map fact fields to user model fields (customize as needed)
            field_mapping = {
                "major": "degree",
                "academic_year": "year",
                "career_goal": "goal",
                "main_concern": "biggest_worry",
                "favorite_subject": "fav_subject",
                # Add more mappings as needed
            }

            mapped_updates = {}
            for fact_field, value in profile_updates.items():
                if fact_field in field_mapping:
                    user_field = field_mapping[fact_field]
                    mapped_updates[user_field] = value
                    updated_fields += 1

            if mapped_updates:
                DatabaseService.update_user_profile(user_id, **mapped_updates)

        return {
            "status": "completed",
            "user_id": user_id,
            "facts_processed": len(fact_memories),
            "profile_updates": updated_fields,
            "updated_fields": list(profile_updates.keys()),
        }

    except Exception as e:
        print(f"❌ Profile update from facts failed: {e}")
        return {"status": "failed", "user_id": user_id, "error": str(e)}
