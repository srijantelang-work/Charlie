"""
Enhanced Gemini AI service for processing user inputs - Phase 2
"""

import asyncio
import logging
import time
import json
import base64
from typing import Optional, Dict, Any, List, AsyncGenerator
from io import BytesIO
from PIL import Image

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.services.memory.context_service import ContextService
from app.models.schemas.ai import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class GeminiService:
    """Enhanced Gemini AI service with Phase 2 features"""
    
    def __init__(self):
        """Initialize Gemini service with enhanced configuration"""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Initialize both text and multimodal models
            self.text_model = genai.GenerativeModel("gemini-2.5-pro")
            self.multimodal_model = genai.GenerativeModel("gemini-2.5-pro")
            
            # Configure safety settings
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Generation configuration
            self.default_generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
            )
            
            self.context_service = ContextService()
            logger.info("Enhanced Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            raise AIServiceError(f"Gemini initialization failed: {e}")
    
    async def generate_response_stream(self, user_input: str, user_id: str, 
                                     session_id: Optional[str] = None,
                                     context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate streaming AI response to user input"""
        start_time = time.time()
        full_response = ""
        
        try:
            # Retrieve user context and memory
            user_context = await self.context_service.get_user_context(user_id)
            
            # Build enhanced prompt with context
            prompt = await self._build_enhanced_prompt(user_input, user_context, context)
            
            # Generate streaming response using Gemini
            loop = asyncio.get_event_loop()
            
            def _generate_stream():
                return self.text_model.generate_content(
                    prompt,
                    generation_config=self.default_generation_config,
                    safety_settings=self.safety_settings,
                    stream=True
                )
            
            response_stream = await loop.run_in_executor(None, _generate_stream)
            
            async for chunk in self._async_generator_wrapper(response_stream):
                if chunk and hasattr(chunk, 'text') and chunk.text:
                    full_response += chunk.text
                    yield chunk.text
            
            # Store complete interaction in memory
            await self.context_service.store_interaction(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input,
                ai_response=full_response,
                context=context
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Generated streaming response in {processing_time}ms")
            
        except Exception as e:
            logger.error(f"Gemini streaming response generation failed: {e}")
            error_response = await self._handle_generation_error(e, user_input)
            yield error_response
    
    async def _async_generator_wrapper(self, sync_generator):
        """Convert sync generator to async generator"""
        loop = asyncio.get_event_loop()
        
        def _get_next():
            try:
                return next(sync_generator), False
            except StopIteration:
                return None, True
        
        while True:
            chunk, done = await loop.run_in_executor(None, _get_next)
            if done:
                break
            yield chunk
    
    async def generate_response(self, user_input: str, user_id: str, 
                              session_id: Optional[str] = None,
                              context: Optional[Dict[str, Any]] = None) -> str:
        """Generate AI response to user input"""
        start_time = time.time()
        
        try:
            # Retrieve user context and memory
            user_context = await self.context_service.get_user_context(user_id)
            
            # Build enhanced prompt with context
            prompt = await self._build_enhanced_prompt(user_input, user_context, context)
            
            # Generate response using Gemini
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.text_model.generate_content(
                    prompt,
                    generation_config=self.default_generation_config,
                    safety_settings=self.safety_settings
                )
            )
            
            ai_response = response.text
            
            # Store interaction in memory
            await self.context_service.store_interaction(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input,
                ai_response=ai_response,
                context=context
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Generated response in {processing_time}ms")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Gemini response generation failed: {e}")
            return await self._handle_generation_error(e, user_input)
    
    async def chat_completion(self, request: ChatRequest, user_id: str) -> ChatResponse:
        """Process enhanced chat completion request"""
        start_time = time.time()
        
        try:
            # Get user memory if requested
            memory_count = 0
            relevant_memories = []
            if request.include_memory:
                relevant_memories = await self.context_service.get_relevant_memories(
                    user_id, request.message, limit=5
                )
                memory_count = len(relevant_memories)
            
            # Get conversation context if session exists
            conversation_context = []
            if request.session_id:
                conversation_context = await self.context_service.get_conversation_history(
                    user_id, request.session_id, limit=10
                )
            
            # Build context-aware prompt
            user_context = await self.context_service.get_user_context(user_id)
            enhanced_context = {
                **(request.context or {}),
                "memories": relevant_memories,
                "conversation_history": conversation_context,
                "user_context": user_context
            }
            
            prompt = await self._build_enhanced_prompt(request.message, user_context, enhanced_context)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=0.8,
                top_k=40
            )
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.text_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
            )
            
            ai_response = response.text
            
            # Store conversation
            conversation_id = await self.context_service.store_interaction(
                user_id=user_id,
                session_id=request.session_id,
                user_input=request.message,
                ai_response=ai_response,
                context=enhanced_context
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ChatResponse(
                response=ai_response,
                session_id=request.session_id or conversation_id,
                conversation_id=conversation_id,
                tokens_used=self._estimate_tokens(prompt + ai_response),
                processing_time_ms=processing_time,
                memory_retrieved=memory_count,
                context_used=len(conversation_context) > 0
            )
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise AIServiceError(f"Chat completion failed: {e}")
    
    async def analyze_multimodal(self, text: str, media_data: bytes, 
                               media_type: str, user_id: str) -> Dict[str, Any]:
        """Enhanced multimodal input analysis"""
        try:
            start_time = time.time()
            
            # Prepare analysis result
            analysis_result: Dict[str, Any] = {"type": media_type}
            
            if media_type.startswith("image/"):
                # Process image
                try:
                    image = Image.open(BytesIO(media_data))
                    
                    # Convert to supported format if needed
                    if image.format not in ['JPEG', 'PNG', 'WEBP']:
                        image = image.convert('RGB')
                    
                    analysis_result["image_info"] = {
                        "format": str(image.format),
                        "size": f"{image.size[0]}x{image.size[1]}",
                        "mode": str(image.mode)
                    }
                    
                    # Get user context for better analysis
                    user_context = await self.context_service.get_user_context(user_id)
                    
                    # Enhanced prompt for image analysis
                    enhanced_prompt = f"""
You are Charlie, an advanced AI assistant. Analyze the provided image and respond to the user's request.

User Context:
- User preferences: {user_context.get('preferences', {})}
- Recent topics: {user_context.get('recent_topics', [])}

User Request: {text}

Please provide a detailed, helpful response based on the image provided.
"""
                    
                    # Generate response with image
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.multimodal_model.generate_content(
                            [enhanced_prompt, image],
                            generation_config=self.default_generation_config,
                            safety_settings=self.safety_settings
                        )
                    )
                    
                except Exception as img_error:
                    logger.error(f"Image processing error: {img_error}")
                    raise AIServiceError(f"Image processing failed: {img_error}")
                    
            elif media_type == "application/pdf":
                # Handle PDF - simplified implementation
                analysis_result["pdf_info"] = {"size": len(media_data), "type": "pdf"}
                
                # Get user context for better analysis
                user_context = await self.context_service.get_user_context(user_id)
                
                # Enhanced prompt for PDF analysis
                enhanced_prompt = f"""
You are Charlie, an advanced AI assistant. The user has provided a PDF document and asked: {text}

User Context:
- User preferences: {user_context.get('preferences', {})}
- Recent topics: {user_context.get('recent_topics', [])}

PDF Information: Document size is {len(media_data)} bytes.

Please provide a helpful response. Note that full PDF content analysis is not yet implemented, but you can acknowledge the document and provide general guidance.
"""
                
                # Generate response for PDF
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.text_model.generate_content(
                        enhanced_prompt,
                        generation_config=self.default_generation_config,
                        safety_settings=self.safety_settings
                    )
                )
                
            else:
                raise AIServiceError(f"Unsupported media type: {media_type}")
            
            ai_response = response.text
            processing_time = int((time.time() - start_time) * 1000)
            
            # Store multimodal interaction
            await self.context_service.store_interaction(
                user_id=user_id,
                user_input=f"[MULTIMODAL] {text}",
                ai_response=ai_response,
                context={
                    "media_type": media_type,
                    "media_size": len(media_data),
                    "analysis": analysis_result
                }
            )
            
            return {
                "response": ai_response,
                "analysis": analysis_result,
                "processing_time_ms": processing_time,
                "tokens_used": self._estimate_tokens(enhanced_prompt + ai_response)
            }
            
        except Exception as e:
            logger.error(f"Multimodal analysis failed: {e}")
            raise AIServiceError(f"Multimodal analysis failed: {e}")
    
    async def _build_enhanced_prompt(self, user_input: str, user_context: Dict[str, Any], 
                                   additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Build enhanced prompt with comprehensive context"""
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = f"""You are Charlie, an advanced AI assistant inspired by JARVIS from Iron Man. 

Current Date/Time: {current_time}

CORE IDENTITY:
- Professional yet friendly and approachable
- Highly intelligent with broad knowledge
- Proactive in offering assistance and insights
- Context-aware of user preferences and history
- Capable of complex reasoning and multi-step tasks
- Respectful of user privacy and preferences

CAPABILITIES:
- Natural conversation and task assistance
- Multimodal analysis (images, documents)
- Memory of past interactions and preferences
- Integration with various tools and APIs
- Complex problem-solving and reasoning

USER CONTEXT:
"""
        
        # Add user preferences
        if user_context.get("preferences"):
            prefs = user_context["preferences"]
            system_prompt += f"\nUser Preferences:\n"
            for key, value in prefs.items():
                system_prompt += f"- {key}: {value}\n"
        
        # Add conversation context
        if user_context.get("recent_topics"):
            topics = user_context["recent_topics"][:3]  # Last 3 topics
            system_prompt += f"\nRecent Conversation Topics: {', '.join(topics)}\n"
        
        # Add user statistics
        if user_context.get("memory_count"):
            system_prompt += f"\nUser has {user_context['memory_count']} stored memories"
        
        # Add relevant memories
        if additional_context and additional_context.get("memories"):
            memories = additional_context["memories"]
            if memories:
                system_prompt += f"\n\nRELEVANT MEMORIES:\n"
                for memory in memories[:3]:  # Top 3 most relevant
                    system_prompt += f"- {memory['content'][:100]}...\n"
        
        # Add conversation history
        if additional_context and additional_context.get("conversation_history"):
            history = additional_context["conversation_history"]
            if history:
                system_prompt += f"\n\nRECENT CONVERSATION:\n"
                for conv in history[-5:]:  # Last 5 exchanges
                    system_prompt += f"User: {conv['user_input'][:50]}...\n"
                    system_prompt += f"Charlie: {conv['ai_response'][:50]}...\n"
        
        system_prompt += f"\n\nUSER REQUEST: {user_input}\n\nPlease provide a helpful, contextual response as Charlie."
        
        return system_prompt
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: 4 characters per token
        return len(text) // 4
    
    async def _handle_generation_error(self, error: Exception, user_input: str) -> str:
        """Handle AI generation errors with fallback responses"""
        error_type = type(error).__name__
        
        fallback_responses = {
            "ResourceExhausted": "I'm experiencing high demand right now. Please try again in a moment.",
            "InvalidArgument": "I had trouble understanding your request. Could you rephrase it?",
            "Unauthenticated": "There's an authentication issue. Please check your connection.",
            "PermissionDenied": "I don't have permission to process that request.",
            "DeadlineExceeded": "That request is taking too long. Please try a simpler question.",
        }
        
        fallback = fallback_responses.get(error_type, 
            "I encountered an unexpected issue. Please try again or contact support if the problem persists.")
        
        logger.warning(f"Using fallback response for {error_type}: {str(error)}")
        return fallback
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get enhanced model information"""
        try:
            return {
                "model": "gemini-2.5-pro",
                "capabilities": [
                    "text_generation",
                    "multimodal_analysis", 
                    "image_understanding",
                    "conversation_context",
                    "streaming_responses",
                    "function_calling"
                ],
                "context_window": 1000000,  # 1M tokens
                "max_output_tokens": 8192,
                "supported_media_types": [
                    "image/jpeg",
                    "image/png", 
                    "image/webp",
                    "application/pdf"
                ],
                "safety_settings": "medium_and_above",
                "generation_config": {
                    "temperature": self.default_generation_config.temperature,
                    "top_p": self.default_generation_config.top_p,
                    "top_k": self.default_generation_config.top_k
                }
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            raise AIServiceError(f"Model info retrieval failed: {e}")
    
    async def summarize_conversation(self, conversation_history: List[Dict[str, Any]], 
                                   user_id: str) -> str:
        """Summarize conversation for memory storage"""
        try:
            if not conversation_history:
                return ""
            
            # Build conversation text
            conv_text = ""
            for conv in conversation_history:
                conv_text += f"User: {conv['user_input']}\n"
                conv_text += f"Charlie: {conv['ai_response']}\n\n"
            
            # Create summarization prompt
            prompt = f"""Please provide a concise summary of this conversation between a user and Charlie AI assistant. Focus on:
1. Main topics discussed
2. Key decisions or outcomes
3. Important information shared
4. Tasks or actions mentioned

Conversation:
{conv_text}

Summary:"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.text_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=500
                    )
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Conversation summarization failed: {e}")
            return "Summary generation failed" 