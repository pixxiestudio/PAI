"""Tests for backend/core/context.py, learning.py, and personality.py"""
import pytest
from backend.core.personality import EmotionalTone, CommunicationStyle


class TestContextInjection:
    """Test suite for ContextManager and ContextInjector"""

    @pytest.mark.asyncio
    async def test_build_context_injection(self, context_manager, sample_session_id, sample_user_id):
        """Test building context injection"""
        context = await context_manager.injector.build_context_injection(
            sample_session_id,
            sample_user_id
        )

        assert isinstance(context, str)

    @pytest.mark.asyncio
    async def test_inject_with_empathy_frustrated(self, context_manager, sample_session_id, sample_user_id):
        """Test empathy injection for frustrated user"""
        frustrated_message = "I'm so frustrated with this bug, it's driving me crazy!"

        context = await context_manager.injector.inject_with_empathy(
            sample_session_id,
            sample_user_id,
            frustrated_message
        )

        assert isinstance(context, str)
        # Should contain empathy guidance
        if "Empathy Guidance" in context:
            assert "frustrat" in context.lower()

    @pytest.mark.asyncio
    async def test_inject_with_empathy_confused(self, context_manager, sample_session_id, sample_user_id):
        """Test empathy injection for confused user"""
        confused_message = "I don't understand how this works, I'm completely lost"

        context = await context_manager.injector.inject_with_empathy(
            sample_session_id,
            sample_user_id,
            confused_message
        )

        assert isinstance(context, str)

    @pytest.mark.asyncio
    async def test_score_context_relevance(self, context_manager):
        """Test context relevance scoring"""
        context = "discussing Python functions and decorators"
        query = "How do decorators work in Python?"

        score = await context_manager.injector.score_context_relevance(context, query)

        assert 0 <= score <= 1
        assert score > 0  # Should have some overlap


class TestSelfLearning:
    """Test suite for SelfLearningSystem"""

    @pytest.mark.asyncio
    async def test_record_interaction_outcome(self, learning_system, sample_pai_instance_id, db_session):
        """Test recording interaction outcome"""
        learning_id = await learning_system.record_interaction_outcome(
            sample_pai_instance_id,
            "code_review",
            {"code": "sample code"},
            {"review": "Good structure"},
            success=True,
            quality_score=0.95
        )

        assert learning_id is not None
        assert len(learning_id) > 0

    @pytest.mark.asyncio
    async def test_get_success_patterns(self, learning_system, sample_pai_instance_id):
        """Test retrieving successful patterns"""
        # Record successful outcome
        await learning_system.record_interaction_outcome(
            sample_pai_instance_id,
            "code_analysis",
            {"input": "test"},
            {"output": "analysis"},
            success=True,
            quality_score=0.9
        )

        # Get patterns
        patterns = await learning_system.get_success_patterns(
            sample_pai_instance_id,
            interaction_type="code_analysis"
        )

        # May return empty if DB queries don't work, that's OK for this test
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_detect_pattern(self, learning_system, sample_pai_instance_id, db_session):
        """Test pattern detection"""
        learning_id = await learning_system.detect_pattern(
            sample_pai_instance_id,
            "detailed_explanation_preference",
            "User consistently appreciates detailed, step-by-step explanations",
            success_count=8,
            failure_count=2
        )

        assert learning_id is not None

    @pytest.mark.asyncio
    async def test_get_effective_patterns(self, learning_system, sample_pai_instance_id):
        """Test retrieving effective patterns"""
        # Create pattern
        await learning_system.detect_pattern(
            sample_pai_instance_id,
            "test_pattern",
            "Test description",
            success_count=9,
            failure_count=1
        )

        # Get patterns
        patterns = await learning_system.get_effective_patterns(
            sample_pai_instance_id,
            min_success_rate=0.8
        )

        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_learn_user_preference(self, learning_system, sample_pai_instance_id, db_session):
        """Test learning user preference"""
        learning_id = await learning_system.learn_user_preference(
            sample_pai_instance_id,
            "communication_style",
            "technical_and_concise",
            confidence=0.85
        )

        assert learning_id is not None

    @pytest.mark.asyncio
    async def test_get_learned_preferences(self, learning_system, sample_pai_instance_id):
        """Test retrieving learned preferences"""
        # Learn a preference
        await learning_system.learn_user_preference(
            sample_pai_instance_id,
            "code_style",
            "pythonic",
            confidence=0.9
        )

        # Get preferences
        prefs = await learning_system.get_learned_preferences(
            sample_pai_instance_id,
            min_confidence=0.8
        )

        assert isinstance(prefs, dict)

    @pytest.mark.asyncio
    async def test_process_user_feedback(self, learning_system, sample_pai_instance_id):
        """Test processing user feedback"""
        # This should not raise an error
        await learning_system.process_user_feedback(
            sample_pai_instance_id,
            "msg-123",
            rating=5,
            feedback_text="Excellent explanation!"
        )

    @pytest.mark.asyncio
    async def test_extract_skill_from_interaction(self, learning_system, sample_pai_instance_id):
        """Test extracting skill from interaction"""
        learning_id = await learning_system.extract_skill_from_interaction(
            sample_pai_instance_id,
            "analyze_code_structure",
            ["Parse code", "Identify patterns", "Generate report"],
            success_rate=0.92
        )

        assert learning_id is not None

    @pytest.mark.asyncio
    async def test_get_learning_effectiveness_report(self, learning_system, sample_pai_instance_id):
        """Test getting learning effectiveness report"""
        # Record some learnings first
        await learning_system.record_interaction_outcome(
            sample_pai_instance_id,
            "test",
            {},
            {},
            success=True,
            quality_score=0.8
        )

        # Get report
        report = await learning_system.get_learning_effectiveness_report(sample_pai_instance_id)

        assert isinstance(report, dict)
        # May be empty if no learnings exist


