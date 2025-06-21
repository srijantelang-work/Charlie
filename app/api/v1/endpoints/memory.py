"""
Enhanced memory management endpoints - Phase 2
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user
from app.services.memory.context_service import ContextService
from app.models.database.memory import Memory, MemoryCreate, MemoryUpdate, MemorySearch

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize enhanced context service
context_service = ContextService()


@router.post("/", response_model=dict)
@limiter.limit("50/minute")
async def create_enhanced_memory(
    request: Request,
    memory_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create an enhanced memory with automatic categorization"""
    try:
        user_id = current_user["id"]
        
        # Enhanced memory creation with validation
        memory_type = memory_data.get("memory_type", "general")
        content = memory_data.get("content", "")
        importance = memory_data.get("importance", 1)
        tags = memory_data.get("tags", [])
        
        # Auto-generate tags if not provided
        if not tags and content:
            auto_tags = context_service._extract_keyword_memories(content)
            if auto_tags:
                tags = auto_tags[0].get("tags", [])
        
        # Validate memory type
        if memory_type not in context_service.memory_types:
            # Try to auto-detect memory type
            keyword_memories = context_service._extract_keyword_memories(content)
            if keyword_memories:
                memory_type = keyword_memories[0]["memory_type"]
        
        memory_id = await context_service.store_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            tags=tags
        )
        
        return {
            "id": memory_id,
            "message": "Enhanced memory created successfully",
            "memory_type": memory_type,
            "auto_tags": tags,
            "importance": importance
        }
        
    except Exception as e:
        logger.error(f"Enhanced memory creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory creation failed: {str(e)}"
        )


@router.get("/search")
async def enhanced_memory_search(
    query: str = Query(None, description="Search query"),
    memory_types: Optional[str] = Query(None, description="Comma-separated memory types"),
    importance_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum importance"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    include_stats: bool = Query(False, description="Include search statistics"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enhanced memory search with filtering and analytics"""
    try:
        user_id = current_user["id"]
        
        # Parse memory types
        memory_type_list = None
        if memory_types:
            memory_type_list = [t.strip() for t in memory_types.split(",")]
        
        if query:
            memories = await context_service.get_relevant_memories(
                user_id=user_id,
                query=query,
                limit=limit,
                memory_types=memory_type_list
            )
        else:
            # Get recent memories if no query provided
            memories = await context_service.get_relevant_memories(
                user_id=user_id,
                query="",
                limit=limit,
                memory_types=memory_type_list
            )
        
        # Filter by importance if specified
        if importance_min:
            memories = [m for m in memories if m.get("importance", 1) >= importance_min]
        
        result = {
            "memories": memories,
            "total": len(memories),
            "query": query,
            "filters": {
                "memory_types": memory_type_list,
                "importance_min": importance_min
            }
        }
        
        # Add search statistics if requested
        if include_stats:
            result["statistics"] = {
                "memory_type_distribution": {},
                "importance_distribution": {},
                "avg_relevance": 0
            }
            
            for memory in memories:
                mem_type = memory.get("memory_type", "unknown")
                importance = memory.get("importance", 1)
                
                result["statistics"]["memory_type_distribution"][mem_type] = \
                    result["statistics"]["memory_type_distribution"].get(mem_type, 0) + 1
                result["statistics"]["importance_distribution"][str(importance)] = \
                    result["statistics"]["importance_distribution"].get(str(importance), 0) + 1
            
            if memories:
                avg_relevance = sum(m.get("calculated_relevance", 0) for m in memories) / len(memories)
                result["statistics"]["avg_relevance"] = round(avg_relevance, 2)
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced memory search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory search failed: {str(e)}"
        )


