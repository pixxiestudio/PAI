"""Context injection system for PAI - Layer 3 Memory"""
from typing import Optional, List
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session as DBSession
from backend.core.memory import MemorySystem
from backend.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class ContextInjector:
    """Manages context injection for intelligent responses"""

    def __init__(self, memory_system: MemorySystem, db_session: Optional[DBSession] = None):
        """
        Initialize context injector

        Args:
            memory_system: MemorySystem instance
            db_session: Database session for accessing memories
        """
        self.memory_system = memory_system
        self.db_session = db_session

    async def build_context_injection(
        self,
        session_id: str,
        user_id: str,
        current_query: Optional[str] = None,
        token_budget: int = settings.max_injection_tokens
    ) -> str:
        """
        Build comprehensive context injection combining all memory layers

        Args:
            session_id: Current session ID
            user_id: User ID
            current_query: Current user query (for relevance scoring)
            token_budget: Maximum tokens for injection

        Returns:
            Formatted context string for prompt injection
        """
        context_sections = []

        # Section 1: Recent Conversation Context (Layer 1)
        recent_context = await self._build_session_context(session_id)
        if recent_context:
            context_sections.append(("Recent Conversation", recent_context))

        # Section 2: Relevant Learnings (Layer 2)
        learnings_context = await self._build_learnings_context(user_id)
        if learnings_context:
            context_sections.append(("Relevant Learnings", learnings_context))

        # Section 3: User Preferences & Personality (Layer 2+)
        preferences_context = await self._build_preferences_context(user_id)
        if preferences_context:
            context_sections.append(("User Preferences", preferences_context))

        # Combine and format sections with token budgeting
        return self._format_and_budget_context(context_sections, token_budget)

    async def _build_session_context(self, session_id: str) -> Optional[str]:
        """Build recent session history context (Layer 1)"""
        context = await self.memory_system.get_session_context(
            session_id,
            context_count=5
        )
        return context if context else None

    async def _build_learnings_context(self, user_id: str) -> Optional[str]:
        """Build relevant learnings context (Layer 2)"""
        memories = await self.memory_system.get_relevant_memories(
            user_id,
            limit=3,
            min_importance=0.3
        )

        if not memories:
            return None

        lines = []
        for mem in memories:
            importance_pct = f"{mem.importance * 100:.0f}%"
            # Handle both timezone-aware and naive datetimes from database
            created_at = mem.created_at
            if created_at.tzinfo is None:
                # SQLite returns naive datetimes; assume UTC
                created_at = created_at.replace(tzinfo=timezone.utc)
            days_old = (datetime.now(timezone.utc) - created_at).days
            age_indicator = f"({days_old}d old)"

            lines.append(f"• {mem.content[:150]} [{importance_pct} {age_indicator}]")

        return "\n".join(lines) if lines else None

    async def _build_preferences_context(self, user_id: str) -> Optional[str]:
        """Build user preferences and communication style context"""
        if not self.db_session:
            return None

        # In future, this would query learned user preferences
        # For now, return placeholder
        return "User prefers: detailed technical explanations with practical examples"

    def _format_and_budget_context(
        self,
        sections: List[tuple[str, str]],
        token_budget: int
    ) -> str:
        """
        Format sections and apply token budgeting

        Args:
            sections: List of (title, content) tuples
            token_budget: Maximum tokens

        Returns:
            Formatted context string
        """
        formatted = []
        max_chars = token_budget * 4  # Rough estimate: 4 chars per token

        for title, content in sections:
            section = f"[{title}]\n{content}"

            # Check if we can add this section
            current_length = sum(len(s) for s in formatted)
            if current_length + len(section) <= max_chars:
                formatted.append(section)
            else:
                # Truncate this section to fit
                remaining = max_chars - current_length
                if remaining > 100:  # Only add if there's meaningful space
                    truncated = f"[{title}]\n{content[:remaining]}..."
                    formatted.append(truncated)
                break

        if not formatted:
            return ""

        return "\n\n".join(formatted)

    async def inject_with_empathy(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        token_budget: int = settings.max_injection_tokens
    ) -> str:
        """
        Build context injection with empathy awareness

        Detects emotional tone and includes empathy instructions

        Args:
            session_id: Current session ID
            user_id: User ID
            user_message: Current user message
            token_budget: Token budget

        Returns:
            Context injection with empathy instructions
        """
        base_context = await self.build_context_injection(
            session_id,
            user_id,
            user_message,
            token_budget=token_budget - 200  # Reserve 200 tokens for empathy
        )

        # Detect emotional tone
        empathy_instruction = await self._build_empathy_instruction(user_message)

        if empathy_instruction:
            return f"{base_context}\n\n[Empathy Guidance]\n{empathy_instruction}"

        return base_context

    async def _build_empathy_instruction(self, user_message: str) -> Optional[str]:
        """
        Build empathy instruction based on message tone

        Args:
            user_message: User's message

        Returns:
            Empathy instruction or None
        """
        user_message_lower = user_message.lower()

        # Simple keyword-based tone detection
        frustration_keywords = ["frustrated", "annoyed", "angry", "hate", "terrible", "awful"]
        confusion_keywords = ["confused", "don't understand", "unclear", "lost", "stuck"]
        excitement_keywords = ["excited", "great", "awesome", "love", "wonderful"]
        stress_keywords = ["stressed", "pressure", "deadline", "urgent", "panic"]

        if any(kw in user_message_lower for kw in frustration_keywords):
            return "User appears frustrated. Acknowledge their frustration, validate their concerns, and provide extra clarity and encouragement."

        elif any(kw in user_message_lower for kw in confusion_keywords):
            return "User appears confused. Break down concepts into simpler parts, use examples, and ask clarifying questions to ensure understanding."

        elif any(kw in user_message_lower for kw in excitement_keywords):
            return "User appears excited/happy. Match their enthusiasm, celebrate progress, and build on their positive momentum."

        elif any(kw in user_message_lower for kw in stress_keywords):
            return "User appears stressed/under pressure. Prioritize essential information, provide clear action steps, and emphasize that you're here to help reduce their burden."

        return None

    async def score_context_relevance(
        self,
        context: str,
        user_query: str
    ) -> float:
        """
        Score how relevant the injected context is to the user query

        Args:
            context: Injected context string
            user_query: User's current query

        Returns:
            Relevance score (0-1)
        """
        # Simple word overlap based scoring
        query_words = set(user_query.lower().split())
        context_words = set(context.lower().split())

        if not query_words or not context_words:
            return 0.0

        overlap = len(query_words & context_words)
        total = len(query_words | context_words)

        return overlap / total if total > 0 else 0.0


class ContextManager:
    """Manages context for PAI responses"""

    def __init__(self, memory_system: MemorySystem, db_session: Optional[DBSession] = None):
        """Initialize context manager"""
        self.injector = ContextInjector(memory_system, db_session)

    async def prepare_response_context(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        include_empathy: bool = True
    ) -> str:
        """
        Prepare full context for generating a response

        Args:
            session_id: Current session ID
            user_id: User ID
            user_message: Current user message
            include_empathy: Whether to include empathy guidance

        Returns:
            Context string ready for prompt injection
        """
        if include_empathy:
            return await self.injector.inject_with_empathy(
                session_id,
                user_id,
                user_message
            )
        else:
            return await self.injector.build_context_injection(
                session_id,
                user_id,
                user_message
            )


# Global context manager instance
context_manager: Optional[ContextManager] = None


def get_context_manager(
    memory_system: MemorySystem,
    db_session: Optional[DBSession] = None
) -> ContextManager:
    """Get or create global context manager"""
    global context_manager
    if context_manager is None:
        context_manager = ContextManager(memory_system, db_session)
    return context_manager
