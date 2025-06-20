# backend/src/chains/horizon_chat.py (completely rewrite)
from typing import Dict, List, Optional, Any, AsyncGenerator
import json
import asyncio
from datetime import datetime

from ai.fact_extraction import FactExtractionPipeline, FactExtractionResult
from ai.task_creation import TaskCreationEngine, TaskCreationResult
from ai.context_aware_generator import ContextAwareGenerator

class HorizonChatChain:
    def __init__(self):
        self.fact_extractor = FactExtractionPipeline()
        self.task_creator = TaskCreationEngine()
        self.response_generator = ContextAwareGenerator()
        print("✅ Enhanced Horizon Chat Chain initialized")
    
    async def chat_stream(
        self,
        message: str,
        user_context: Dict[str, Any] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Enhanced chat stream with parallel fact extraction, task creation, and context-aware responses.
        """
        
        if not user_context:
            user_context = {}
        
        if not conversation_history:
            conversation_history = []
        
        try:
            print(f"🤖 Processing message: {message[:50]}...")
            
            # Step 1: Start parallel processing
            print("🔄 Starting parallel AI analysis...")
            
            # Run fact extraction and initial analysis in parallel
            fact_extraction_task = asyncio.create_task(
                self.fact_extractor.extract_facts(message, user_context, conversation_history)
            )
            
            # Step 2: Get fact extraction results
            yield {
                "type": "processing_update",
                "data": {"message": "Analyzing your message..."}
            }
            
            fact_result: FactExtractionResult = await fact_extraction_task
            print(f"✅ Fact extraction complete. Found {len(fact_result.facts)} facts")
            
            # Step 3: Stream fact updates if any facts were found
            if fact_result.facts:
                print("📊 Streaming fact updates...")
                
                # Send fact updates
                fact_updates = {}
                for fact in fact_result.facts:
                    # Convert fact to database format
                    if fact.field == "skills" and isinstance(fact.value, list):
                        fact_updates[fact.field] = json.dumps(fact.value)
                    else:
                        fact_updates[fact.field] = fact.value
                
                yield {
                    "type": "facts_update",
                    "data": fact_updates
                }
                
                # Show visual feedback for fact discovery
                yield {
                    "type": "fact_discovery",
                    "data": {
                        "facts_discovered": len(fact_result.facts),
                        "facts": [
                            {
                                "field": fact.field,
                                "value": fact.value,
                                "confidence": fact.confidence
                            }
                            for fact in fact_result.facts
                        ]
                    }
                }
            
            # Step 4: Analyze for task creation
            print("📋 Analyzing for task creation...")
            
            task_result: TaskCreationResult = await self.task_creator.analyze_for_tasks(
                message, 
                user_context, 
                fact_result.user_intent, 
                fact_result.emotional_state,
                conversation_history
            )
            
            print(f"✅ Task analysis complete. Should create tasks: {task_result.should_create_tasks}")
            
            # Step 5: Create tasks if recommended
            if task_result.should_create_tasks and task_result.tasks:
                print(f"📝 Creating {len(task_result.tasks)} tasks...")
                
                for task in task_result.tasks:
                    # Convert relative date to actual date
                    due_date = None
                    if task.due_date_suggestion:
                        due_date = self.task_creator._parse_relative_date(task.due_date_suggestion)
                    
                    yield {
                        "type": "task_created",
                        "data": {
                            "title": task.title,
                            "description": task.description,
                            "priority": task.priority,
                            "due_date": due_date.isoformat() if due_date else None,
                            "category": task.category,
                            "confidence": task.confidence,
                            "reasoning": task.reasoning
                        }
                    }
            
            # Step 6: Generate context-aware response
            print("💬 Generating context-aware response...")
            
            yield {
                "type": "processing_update",
                "data": {"message": "Crafting personalized response..."}
            }
            
            # Generate enhanced response with all context
            response = await self.response_generator.generate_contextual_response(
                message,
                user_context,
                fact_result.facts,
                fact_result.user_intent,
                fact_result.emotional_state,
                conversation_history
            )
            
            print(f"✅ Response generated: {len(response)} characters")
            
            # Step 7: Stream response tokens
            # Simulate streaming for visual effect (in production, use actual streaming)
            words = response.split()
            current_response = ""
            
            for i, word in enumerate(words):
                current_response += word + " "
                
                yield {
                    "type": "token",
                    "data": word + " "
                }
                
                # Add small delay for realistic streaming effect
                if i % 3 == 0:  # Every 3 words
                    await asyncio.sleep(0.05)
            
            # Step 8: Send completion signal with summary
            yield {
                "type": "stream_complete",
                "data": {
                    "facts_extracted": len(fact_result.facts),
                    "tasks_created": len(task_result.tasks) if task_result.should_create_tasks else 0,
                    "user_intent": fact_result.user_intent,
                    "emotional_state": fact_result.emotional_state,
                    "suggested_follow_up": fact_result.suggested_follow_up
                }
            }
            
            print("✅ Enhanced chat stream completed successfully")
            
        except Exception as e:
            print(f"❌ Enhanced chat stream error: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            
            yield {
                "type": "error",
                "data": {
                    "message": "I encountered an error while processing your message. Let me try to help you anyway.",
                    "error_code": "PROCESSING_ERROR"
                }
            }
            
            # Fallback simple response
            yield {
                "type": "token",
                "data": "I apologize for the technical difficulty. How can I help you with your studies today?"
            }