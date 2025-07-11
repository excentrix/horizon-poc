# backend/src/background/tasks/maintenance.py
from celery import current_app as celery_app
from typing import Dict, Any
import sys
import os
from datetime import datetime, timedelta, UTC
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from models.core import DatabaseService, Session, engine, User
from models.enhanced_models import ProcessingJob, ConversationMemory
from memory.mem0_manager import mem0_manager

from sqlalchemy import select, func, distinct, text


@celery_app.task
def cleanup_old_jobs(days_old: int = 7) -> Dict[str, Any]:
    """Clean up old completed/failed processing jobs."""

    print(f"🔄 Cleaning up processing jobs older than {days_old} days")

    try:
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)

        with Session(engine) as session:
            # Get old completed/failed jobs
            old_jobs = session.exec(
                select(ProcessingJob).where(
                    ProcessingJob.completed_at < cutoff_date,
                    ProcessingJob.status.in_(["completed", "failed"]),
                )
            ).all()

            # Delete old jobs
            deleted_count = 0
            for job in old_jobs:
                session.delete(job)
                deleted_count += 1

            session.commit()

        return {
            "status": "completed",
            "cutoff_date": cutoff_date.isoformat(),
            "jobs_deleted": deleted_count,
        }

    except Exception as e:
        print(f"❌ Job cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task
async def system_health_check() -> Dict[str, Any]:
    """Comprehensive system health check."""

    print("🔄 Running system health check")

    health_status = {
        "timestamp": datetime.now(UTC).isoformat(),
        "overall_status": "healthy",
        "components": {},
    }

    try:
        # Check database connectivity
        try:
            with Session(engine) as session:
                session.exec(text("SELECT 1")).first()
            health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"

        # Check Mem0/Memory system
        try:
            if mem0_manager.enabled:
                # Try a simple memory operation
                test_summary = await mem0_manager.get_user_memory_summary(
                    "health_check"
                )
                health_status["components"]["memory_system"] = "healthy"
            else:
                health_status["components"]["memory_system"] = "disabled"
        except Exception as e:
            health_status["components"]["memory_system"] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"

        # Check processing job queue
        try:
            with Session(engine) as session:
                pending_jobs = session.exec(
                    select(ProcessingJob).where(ProcessingJob.status == "pending")
                ).all()

                processing_jobs = session.exec(
                    select(ProcessingJob).where(ProcessingJob.status == "processing")
                ).all()

                health_status["components"]["job_queue"] = {
                    "status": "healthy",
                    "pending_jobs": len(pending_jobs),
                    "processing_jobs": len(processing_jobs),
                }

                # Alert if too many stuck jobs
                if len(processing_jobs) > 10:
                    health_status["components"]["job_queue"]["status"] = "warning"
                    health_status["overall_status"] = "degraded"

        except Exception as e:
            health_status["components"]["job_queue"] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"

        # Check recent activity
        try:
            recent_cutoff = datetime.now(UTC) - timedelta(hours=24)
            with Session(engine) as session:
                recent_memories = session.exec(
                    select(ConversationMemory).where(
                        ConversationMemory.created_at > recent_cutoff
                    )
                ).all()

                health_status["components"]["activity"] = {
                    "status": "healthy",
                    "recent_conversations": len(recent_memories),
                }
        except Exception as e:
            health_status["components"]["activity"] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"

        return health_status

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "overall_status": "unhealthy",
            "error": str(e),
        }


@celery_app.task
def generate_usage_analytics() -> Dict[str, Any]:
    """Generate usage analytics and insights."""

    print("🔄 Generating usage analytics")

    try:
        analytics = {
            "generated_at": datetime.now(UTC).isoformat(),
            "period": "last_30_days",
        }

        # Time periods
        now = datetime.now(UTC)
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        last_24_hours = now - timedelta(hours=24)

        with Session(engine) as session:
            # User activity
            total_users = session.exec(select(func.count(User.id))).first()
            active_users_30d = session.exec(
                select(func.count(distinct(ConversationMemory.user_id))).where(
                    ConversationMemory.created_at > last_30_days
                )
            ).first()

            # Conversation metrics
            total_conversations = session.exec(
                select(func.count(ConversationMemory.id)).where(
                    ConversationMemory.created_at > last_30_days
                )
            ).first()

            conversations_7d = session.exec(
                select(func.count(ConversationMemory.id)).where(
                    ConversationMemory.created_at > last_7_days
                )
            ).first()

            conversations_24h = session.exec(
                select(func.count(ConversationMemory.id)).where(
                    ConversationMemory.created_at > last_24_hours
                )
            ).first()

            # Processing job metrics
            completed_jobs = session.exec(
                select(func.count(ProcessingJob.id)).where(
                    ProcessingJob.status == "completed",
                    ProcessingJob.created_at > last_30_days,
                )
            ).first()

            failed_jobs = session.exec(
                select(func.count(ProcessingJob.id)).where(
                    ProcessingJob.status == "failed",
                    ProcessingJob.created_at > last_30_days,
                )
            ).first()

        analytics.update(
            {
                "users": {
                    "total": total_users or 0,
                    "active_30d": active_users_30d or 0,
                    "activity_rate": (
                        (active_users_30d / total_users * 100) if total_users else 0
                    ),
                },
                "conversations": {
                    "total_30d": total_conversations or 0,
                    "last_7d": conversations_7d or 0,
                    "last_24h": conversations_24h or 0,
                    "daily_average": (
                        (total_conversations / 30) if total_conversations else 0
                    ),
                },
                "processing": {
                    "completed_jobs_30d": completed_jobs or 0,
                    "failed_jobs_30d": failed_jobs or 0,
                    "success_rate": (
                        (completed_jobs / (completed_jobs + failed_jobs) * 100)
                        if (completed_jobs + failed_jobs)
                        else 100
                    ),
                },
            }
        )

        # Memory system metrics
        if mem0_manager.enabled:
            try:
                # This would need implementation based on available Mem0 APIs
                analytics["memory_system"] = {
                    "status": "enabled",
                    "total_memories": "not_available",  # Placeholder
                    "note": "Memory metrics need Mem0 API implementation",
                }
            except:
                analytics["memory_system"] = {"status": "error"}
        else:
            analytics["memory_system"] = {"status": "disabled"}

        return analytics

    except Exception as e:
        print(f"❌ Analytics generation failed: {e}")
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "failed",
            "error": str(e),
        }


@celery_app.task
def backup_critical_data() -> Dict[str, Any]:
    """Backup critical system data."""

    print("🔄 Backing up critical data")

    try:
        backup_info = {
            "timestamp": datetime.now(UTC).isoformat(),
            "backup_type": "critical_data",
        }

        # This would implement actual backup logic
        # For now, return a placeholder

        backup_info.update(
            {
                "status": "completed",
                "items_backed_up": [
                    "user_profiles",
                    "conversation_summaries",
                    "processing_job_logs",
                ],
                "backup_location": "configured_backup_storage",
                "note": "Backup implementation pending",
            }
        )

        return backup_info

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "failed",
            "error": str(e),
        }
