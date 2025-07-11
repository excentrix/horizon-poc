# backend/src/agents/mentor_agent.py (complete version)
from typing import Dict, Any, List, Optional, AsyncGenerator
import json
from datetime import datetime, UTC
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
import os

from .base_agent import BaseAgent
from prompts.prompt_manager import PromptType
from memory.mem0_manager import mem0_manager


class MentorAgent(BaseAgent):
    def __init__(self):
        """Initialize Enhanced MentorAgent with complete integrations."""
        super().__init__("Mentor")

        # Enhanced LLM configuration
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.7,
            max_tokens=1000,
            request_timeout=30,
        )

        # Memory integration
        self.memory = mem0_manager

        print(f"✅ Enhanced MentorAgent initialized:")
        print(
            f"   - Memory System: {'Mem0+Qdrant' if self.memory.enabled else 'Disabled'}"
        )
        print(
            f"   - Background Processing: {'Enabled' if os.getenv('ENABLE_BACKGROUND_PROCESSING') == 'true' else 'Disabled'}"
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete process method for batch processing and background tasks.

        Supports multiple processing types:
        - standard: Regular conversation processing
        - analysis: Fact extraction and analysis
        - summary: Session summarization
        - memory_search: Search and retrieve memories
        """
        try:
            message = input_data.get("message", "")
            user_context = input_data.get("user_context", {})
            conversation_history = input_data.get("conversation_history", [])
            processing_type = input_data.get("type", "standard")

            if not message and processing_type != "memory_search":
                return {
                    "status": "error",
                    "error": "No message provided",
                    "response": None,
                }

            user_id = user_context.get("user_id", "")

            print(f"🔄 Processing {processing_type} request for user {user_id}")
            print(f"   Message: {message[:100]}...")

            start_time = datetime.now(UTC)

            # Handle different processing types
            if processing_type == "memory_search":
                return await self._process_memory_search(
                    user_id, input_data.get("query", "")
                )

            elif processing_type == "analysis":
                return await self._process_fact_extraction(message, user_context)

            elif processing_type == "summary":
                return await self._process_session_summary(
                    conversation_history, user_context
                )

            else:  # standard conversation
                return await self._process_standard_conversation(
                    message, user_context, start_time
                )

        except Exception as e:
            print(f"❌ MentorAgent process error: {e}")
            import traceback

            traceback.print_exc()

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "response": "I apologize, but I encountered an error while processing your request.",
                "metadata": {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "processing_type": input_data.get("type", "standard"),
                },
            }

    async def _process_memory_search(self, user_id: str, query: str) -> Dict[str, Any]:
        """Process memory search requests."""
        if not self.memory.enabled:
            return {
                "status": "error",
                "error": "Memory system not available",
                "memories": [],
            }

        try:
            memories = await self.memory.search_relevant_memories(
                user_id=user_id, query=query, limit=10, threshold=0.6
            )

            return {
                "status": "success",
                "memories": memories,
                "total_found": len(memories),
                "query": query,
                "memory_system": "mem0_qdrant",
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "memories": []}

    async def _process_fact_extraction(
        self, conversation_text: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process fact extraction from conversation."""
        try:
            # Format existing profile
            existing_profile = self.format_user_context(user_context)

            # Get fact extraction prompt
            system_message = await self.get_system_message(
                PromptType.FACT_EXTRACTION,
                {
                    "existing_profile": existing_profile,
                    "conversation_text": conversation_text,
                },
            )

            # Create messages
            messages = [
                system_message,
                HumanMessage(
                    content=f"Extract facts from this conversation:\n{conversation_text}"
                ),
            ]

            # Generate analysis
            response = await self.llm.ainvoke(messages)
            response_content = response.content

            # Try to parse JSON response
            extracted_facts = None
            fact_count = 0

            try:
                if response_content.strip().startswith("{"):
                    extracted_facts = json.loads(response_content)
                    fact_count = len(extracted_facts.get("facts", []))
            except json.JSONDecodeError:
                print("⚠️ Could not parse fact extraction as JSON")

            return {
                "status": "success",
                "response": response_content,
                "extracted_facts": extracted_facts,
                "fact_count": fact_count,
                "processing_type": "fact_extraction",
                "metadata": {
                    "conversation_length": len(conversation_text),
                    "user_id": user_context.get("user_id", ""),
                    "timestamp": datetime.now(UTC),
                },
            }

        except Exception as e:
            print(f"❌ Fact extraction error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "extracted_facts": None,
                "fact_count": 0,
            }

    async def _process_session_summary(
        self, conversation_history: List[Dict[str, str]], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process session summarization."""
        try:
            # Format conversation history
            formatted_history = "\n".join(
                [
                    f"{'User' if msg.get('is_user') else 'AI'}: {msg.get('content', '')}"
                    for msg in conversation_history
                ]
            )

            # Format user context
            formatted_context = self.format_user_context(user_context)

            # Get session summary prompt
            system_message = await self.get_system_message(
                PromptType.SESSION_SUMMARY,
                {
                    "user_context": formatted_context,
                    "conversation_history": formatted_history,
                },
            )

            # Create messages
            messages = [
                system_message,
                HumanMessage(
                    content="Please create a comprehensive summary of this conversation session."
                ),
            ]

            # Generate summary
            response = await self.llm.ainvoke(messages)
            summary_content = response.content

            return {
                "status": "success",
                "response": summary_content,
                "processing_type": "session_summary",
                "metadata": {
                    "message_count": len(conversation_history),
                    "summary_length": len(summary_content),
                    "user_id": user_context.get("user_id", ""),
                    "session_id": user_context.get("session_id", ""),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }

        except Exception as e:
            print(f"❌ Session summary error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "Failed to generate session summary",
            }

    async def _process_standard_conversation(
        self, message: str, user_context: Dict[str, Any], start_time: datetime
    ) -> Dict[str, Any]:
        """Process standard conversation with memory integration."""
        try:
            user_id = user_context.get("user_id", "")

            # Search relevant memories
            memories = []
            if self.memory.enabled and user_id:
                memories = await self.memory.search_relevant_memories(
                    user_id=user_id, query=message, limit=5, threshold=0.7
                )

            # Build conversation highlights
            conversation_highlights = ""
            if memories:
                highlights = []
                for memory in memories:
                    content_preview = (
                        memory["content"][:150] if memory["content"] else ""
                    )
                    score = memory.get("score", 0.0)
                    highlights.append(
                        f"- {content_preview}... (relevance: {score:.2f})"
                    )
                conversation_highlights = "\n".join(highlights)
            else:
                conversation_highlights = "Building your learning profile as we chat..."

            # Format user context
            formatted_context = self.format_user_context(user_context)

            # Get system message
            system_message = await self.get_system_message(
                PromptType.MENTOR_CONVERSATION,
                {
                    "user_context": formatted_context,
                    "conversation_highlights": conversation_highlights,
                },
            )

            # Create messages
            messages = [system_message, HumanMessage(content=message)]

            # Generate response
            response = await self.llm.ainvoke(messages)
            response_content = response.content
            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # Store conversation in memory
            memory_id = None
            if response_content and self.memory.enabled and user_id:
                memory_id = await self.memory.add_conversation_memory(
                    user_id=user_id,
                    messages=[
                        {"content": message, "is_user": True},
                        {"content": response_content, "is_user": False},
                    ],
                    metadata={
                        "session_id": user_context.get("session_id", ""),
                        "processing_time": processing_time,
                        "memories_used": len(memories),
                        "interaction_type": "standard_conversation",
                    },
                )

            return {
                "status": "success",
                "response": response_content,
                "memories_used": len(memories),
                "memory_system": "mem0_qdrant" if self.memory.enabled else "disabled",
                "metadata": {
                    "response_length": len(response_content),
                    "processing_time_seconds": processing_time,
                    "user_id": user_id,
                    "session_id": user_context.get("session_id", ""),
                    "memory_id": memory_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }

        except Exception as e:
            print(f"❌ Standard conversation error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "I apologize, but I encountered an error. How can I help you?",
            }

    async def chat_stream(
        self,
        message: str,
        user_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Enhanced streaming chat with complete memory integration."""

        try:
            user_id = user_context.get("user_id", "")

            # Search relevant memories
            memories = []
            if self.memory.enabled and user_id:
                memories = await self.memory.search_relevant_memories(
                    user_id=user_id, query=message, limit=5, threshold=0.7
                )

                # Send memory search update
                yield {
                    "type": "memory_search",
                    "data": {
                        "memories_found": len(memories),
                        "search_query": (
                            message[:50] + "..." if len(message) > 50 else message
                        ),
                    },
                }

            # Build conversation highlights
            conversation_highlights = ""
            if memories:
                highlights = []
                for memory in memories:
                    content_preview = (
                        memory["content"][:150] if memory["content"] else ""
                    )
                    score = memory.get("score", 0.0)
                    highlights.append(
                        f"- {content_preview}... (relevance: {score:.2f})"
                    )
                conversation_highlights = "\n".join(highlights)
            else:
                conversation_highlights = "Building your learning profile as we chat..."

            # Format user context
            formatted_context = self.format_user_context(user_context)

            # Get system message
            system_message = await self.get_system_message(
                PromptType.MENTOR_CONVERSATION,
                {
                    "user_context": formatted_context,
                    "conversation_highlights": conversation_highlights,
                },
            )

            # Create messages
            messages = [system_message, HumanMessage(content=message)]

            print(f"🤖 Enhanced Mentor streaming response for: {message[:50]}...")
            print(f"🧠 Using {len(memories)} relevant memories from Mem0")

            # Stream response
            response_content = ""
            word_count = 0
            start_time = datetime.now(UTC)

            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    response_content += chunk.content
                    word_count += len(chunk.content.split())

                    yield {"type": "token", "data": chunk.content}

                    # Progress updates for longer responses
                    if word_count > 0 and word_count % 25 == 0:
                        yield {
                            "type": "progress",
                            "data": {
                                "words_generated": word_count,
                                "estimated_completion": min(
                                    95, (word_count / 200) * 100
                                ),
                            },
                        }

            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # Store conversation in Mem0
            memory_id = None
            if response_content and self.memory.enabled and user_id:
                memory_id = await self.memory.add_conversation_memory(
                    user_id=user_id,
                    messages=[
                        {"content": message, "is_user": True},
                        {"content": response_content, "is_user": False},
                    ],
                    metadata={
                        "session_id": user_context.get("session_id", ""),
                        "processing_time": processing_time,
                        "memories_used": len(memories),
                        "interaction_type": "streaming_chat",
                        "word_count": word_count,
                    },
                )

                if memory_id:
                    yield {"type": "memory_stored", "data": {"memory_id": memory_id}}

            # Final completion with comprehensive metadata
            yield {
                "type": "stream_complete",
                "data": {
                    "response_length": len(response_content),
                    "word_count": word_count,
                    "processing_time_seconds": processing_time,
                    "memories_used": len(memories),
                    "memory_system": (
                        "mem0_qdrant" if self.memory.enabled else "disabled"
                    ),
                    "memory_id": memory_id,
                    "agent_version": "v2_complete",
                    "features": {
                        "memory_search": self.memory.enabled,
                        "background_processing": os.getenv(
                            "ENABLE_BACKGROUND_PROCESSING"
                        )
                        == "true",
                        "vector_search": True,
                    },
                },
            }

        except Exception as e:
            print(f"❌ Enhanced streaming error: {e}")
            import traceback

            traceback.print_exc()

            yield {
                "type": "error",
                "data": {
                    "message": "I apologize, but I encountered an error. How can I help you?",
                    "error_code": "ENHANCED_STREAM_ERROR",
                    "error_type": type(e).__name__,
                    "memory_system": (
                        "mem0_qdrant" if self.memory.enabled else "disabled"
                    ),
                },
            }
