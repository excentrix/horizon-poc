# backend/src/ai/task_creation.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
from openai import AsyncAzureOpenAI
import os

class SuggestedTask(BaseModel):
    title: str
    description: str
    priority: str  # low, medium, high, urgent
    estimated_duration: str  # "30 minutes", "2 hours", "1 week"
    due_date_suggestion: Optional[str]  # relative like "in 3 days" or "next week"
    category: str  # academic, career, skill_building, research
    confidence: float
    reasoning: str

class TaskCreationResult(BaseModel):
    tasks: List[SuggestedTask]
    should_create_tasks: bool
    context_analysis: str

class TaskCreationEngine:
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-06"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    async def analyze_for_tasks(
        self,
        message: str,
        user_context: Dict[str, Any],
        user_intent: str,
        emotional_state: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> TaskCreationResult:
        """Analyze conversation for actionable task creation opportunities."""
        
        context_summary = self._build_context_summary(user_context)
        
        task_analysis_prompt = f"""
You are an expert AI mentor analyzing a conversation to determine if actionable tasks should be created for the student.

USER CONTEXT:
{context_summary}

USER'S MESSAGE: "{message}"
USER INTENT: {user_intent}
EMOTIONAL STATE: {emotional_state}

TASK CREATION GUIDELINES:
1. Only suggest tasks when the user explicitly mentions goals, problems, or asks for help
2. Tasks should be SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
3. Consider the user's current academic level and constraints
4. Don't overwhelm - suggest 1-3 relevant tasks maximum
5. Tasks should directly address the user's stated needs or goals

TASK CATEGORIES:
- academic: homework, studying, research, assignments
- career: job applications, networking, skill building
- skill_building: learning new technologies, practice projects
- research: exploring career paths, academic programs

WHEN TO CREATE TASKS:
✅ User mentions specific goals or deadlines
✅ User asks for help with something actionable
✅ User expresses challenges that need structured approach
✅ User mentions wanting to learn or improve something

WHEN NOT TO CREATE TASKS:
❌ General conversation or questions
❌ User is just sharing information
❌ Emotional support conversations
❌ Simple clarification questions

RESPONSE FORMAT (JSON):
{{
    "should_create_tasks": true/false,
    "context_analysis": "explanation of why tasks should/shouldn't be created",
    "tasks": [
        {{
            "title": "Clear, actionable task title",
            "description": "Detailed description with specific steps",
            "priority": "low|medium|high|urgent",
            "estimated_duration": "realistic time estimate",
            "due_date_suggestion": "relative timeframe like 'in 3 days'",
            "category": "academic|career|skill_building|research",
            "confidence": 0.85,
            "reasoning": "why this task is relevant and helpful"
        }}
    ]
}}

Be conservative - only create tasks when they would genuinely help the user achieve their goals.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": task_analysis_prompt}],
                temperature=0.2,  # Low temperature for consistent task creation
                max_tokens=1200,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Validate and process suggested tasks
            validated_tasks = []
            for task_data in result_json.get("tasks", []):
                try:
                    task = SuggestedTask(**task_data)
                    if task.confidence >= 0.7:  # Only high-confidence tasks
                        validated_tasks.append(task)
                except Exception as e:
                    print(f"⚠️ Invalid task suggested: {task_data}, error: {e}")
            
            return TaskCreationResult(
                tasks=validated_tasks,
                should_create_tasks=result_json.get("should_create_tasks", False),
                context_analysis=result_json.get("context_analysis", "")
            )
            
        except Exception as e:
            print(f"❌ Task creation analysis error: {e}")
            return TaskCreationResult(
                tasks=[],
                should_create_tasks=False,
                context_analysis="Error analyzing for tasks"
            )
    
    def _build_context_summary(self, user_context: Dict[str, Any]) -> str:
        """Build context summary for task creation."""
        context_parts = []
        
        if user_context.get("name"):
            context_parts.append(f"Student: {user_context['name']}")
        if user_context.get("degree") and user_context.get("year"):
            context_parts.append(f"Academic: {user_context['year']} year {user_context['degree']} student")
        if user_context.get("goal"):
            context_parts.append(f"Primary Goal: {user_context['goal']}")
        if user_context.get("biggest_worry"):
            context_parts.append(f"Main Challenge: {user_context['biggest_worry']}")
        if user_context.get("gpa"):
            context_parts.append(f"GPA: {user_context['gpa']}")
        
        return "\n".join(context_parts) if context_parts else "Limited context available"
    
    def _parse_relative_date(self, relative_date: str) -> Optional[datetime]:
        """Convert relative date suggestions to actual dates."""
        try:
            relative_date = relative_date.lower().strip()
            now = datetime.now()
            
            if "today" in relative_date:
                return now
            elif "tomorrow" in relative_date:
                return now + timedelta(days=1)
            elif "in 3 days" in relative_date:
                return now + timedelta(days=3)
            elif "next week" in relative_date:
                return now + timedelta(weeks=1)
            elif "in a week" in relative_date:
                return now + timedelta(weeks=1)
            elif "in 2 weeks" in relative_date:
                return now + timedelta(weeks=2)
            elif "next month" in relative_date:
                return now + timedelta(days=30)
            
            return None
        except:
            return None