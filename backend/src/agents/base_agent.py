# backend/src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

from prompts.prompt_manager import PromptManager, PromptType
from memory.memory_manager import MemoryManager

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.llm = AzureChatOpenAI(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-06"),
            temperature=0.7
        )
        self.prompt_manager = PromptManager()
        self.memory_manager = MemoryManager()
        print(f"✅ {self.name} agent initialized")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result."""
        pass
    
    async def get_system_message(self, prompt_type: PromptType, variables: Dict[str, Any] = None) -> SystemMessage:
        """Get system message from prompt manager."""
        content = self.prompt_manager.get_prompt(prompt_type, variables)
        return SystemMessage(content=content)
    
    def format_user_context(self, user_data: Dict[str, Any]) -> str:
        """Format user context for prompts."""
        context_parts = []
        
        if user_data.get("name"):
            context_parts.append(f"Name: {user_data['name']}")
        if user_data.get("degree") and user_data.get("year"):
            context_parts.append(f"Academic: {user_data['year']} year {user_data['degree']} student")
        if user_data.get("goal"):
            context_parts.append(f"Goal: {user_data['goal']}")
        if user_data.get("biggest_worry"):
            context_parts.append(f"Challenge: {user_data['biggest_worry']}")
        if user_data.get("skills"):
            skills = user_data["skills"][:3] if user_data["skills"] else []
            if skills:
                context_parts.append(f"Skills: {', '.join(skills)}")
        
        return "\n".join(context_parts) if context_parts else "New student - building profile"