"""Claude Code Agent SDK wrapper - Core AI Engine for PAI"""
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import uuid
import asyncio
import logging
from anthropic import Anthropic
from backend.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for a conversation session"""
    session_id: str
    messages: List[Dict[str, str]]
    model: str = settings.default_model
    max_tokens: int = 4096


class PAIEngine:
    """Main AI engine using Claude Code Agent SDK"""

    def __init__(self, db_session=None):
        """Initialize the Claude API client

        Args:
            db_session: Optional SQLAlchemy database session for persistence
        """
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.sessions: Dict[str, ConversationContext] = {}
        self.db_session = db_session
        self.default_system_prompt = """You are PAI (Personal AI Assistant), a helpful, intelligent, and empathetic AI assistant powered by Claude Code.

You have the following capabilities:
- Analyze code and provide improvements
- Help with software architecture and design decisions
- Interact with GitHub repositories and manage issues/PRs
- Learn from interactions to improve over time
- Adapt your communication style to the user's preferences
- Work collaboratively to solve complex problems

Always aim to be:
- Clear and concise in explanations
- Empathetic to user frustrations and concerns
- Proactive in offering suggestions
- Honest about limitations and uncertainties
- Focused on practical, actionable solutions"""

    async def create_session(self, user_id: str, session_type: str = "chat") -> str:
        """
        Create a new conversation session

        Args:
            user_id: User identifier
            session_type: Type of session (chat, skill_execution, debate, learning)

        Returns:
            session_id: Unique session identifier
        """
        from backend.db.models import Session as SessionModel

        session_id = str(uuid.uuid4())

        # Store in memory
        self.sessions[session_id] = ConversationContext(
            session_id=session_id,
            messages=[],
            model=settings.default_model
        )

        # Persist to database
        if self.db_session:
            try:
                db_session = SessionModel(
                    id=session_id,
                    user_id=user_id,
                    session_type=session_type,
                    created_at=datetime.utcnow()
                )
                self.db_session.add(db_session)
                self.db_session.commit()
                logger.info(f"Session {session_id} created for user {user_id}")
            except Exception as e:
                logger.error(f"Error saving session to database: {str(e)}")
                # Continue anyway - session exists in memory

        return session_id

    async def send_message(
        self,
        session_id: str,
        user_message: str,
        context_injection: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Send a message and get a response (async-safe)

        Args:
            session_id: Session identifier
            user_message: User's message text
            context_injection: Additional context to inject (from memory, etc.)
            model: Optional model override

        Returns:
            Response text from Claude
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        context = self.sessions[session_id]
        current_model = model or context.model

        # Add user message to history
        context.messages.append({
            "role": "user",
            "content": user_message
        })

        # Build system prompt with context injection
        system_prompt = self.default_system_prompt
        if context_injection:
            system_prompt += f"\n\nRelevant context from previous interactions:\n{context_injection}"

        try:
            # Use asyncio.to_thread to properly handle sync API call without blocking event loop
            response_text = await asyncio.to_thread(
                self._call_claude_api,
                current_model,
                context.max_tokens,
                system_prompt,
                context.messages.copy()
            )

            # Add assistant response to history
            context.messages.append({
                "role": "assistant",
                "content": response_text
            })

            logger.debug(f"Message sent in session {session_id}, response length: {len(response_text)}")
            return response_text

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            raise RuntimeError(f"Error calling Claude API: {str(e)}")

    def _call_claude_api(
        self,
        model: str,
        max_tokens: int,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """
        Synchronous wrapper for Claude API call (runs in thread)

        Args:
            model: Model to use
            max_tokens: Max tokens in response
            system_prompt: System prompt
            messages: Message history

        Returns:
            Response text
        """
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text

    async def stream_message(
        self,
        session_id: str,
        user_message: str,
        context_injection: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Send a message and stream the response (async-safe)

        Args:
            session_id: Session identifier
            user_message: User's message text
            context_injection: Additional context to inject
            model: Optional model override

        Yields:
            Response text chunks
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        context = self.sessions[session_id]
        current_model = model or context.model

        # Add user message to history
        context.messages.append({
            "role": "user",
            "content": user_message
        })

        # Build system prompt with context injection
        system_prompt = self.default_system_prompt
        if context_injection:
            system_prompt += f"\n\nRelevant context from previous interactions:\n{context_injection}"

        full_response = ""
        try:
            # Use asyncio.to_thread to properly handle streaming
            async for chunk in await asyncio.to_thread(
                self._stream_claude_api,
                current_model,
                context.max_tokens,
                system_prompt,
                context.messages.copy()
            ):
                full_response += chunk
                yield chunk

            # Add full assistant response to history
            context.messages.append({
                "role": "assistant",
                "content": full_response
            })

            logger.debug(f"Stream completed in session {session_id}, response length: {len(full_response)}")

        except Exception as e:
            logger.error(f"Error streaming from Claude API: {str(e)}")
            raise RuntimeError(f"Error streaming from Claude API: {str(e)}")

    def _stream_claude_api(
        self,
        model: str,
        max_tokens: int,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Synchronous stream wrapper for Claude API (runs in thread)

        Args:
            model: Model to use
            max_tokens: Max tokens in response
            system_prompt: System prompt
            messages: Message history

        Yields:
            Response text chunks
        """
        with self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        return self.sessions[session_id].messages

    async def get_last_n_messages(
        self,
        session_id: str,
        n: int = settings.max_session_history
    ) -> List[Dict[str, str]]:
        """Get last N messages from a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        messages = self.sessions[session_id].messages
        return messages[-n:] if len(messages) > n else messages

    async def end_session(self, session_id: str) -> None:
        """End a session and clean up"""
        from backend.db.models import Session as SessionModel

        if session_id in self.sessions:
            # Update database to mark session as ended
            if self.db_session:
                try:
                    db_session = self.db_session.query(SessionModel).filter_by(id=session_id).first()
                    if db_session:
                        db_session.ended_at = datetime.utcnow()
                        self.db_session.commit()
                        logger.info(f"Session {session_id} ended")
                except Exception as e:
                    logger.error(f"Error ending session in database: {str(e)}")

            # Remove from memory
            del self.sessions[session_id]

    def set_model(self, session_id: str, model: str) -> None:
        """Set the model for a specific session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        self.sessions[session_id].model = model

    def clear_history(self, session_id: str) -> None:
        """Clear conversation history for a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        self.sessions[session_id].messages = []


# Global engine instance
engine: Optional[PAIEngine] = None


def get_engine() -> PAIEngine:
    """Get or create the global PAI engine instance"""
    global engine
    if engine is None:
        engine = PAIEngine()
    return engine
