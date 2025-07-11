# backend/src/background/__init__.py
"""
Background processing module for Horizon AI Mentor.

This module contains all background tasks for:
- Session analysis and fact extraction
- Memory consolidation and optimization
- System maintenance and health checks
- Usage analytics and reporting
"""

from .celery_app import celery_app

__all__ = ['celery_app']