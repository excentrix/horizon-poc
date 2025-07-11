# backend/src/background/tasks/__init__.py
"""
Background task modules for Horizon AI Mentor.

Available task modules:
- session_analysis: Post-session conversation analysis
- fact_extraction: Extract and process user facts
- memory_consolidation: Optimize and consolidate memories
- maintenance: System maintenance and health checks
"""

# Import all task modules to register them with Celery
from . import session_analysis
from . import fact_extraction
from . import memory_consolidation
from . import maintenance

__all__ = [
    'session_analysis',
    'fact_extraction', 
    'memory_consolidation',
    'maintenance'
]