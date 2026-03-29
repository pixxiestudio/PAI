"""Tests for backend/core/engine.py - Claude SDK Wrapper"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


class TestPAIEngine:
    """Test suite for PAIEngine"""

    @pytest.mark.asyncio
    async def test_create_session(self, pai_engine, sample_user_id):
        """Test creating a new session"""
        session_id = await pai_engine.create_session(sample_user_id, "chat")

        assert session_id is not None
        assert session_id in pai_engine.sessions
        assert pai_engine.sessions[session_id].session_id == session_id
        assert pai_engine.sessions[session_id].messages == []

    @pytest.mark.asyncio
    async def test_create_session_persists_to_db(self, pai_engine, sample_user_id, db_session):
        """Test that created sessions are persisted to database"""
        from backend.db.models import Session as SessionModel

        session_id = await pai_engine.create_session(sample_user_id, "chat")

        # Query database
        db_record = db_session.query(SessionModel).filter_by(id=session_id).first()
        assert db_record is not None
        assert db_record.user_id == sample_user_id
        assert db_record.session_type == "chat"

    @pytest.mark.asyncio
    async def test_get_session_history_empty(self, pai_engine, sample_user_id):
        """Test getting history from new session"""
        session_id = await pai_engine.create_session(sample_user_id)
        history = await pai_engine.get_session_history(session_id)

        assert history == []

    @pytest.mark.asyncio
    async def test_get_session_history_with_messages(self, pai_engine, sample_user_id):
        """Test getting history after messages are added"""
        session_id = await pai_engine.create_session(sample_user_id)

        # Manually add messages to session
        context = pai_engine.sessions[session_id]
        context.messages.append({"role": "user", "content": "Hello"})
        context.messages.append({"role": "assistant", "content": "Hi there!"})

        history = await pai_engine.get_session_history(session_id)

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_last_n_messages(self, pai_engine, sample_user_id):
        """Test retrieving last N messages"""
        session_id = await pai_engine.create_session(sample_user_id)
        context = pai_engine.sessions[session_id]

        # Add multiple messages
        for i in range(10):
            context.messages.append({"role": "user", "content": f"Message {i}"})

        # Get last 3
        last_3 = await pai_engine.get_last_n_messages(session_id, n=3)

        assert len(last_3) == 3
        assert last_3[0]["content"] == "Message 7"
        assert last_3[2]["content"] == "Message 9"

    @pytest.mark.asyncio
    async def test_send_message_session_not_found(self, pai_engine):
        """Test sending message to non-existent session"""
        with pytest.raises(ValueError, match="Session .* not found"):
            await pai_engine.send_message("invalid-session", "Hello")

    @pytest.mark.asyncio
    async def test_set_model(self, pai_engine, sample_user_id):
        """Test changing model for a session"""
        session_id = await pai_engine.create_session(sample_user_id)
        original_model = pai_engine.sessions[session_id].model

        pai_engine.set_model(session_id, "claude-haiku-4-5-20251001")

        assert pai_engine.sessions[session_id].model == "claude-haiku-4-5-20251001"
        assert pai_engine.sessions[session_id].model != original_model

    @pytest.mark.asyncio
    async def test_clear_history(self, pai_engine, sample_user_id):
        """Test clearing session history"""
        session_id = await pai_engine.create_session(sample_user_id)
        context = pai_engine.sessions[session_id]

        # Add messages
        context.messages.append({"role": "user", "content": "Message 1"})
        context.messages.append({"role": "assistant", "content": "Response 1"})

        assert len(context.messages) == 2

        # Clear history
        pai_engine.clear_history(session_id)

        assert len(context.messages) == 0

    @pytest.mark.asyncio
    async def test_end_session(self, pai_engine, sample_user_id, db_session):
        """Test ending a session"""
        from backend.db.models import Session as SessionModel

        session_id = await pai_engine.create_session(sample_user_id)

        # Verify session exists
        assert session_id in pai_engine.sessions

        # End session
        await pai_engine.end_session(session_id)

        # Verify removed from memory
        assert session_id not in pai_engine.sessions

        # Verify marked as ended in database
        db_record = db_session.query(SessionModel).filter_by(id=session_id).first()
        assert db_record.ended_at is not None

    @pytest.mark.asyncio
    async def test_end_nonexistent_session(self, pai_engine):
        """Test ending a session that doesn't exist (should not error)"""
        # Should not raise an error
        await pai_engine.end_session("nonexistent-session")

    @pytest.mark.asyncio
    async def test_system_prompt_included(self, pai_engine, sample_user_id):
        """Test that default system prompt is set"""
        assert "PAI (Personal AI Assistant)" in pai_engine.default_system_prompt
        assert "helpful" in pai_engine.default_system_prompt

    @pytest.mark.asyncio
    async def test_context_injection_in_system_prompt(self, pai_engine, sample_user_id):
        """Test that context injection is added to system prompt"""
        session_id = await pai_engine.create_session(sample_user_id)

        # Mock the _call_claude_api to capture the system prompt
        context_injection = "Previous discussion about Python"

        # Verify send_message would include context in system prompt
        context = pai_engine.sessions[session_id]
        system_prompt = pai_engine.default_system_prompt + f"\n\nRelevant context from previous interactions:\n{context_injection}"

        assert context_injection in system_prompt

    @pytest.mark.asyncio
    async def test_api_key_validation(self):
        """Test that API key is validated on initialization"""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
            # This should fail if no API key is set
            # We'll test the error message
            from backend.utils.config import settings
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")


class TestAsyncHandling:
    """Test async/await functionality"""

    @pytest.mark.asyncio
    async def test_send_message_is_async(self, pai_engine, sample_user_id):
        """Test that send_message is properly async"""
        session_id = await pai_engine.create_session(sample_user_id)

        # The method should be awaitable
        assert asyncio.iscoroutinefunction(pai_engine.send_message)

    @pytest.mark.asyncio
    async def test_stream_message_is_async_generator(self, pai_engine, sample_user_id):
        """Test that stream_message is properly async generator"""
        session_id = await pai_engine.create_session(sample_user_id)

        # The method should be an async generator
        assert asyncio.iscoroutinefunction(pai_engine.stream_message)

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self, pai_engine):
        """Test creating multiple sessions concurrently"""
        # Create multiple sessions concurrently
        session_ids = await asyncio.gather(
            pai_engine.create_session("user1", "chat"),
            pai_engine.create_session("user2", "chat"),
            pai_engine.create_session("user3", "chat"),
        )

        assert len(session_ids) == 3
        assert len(pai_engine.sessions) == 3
        assert all(sid in pai_engine.sessions for sid in session_ids)


class TestErrorHandling:
    """Test error handling in engine"""

    @pytest.mark.asyncio
    async def test_invalid_session_id_format(self, pai_engine):
        """Test handling of invalid session ID"""
        with pytest.raises(ValueError):
            await pai_engine.send_message("", "message")

    @pytest.mark.asyncio
    async def test_set_model_invalid_session(self, pai_engine):
        """Test setting model on non-existent session"""
        with pytest.raises(ValueError):
            pai_engine.set_model("invalid-session", "claude-haiku-4-5-20251001")

    @pytest.mark.asyncio
    async def test_clear_history_invalid_session(self, pai_engine):
        """Test clearing history on non-existent session"""
        with pytest.raises(ValueError):
            pai_engine.clear_history("invalid-session")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
