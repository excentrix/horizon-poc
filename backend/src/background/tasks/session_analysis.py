# backend/src/background/tasks/session_analysis.py (updated complete version)
from celery import current_app as celery_app
from typing import Dict, Any, List
import sys
import os
from datetime import datetime, UTC
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.mentor_agent import MentorAgent
from models.core import DatabaseService, Session, engine
from models.enhanced_models import ProcessingJob, SessionSummary
from memory.mem0_manager import mem0_manager


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3, "countdown": 60})
async def analyze_session_end(self, session_id: str, user_id: str) -> Dict[str, Any]:
    """Comprehensive session analysis after conversation ends."""

    job_id = self.request.id
    print(
        f"🔄 Starting comprehensive session analysis {job_id} for session {session_id}"
    )

    try:
        # Create processing job record
        with Session(engine) as session_db:
            job = ProcessingJob(
                id=job_id,
                job_type="session_analysis",
                status="processing",
                session_id=session_id,
                user_id=user_id,
                started_at=datetime.now(UTC),
                input_data=json.dumps(
                    {"session_id": session_id, "analysis_type": "comprehensive"}
                ),
            )
            session_db.add(job)
            session_db.commit()

        # Get session messages
        messages = DatabaseService.get_session_messages(session_id)
        if not messages:
            return {"status": "no_messages", "session_id": session_id}

        print(f"📊 Analyzing {len(messages)} messages from session {session_id}")

        # Get user context
        user = DatabaseService.get_user_by_id(user_id)
        user_context = {
            "user_id": user_id,
            "session_id": session_id,
            "name": user.name,
            "email": user.email,
            "degree": user.degree,
            "year": user.year,
            "goal": user.goal,
            "biggest_worry": user.biggest_worry,
            "fav_subject": user.fav_subject,
            "skills": json.loads(user.skills) if user.skills else [],
        }

        # Initialize mentor agent
        mentor = MentorAgent()

        # Format conversation for analysis
        conversation_text = ""
        conversation_messages = []

        for msg in messages:
            role = "User" if msg.is_user else "Assistant"
            conversation_text += f"{role}: {msg.content}\n"
            conversation_messages.append(
                {
                    "content": msg.content,
                    "is_user": msg.is_user,
                    "timestamp": msg.created_at.isoformat(),
                    "message_id": msg.id,
                }
            )

        analysis_results = {}

        # 1. Fact Extraction Analysis
        print("🔍 Performing fact extraction...")
        fact_analysis = await mentor.process(
            {
                "message": conversation_text,
                "user_context": user_context,
                "type": "analysis",
            }
        )

        extracted_facts = fact_analysis.get("extracted_facts", {})
        facts_count = fact_analysis.get("fact_count", 0)
        analysis_results["fact_extraction"] = {
            "facts_count": facts_count,
            "extracted_facts": extracted_facts,
        }

        # 2. Session Summarization
        print("📝 Creating session summary...")
        summary_analysis = await mentor.process(
            {
                "message": "Create a comprehensive summary of this learning session",
                "user_context": user_context,
                "conversation_history": conversation_messages,
                "type": "summary",
            }
        )

        session_summary = summary_analysis.get("response", "")
        analysis_results["session_summary"] = {
            "summary": session_summary,
            "summary_length": len(session_summary),
        }

        # 3. Store conversation in Mem0
        print("💾 Storing conversation in memory system...")
        memory_id = None
        if mem0_manager.enabled:
            memory_id = await mem0_manager.add_conversation_memory(
                user_id=user_id,
                messages=conversation_messages,
                metadata={
                    "session_id": session_id,
                    "analysis_job_id": job_id,
                    "message_count": len(messages),
                    "facts_extracted": facts_count,
                    "session_type": "comprehensive_analysis",
                },
            )

        analysis_results["memory_storage"] = {
            "memory_id": memory_id,
            "system": "mem0" if mem0_manager.enabled else "disabled",
        }

        # 4. Update user profile with high-confidence facts
        print("👤 Updating user profile...")
        profile_updates = {}
        if facts_count > 0 and extracted_facts:
            for fact in extracted_facts.get("facts", []):
                confidence = fact.get("confidence", 0)
                if confidence >= 0.85:  # Very high confidence only
                    field = fact.get("field", "")
                    value = fact.get("value", "")

                    # Map fact fields to user profile fields
                    field_mappings = {
                        "major": "degree",
                        "academic_year": "year",
                        "career_goal": "goal",
                        "main_worry": "biggest_worry",
                        "favorite_subject": "fav_subject",
                    }

                    if field in field_mappings:
                        profile_field = field_mappings[field]
                        profile_updates[profile_field] = value

            if profile_updates:
                DatabaseService.update_user_profile(user_id, **profile_updates)

        analysis_results["profile_updates"] = {
            "updated_fields": list(profile_updates.keys()),
            "update_count": len(profile_updates),
        }

        # 5. Store session summary in database
        print("💽 Storing session summary...")
        summary_record = SessionSummary(
            session_id=session_id,
            user_id=user_id,
            summary=session_summary,
            key_topics=json.dumps(extracted_facts.get("conversation_summary", "")),
            facts_extracted=json.dumps(extracted_facts),
            emotional_tone=extracted_facts.get("emotional_tone", "neutral"),
            learning_progress=json.dumps(
                {
                    "facts_learned": facts_count,
                    "profile_updates": len(profile_updates),
                    "engagement_level": "high",  # Could be calculated
                }
            ),
            message_count=len(messages),
        )

        with Session(engine) as session_db:
            session_db.add(summary_record)
            session_db.commit()
            session_db.refresh(summary_record)

        analysis_results["database_storage"] = {
            "summary_id": summary_record.id,
            "stored": True,
        }

        # 6. Complete the processing job
        print("✅ Completing analysis job...")
        with Session(engine) as session_db:
            job = session_db.get(ProcessingJob, job_id)
            if job:
                job.status = "completed"
                job.completed_at = datetime.now(UTC)
                job.result_data = json.dumps(analysis_results)
                session_db.commit()

        # 7. Trigger follow-up tasks if needed
        if facts_count > 5:  # Lots of facts extracted
            from .fact_extraction import update_user_profile_from_facts

            update_user_profile_from_facts.delay(user_id)

        final_result = {
            "status": "completed",
            "session_id": session_id,
            "user_id": user_id,
            "analysis_results": analysis_results,
            "processing_time": "calculated",  # TODO: Add actual timing
            "follow_up_tasks": ["profile_update"] if facts_count > 5 else [],
        }

        print(f"🎉 Session analysis completed successfully: {final_result}")
        return final_result

    except Exception as e:
        print(f"❌ Session analysis failed: {e}")
        import traceback

        traceback.print_exc()

        # Mark job as failed
        with Session(engine) as session_db:
            job = session_db.get(ProcessingJob, job_id)
            if job:
                job.status = "failed"
                job.completed_at = datetime.now(UTC)
                job.error_message = str(e)
                session_db.commit()

        # Retry if not max retries
        if self.request.retries < 3:
            print(f"🔄 Retrying session analysis (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))

        return {
            "status": "failed",
            "session_id": session_id,
            "error": str(e),
            "retries": self.request.retries,
        }


@celery_app.task
def analyze_multiple_sessions(session_ids: List[str], user_id: str) -> Dict[str, Any]:
    """Analyze multiple sessions in batch."""

    print(f"🔄 Starting batch analysis for {len(session_ids)} sessions")

    analysis_jobs = []
    for session_id in session_ids:
        job = analyze_session_end.delay(session_id, user_id)
        analysis_jobs.append({"session_id": session_id, "job_id": job.id})

    return {
        "status": "started",
        "user_id": user_id,
        "sessions_queued": len(session_ids),
        "analysis_jobs": analysis_jobs,
    }
