"""
Enhanced context service for managing user memory and conversation history - Phase 2
"""

import logging
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from app.core.database import get_supabase_client
from app.core.exceptions import DatabaseError
from app.models.database.conversation import ConversationCreate
from app.models.database.memory import MemoryCreate

logger = logging.getLogger(__name__)


class ContextService:
    """Enhanced context and memory management service with Phase 2 features"""
    
    def __init__(self):
        """Initialize enhanced context service"""
        self.supabase = get_supabase_client()
        
        # Memory types and their importance weights
        self.memory_types = {
            "preference": 3,
            "personal_fact": 4, 
            "goal": 5,
            "skill": 3,
            "relationship": 4,
            "experience": 2,
            "habit": 3,
            "knowledge": 2,
            "task": 2,
            "decision": 4
        }
        
        # Keywords for memory extraction
        self.memory_keywords = {
            "preference": ["prefer", "like", "love", "hate", "dislike", "favorite", "enjoy", "want", "need"],
            "personal_fact": ["i am", "i work", "i live", "my name", "my job", "my family", "i have"],
            "goal": ["goal", "want to", "planning to", "hope to", "aim to", "working towards"],
            "skill": ["i can", "i know how", "good at", "skilled in", "expert in", "learned"],
            "relationship": ["my friend", "my family", "my colleague", "my boss", "my partner"],
            "experience": ["i did", "i went", "i experienced", "i learned", "happened to me"],
            "habit": ["i usually", "i always", "i often", "i never", "routine", "every day"],
            "decision": ["decided", "chose", "will do", "planning", "committed to"]
        }
        
        logger.info("Enhanced context service initialized")
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get enhanced user context including preferences and recent activity"""
        try:
            # Get user preferences
            user_response = self.supabase.table("users").select(
                "preferences, created_at"
            ).eq("id", user_id).execute()
            
            user_data = user_response.data[0] if user_response.data else {}
            preferences = user_data.get("preferences", {})
            
            # Get recent conversation topics (last 7 days)
            since_date = (datetime.now() - timedelta(days=7)).isoformat()
            
            conversations_response = self.supabase.table("conversations").select(
                "user_input, ai_response, created_at"
            ).eq("user_id", user_id).gte(
                "created_at", since_date
            ).order("created_at", desc=True).limit(20).execute()
            
            # Extract topics from recent conversations
            recent_topics = await self._extract_conversation_topics(conversations_response.data or [])
            
            # Get memory statistics by type
            memory_stats = await self._get_memory_statistics(user_id)
            
            # Get user learning patterns
            learning_patterns = await self._analyze_learning_patterns(user_id)
            
            return {
                "user_id": user_id,
                "preferences": preferences,
                "recent_topics": recent_topics[:5],
                "memory_stats": memory_stats,
                "learning_patterns": learning_patterns,
                "member_since": user_data.get("created_at"),
                "total_conversations": len(conversations_response.data or []),
                "active_sessions": await self._count_active_sessions(user_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            raise DatabaseError(f"Context retrieval failed: {e}")
    
    async def _extract_conversation_topics(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from recent conversations using NLP techniques"""
        topics = []
        topic_frequency = {}
        
        for conv in conversations:
            user_input = conv.get("user_input", "")
            
            # Extract nouns and important phrases (simplified approach)
            words = re.findall(r'\b[A-Za-z]{3,}\b', user_input.lower())
            
            # Filter out common words and keep meaningful terms
            stop_words = {"the", "and", "but", "can", "you", "how", "what", "when", "where", "why"}
            meaningful_words = [word for word in words if word not in stop_words]
            
            for word in meaningful_words:
                topic_frequency[word] = topic_frequency.get(word, 0) + 1
        
        # Get most frequent topics
        sorted_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)
        topics = [topic[0] for topic in sorted_topics[:10]]
        
        return topics
    
    async def _get_memory_statistics(self, user_id: str) -> Dict[str, int]:
        """Get memory statistics by type"""
        try:
            stats = {}
            for memory_type in self.memory_types.keys():
                response = self.supabase.table("memories").select(
                    "id"
                ).eq("user_id", user_id).eq("memory_type", memory_type).execute()
                stats[memory_type] = response.count or 0
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {}
    
    async def _analyze_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user learning patterns from conversation history"""
        try:
            # Get conversations from last 30 days
            since_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            response = self.supabase.table("conversations").select(
                "user_input, ai_response, created_at"
            ).eq("user_id", user_id).gte("created_at", since_date).execute()
            
            conversations = response.data or []
            
            patterns = {
                "question_types": {},
                "topics_explored": {},
                "learning_depth": "surface",  # surface, intermediate, deep
                "preferred_explanation_style": "detailed"  # brief, detailed, example-based
            }
            
            # Analyze question types
            for conv in conversations:
                user_input = conv.get("user_input", "").lower()
                
                if any(word in user_input for word in ["how", "explain", "what is"]):
                    patterns["question_types"]["explanatory"] = patterns["question_types"].get("explanatory", 0) + 1
                elif any(word in user_input for word in ["why", "because", "reason"]):
                    patterns["question_types"]["analytical"] = patterns["question_types"].get("analytical", 0) + 1
                elif any(word in user_input for word in ["help", "assist", "do this"]):
                    patterns["question_types"]["task_oriented"] = patterns["question_types"].get("task_oriented", 0) + 1
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze learning patterns: {e}")
            return {}
    
    async def _count_active_sessions(self, user_id: str) -> int:
        """Count active sessions in the last 24 hours"""
        try:
            since_date = (datetime.now() - timedelta(hours=24)).isoformat()
            
            response = self.supabase.table("conversations").select(
                "session_id"
            ).eq("user_id", user_id).gte("created_at", since_date).execute()
            
            sessions = set(conv.get("session_id") for conv in response.data or [] if conv.get("session_id"))
            return len(sessions)
            
        except Exception as e:
            logger.error(f"Failed to count active sessions: {e}")
            return 0
    
    async def store_interaction(self, user_id: str, user_input: str, 
                              ai_response: str, session_id: Optional[str] = None,
                              context: Optional[Dict[str, Any]] = None) -> str:
        """Store conversation interaction with enhanced memory extraction"""
        try:
            conversation_data = {
                "user_id": user_id,
                "session_id": session_id,
                "user_input": user_input,
                "ai_response": ai_response,
                "context": context or {},
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "input_length": len(user_input),
                    "response_length": len(ai_response),
                    "input_type": self._classify_input_type(user_input),
                    "sentiment": self._analyze_sentiment(user_input)
                }
            }
            
            response = self.supabase.table("conversations").insert(
                conversation_data
            ).execute()
            
            conversation_id = response.data[0]["id"]
            
            # Enhanced memory extraction from the interaction
            await self._extract_enhanced_memories(user_id, user_input, ai_response, conversation_id)
            
            logger.info(f"Stored enhanced conversation {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
            raise DatabaseError(f"Interaction storage failed: {e}")
    
    def _classify_input_type(self, user_input: str) -> str:
        """Classify the type of user input"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["?", "how", "what", "why", "when", "where"]):
            return "question"
        elif any(word in input_lower for word in ["help", "assist", "do", "create", "make"]):
            return "request"
        elif any(word in input_lower for word in ["i think", "i feel", "in my opinion"]):
            return "opinion"
        elif any(word in input_lower for word in ["i did", "i went", "yesterday", "today"]):
            return "experience_sharing"
        else:
            return "general"
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis of user input"""
        positive_words = ["good", "great", "excellent", "love", "like", "happy", "pleased"]
        negative_words = ["bad", "terrible", "hate", "dislike", "angry", "frustrated", "disappointed"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def get_conversation_history(self, user_id: str, session_id: Optional[str] = None,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for user or session"""
        try:
            query = self.supabase.table("conversations").select(
                "id, user_input, ai_response, created_at, context, metadata"
            ).eq("user_id", user_id)
            
            if session_id:
                query = query.eq("session_id", session_id)
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def summarize_conversation_session(self, user_id: str, session_id: str) -> str:
        """Summarize a conversation session"""
        try:
            # Get all conversations in the session
            conversations = await self.get_conversation_history(user_id, session_id, limit=50)
            
            if not conversations:
                return "No conversations found in this session."
            
            # Create a structured summary
            topics_discussed = set()
            questions_asked = []
            decisions_made = []
            user_preferences_mentioned = []
            
            for conv in conversations:
                user_input = conv.get("user_input", "")
                ai_response = conv.get("ai_response", "")
                
                # Extract topics (simplified)
                input_words = user_input.lower().split()
                topics_discussed.update([word for word in input_words if len(word) > 4])
                
                # Identify questions
                if "?" in user_input or any(word in user_input.lower() for word in ["how", "what", "why"]):
                    questions_asked.append(user_input[:100])
                
                # Identify decisions or preferences
                if any(word in user_input.lower() for word in ["decided", "prefer", "choose", "will"]):
                    decisions_made.append(user_input[:100])
            
            # Build summary
            summary_parts = [
                f"Conversation session summary for {len(conversations)} exchanges:",
                f"Main topics: {', '.join(list(topics_discussed)[:5])}",
            ]
            
            if questions_asked:
                summary_parts.append(f"Key questions: {len(questions_asked)} questions asked")
            
            if decisions_made:
                summary_parts.append(f"Decisions/preferences: {len(decisions_made)} items mentioned")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            return "Summary generation failed"
    
    async def store_memory(self, user_id: str, memory_type: str, content: str,
                          importance: int = 1, tags: Optional[List[str]] = None,
                          source_conversation_id: Optional[str] = None) -> str:
        """Store an enhanced memory for the user"""
        try:
            memory_data = {
                "user_id": user_id,
                "memory_type": memory_type,
                "content": content,
                "importance": importance,
                "tags": tags or [],
                "metadata": {
                    "created_timestamp": datetime.now().isoformat(),
                    "auto_generated": source_conversation_id is not None,
                    "source_conversation_id": source_conversation_id,
                    "last_accessed": datetime.now().isoformat(),
                    "access_count": 0,
                    "relevance_score": self._calculate_relevance_score(memory_type, importance, tags or [])
                }
            }
            
            response = self.supabase.table("memories").insert(memory_data).execute()
            memory_id = response.data[0]["id"]
            
            logger.info(f"Stored enhanced memory {memory_id} of type {memory_type}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise DatabaseError(f"Memory storage failed: {e}")
    
    def _calculate_relevance_score(self, memory_type: str, importance: int, tags: List[str]) -> float:
        """Calculate relevance score for memory ranking"""
        base_score = importance * self.memory_types.get(memory_type, 1)
        tag_bonus = len(tags) * 0.1  # Small bonus for more specific memories
        return min(base_score + tag_bonus, 10.0)  # Cap at 10.0
    
    async def get_relevant_memories(self, user_id: str, query: str, 
                                  limit: int = 5, memory_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get memories relevant to the current query with enhanced ranking"""
        try:
            # Build query
            query_builder = self.supabase.table("memories").select(
                "id, memory_type, content, importance, tags, created_at, metadata"
            ).eq("user_id", user_id)
            
            # Filter by memory types if specified
            if memory_types:
                query_builder = query_builder.in_("memory_type", memory_types)
            
            response = query_builder.order("importance", desc=True).order(
                "created_at", desc=True
            ).limit(limit * 3).execute()  # Get more to filter from
            
            memories = response.data or []
            
            # Enhanced relevance filtering
            relevant_memories = []
            query_words = set(query.lower().split())
            
            for memory in memories:
                relevance_score = self._calculate_memory_relevance(memory, query_words)
                if relevance_score > 0:
                    memory["calculated_relevance"] = relevance_score
                    relevant_memories.append(memory)
                    
                    # Update access tracking
                    await self._update_memory_access(memory["id"])
            
            # Sort by relevance and return top results
            relevant_memories.sort(key=lambda x: x["calculated_relevance"], reverse=True)
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get relevant memories: {e}")
            return []
    
    def _calculate_memory_relevance(self, memory: Dict[str, Any], query_words: set) -> float:
        """Calculate how relevant a memory is to the current query"""
        content = memory.get("content", "").lower()
        tags = memory.get("tags", [])
        memory_type = memory.get("memory_type", "")
        importance = memory.get("importance", 1)
        
        # Word overlap score
        memory_words = set(content.split())
        word_overlap = len(query_words & memory_words)
        word_score = word_overlap / max(len(query_words), 1)
        
        # Tag overlap score
        tag_words = set(" ".join(tags).lower().split())
        tag_overlap = len(query_words & tag_words)
        tag_score = tag_overlap * 0.5
        
        # Memory type relevance
        type_score = self.memory_types.get(memory_type, 1) * 0.1
        
        # Importance weighting
        importance_score = importance * 0.2
        
        # Time decay (recent memories get slight boost)
        time_score = 0.1  # Simplified for now
        
        total_score = word_score + tag_score + type_score + importance_score + time_score
        return min(total_score, 10.0)
    
    async def _update_memory_access(self, memory_id: str) -> None:
        """Update memory access tracking"""
        try:
            # Get current metadata
            response = self.supabase.table("memories").select("metadata").eq("id", memory_id).execute()
            
            if response.data:
                metadata = response.data[0].get("metadata", {})
                metadata["last_accessed"] = datetime.now().isoformat()
                metadata["access_count"] = metadata.get("access_count", 0) + 1
                
                # Update the record
                self.supabase.table("memories").update({"metadata": metadata}).eq("id", memory_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update memory access: {e}")
    
    async def update_user_preferences(self, user_id: str, 
                                    preferences: Dict[str, Any]) -> bool:
        """Update user preferences with learning integration"""
        try:
            # Get current preferences
            current_response = self.supabase.table("users").select("preferences").eq("id", user_id).execute()
            current_prefs = current_response.data[0].get("preferences", {}) if current_response.data else {}
            
            # Merge with new preferences
            updated_prefs = {**current_prefs, **preferences}
            
            # Update database
            response = self.supabase.table("users").update(
                {"preferences": updated_prefs}
            ).eq("id", user_id).execute()
            
            # Store preference changes as memories
            for key, value in preferences.items():
                await self.store_memory(
                    user_id=user_id,
                    memory_type="preference",
                    content=f"User preference: {key} = {value}",
                    importance=3,
                    tags=["preference", "auto_generated", key]
                )
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False
    
    async def _extract_enhanced_memories(self, user_id: str, user_input: str, 
                                       ai_response: str, conversation_id: str) -> None:
        """Enhanced memory extraction with multiple extraction strategies"""
        try:
            memories_to_store = []
            
            # Strategy 1: Keyword-based extraction
            keyword_memories = self._extract_keyword_memories(user_input)
            memories_to_store.extend(keyword_memories)
            
            # Strategy 2: Pattern-based extraction
            pattern_memories = self._extract_pattern_memories(user_input)
            memories_to_store.extend(pattern_memories)
            
            # Strategy 3: Context-based extraction
            context_memories = self._extract_context_memories(user_input, ai_response)
            memories_to_store.extend(context_memories)
            
            # Store all extracted memories
            for memory in memories_to_store:
                await self.store_memory(
                    user_id=user_id,
                    memory_type=memory["memory_type"],
                    content=memory["content"],
                    importance=memory["importance"],
                    tags=memory["tags"],
                    source_conversation_id=conversation_id
                )
            
        except Exception as e:
            logger.warning(f"Enhanced memory extraction failed: {e}")
    
    def _extract_keyword_memories(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract memories based on keyword matching"""
        memories = []
        input_lower = user_input.lower()
        
        for memory_type, keywords in self.memory_keywords.items():
            for keyword in keywords:
                if keyword in input_lower:
                    memories.append({
                        "memory_type": memory_type,
                        "content": user_input,
                        "importance": self.memory_types.get(memory_type, 1),
                        "tags": [memory_type, "keyword_extracted", keyword.replace(" ", "_")]
                    })
                    break  # Only one memory per type per input
        
        return memories
    
    def _extract_pattern_memories(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract memories based on pattern matching"""
        memories = []
        
        # Pattern: "I am [something]"
        if match := re.search(r'i am (a |an )?(\w+)', user_input.lower()):
            memories.append({
                "memory_type": "personal_fact",
                "content": f"User identity: {match.group(2)}",
                "importance": 4,
                "tags": ["identity", "pattern_extracted"]
            })
        
        # Pattern: "My [relationship] is [name]"
        if match := re.search(r'my (\w+) is (\w+)', user_input.lower()):
            memories.append({
                "memory_type": "relationship",
                "content": f"User's {match.group(1)}: {match.group(2)}",
                "importance": 3,
                "tags": ["relationship", "pattern_extracted", match.group(1)]
            })
        
        # Pattern: "I want to [goal]"
        if match := re.search(r'i want to (.+)', user_input.lower()):
            memories.append({
                "memory_type": "goal",
                "content": f"User goal: {match.group(1)}",
                "importance": 5,
                "tags": ["goal", "pattern_extracted"]
            })
        
        return memories
    
    def _extract_context_memories(self, user_input: str, ai_response: str) -> List[Dict[str, Any]]:
        """Extract memories based on conversation context"""
        memories = []
        
        # If AI provided information that user seemed to learn
        if any(phrase in ai_response.lower() for phrase in ["learned", "understand", "remember"]):
            memories.append({
                "memory_type": "knowledge",
                "content": f"Learning moment: {user_input} -> {ai_response[:100]}...",
                "importance": 2,
                "tags": ["learning", "context_extracted"]
            })
        
        # If user made a decision during conversation
        if any(word in user_input.lower() for word in ["decided", "choose", "will go with"]):
            memories.append({
                "memory_type": "decision",
                "content": f"User decision: {user_input}",
                "importance": 4,
                "tags": ["decision", "context_extracted"]
            })
        
        return memories
    
    async def optimize_memories(self, user_id: str) -> Dict[str, Any]:
        """Optimize user memories by removing duplicates and low-value entries"""
        try:
            # Get all user memories
            response = self.supabase.table("memories").select("*").eq("user_id", user_id).execute()
            memories = response.data or []
            
            if not memories:
                return {"optimized": 0, "removed": 0, "total": 0}
            
            # Group similar memories
            memory_groups = self._group_similar_memories(memories)
            
            # Remove duplicates and merge similar memories
            optimized_count = 0
            removed_count = 0
            
            for group in memory_groups:
                if len(group) > 1:
                    # Keep the most important memory and remove others
                    group.sort(key=lambda x: (x["importance"], x["created_at"]), reverse=True)
                    best_memory = group[0]
                    duplicates = group[1:]
                    
                    # Update the best memory with combined tags
                    all_tags = set(best_memory.get("tags", []))
                    for dup in duplicates:
                        all_tags.update(dup.get("tags", []))
                    
                    # Update best memory
                    self.supabase.table("memories").update({
                        "tags": list(all_tags),
                        "metadata": {
                            **best_memory.get("metadata", {}),
                            "optimized": True,
                            "combined_memories": len(group)
                        }
                    }).eq("id", best_memory["id"]).execute()
                    
                    # Remove duplicates
                    for dup in duplicates:
                        self.supabase.table("memories").delete().eq("id", dup["id"]).execute()
                        removed_count += 1
                    
                    optimized_count += 1
            
            logger.info(f"Memory optimization complete: {optimized_count} optimized, {removed_count} removed")
            return {
                "optimized": optimized_count,
                "removed": removed_count,
                "total": len(memories)
            }
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {"error": str(e)}
    
    def _group_similar_memories(self, memories: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group similar memories for optimization"""
        groups = []
        used_memories = set()
        
        for i, memory in enumerate(memories):
            if i in used_memories:
                continue
                
            similar_group = [memory]
            used_memories.add(i)
            
            for j, other_memory in enumerate(memories[i+1:], i+1):
                if j in used_memories:
                    continue
                    
                # Check similarity
                if self._are_memories_similar(memory, other_memory):
                    similar_group.append(other_memory)
                    used_memories.add(j)
            
            groups.append(similar_group)
        
        return groups
    
    def _are_memories_similar(self, memory1: Dict[str, Any], memory2: Dict[str, Any]) -> bool:
        """Check if two memories are similar enough to be merged"""
        # Same type and similar content
        if memory1.get("memory_type") != memory2.get("memory_type"):
            return False
        
        content1 = memory1.get("content", "").lower()
        content2 = memory2.get("content", "").lower()
        
        # Simple similarity check - more than 60% word overlap
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        similarity = overlap / union
        
        return similarity > 0.6 