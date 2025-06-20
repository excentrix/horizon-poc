# backend/src/agents/mentor_agent.py (complete implementation)
from typing import Dict, Any, List, Optional, AsyncGenerator
import json
from datetime import datetime
from langchain_core.messages import HumanMessage

from .base_agent import BaseAgent
from prompts.prompt_manager import PromptType
from memory.mem0_integration import mem0_memory_manager

class MentorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Mentor")
        self.mem0_memory = mem0_memory_manager
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input for non-streaming use cases.
        This satisfies the abstract method requirement from BaseAgent.
        
        Use cases:
        - Batch processing of messages
        - Background analysis
        - Tool integration
        - Testing and validation
        """
        try:
            message = input_data.get("message", "")
            user_context = input_data.get("user_context", {})
            conversation_history = input_data.get("conversation_history", [])
            processing_type = input_data.get("type", "standard")  # standard, analysis, summary
            
            if not message:
                return {
                    "status": "error",
                    "error": "No message provided",
                    "response": None
                }
            
            user_id = user_context.get("user_id", "")
            
            print(f"🔄 Processing {processing_type} request for user {user_id}: {message[:50]}...")
            
            # Search relevant memories
            memories = []
            if self.mem0_memory.enabled and user_id:
                try:
                    memories = await self.mem0_memory.search_memories(
                        user_id=user_id,
                        query=message,
                        limit=3
                    )
                    print(f"🧠 Found {len(memories)} relevant memories")
                except Exception as e:
                    print(f"⚠️ Memory search failed: {e}")
            
            # Build conversation highlights
            conversation_highlights = ""
            if memories:
                highlights = []
                for memory in memories:
                    highlights.append(f"- {memory['content'][:100]}...")
                conversation_highlights = "\n".join(highlights)
            else:
                conversation_highlights = "No previous relevant context found"
            
            # Format user context
            formatted_context = self.format_user_context(user_context)
            
            # Choose prompt based on processing type
            if processing_type == "analysis":
                prompt_type = PromptType.FACT_EXTRACTION
                prompt_variables = {
                    "existing_profile": formatted_context,
                    "conversation_text": message
                }
            elif processing_type == "summary":
                prompt_type = PromptType.SESSION_SUMMARY
                prompt_variables = {
                    "user_context": formatted_context,
                    "conversation_history": "\n".join([
                        f"{'User' if msg.get('is_user') else 'AI'}: {msg.get('content', '')}"
                        for msg in conversation_history
                    ])
                }
            else:  # standard conversation
                prompt_type = PromptType.MENTOR_CONVERSATION
                prompt_variables = {
                    "user_context": formatted_context,
                    "conversation_highlights": conversation_highlights
                }
            
            # Get system message
            system_message = await self.get_system_message(prompt_type, prompt_variables)
            
            # Create messages
            messages = [
                system_message,
                HumanMessage(content=message)
            ]
            
            # Generate non-streaming response
            start_time = datetime.utcnow()
            response = await self.llm.ainvoke(messages)
            response_content = response.content
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            print(f"✅ Generated response in {processing_time:.2f}s: {len(response_content)} chars")
            
            # Store in memory if enabled and it's a standard conversation
            memory_id = None
            if response_content and self.mem0_memory.enabled and processing_type == "standard":
                try:
                    conversation_messages = [
                        {"content": message, "is_user": True},
                        {"content": response_content, "is_user": False}
                    ]
                    
                    memory_id = await self.mem0_memory.add_memory(
                        user_id=user_id,
                        messages=conversation_messages,
                        metadata={
                            "session_id": user_context.get("session_id", ""),
                            "timestamp": datetime.utcnow().isoformat(),
                            "processing_type": "batch",
                            "processing_time": processing_time,
                            "response_length": len(response_content)
                        }
                    )
                    print(f"💾 Stored conversation in memory: {memory_id}")
                except Exception as e:
                    print(f"⚠️ Failed to store memory: {e}")
            
            # Prepare result
            result = {
                "status": "success",
                "response": response_content,
                "processing_type": processing_type,
                "memories_used": len(memories),
                "memory_system": "mem0" if self.mem0_memory.enabled else "basic",
                "metadata": {
                    "response_length": len(response_content),
                    "user_id": user_id,
                    "session_id": user_context.get("session_id", ""),
                    "processing_time_seconds": processing_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_id": memory_id
                }
            }
            
            # Add type-specific metadata
            if processing_type == "analysis":
                # For fact extraction, try to parse structured output
                try:
                    if response_content.strip().startswith('{'):
                        parsed_facts = json.loads(response_content)
                        result["extracted_facts"] = parsed_facts
                        result["fact_count"] = len(parsed_facts.get("facts", []))
                except:
                    result["extracted_facts"] = None
                    result["fact_count"] = 0
            
            return result
            
        except Exception as e:
            print(f"❌ MentorAgent process error: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "response": "I apologize, but I encountered an error while processing your request.",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_type": input_data.get("type", "standard")
                }
            }
    
    async def chat_stream(
        self,
        message: str,
        user_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Enhanced chat stream with Mem0 memory integration."""
        
        try:
            user_id = user_context.get("user_id", "")
            
            # Search relevant memories using Mem0
            memories = []
            if self.mem0_memory.enabled and user_id:
                try:
                    memories = await self.mem0_memory.search_memories(
                        user_id=user_id,
                        query=message,
                        limit=3
                    )
                    
                    # Build conversation highlights from Mem0
                    conversation_highlights = ""
                    if memories:
                        highlights = []
                        for memory in memories:
                            content_preview = memory['content'][:100] if memory['content'] else ""
                            score = memory.get('score', 0.0)
                            highlights.append(f"- {content_preview}... (relevance: {score:.2f})")
                        conversation_highlights = "\n".join(highlights)
                    else:
                        conversation_highlights = "No previous relevant context found"
                except Exception as e:
                    print(f"⚠️ Memory search failed, continuing without: {e}")
                    conversation_highlights = "Memory system temporarily unavailable"
            else:
                conversation_highlights = "Memory system not available"
            
            # Format user context
            formatted_context = self.format_user_context(user_context)
            
            # Get system message with enhanced context
            system_message = await self.get_system_message(
                PromptType.MENTOR_CONVERSATION,
                {
                    "user_context": formatted_context,
                    "conversation_highlights": conversation_highlights
                }
            )
            
            # Create messages
            messages = [
                system_message,
                HumanMessage(content=message)
            ]
            
            print(f"🤖 Enhanced Mentor streaming response for: {message[:50]}...")
            print(f"🧠 Using {len(memories)} relevant memories")
            
            # Stream response
            response_content = ""
            word_count = 0
            start_time = datetime.utcnow()
            
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    response_content += chunk.content
                    word_count += len(chunk.content.split())
                    
                    yield {
                        "type": "token",
                        "data": chunk.content
                    }
                    
                    # Show progress for longer responses
                    if word_count > 0 and word_count % 30 == 0:
                        yield {
                            "type": "progress",
                            "data": {
                                "words_generated": word_count,
                                "estimated_completion": min(90, (word_count / 150) * 100)  # Rough estimate
                            }
                        }
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Store conversation in Mem0 (for future context)
            memory_id = None
            if response_content and self.mem0_memory.enabled and user_id:
                try:
                    conversation_messages = [
                        {"content": message, "is_user": True},
                        {"content": response_content, "is_user": False}
                    ]
                    
                    memory_id = await self.mem0_memory.add_memory(
                        user_id=user_id,
                        messages=conversation_messages,
                        metadata={
                            "session_id": user_context.get("session_id", ""),
                            "timestamp": datetime.utcnow().isoformat(),
                            "response_length": len(response_content),
                            "processing_time": processing_time,
                            "user_goal": user_context.get("goal", ""),
                            "user_worry": user_context.get("biggest_worry", ""),
                            "interaction_type": "streaming_chat"
                        }
                    )
                    print(f"💾 Stored streaming conversation in memory: {memory_id}")
                except Exception as e:
                    print(f"⚠️ Failed to store streaming memory: {e}")
            
            yield {
                "type": "stream_complete",
                "data": {
                    "response_length": len(response_content),
                    "word_count": word_count,
                    "processing_time_seconds": processing_time,
                    "memories_used": len(memories),
                    "memory_system": "mem0" if self.mem0_memory.enabled else "basic",
                    "memory_id": memory_id,
                    "agent_version": "v2_enhanced"
                }
            }
            
        except Exception as e:
            print(f"❌ Enhanced Mentor agent streaming error: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            
            yield {
                "type": "error",
                "data": {
                    "message": "I apologize, but I encountered an error. How can I help you?",
                    "error_code": "ENHANCED_MENTOR_ERROR",
                    "error_type": type(e).__name__
                }
            }
    
    async def analyze_conversation(
        self, 
        conversation_text: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze conversation for fact extraction using the process method."""
        return await self.process({
            "message": conversation_text,
            "user_context": user_context,
            "type": "analysis"
        })
    
    async def summarize_session(
        self, 
        conversation_history: List[Dict[str, str]], 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize a conversation session using the process method."""
        return await self.process({
            "message": "Please summarize this conversation session",
            "user_context": user_context,
            "conversation_history": conversation_history,
            "type": "summary"
        })