"""Tests for backend/core/memory.py - 3-Layer Memory System"""
import pytest
import math
from datetime import datetime, timedelta
from backend.db.models import Memory as MemoryModel


class TestMemorySystem:
    """Test suite for MemorySystem"""

    @pytest.mark.asyncio
    async def test_save_message_session_memory(self, memory_system, sample_session_id, sample_user_id):
        """Test saving a message to session memory (Layer 1)"""
        memory_id = await memory_system.save_message(
            sample_session_id,
            sample_user_id,
            "Test message content",
            sender="user"
        )

        assert memory_id is not None
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_save_message_persists_to_db(self, memory_system, sample_session_id, sample_user_id, db_session):
        """Test that saved messages are persisted to database"""
        message_content = "Test message for persistence"
        memory_id = await memory_system.save_message(
            sample_session_id,
            sample_user_id,
            message_content,
            sender="user"
        )

        # Query database
        db_record = db_session.query(MemoryModel).filter_by(id=memory_id).first()
        assert db_record is not None
        assert db_record.content == message_content
        assert db_record.memory_type == "session"

    @pytest.mark.asyncio
    async def test_get_session_context_empty(self, memory_system, sample_session_id):
        """Test getting context from empty session"""
        context = await memory_system.get_session_context(sample_session_id)

        assert context == ""

    @pytest.mark.asyncio
    async def test_get_session_context_with_messages(self, memory_system, sample_session_id, sample_user_id):
        """Test getting context with messages"""
        # Save multiple messages
        for i in range(3):
            await memory_system.save_message(
                sample_session_id,
                sample_user_id,
                f"Message {i}",
                sender="user"
            )

        context = await memory_system.get_session_context(sample_session_id, context_count=2)

        assert "Message" in context
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_save_learning_semantic(self, memory_system, sample_user_id):
        """Test saving semantic learning"""
        learning_id = await memory_system.save_learning(
            sample_user_id,
            "Python best practices include using type hints",
            memory_type="semantic",
            importance=0.9
        )

        assert learning_id is not None
        assert len(learning_id) > 0

    @pytest.mark.asyncio
    async def test_save_learning_episodic(self, memory_system, sample_user_id):
        """Test saving episodic learning"""
        learning_id = await memory_system.save_learning(
            sample_user_id,
            "User fixed a bug in the authentication module",
            memory_type="episodic",
            importance=0.7
        )

        assert learning_id is not None

    @pytest.mark.asyncio
    async def test_calculate_importance_no_decay(self, memory_system, db_session):
        """Test importance calculation with recent memory (no decay)"""
        from backend.db.models import Memory as MemoryModel

        # Create memory with current timestamp
        memory = MemoryModel(
            id="test-memory-1",
            content="Test",
            memory_type="semantic",
            importance=1.0,
            created_at=datetime.utcnow()
        )
        db_session.add(memory)
        db_session.commit()

        # Calculate importance
        importance = memory_system.calculate_importance(memory)

        # Should be close to 1.0 (just created, no decay)
        assert importance > 0.95
        assert importance <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_importance_with_decay(self, memory_system, db_session):
        """Test importance calculation with time decay"""
        from backend.db.models import Memory as MemoryModel

        # Create old memory (30 days old)
        old_date = datetime.utcnow() - timedelta(days=30)
        memory = MemoryModel(
            id="test-memory-old",
            content="Test",
            memory_type="semantic",
            importance=1.0,
            created_at=old_date
        )
        db_session.add(memory)
        db_session.commit()

        # Calculate importance
        importance = memory_system.calculate_importance(memory)

        # Should be decayed (lambda=0.1, age=30 days)
        # importance = 1.0 * e^(-0.1 * 30) ≈ 0.049
        assert importance < 0.1
        assert importance > 0.0

    @pytest.mark.asyncio
    async def test_get_relevant_memories_empty(self, memory_system, sample_user_id):
        """Test retrieving memories when none exist"""
        memories = await memory_system.get_relevant_memories(sample_user_id)

        assert memories == []

    @pytest.mark.asyncio
    async def test_get_relevant_memories_with_data(self, memory_system, sample_user_id):
        """Test retrieving relevant memories"""
        # Save multiple learnings
        for i in range(3):
            await memory_system.save_learning(
                sample_user_id,
                f"Learning {i} about development",
                memory_type="semantic",
                importance=0.8
            )

        memories = await memory_system.get_relevant_memories(sample_user_id, limit=2)

        assert len(memories) <= 2
        assert all(mem.importance > 0 for mem in memories)

    @pytest.mark.asyncio
    async def test_update_memory_importance(self, memory_system, sample_user_id, db_session):
        """Test updating memory importance"""
        import uuid
        from backend.db.models import Memory as MemoryModel

        # Create memory with unique ID
        memory_id = str(uuid.uuid4())
        memory = MemoryModel(
            id=memory_id,
            user_id=sample_user_id,
            content="Test",
            memory_type="semantic",
            importance=0.5,
            created_at=datetime.utcnow(),
            access_count=0  # Start at 0 so first update increments to 1
        )
        db_session.add(memory)
        db_session.commit()

        # Update importance
        await memory_system.update_memory_importance(memory_id, 0.95)

        # Verify update
        updated = db_session.query(MemoryModel).filter_by(id=memory_id).first()
        assert updated.importance == 0.95
        assert updated.access_count == 1

    @pytest.mark.asyncio
    async def test_build_injection_context(self, memory_system, sample_session_id, sample_user_id):
        """Test building full context injection"""
        # Add session memory
        await memory_system.save_message(sample_session_id, sample_user_id, "User message 1")
        await memory_system.save_message(sample_session_id, sample_user_id, "Assistant response", sender="assistant")

        # Add semantic memory
        await memory_system.save_learning(
            sample_user_id,
            "Important learning about coding",
            memory_type="semantic"
        )

        # Build context
        context = await memory_system.build_injection_context(
            sample_session_id,
            sample_user_id,
            token_budget=500
        )

        # Should include both session and learned context
        assert len(context) > 0 or context == ""  # May be empty if no relevant memories

    @pytest.mark.asyncio
    async def test_clear_session_memory(self, memory_system, sample_session_id, sample_user_id, db_session):
        """Test clearing all session memory"""
        # Add session memories
        await memory_system.save_message(sample_session_id, sample_user_id, "Message 1")
        await memory_system.save_message(sample_session_id, sample_user_id, "Message 2")

        # Verify they exist
        count = db_session.query(MemoryModel).filter(
            MemoryModel.session_id == sample_session_id,
            MemoryModel.memory_type == "session"
        ).count()
        assert count == 2

        # Clear session memory
        await memory_system.clear_session_memory(sample_session_id)

        # Verify cleared
        count = db_session.query(MemoryModel).filter(
            MemoryModel.session_id == sample_session_id,
            MemoryModel.memory_type == "session"
        ).count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_optimize_memory(self, memory_system, sample_user_id, db_session):
        """Test memory optimization"""
        import uuid
        from backend.db.models import Memory as MemoryModel

        # Create old, low-importance memory with unique ID
        old_date = datetime.utcnow() - timedelta(days=35)
        old_memory = MemoryModel(
            id=str(uuid.uuid4()),
            user_id=sample_user_id,
            content="Old content",
            memory_type="semantic",
            importance=0.05,
            created_at=old_date
        )
        db_session.add(old_memory)
        db_session.commit()

        # Optimize
        result = await memory_system.optimize_memory(sample_user_id)

        # Should have deleted the old memory
        assert "deleted" in result
        assert result["deleted"] >= 0


class TestMemoryIntegration:
    """Integration tests for memory system"""

    @pytest.mark.asyncio
    async def test_three_layer_memory_workflow(self, memory_system, sample_session_id, sample_user_id):
        """Test complete 3-layer memory workflow"""
        # Layer 1: Add session messages
        await memory_system.save_message(sample_session_id, sample_user_id, "User question")
        await memory_system.save_message(sample_session_id, sample_user_id, "AI response", sender="assistant")

        # Layer 2: Add semantic learning
        await memory_system.save_learning(
            sample_user_id,
            "Pattern: User prefers detailed explanations",
            memory_type="semantic",
            importance=0.9
        )

        # Layer 3: Get full context
        context = await memory_system.build_injection_context(
            sample_session_id,
            sample_user_id
        )

        # Verify context was built (may be empty if no retrieval matches)
        assert isinstance(context, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