@router.get("/context")
async def get_enhanced_user_context(
    include_analytics: bool = Query(False, description="Include detailed analytics"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get enhanced user context with analytics"""
    try:
        user_id = current_user["id"]
        
        context = await context_service.get_user_context(user_id)
        
        if include_analytics:
            # Add detailed analytics
            context["analytics"] = {
                "memory_growth": await _calculate_memory_growth(user_id),
                "interaction_patterns": await _analyze_interaction_patterns(user_id),
                "learning_velocity": await _calculate_learning_velocity(user_id)
            }
        
        return context
        
    except Exception as e:
        logger.error(f"Enhanced context retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context retrieval failed: {str(e)}"
        )


async def _calculate_memory_growth(user_id: str) -> Dict[str, Any]:
    """Calculate memory growth statistics"""
    try:
        # This would involve querying memory creation timestamps
        # Simplified implementation for demo
        return {
            "memories_this_week": 0,
            "memories_last_week": 0,
            "growth_rate": 0,
            "most_active_type": "general"
        }
    except Exception:
        return {}


async def _analyze_interaction_patterns(user_id: str) -> Dict[str, Any]:
    """Analyze user interaction patterns"""
    try:
        # This would involve analyzing conversation timestamps and patterns
        # Simplified implementation for demo
        return {
            "most_active_time": "afternoon",
            "avg_session_length": 15,
            "preferred_topics": [],
            "interaction_frequency": "daily"
        }
    except Exception:
        return {}


async def _calculate_learning_velocity(user_id: str) -> Dict[str, Any]:
    """Calculate how quickly user learns new things"""
    try:
        # This would involve analyzing knowledge-type memories over time
        # Simplified implementation for demo
        return {
            "concepts_per_week": 0,
            "retention_rate": 0.85,
            "learning_efficiency": "moderate"
        }
    except Exception:
        return {}


@router.get("/conversations")
async def get_enhanced_conversation_history(
    session_id: str = Query(None, description="Session ID filter"),
    limit: int = Query(10, ge=1, le=50, description="Number of conversations"),
    include_analysis: bool = Query(False, description="Include conversation analysis"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get enhanced conversation history with analysis"""
    try:
        user_id = current_user["id"]
        
        conversations = await context_service.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        result = {
            "conversations": conversations,
            "total": len(conversations),
            "session_id": session_id
        }
        
        if include_analysis and conversations:
            # Add conversation analysis
            result["analysis"] = {
                "total_exchanges": len(conversations),
                "avg_input_length": sum(len(c.get("user_input", "")) for c in conversations) / len(conversations),
                "avg_response_length": sum(len(c.get("ai_response", "")) for c in conversations) / len(conversations),
                "topics_discussed": await context_service._extract_conversation_topics(conversations),
                "sentiment_distribution": _analyze_conversation_sentiment(conversations),
                "time_span": {
                    "start": conversations[-1]["created_at"] if conversations else None,
                    "end": conversations[0]["created_at"] if conversations else None
                }
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced conversation history retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation history retrieval failed: {str(e)}"
        )


def _analyze_conversation_sentiment(conversations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze sentiment distribution in conversations"""
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    
    for conv in conversations:
        metadata = conv.get("metadata", {})
        sentiment = metadata.get("sentiment", "neutral")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    return sentiment_counts


@router.put("/preferences")
async def update_enhanced_preferences(
    preferences: dict,
    merge_mode: bool = Query(True, description="Whether to merge with existing preferences"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user preferences with enhanced learning integration"""
    try:
        user_id = current_user["id"]
        
        success = await context_service.update_user_preferences(
            user_id=user_id,
            preferences=preferences
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )
        
        # Get updated context to return current state
        updated_context = await context_service.get_user_context(user_id)
        
        return {
            "message": "Preferences updated successfully",
            "preferences": updated_context.get("preferences", {}),
            "merge_mode": merge_mode,
            "memories_created": len(preferences)  # One memory per preference
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced preferences update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preferences update failed: {str(e)}"
        )


@router.get("/analytics")
@limiter.limit("10/minute")
async def get_memory_analytics(
    request: Request,
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get comprehensive memory and learning analytics"""
    try:
        user_id = current_user["id"]
        
        # Get user context with statistics
        context = await context_service.get_user_context(user_id)
        
        analytics = {
            "overview": {
                "total_memories": sum(context.get("memory_stats", {}).values()),
                "total_conversations": context.get("total_conversations", 0),
                "active_sessions": context.get("active_sessions", 0),
                "member_since": context.get("member_since")
            },
            "memory_distribution": context.get("memory_stats", {}),
            "learning_patterns": context.get("learning_patterns", {}),
            "recent_activity": {
                "topics": context.get("recent_topics", []),
                "session_count": context.get("active_sessions", 0)
            },
            "recommendations": await _generate_learning_recommendations(user_id, context)
        }
        
        return {
            "analytics": analytics,
            "time_range": time_range,
            "generated_at": context.get("member_since")
        }
        
    except Exception as e:
        logger.error(f"Memory analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics generation failed: {str(e)}"
        )


async def _generate_learning_recommendations(user_id: str, context: Dict[str, Any]) -> List[str]:
    """Generate personalized learning recommendations"""
    recommendations = []
    
    memory_stats = context.get("memory_stats", {})
    learning_patterns = context.get("learning_patterns", {})
    
    # Analyze memory distribution
    total_memories = sum(memory_stats.values())
    if total_memories < 10:
        recommendations.append("Start building your knowledge base by sharing more about your interests and goals")
    
    # Check for knowledge gaps
    if memory_stats.get("skill", 0) < memory_stats.get("goal", 0):
        recommendations.append("Consider documenting your skills to better match them with your goals")
    
    # Analyze learning patterns
    question_types = learning_patterns.get("question_types", {})
    if question_types.get("explanatory", 0) > question_types.get("analytical", 0):
        recommendations.append("Try asking more 'why' questions to deepen your analytical thinking")
    
    # General recommendations
    if len(recommendations) == 0:
        recommendations.append("Continue engaging with diverse topics to expand your knowledge base")
    
    return recommendations


@router.post("/optimize")
@limiter.limit("5/minute")
async def optimize_user_memories(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Optimize user memories by removing duplicates and improving organization"""
    try:
        user_id = current_user["id"]
        
        optimization_result = await context_service.optimize_memories(user_id)
        
        return {
            "message": "Memory optimization completed",
            "results": optimization_result,
            "recommendations": [
                "Memory optimization helps improve retrieval speed",
                "Consider reviewing and updating important memories regularly",
                "Add more specific tags to improve searchability"
            ]
        }
        
    except Exception as e:
        logger.error(f"Memory optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory optimization failed: {str(e)}"
        )


@router.get("/export")
@limiter.limit("3/minute")
async def export_user_memories(
    request: Request,
    format: str = Query("json", description="Export format: json, csv"),
    memory_types: Optional[str] = Query(None, description="Comma-separated memory types to include"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Export user memories in various formats"""
    try:
        user_id = current_user["id"]
        
        # Parse memory types filter
        memory_type_list = None
        if memory_types:
            memory_type_list = [t.strip() for t in memory_types.split(",")]
        
        # Get all relevant memories
        memories = await context_service.get_relevant_memories(
            user_id=user_id,
            query="",
            limit=1000,  # Large limit for export
            memory_types=memory_type_list
        )
        
        # Get user context for metadata
        context = await context_service.get_user_context(user_id)
        
        export_data = {
            "export_info": {
                "user_id": user_id,
                "export_date": context.get("member_since"),
                "total_memories": len(memories),
                "format": format,
                "filtered_types": memory_type_list
            },
            "user_context": {
                "preferences": context.get("preferences", {}),
                "recent_topics": context.get("recent_topics", []),
                "memory_stats": context.get("memory_stats", {})
            },
            "memories": memories
        }
        
        return export_data
        
    except Exception as e:
        logger.error(f"Memory export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory export failed: {str(e)}"
        )


@router.post("/import")
@limiter.limit("2/minute")
async def import_user_memories(
    request: Request,
    import_data: dict,
    merge_duplicates: bool = Query(True, description="Whether to merge duplicate memories"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Import memories from external sources with conflict resolution"""
    try:
        user_id = current_user["id"]
        
        memories_to_import = import_data.get("memories", [])
        import_count = 0
        error_count = 0
        
        for memory_data in memories_to_import:
            try:
                await context_service.store_memory(
                    user_id=user_id,
                    memory_type=memory_data.get("memory_type", "general"),
                    content=memory_data.get("content", ""),
                    importance=memory_data.get("importance", 1),
                    tags=memory_data.get("tags", [])
                )
                import_count += 1
            except Exception as e:
                logger.warning(f"Failed to import memory: {e}")
                error_count += 1
        
        # Optimize memories after import if requested
        if merge_duplicates and import_count > 0:
            await context_service.optimize_memories(user_id)
        
        return {
            "message": "Memory import completed",
            "imported": import_count,
            "errors": error_count,
            "total_attempted": len(memories_to_import),
            "duplicates_merged": merge_duplicates
        }
        
    except Exception as e:
        logger.error(f"Memory import failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory import failed: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific conversation and related memories"""
    try:
        user_id = current_user["id"]
        
        # This would implement conversation deletion
        # For now, return a placeholder response
        
        return {
            "message": f"Conversation {conversation_id} deletion requested",
            "user_id": user_id,
            "note": "Deletion functionality would be implemented here"
        }
        
    except Exception as e:
        logger.error(f"Conversation deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation deletion failed: {str(e)}"
        )


@router.post("/clear")
async def clear_enhanced_user_data(
    data_type: str = Query("all", description="Type of data to clear (memories, conversations, all)"),
    confirm: bool = Query(False, description="Confirmation flag for safety"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enhanced data clearing with safety measures"""
    try:
        user_id = current_user["id"]
        
        if not confirm:
            return {
                "message": "Data clearing requires explicit confirmation",
                "user_id": user_id,
                "data_type": data_type,
                "confirmation_required": True,
                "warning": "This action cannot be undone"
            }
        
        # Get current stats before clearing
        context = await context_service.get_user_context(user_id)
        
        # This would implement the actual clearing logic
        # For now, return a placeholder response
        
        return {
            "message": f"Data clearing completed for type: {data_type}",
            "user_id": user_id,
            "data_type": data_type,
            "cleared_stats": {
                "memories_before": sum(context.get("memory_stats", {}).values()),
                "conversations_before": context.get("total_conversations", 0)
            },
            "note": "Actual clearing functionality would be implemented here"
        }
        
    except Exception as e:
        logger.error(f"Enhanced data clearing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data clearing failed: {str(e)}"
        ) 