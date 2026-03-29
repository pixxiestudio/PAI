"""3-Layer Memory System for PAI"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid
import math
import logging
from sqlalchemy.orm import Session as DBSession
from backend.db.models import Memory as MemoryModel
from backend.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a memory entry"""
    id: str
    content: str
    memory_type: str  # "session", "semantic", "episodic"
    importance: float = 1.0
    created_at: datetime = None
    accessed_at: datetime = None
    access_count: int = 0


class MemorySystem:
    """3-Layer Memory Architecture for PAI"""

    def __init__(self, db_session: Optional[DBSession] = None,
                 memory_decay_lambda: Optional[float] = None):
        """
        Initialize memory system

        Args:
            db_session: SQLAlchemy database session for persistence
            memory_decay_lambda: Exponential decay rate for memory importance
                                Uses settings.memory_decay_lambda if not provided
                                Formula: importance = base × e^(-lambda × age_days)
        """
        self.db_session = db_session
        self.memory_decay_lambda = memory_decay_lambda or settings.memory_decay_lambda

    # Layer 1: Session Memory (Conversation History)

    async def save_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        sender: str = "user"
    ) -> str:
        """
        Save a message to session memory (Layer 1)

        Args:
            session_id: Session identifier
            user_id: User identifier
            content: Message content
            sender: "user" or "assistant"

        Returns:
            memory_id: Unique memory identifier
        """
        memory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        memory_entry = MemoryModel(
            id=memory_id,
            session_id=session_id,
            user_id=user_id,
            memory_type="session",
            content=content,
            importance=1.0,  # Current message always has full importance
            created_at=now,
            accessed_at=now,
            access_count=1
        )

        if self.db_session:
            self.db_session.add(memory_entry)
            self.db_session.commit()

        return memory_id

    async def get_session_context(
        self,
        session_id: str,
        context_count: int = settings.max_session_history
    ) -> str:
        """
        Get formatted context from recent session history (Layer 1)

        Args:
            session_id: Session identifier
            context_count: Number of recent messages to include

        Returns:
            Formatted context string for injection into prompts
        """
        if not self.db_session:
            return ""

        # Get last N session messages
        memories = (
            self.db_session.query(MemoryModel)
            .filter(
                MemoryModel.session_id == session_id,
                MemoryModel.memory_type == "session"
            )
            .order_by(MemoryModel.created_at.desc())
            .limit(context_count)
            .all()
        )

        if not memories:
            return ""

        # Format as context
        context_parts = []
        for memory in reversed(memories):  # Reverse to chronological order
            context_parts.append(f"- {memory.content[:200]}")  # Truncate long messages

        return "\n".join(context_parts)

    # Layer 2: Semantic & Episodic Memory (with Time Decay)

    async def save_learning(
        self,
        user_id: str,
        content: str,
        memory_type: str = "semantic",
        importance: float = 1.0
    ) -> str:
        """
        Save a learning memory (Layer 2)

        Args:
            user_id: User identifier
            content: Memory content
            memory_type: "semantic" or "episodic"
            importance: Initial importance score (0-1)

        Returns:
            memory_id: Unique memory identifier
        """
        memory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        memory_entry = MemoryModel(
            id=memory_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            created_at=now,
            accessed_at=now,
            access_count=0
        )

        if self.db_session:
            self.db_session.add(memory_entry)
            self.db_session.commit()

        return memory_id

    def calculate_importance(self, memory: MemoryModel) -> float:
        """
        Calculate importance using time decay

        Formula: importance = base_importance × e^(-λ × age_days)

        Args:
            memory: Memory entry

        Returns:
            Computed importance score (0-1)
        """
        # Handle both timezone-aware and naive datetimes from database
        created_at = memory.created_at
        if created_at.tzinfo is None:
            # SQLite returns naive datetimes; assume UTC
            created_at = created_at.replace(tzinfo=timezone.utc)

        age_days = (datetime.now(timezone.utc) - created_at).days
        decayed = memory.importance * math.exp(-self.memory_decay_lambda * age_days)
        return max(0.0, min(1.0, decayed))  # Clamp to [0, 1]

    async def get_relevant_memories(
        self,
        user_id: str,
        query: str = "",
        limit: int = 5,
        min_importance: float = 0.2
    ) -> List[MemoryEntry]:
        """
        Retrieve relevant memories from Layer 2 (semantic + episodic)

        Args:
            user_id: User identifier
            query: Optional search query
            limit: Maximum memories to return
            min_importance: Minimum importance threshold (after decay)

        Returns:
            List of relevant memory entries
        """
        if not self.db_session:
            return []

        # Query Layer 2 memories (semantic + episodic, not session)
        query_obj = (
            self.db_session.query(MemoryModel)
            .filter(
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type.in_(["semantic", "episodic"])
            )
            .order_by(MemoryModel.accessed_at.desc())
            .limit(limit * 2)  # Get extra to filter by importance
            .all()
        )

        # Filter by importance and format
        relevant = []
        for memory in query_obj:
            importance = self.calculate_importance(memory)
            if importance >= min_importance:
                relevant.append(
                    MemoryEntry(
                        id=memory.id,
                        content=memory.content,
                        memory_type=memory.memory_type,
                        importance=importance,
                        created_at=memory.created_at,
                        accessed_at=memory.accessed_at,
                        access_count=memory.access_count
                    )
                )

        return relevant[:limit]

    async def update_memory_importance(
        self,
        memory_id: str,
        new_importance: float
    ) -> None:
        """
        Update importance score for a memory

        Args:
            memory_id: Memory identifier
            new_importance: New importance score
        """
        if not self.db_session:
            return

        memory = self.db_session.query(MemoryModel).filter_by(id=memory_id).first()
        if memory:
            memory.importance = max(0.0, min(1.0, new_importance))
            memory.accessed_at = datetime.now(timezone.utc)
            memory.access_count += 1
            self.db_session.commit()

    # Layer 3: Context Injection

    async def build_injection_context(
        self,
        session_id: str,
        user_id: str,
        token_budget: int = settings.max_injection_tokens
    ) -> str:
        """
        Build full context injection (Layer 3) combining session + semantic

        Args:
            session_id: Current session identifier
            user_id: User identifier
            token_budget: Maximum tokens for injection

        Returns:
            Full formatted context string
        """
        context_parts = []

        # Add recent session context (Layer 1)
        session_context = await self.get_session_context(session_id, context_count=5)
        if session_context:
            context_parts.append("Recent conversation:")
            context_parts.append(session_context)

        # Add relevant learned memories (Layer 2)
        learned_memories = await self.get_relevant_memories(
            user_id,
            limit=3
        )
        if learned_memories:
            context_parts.append("\nRelated learnings:")
            for mem in learned_memories:
                score = f"[{mem.importance:.1%}]"
                context_parts.append(f"- {score} {mem.content[:150]}")

        full_context = "\n".join(context_parts)

        # Truncate if needed (rough token estimate: 4 chars per token)
        max_chars = token_budget * 4
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "..."

        return full_context

    # Utility methods

    async def clear_session_memory(self, session_id: str) -> None:
        """Clear all session memories"""
        if not self.db_session:
            return

        self.db_session.query(MemoryModel).filter_by(
            session_id=session_id,
            memory_type="session"
        ).delete()
        self.db_session.commit()

    async def optimize_memory(self, user_id: str) -> Dict[str, int]:
        """
        Optimize memory by cleaning low-importance old memories

        Args:
            user_id: User identifier

        Returns:
            Dictionary with cleanup statistics
        """
        if not self.db_session:
            return {"deleted": 0}

        # Remove memories older than 30 days with importance < 0.1
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        old_low_importance = (
            self.db_session.query(MemoryModel)
            .filter(
                MemoryModel.user_id == user_id,
                MemoryModel.created_at < cutoff_date,
                MemoryModel.importance < 0.1
            )
            .delete()
        )

        self.db_session.commit()

        return {"deleted": old_low_importance}


# Global memory system instance
memory_system: Optional[MemorySystem] = None


def get_memory_system(db_session: Optional[DBSession] = None) -> MemorySystem:
    """Get or create the global memory system instance"""
    global memory_system
    if memory_system is None:
        memory_system = MemorySystem(db_session)
    return memory_system
