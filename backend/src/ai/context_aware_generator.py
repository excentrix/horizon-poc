# backend/src/ai/context_aware_generator.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import json
from openai import AsyncAzureOpenAI
import os

class ResponseContext(BaseModel):
    user_profile_completeness: float
    conversation_stage: str  # introduction, exploration, goal_setting, problem_solving, follow_up
    mentoring_approach: str  # supportive, challenging, informative, motivational
    personalization_level: str  # high, medium, low

class ContextAwareGenerator:
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-06"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    async def generate_contextual_response(
        self,
        message: str,
        user_context: Dict[str, Any],
        extracted_facts: List[Any],
        user_intent: str,
        emotional_state: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate context-aware, personalized mentoring response."""
        
        # Analyze conversation context
        response_context = self._analyze_response_context(user_context, conversation_history)
        
        # Build comprehensive context for response generation
        context_summary = self._build_comprehensive_context(
            user_context, extracted_facts, response_context
        )
        
        # Generate personalized response
        response_prompt = f"""
You are Horizon, an expert AI learning mentor. You're having a conversation with a student, and you need to provide a helpful, personalized response based on their context and needs.

STUDENT CONTEXT:
{context_summary}

CONVERSATION ANALYSIS:
- User Intent: {user_intent}
- Emotional State: {emotional_state}
- Profile Completeness: {response_context.user_profile_completeness:.1%}
- Conversation Stage: {response_context.conversation_stage}
- Recommended Approach: {response_context.mentoring_approach}

STUDENT'S MESSAGE: "{message}"

RECENTLY DISCOVERED FACTS:
{self._format_extracted_facts(extracted_facts)}

MENTORING PRINCIPLES:
1. Be supportive but constructively challenging
2. Reference their specific context, goals, and challenges
3. Provide actionable advice tailored to their situation
4. Ask thoughtful follow-up questions to deepen understanding
5. Celebrate progress and acknowledge their efforts
6. Connect current discussion to their broader academic/career goals

RESPONSE GUIDELINES:
- If profile is incomplete (<50%), gently gather more context while helping
- If they're struggling emotionally, prioritize support before solutions
- If they have clear goals, focus on concrete next steps
- If they're exploring, help them discover direction
- Reference their specific degree, year, skills, and challenges when relevant
- Keep responses conversational but substantive (2-4 paragraphs ideal)

Generate a natural, helpful response that feels like talking to an experienced mentor who knows them well.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are Horizon, an empathetic and intelligent AI learning mentor focused on helping students achieve their academic and career goals."
                    },
                    {"role": "user", "content": response_prompt}
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Context-aware response generation error: {e}")
            return "I apologize, but I'm having trouble processing your message right now. Could you please try again?"
    
    def _analyze_response_context(
        self, 
        user_context: Dict[str, Any], 
        conversation_history: List[Dict[str, str]] = None
    ) -> ResponseContext:
        """Analyze the context to determine appropriate response strategy."""
        
        # Calculate profile completeness
        profile_fields = ["name", "degree", "year", "goal", "biggest_worry", "fav_subject", "skills", "gpa"]
        completed_fields = sum(1 for field in profile_fields if user_context.get(field))
        completeness = completed_fields / len(profile_fields)
        
        # Determine conversation stage
        message_count = len(conversation_history) if conversation_history else 0
        if message_count < 3:
            stage = "introduction"
        elif completeness < 0.5:
            stage = "exploration"
        elif user_context.get("goal") and not user_context.get("biggest_worry"):
            stage = "goal_setting"
        else:
            stage = "problem_solving"
        
        # Determine mentoring approach based on context
        if user_context.get("biggest_worry"):
            approach = "supportive"
        elif user_context.get("goal") and completeness > 0.7:
            approach = "challenging"
        elif completeness < 0.4:
            approach = "informative"
        else:
            approach = "motivational"
        
        # Determine personalization level
        if completeness > 0.6:
            personalization = "high"
        elif completeness > 0.3:
            personalization = "medium"
        else:
            personalization = "low"
        
        return ResponseContext(
            user_profile_completeness=completeness,
            conversation_stage=stage,
            mentoring_approach=approach,
            personalization_level=personalization
        )
    
    def _build_comprehensive_context(
        self, 
        user_context: Dict[str, Any], 
        extracted_facts: List[Any],
        response_context: ResponseContext
    ) -> str:
        """Build comprehensive context summary for response generation."""
        
        context_parts = []
        
        # Basic profile
        if user_context.get("name"):
            context_parts.append(f"Student: {user_context['name']}")
        
        # Academic context
        academic_info = []
        if user_context.get("degree"):
            academic_info.append(user_context["degree"])
        if user_context.get("year"):
            academic_info.append(f"Year {user_context['year']}")
        if user_context.get("gpa"):
            academic_info.append(f"GPA: {user_context['gpa']}")
        if academic_info:
            context_parts.append(f"Academic: {', '.join(academic_info)}")
        
        # Goals and challenges
        if user_context.get("goal"):
            context_parts.append(f"Primary Goal: {user_context['goal']}")
        if user_context.get("biggest_worry"):
            context_parts.append(f"Main Challenge: {user_context['biggest_worry']}")
        if user_context.get("fav_subject"):
            context_parts.append(f"Favorite Subject: {user_context['fav_subject']}")
        
        # Skills
        if user_context.get("skills"):
            skills = user_context["skills"]
            if skills:
                context_parts.append(f"Skills: {', '.join(skills[:5])}")
        
        return "\n".join(context_parts) if context_parts else "New student - limited context available"
    
    def _format_extracted_facts(self, extracted_facts: List[Any]) -> str:
        """Format recently extracted facts for context."""
        if not extracted_facts:
            return "No new facts discovered in this message"
        
        fact_summaries = []
        for fact in extracted_facts:
            fact_summaries.append(f"- {fact.field}: {fact.value} (confidence: {fact.confidence:.2f})")
        
        return "\n".join(fact_summaries)