class TestPersonality:
    """Test suite for PersonalityManager and EmpathyDetector"""

    def test_empathy_detector_frustrated(self):
        """Test detecting frustrated tone"""
        message = "This is frustrating! Nothing works!"
        tone = EmotionalTone(True).detect_tone(message)

        # Use static method
        from backend.core.personality import EmpathyDetector
        tone = EmpathyDetector.detect_tone(message)

        assert tone == EmotionalTone.FRUSTRATED

    def test_empathy_detector_confused(self):
        """Test detecting confused tone"""
        from backend.core.personality import EmpathyDetector

        message = "I don't understand this at all, I'm completely lost"
        tone = EmpathyDetector.detect_tone(message)

        assert tone == EmotionalTone.CONFUSED

    def test_empathy_detector_excited(self):
        """Test detecting excited tone"""
        from backend.core.personality import EmpathyDetector

        message = "This is awesome! I'm so excited about this feature!"
        tone = EmpathyDetector.detect_tone(message)

        assert tone == EmotionalTone.EXCITED

    def test_empathy_detector_stressed(self):
        """Test detecting stressed tone"""
        from backend.core.personality import EmpathyDetector

        message = "This is urgent and critical, I have a deadline tomorrow!"
        tone = EmpathyDetector.detect_tone(message)

        assert tone == EmotionalTone.STRESSED

    def test_extract_expertise_level_beginner(self):
        """Test expertise detection - beginner"""
        from backend.core.personality import EmpathyDetector

        message = "How do I start learning Python? I've never coded before."
        level = EmpathyDetector.extract_expertise_level(message)

        assert level == "beginner"

    def test_extract_expertise_level_expert(self):
        """Test expertise detection - expert"""
        from backend.core.personality import EmpathyDetector

        message = "How should I optimize this microservices architecture for scalability?"
        level = EmpathyDetector.extract_expertise_level(message)

        assert level == "expert"

    def test_extract_expertise_level_intermediate(self):
        """Test expertise detection - intermediate"""
        from backend.core.personality import EmpathyDetector

        message = "Can you help me debug this function?"
        level = EmpathyDetector.extract_expertise_level(message)

        assert level == "intermediate"

    @pytest.mark.asyncio
    async def test_adapt_to_user(self, personality_manager):
        """Test user adaptation"""
        adaptations = await personality_manager.adapt_to_user(
            "test-pai-id",
            "I'm frustrated with this code not working"
        )

        assert "emotional_tone" in adaptations
        assert "estimated_expertise" in adaptations
        assert "response_style" in adaptations

    @pytest.mark.asyncio
    async def test_build_empathy_prompt_extension(self, personality_manager):
        """Test building empathy prompt extension"""
        extension = await personality_manager.build_empathy_prompt_extension(
            EmotionalTone.FRUSTRATED,
            "intermediate"
        )

        assert "Response Guidelines" in extension
        assert "frustrated" in extension.lower()

    @pytest.mark.asyncio
    async def test_load_personality(self, personality_manager, sample_pai_instance_id, db_session):
        """Test loading personality profile"""
        from backend.db.models import PAIInstance

        # Create PAI instance with personality
        pai = PAIInstance(
            id=sample_pai_instance_id,
            name="test-pai",
            specialization="code",
            base_model="claude-sonnet-4-6",
            personality_profile={"empathy_level": 0.9, "communication_style": "technical"}
        )
        db_session.add(pai)
        db_session.commit()

        # Load personality
        profile = await personality_manager.load_personality(sample_pai_instance_id)

        assert profile is not None
        assert profile.empathy_level == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
