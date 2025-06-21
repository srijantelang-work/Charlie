"""
Enhanced AI processing endpoints - Phase 2
"""

import asyncio
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user
from app.services.ai.gemini_service import GeminiService
from app.services.memory.context_service import ContextService
from app.models.schemas.ai import (
    ChatRequest, ChatResponse,
    ConversationRequest, ConversationResponse,
    MultimodalRequest, MultimodalResponse,
    StreamingChatChunk
)

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize services
gemini_service = GeminiService()
context_service = ContextService()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def enhanced_chat_completion(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enhanced chat completion with improved context and memory"""
    try:
        user_id = current_user["id"]
        
        response = await gemini_service.chat_completion(
            request=request,
            user_id=user_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Enhanced chat completion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/chat/stream")
@limiter.limit("20/minute")
async def streaming_chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Streaming chat completion for real-time responses"""
    try:
        user_id = current_user["id"]
        
        async def generate_stream():
            chunk_id = 0
            session_id = request.session_id or "default"
            
            async for chunk_text in gemini_service.generate_response_stream(
                user_input=request.message,
                user_id=user_id,
                session_id=request.session_id,
                context=request.context
            ):
                chunk = StreamingChatChunk(
                    chunk=chunk_text,
                    is_final=False,
                    chunk_id=chunk_id,
                    session_id=session_id
                )
                yield f"data: {chunk.model_dump_json()}\n\n"
                chunk_id += 1
                
                # Add small delay to prevent overwhelming
                await asyncio.sleep(0.01)
            
            # Send final chunk
            final_chunk = StreamingChatChunk(
                chunk="",
                is_final=True,
                chunk_id=chunk_id,
                session_id=session_id
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming chat failed: {str(e)}"
        )


@router.post("/conversation", response_model=ConversationResponse)
@limiter.limit("20/minute")
async def multi_turn_conversation(
    request: ConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enhanced multi-turn conversation with better context management"""
    try:
        user_id = current_user["id"]
        
        # Convert conversation messages to context-aware prompt
        conversation_text = ""
        for msg in request.messages:
            conversation_text += f"{msg.role.value}: {msg.content}\n"
        
        # Get conversation context if session exists
        conversation_context = []
        if request.session_id:
            conversation_context = await context_service.get_conversation_history(
                user_id, request.session_id, limit=10
            )
        
        # Enhanced context for multi-turn conversation
        enhanced_context = {
            **(request.context or {}),
            "conversation_history": conversation_context,
            "message_count": len(request.messages),
            "conversation_type": "multi_turn"
        }
        
        response_text = await gemini_service.generate_response(
            user_input=conversation_text,
            user_id=user_id,
            session_id=request.session_id,
            context=enhanced_context
        )
        
        # Store as a conversation interaction
        conversation_id = await context_service.store_interaction(
            user_id=user_id,
            session_id=request.session_id,
            user_input=conversation_text,
            ai_response=response_text,
            context=enhanced_context
        )
        
        return ConversationResponse(
            response=response_text,
            session_id=request.session_id or conversation_id,
            conversation_id=conversation_id,
            tokens_used=len(conversation_text.split()) + len(response_text.split()),
            processing_time_ms=0  # Would be calculated in production
        )
        
    except Exception as e:
        logger.error(f"Multi-turn conversation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation processing failed: {str(e)}"
        )


@router.post("/multimodal", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def enhanced_multimodal_analysis(
    request: MultimodalRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enhanced multimodal input processing with detailed analysis"""
    try:
        user_id = current_user["id"]
        
        if not request.media_data or not request.media_type:
            # Process as text-only with enhanced context
            response_text = await gemini_service.generate_response(
                user_input=request.text,
                user_id=user_id,
                session_id=request.session_id,
                context=request.context
            )
            
            return {
                "response": response_text,
                "session_id": request.session_id or "default",
                "conversation_id": "text-only",
                "analysis": {"type": "text_only"},
                "tokens_used": len(request.text.split()) + len(response_text.split()),
                "processing_time_ms": 0
            }
        else:
            # Process enhanced multimodal input
            import base64
            media_bytes = base64.b64decode(request.media_data)
            
            analysis_result = await gemini_service.analyze_multimodal(
                text=request.text,
                media_data=media_bytes,
                media_type=request.media_type,
                user_id=user_id
            )
            
            return {
                **analysis_result,
                "session_id": request.session_id or "default",
                "conversation_id": "multimodal",
            }
        
    except Exception as e:
        logger.error(f"Enhanced multimodal analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multimodal analysis failed: {str(e)}"
        )


@router.get("/model-info")
async def get_enhanced_model_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get enhanced AI model information"""
    try:
        model_info = await gemini_service.get_model_info()
        return model_info
        
    except Exception as e:
        logger.error(f"Failed to get enhanced model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information"
        )


@router.post("/summarize-session")
@limiter.limit("15/minute")
async def summarize_conversation_session(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Summarize a conversation session using AI"""
    try:
        user_id = current_user["id"]
        session_id = request.get("session_id")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required"
            )
        
        # Get conversation history
        conversations = await context_service.get_conversation_history(
            user_id, session_id, limit=50
        )
        
        if not conversations:
            return {
                "summary": "No conversations found in this session.",
                "session_id": session_id,
                "conversation_count": 0
            }
        
        # Use AI to generate detailed summary
        summary = await gemini_service.summarize_conversation(conversations, user_id)
        
        # Also get structured summary from context service
        structured_summary = await context_service.summarize_conversation_session(
            user_id, session_id
        )
        
        return {
            "ai_summary": summary,
            "structured_summary": structured_summary,
            "session_id": session_id,
            "conversation_count": len(conversations),
            "analysis": {
                "total_exchanges": len(conversations),
                "time_span": {
                    "start": conversations[-1]["created_at"] if conversations else None,
                    "end": conversations[0]["created_at"] if conversations else None
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session summarization failed: {str(e)}"
        )


@router.post("/analyze-context")
@limiter.limit("20/minute")
async def analyze_conversation_context(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze conversation context and provide insights"""
    try:
        user_id = current_user["id"]
        query = request.get("query", "")
        context_type = request.get("context_type", "general")  # general, learning, preferences
        
        # Get user context
        user_context = await context_service.get_user_context(user_id)
        
        # Get relevant memories based on context type
        memory_types = []
        if context_type == "learning":
            memory_types = ["knowledge", "skill", "experience"]
        elif context_type == "preferences":
            memory_types = ["preference", "goal", "habit"]
        elif context_type == "personal":
            memory_types = ["personal_fact", "relationship", "goal"]
        
        relevant_memories = await context_service.get_relevant_memories(
            user_id, query, limit=10, memory_types=memory_types if memory_types else None
        )
        
        # Prepare analysis prompt for AI
        analysis_prompt = f"""
Analyze the user's conversation context and provide insights.

Query: {query}
Context Type: {context_type}

User Context:
- Recent topics: {', '.join(user_context.get('recent_topics', []))}
- Learning patterns: {user_context.get('learning_patterns', {})}
- Memory stats: {user_context.get('memory_stats', {})}

Relevant Memories ({len(relevant_memories)} found):
{chr(10).join([f"- {mem['content'][:100]}..." for mem in relevant_memories[:5]])}

Please provide insights about the user's interests, learning patterns, and suggestions for personalized assistance.
"""
        
        ai_analysis = await gemini_service.generate_response(
            user_input=analysis_prompt,
            user_id=user_id,
            context={"analysis_type": "context_analysis"}
        )
        
        return {
            "analysis": ai_analysis,
            "context_summary": {
                "query": query,
                "context_type": context_type,
                "memories_found": len(relevant_memories),
                "user_stats": user_context.get('memory_stats', {}),
                "recent_topics": user_context.get('recent_topics', []),
                "learning_patterns": user_context.get('learning_patterns', {})
            },
            "relevant_memories": relevant_memories[:5],  # Return top 5 for reference
            "suggestions": {
                "memory_optimization": len(relevant_memories) > 20,
                "learning_opportunities": context_type == "learning",
                "preference_updates": context_type == "preferences"
            }
        }
        
    except Exception as e:
        logger.error(f"Context analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context analysis failed: {str(e)}"
        )


@router.post("/generate")
@limiter.limit("25/minute")
async def enhanced_generate_response(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enhanced AI response generation with better context handling"""
    try:
        user_id = current_user["id"]
        user_input = request.get("input", "")
        include_memory = request.get("include_memory", True)
        response_style = request.get("response_style", "balanced")  # brief, balanced, detailed
        
        if not user_input:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input text is required"
            )
        
        # Build enhanced context based on request
        context = request.get("context", {})
        context["response_style"] = response_style
        context["include_memory"] = include_memory
        
        # Adjust AI parameters based on response style
        if response_style == "brief":
            context["max_tokens"] = 200
            context["temperature"] = 0.3
        elif response_style == "detailed":
            context["max_tokens"] = 1000
            context["temperature"] = 0.7
        else:  # balanced
            context["max_tokens"] = 500
            context["temperature"] = 0.5
        
        response_text = await gemini_service.generate_response(
            user_input=user_input,
            user_id=user_id,
            session_id=request.get("session_id"),
            context=context
        )
        
        return {
            "response": response_text,
            "user_input": user_input,
            "session_id": request.get("session_id", "default"),
            "response_style": response_style,
            "context_used": include_memory,
            "estimated_tokens": len(user_input.split()) + len(response_text.split())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced response generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response generation failed: {str(e)}"
        ) 