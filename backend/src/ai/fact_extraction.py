# backend/src/ai/fact_extraction.py
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel
import json
import asyncio
from openai import AsyncAzureOpenAI
import os

class ExtractedFact(BaseModel):
    field: str
    value: Any
    confidence: float
    source_text: str
    reasoning: str

class FactExtractionResult(BaseModel):
    facts: List[ExtractedFact]
    user_intent: str
    emotional_state: str
    suggested_follow_up: Optional[str]

class FactExtractionPipeline:
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-06"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    async def extract_facts(
        self, 
        message: str, 
        user_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> FactExtractionResult:
        """Extract structured facts from user message with confidence scoring."""
        
        # Build context for fact extraction
        context_summary = self._build_context_summary(user_context)
        history_summary = self._build_history_summary(conversation_history or [])
        
        extraction_prompt = f"""
You are an expert AI mentor analyzing a student's message to extract key information for building their academic profile.

CURRENT USER CONTEXT:
{context_summary}

RECENT CONVERSATION:
{history_summary}

USER'S LATEST MESSAGE:
"{message}"

TASK: Extract structured facts from this message that would be useful for academic mentoring.

EXTRACTION RULES:
1. Only extract facts that are explicitly stated or strongly implied
2. Assign confidence scores: 0.9+ (explicitly stated), 0.7-0.8 (strongly implied), 0.5-0.6 (suggested)
3. Focus on academic, career, and personal development information
4. Don't extract facts that contradict existing confirmed information

FACT CATEGORIES TO LOOK FOR:
- Academic: degree, year, major, GPA, courses, academic challenges
- Skills: technical skills, soft skills, programming languages, tools
- Goals: career goals, academic goals, immediate objectives
- Challenges: biggest worries, current struggles, obstacles
- Interests: favorite subjects, hobbies, passions
- Experience: internships, projects, work experience
- Timeline: deadlines, important dates, milestones

RESPONSE FORMAT (JSON):
{{
    "facts": [
        {{
            "field": "degree|year|gpa|skills|goal|biggest_worry|fav_subject|[custom_field]",
            "value": "extracted_value",
            "confidence": 0.95,
            "source_text": "relevant part of user message",
            "reasoning": "why this fact was extracted"
        }}
    ],
    "user_intent": "what the user is trying to accomplish",
    "emotional_state": "user's current emotional state/tone",
    "suggested_follow_up": "natural follow-up question or suggestion"
}}

IMPORTANT: Only extract facts with confidence >= 0.5. Be conservative and accurate.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Validate and clean extracted facts
            validated_facts = []
            for fact_data in result_json.get("facts", []):
                try:
                    fact = ExtractedFact(**fact_data)
                    if fact.confidence >= 0.5:  # Only include confident facts
                        validated_facts.append(fact)
                except Exception as e:
                    print(f"⚠️ Invalid fact extracted: {fact_data}, error: {e}")
            
            return FactExtractionResult(
                facts=validated_facts,
                user_intent=result_json.get("user_intent", "unclear"),
                emotional_state=result_json.get("emotional_state", "neutral"),
                suggested_follow_up=result_json.get("suggested_follow_up")
            )
            
        except Exception as e:
            print(f"❌ Fact extraction error: {e}")
            return FactExtractionResult(
                facts=[],
                user_intent="unclear",
                emotional_state="neutral",
                suggested_follow_up=None
            )
    
    def _build_context_summary(self, user_context: Dict[str, Any]) -> str:
        """Build a summary of current user context."""
        context_parts = []
        
        if user_context.get("name"):
            context_parts.append(f"Name: {user_context['name']}")
        if user_context.get("degree"):
            context_parts.append(f"Degree: {user_context['degree']}")
        if user_context.get("year"):
            context_parts.append(f"Year: {user_context['year']}")
        if user_context.get("goal"):
            context_parts.append(f"Goal: {user_context['goal']}")
        if user_context.get("biggest_worry"):
            context_parts.append(f"Main Concern: {user_context['biggest_worry']}")
        if user_context.get("skills"):
            skills = user_context["skills"]
            if skills:
                context_parts.append(f"Skills: {', '.join(skills[:5])}")  # First 5 skills
        
        return "\n".join(context_parts) if context_parts else "No context available"
    
    def _build_history_summary(self, conversation_history: List[Dict[str, str]]) -> str:
        """Build a summary of recent conversation."""
        if not conversation_history:
            return "No previous conversation"
        
        # Get last 3 exchanges
        recent_messages = conversation_history[-6:]  # Last 3 user + AI messages
        
        summary = []
        for msg in recent_messages:
            role = "User" if msg.get("is_user") else "AI"
            content = msg.get("content", "")[:100]  # First 100 chars
            summary.append(f"{role}: {content}")
        
        return "\n".join(summary)