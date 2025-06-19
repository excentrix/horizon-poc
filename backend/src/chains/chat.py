# backend/src/chains/chat.py
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferWindowMemory
import os
import json

# Facts extraction schema
facts_schema = {
    "name": "extract_facts",
    "description": "Update user profile and session summary",
    "parameters": {
        "type": "object",
        "properties": {
            "profileDelta": {
                "type": "object",
                "properties": {
                    "degree": {"type": "string"},
                    "year": {"type": "integer"},
                    "goal": {"type": "string"},
                    "biggest_worry": {"type": "string"},
                    "fav_subject": {"type": "string"}
                }
            },
            "sessionSummary": {"type": "string"},
            "task": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due": {"type": "string", "format": "date"}
                }
            }
        },
        "required": ["sessionSummary"]
    }
}

class HorizonChatChain:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
            api_key=os.getenv("AOAI_KEY"),
            api_version="2024-02-15-preview",
            deployment_name=os.getenv("AOAI_DEPLOYMENT", "gpt-35-turbo-16k"),
            temperature=0.7,
        )
        self.memory = ConversationBufferWindowMemory(k=10)
        
    async def chat_stream(self, message: str, user_context: dict = None):
        system_prompt = """You are Horizon, an AI mentor for students. You help with:
        1. Academic guidance and career planning
        2. Creating actionable learning tasks
        3. Providing emotional support and motivation
        
        Always be encouraging, specific, and practical. Extract key facts about the user
        and suggest concrete next steps when appropriate.
        
        User context: {context}
        """.format(context=json.dumps(user_context) if user_context else "{}")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        # Stream response with tool calling
        response = await self.llm.agenerate([messages])
        
        # For now, return a simple response
        # TODO: Implement actual streaming with tool calls
        return {
            "content": response.generations[0][0].text,
            "facts": {},  # Will be populated by tool calling
            "task": None  # Will be populated if task is created
        }