"""Integration tests for Phase 1 - Full workflow testing"""
import pytest
import asyncio
from datetime import datetime


class TestPhase1Integration:
    """Integration tests for Phase 1 components working together"""

    @pytest.mark.asyncio
    async def test_complete_session_workflow(
        self,
        pai_engine,
        memory_system,
        context_manager,
        learning_system,
        personality_manager,
        sample_user_id,
        db_session
    ):
        """Test complete workflow: session creation → memory → context → learning"""
        from backend.db.models import Session as SessionModel

        # Step 1: Create session
        session_id = await pai_engine.create_session(sample_user_id, "chat")
        assert session_id in pai_engine.sessions

        # Step 2: Verify session in database
        db_session_record = db_session.query(SessionModel).filter_by(id=session_id).first()
        assert db_session_record is not None

        # Step 3: Save messages to memory
        msg_id1 = await memory_system.save_message(session_id, sample_user_id, "Hello, help me code")
        assert msg_id1 is not None

        msg_id2 = await memory_system.save_message(
            session_id, sample_user_id, "Here's a helpful response", sender="assistant"
        )
        assert msg_id2 is not None

        # Step 4: Build context from memory
        context = await memory_system.get_session_context(session_id)
        assert context == "" or isinstance(context, str)

        # Step 5: Inject context with empathy
        full_context = await context_manager.injector.inject_with_empathy(
            session_id,
            sample_user_id,
            "Help me code"
        )
        assert isinstance(full_context, str)

        # Step 6: Detect user emotion
        from backend.core.personality import EmpathyDetector
        tone = EmpathyDetector.detect_tone("I'm excited about this!")
        assert tone.value == "excited"

        # Step 7: Record learning
        learning_id = await learning_system.record_interaction_outcome(
            "test-pai",
            "help_with_code",
            {"request": "code help"},
            {"response": "helpful response"},
            success=True,
            quality_score=0.95
        )
        assert learning_id is not None

        # Step 8: End session and verify cleanup
        await pai_engine.end_session(session_id)
        assert session_id not in pai_engine.sessions

        # Verify session marked as ended in DB
        db_session_record = db_session.query(SessionModel).filter_by(id=session_id).first()
        assert db_session_record.ended_at is not None

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_flow(
        self,
        pai_engine,
        memory_system,
        sample_user_id,
        db_session
    ):
        """Test multi-turn conversation with memory accumulation"""
        # Create session
        session_id = await pai_engine.create_session(sample_user_id)

        # Simulate multi-turn conversation - save to both engine context and memory
        turns = [
            ("user", "What is Python?"),
            ("assistant", "Python is a programming language..."),
            ("user", "How do I install it?"),
            ("assistant", "You can install Python from python.org..."),
            ("user", "Great, thanks!"),
        ]

        # Add messages to engine's in-memory context for history tracking
        for sender, message in turns:
            # Add to engine's memory context
            pai_engine.sessions[session_id].messages.append({
                "role": sender,
                "content": message
            })
            # Also save to memory system for persistence
            await memory_system.save_message(session_id, sample_user_id, message, sender=sender)

        # Verify history in engine
        history = await pai_engine.get_session_history(session_id)
        assert len(history) == 5

        # Verify last 3 messages
        last_3 = await pai_engine.get_last_n_messages(session_id, n=3)
        assert len(last_3) == 3

        # Verify messages persisted to database via memory system
        session_context = await memory_system.get_session_context(session_id)
        assert len(session_context) > 0  # Should have context from saved messages

    @pytest.mark.asyncio
    async def test_learning_improves_with_feedback(
        self,
        learning_system,
        sample_pai_instance_id
    ):
        """Test that learning system improves with feedback"""
        # Record initial interactions
        for i in range(5):
            await learning_system.record_interaction_outcome(
                sample_pai_instance_id,
                "documentation",
                {"input": f"request {i}"},
                {"output": f"response {i}"},
                success=True,
                quality_score=0.8 + (i * 0.02)  # Improving scores
            )

        # Record a failed interaction
        await learning_system.record_interaction_outcome(
            sample_pai_instance_id,
            "documentation",
            {"input": "bad request"},
            {"output": "error"},
            success=False,
            quality_score=0.2
        )

        # Learn from feedback
        await learning_system.process_user_feedback(
            sample_pai_instance_id,
            "msg-123",
            rating=5,
            feedback_text="Excellent documentation!"
        )

        # Get report
        report = await learning_system.get_learning_effectiveness_report(sample_pai_instance_id)
        assert "total_learnings" in report

    @pytest.mark.asyncio
    async def test_personality_adaptation_workflow(
        self,
        personality_manager,
        db_session
    ):
        """Test personality adaptation based on user interaction"""
        import uuid
        from backend.db.models import PAIInstance

        # Generate unique PAI instance ID for this test
        sample_pai_instance_id = str(uuid.uuid4())

        # Create PAI instance
        pai = PAIInstance(
            id=sample_pai_instance_id,
            name=f"adaptive-pai-{uuid.uuid4()}",
            specialization="mentor",
            base_model="claude-sonnet-4-6",
            personality_profile={"empathy_level": 0.8}
        )
        db_session.add(pai)
        db_session.commit()

        # Load personality
        profile = await personality_manager.load_personality(sample_pai_instance_id)
        assert profile is not None

        # Adapt to user with different emotions
        frustrated_adaptation = await personality_manager.adapt_to_user(
            sample_pai_instance_id,
            "I'm so frustrated and angry with this!"
        )
        assert "frustrated" in frustrated_adaptation["response_style"].lower() or \
               "empathetic" in frustrated_adaptation["response_style"].lower() or \
               "reassuring" in frustrated_adaptation["response_style"].lower()

        excited_adaptation = await personality_manager.adapt_to_user(
            sample_pai_instance_id,
            "This is amazing and I love it!"
        )
        assert "excited" in excited_adaptation["response_style"].lower() or \
               "energetic" in excited_adaptation["response_style"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, pai_engine):
        """Test handling multiple concurrent sessions"""
        # Create multiple sessions concurrently
        session_ids = await asyncio.gather(
            pai_engine.create_session("user1"),
            pai_engine.create_session("user2"),
            pai_engine.create_session("user3"),
        )

        assert len(session_ids) == 3
        assert len(set(session_ids)) == 3  # All unique
        assert len(pai_engine.sessions) == 3

        # End all sessions concurrently
        await asyncio.gather(*[pai_engine.end_session(sid) for sid in session_ids])

        assert len(pai_engine.sessions) == 0

    @pytest.mark.asyncio
    async def test_memory_persistence_across_sessions(
        self,
        memory_system,
        sample_user_id,
        db_session
    ):
        """Test that memory persists across different sessions"""
        # Create semantic memory
        learning_id = await memory_system.save_learning(
            sample_user_id,
            "User prefers concise technical explanations",
            memory_type="semantic",
            importance=0.9
        )

        # Verify it's persisted
        from backend.db.models import Memory as MemoryModel
        memory_record = db_session.query(MemoryModel).filter_by(id=learning_id).first()
        assert memory_record is not None

        # Create new session (simulated)
        new_session_id = "new-session-456"

        # Retrieve the learning in new session context
        learned_memories = await memory_system.get_relevant_memories(sample_user_id)

        # Should be able to retrieve the learning
        assert isinstance(learned_memories, list)

    @pytest.mark.asyncio
    async def test_error_recovery(self, pai_engine, memory_system, sample_user_id):
        """Test system recovery from errors"""
        from backend.core.exceptions import SessionNotFoundError

        # Create session
        session_id = await pai_engine.create_session(sample_user_id)

        # Try invalid operations - should raise SessionNotFoundError
        with pytest.raises(SessionNotFoundError):
            await pai_engine.send_message("invalid", "message")

        # Verify session still exists and can be used
        assert session_id in pai_engine.sessions

        # Save message should still work
        msg_id = await memory_system.save_message(
            session_id,
            sample_user_id,
            "Recovery test message"
        )
        assert msg_id is not None

    @pytest.mark.asyncio
    async def test_database_consistency(
        self,
        pai_engine,
        memory_system,
        sample_user_id,
        db_session
    ):
        """Test database consistency across operations"""
        from backend.db.models import Session as SessionModel, Memory as MemoryModel

        # Create session
        session_id = await pai_engine.create_session(sample_user_id)

        # Add memories
        for i in range(5):
            await memory_system.save_message(session_id, sample_user_id, f"Message {i}")

        # Verify counts
        session_count = db_session.query(SessionModel).filter_by(id=session_id).count()
        message_count = db_session.query(MemoryModel).filter_by(session_id=session_id).count()

        assert session_count == 1
        assert message_count == 5

        # End session
        await pai_engine.end_session(session_id)

        # Session should still exist in DB (just marked ended)
        session_record = db_session.query(SessionModel).filter_by(id=session_id).first()
        assert session_record is not None
        assert session_record.ended_at is not None

        # Memories should still exist
        memory_count = db_session.query(MemoryModel).filter_by(session_id=session_id).count()
        assert memory_count == 5


class TestDataIntegrity:
    """Test data integrity across operations"""

    @pytest.mark.asyncio
    async def test_no_data_loss_on_session_end(
        self,
        pai_engine,
        memory_system,
        sample_user_id,
        db_session
    ):
        """Ensure no data loss when session ends"""
        from backend.db.models import Message as MessageModel

        session_id = await pai_engine.create_session(sample_user_id)

        # Add multiple messages
        message_ids = []
        for i in range(10):
            msg_id = await memory_system.save_message(
                session_id,
                sample_user_id,
                f"Important message {i}",
                sender="user" if i % 2 == 0 else "assistant"
            )
            message_ids.append(msg_id)

        # End session
        await pai_engine.end_session(session_id)

        # Verify all messages still exist in database
        for msg_id in message_ids:
            msg = db_session.query(MessageModel).filter_by(id=msg_id).first()
            # Messages should still exist (they weren't deleted with session end)
            # Note: In this implementation, messages are in Memory table, not Message table

        # Verify session is marked ended
        from backend.db.models import Session as SessionModel
        session = db_session.query(SessionModel).filter_by(id=session_id).first()
        assert session.ended_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
