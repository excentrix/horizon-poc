# backend/src/chains/horizon_chat.py
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function
from typing import Dict, List, Optional, Any
import os
import json
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Define extraction schemas as tools
@tool
def extract_user_facts(
    degree: Optional[str] = None,
    year: Optional[int] = None,
    goal: Optional[str] = None,
    biggest_worry: Optional[str] = None,
    fav_subject: Optional[str] = None,
    skills: Optional[List[str]] = None,
    gpa: Optional[float] = None
) -> Dict[str, Any]:
    """Extract and update user profile information from conversation."""
    return {
        "type": "profile_update",
        "data": {
            "degree": degree,
            "year": year,
            "goal": goal,
            "biggest_worry": biggest_worry,
            "fav_subject": fav_subject,
            "skills": skills,
            "gpa": gpa
        }
    }

@tool
def create_learning_task(
    title: str,
    description: str,
    priority: str = "medium",
    due_days: int = 7
) -> Dict[str, Any]:
    """Create a learning task for the user."""
    due_date = datetime.utcnow() + timedelta(days=due_days)
    return {
        "type": "task_creation",
        "data": {
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date.isoformat()
        }
    }

@tool
def summarize_session(
    summary: str,
    key_topics: List[str],
    next_steps: List[str]
) -> Dict[str, Any]:
    """Summarize the current chat session."""
    return {
        "type": "session_summary",
        "data": {
            "summary": summary,
            "key_topics": key_topics,
            "next_steps": next_steps
        }
    }

class HorizonChatChain:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            temperature=0.7,
            streaming=True,
        )
        
        # Bind tools to LLM
        self.tools = [extract_user_facts, create_learning_task, summarize_session]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
    def _build_system_prompt(self, user_context: Dict = None) -> str:
        """Build dynamic system prompt based on user context."""
        base_prompt = """You are Horizon, an AI learning mentor designed to help students achieve their academic and career goals.

Your personality:
- Encouraging and supportive, never judgmental
- Practical and action-oriented
- Knowledgeable about education and career paths
- Empathetic to student struggles and anxieties

Your capabilities:
1. **Profile Building**: Extract key information about the user's background, goals, and concerns
2. **Learning Guidance**: Provide personalized advice based on their profile
3. **Task Creation**: Suggest specific, actionable learning tasks
4. **Progress Tracking**: Help users stay motivated and on track

Core principles:
- Always be specific and actionable in your advice
- Break down complex goals into manageable steps
- Acknowledge emotions and provide encouragement
- Use the user's context to personalize responses
- Create tasks that are realistic and time-bound
"""
        
        if user_context:
            context_str = f"\nCurrent user context:\n{json.dumps(user_context, indent=2)}"
            base_prompt += context_str
            
        base_prompt += "\n\nRemember to use your tools to extract facts, create tasks, and summarize sessions when appropriate."
        
        return base_prompt
    
    async def chat_stream(
        self, 
        message: str, 
        user_context: Dict = None,
        conversation_history: List[Dict] = None
    ):
        """Stream chat response with function calling."""
        
        # Build messages
        messages = [
            SystemMessage(content=self._build_system_prompt(user_context))
        ]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                if msg['is_user']:
                    messages.append(HumanMessage(content=msg['content']))
                else:
                    messages.append(AIMessage(content=msg['content']))
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        # Stream response
        response_content = ""
        tool_calls = []
        
        async for chunk in self.llm_with_tools.astream(messages):
            if chunk.content:
                response_content += chunk.content
                yield {
                    "type": "token",
                    "data": chunk.content
                }
            
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
        
        # Process tool calls
        extracted_facts = {}
        created_tasks = []
        session_summary = None
        
        for tool_call in tool_calls:
            try:
                if tool_call['name'] == 'extract_user_facts':
                    result = extract_user_facts.invoke(tool_call['args'])
                    extracted_facts = result['data']
                    yield {
                        "type": "facts_update",
                        "data": extracted_facts
                    }
                
                elif tool_call['name'] == 'create_learning_task':
                    result = create_learning_task.invoke(tool_call['args'])
                    created_tasks.append(result['data'])
                    yield {
                        "type": "task_created",
                        "data": result['data']
                    }
                
                elif tool_call['name'] == 'summarize_session':
                    result = summarize_session.invoke(tool_call['args'])
                    session_summary = result['data']
                    yield {
                        "type": "session_summary",
                        "data": session_summary
                    }
                    
            except Exception as e:
                print(f"Tool call error: {e}")
                continue
        
        # Final response metadata
        yield {
            "type": "response_complete",
            "data": {
                "content": response_content,
                "facts_extracted": extracted_facts,
                "tasks_created": created_tasks,
                "session_summary": session_summary
            }
        }