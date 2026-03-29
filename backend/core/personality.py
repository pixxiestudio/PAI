"""Personality & Empathy System for PAI"""
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session as DBSession
from backend.db.models import PAIInstance


class CommunicationStyle(str, Enum):
    """Communication style preferences"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    SIMPLE = "simple"
    DETAILED = "detailed"
    CONCISE = "concise"


class EmotionalTone(str, Enum):
    """Detected emotional tones"""
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    EXCITED = "excited"
    STRESSED = "stressed"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"


@dataclass
class PersonalityProfile:
    """User/PAI personality profile"""
    pai_instance_id: str
    communication_style: str = "balanced"
    technical_depth: str = "intermediate"  # "beginner", "intermediate", "expert"
    empathy_level: float = 0.8  # 0-1 scale
    response_formality: str = "professional"
    collaborative: bool = True
    traits: Dict[str, float] = None  # e.g., {"patient": 0.9, "detail-oriented": 0.7}

    def __post_init__(self):
        if self.traits is None:
            self.traits = {}


class EmpathyDetector:
    """Detects emotional tone and context from user messages"""

    # Emotion keyword mappings
    EMOTION_KEYWORDS = {
        EmotionalTone.FRUSTRATED: [
            "frustrated", "annoyed", "angry", "hate", "terrible", "awful", "useless",
            "doesn't work", "broken", "bug", "error", "fail", "can't", "impossible"
        ],
        EmotionalTone.CONFUSED: [
            "confused", "don't understand", "unclear", "lost", "stuck", "how do i",
            "what's", "why", "explain", "help me", "bewildered", "mystified"
        ],
        EmotionalTone.EXCITED: [
            "excited", "great", "awesome", "wonderful", "love", "amazing", "excellent",
            "perfect", "cool", "nice", "sweet", "yes!", "finally"
        ],
        EmotionalTone.STRESSED: [
            "stressed", "pressure", "deadline", "urgent", "panic", "rush", "time-critical",
            "crunch", "emergency", "asap", "critical", "overwhelmed"
        ],
        EmotionalTone.SATISFIED: [
            "thanks", "thank you", "appreciate", "helpful", "works", "solved", "fixed",
            "good", "perfect", "exactly", "just what i needed"
        ]
    }

    @staticmethod
    def detect_tone(message: str) -> Optional[EmotionalTone]:
        """
        Detect emotional tone from message

        Args:
            message: User message

        Returns:
            Detected emotional tone or None
        """
        message_lower = message.lower()

        for emotion, keywords in EmpathyDetector.EMOTION_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                return emotion

        return EmotionalTone.NEUTRAL

    @staticmethod
    def extract_expertise_level(message: str) -> str:
        """
        Estimate user's technical expertise level from message

        Args:
            message: User message

        Returns:
            "beginner", "intermediate", or "expert"
        """
        message_lower = message.lower()

        # Beginner indicators
        beginner_indicators = [
            "how do i", "what is", "basics", "start from scratch",
            "never used", "first time", "noob", "newbie"
        ]

        # Expert indicators
        expert_indicators = [
            "architecture", "microservices", "optimization", "edge case",
            "scalability", "concurrent", "performance tuning", "algorithm",
            "refactor", "design pattern", "best practice"
        ]

        expert_score = sum(1 for ind in expert_indicators if ind in message_lower)
        beginner_score = sum(1 for ind in beginner_indicators if ind in message_lower)

        if expert_score > beginner_score and expert_score > 0:
            return "expert"
        elif beginner_score > 0:
            return "beginner"
        else:
            return "intermediate"


class PersonalityManager:
    """Manages PAI personality and empathy"""

    def __init__(self, db_session: Optional[DBSession] = None):
        """
        Initialize personality manager

        Args:
            db_session: Database session for persistence
        """
        self.db_session = db_session
        self.empathy_detector = EmpathyDetector()

    async def load_personality(
        self,
        pai_instance_id: str
    ) -> Optional[PersonalityProfile]:
        """
        Load personality profile for a PAI instance

        Args:
            pai_instance_id: PAI instance ID

        Returns:
            PersonalityProfile or None
        """
        if not self.db_session:
            return None

        instance = (
            self.db_session.query(PAIInstance)
            .filter_by(id=pai_instance_id)
            .first()
        )

        if not instance or not instance.personality_profile:
            return None

        profile_data = instance.personality_profile
        return PersonalityProfile(
            pai_instance_id=pai_instance_id,
            communication_style=profile_data.get("communication_style", "balanced"),
            technical_depth=profile_data.get("technical_depth", "intermediate"),
            empathy_level=profile_data.get("empathy_level", 0.8),
            response_formality=profile_data.get("response_formality", "professional"),
            collaborative=profile_data.get("collaborative", True),
            traits=profile_data.get("traits", {})
        )

    async def adapt_to_user(
        self,
        pai_instance_id: str,
        user_message: str
    ) -> Dict[str, any]:
        """
        Detect user context and return adaptation instructions

        Args:
            pai_instance_id: PAI instance ID
            user_message: Current user message

        Returns:
            Dictionary with adaptation instructions
        """
        # Detect emotional tone
        tone = self.empathy_detector.detect_tone(user_message)

        # Estimate expertise level
        expertise = self.empathy_detector.extract_expertise_level(user_message)

        # Build adaptation instructions
        adaptations = {
            "emotional_tone": tone,
            "estimated_expertise": expertise,
            "response_style": self._get_response_style(tone, expertise),
            "emphasis_areas": self._get_emphasis_areas(tone),
            "avoid": self._get_avoid_items(tone)
        }

        return adaptations

    @staticmethod
    def _get_response_style(tone: EmotionalTone, expertise: str) -> str:
        """Get recommended response style based on tone and expertise"""
        if tone == EmotionalTone.FRUSTRATED:
            return "Calm, reassuring, solution-focused"
        elif tone == EmotionalTone.CONFUSED:
            return "Clear, step-by-step, use examples"
        elif tone == EmotionalTone.EXCITED:
            return "Enthusiastic, energetic, celebrate progress"
        elif tone == EmotionalTone.STRESSED:
            return "Practical, prioritized, action-oriented"
        elif expertise == "beginner":
            return "Educational, patience-focused, no jargon"
        elif expertise == "expert":
            return "Technical, assume knowledge, focus on optimization"
        else:
            return "Professional, balanced, accessible"

    @staticmethod
    def _get_emphasis_areas(tone: EmotionalTone) -> List[str]:
        """Get areas to emphasize in response based on tone"""
        emphasis_map = {
            EmotionalTone.FRUSTRATED: ["validation", "acknowledgment", "solution"],
            EmotionalTone.CONFUSED: ["clarity", "examples", "step-by-step"],
            EmotionalTone.EXCITED: ["celebration", "next_steps", "resources"],
            EmotionalTone.STRESSED: ["priority", "efficiency", "quick_wins"],
            EmotionalTone.SATISFIED: ["reinforcement", "build_on_success"],
            EmotionalTone.NEUTRAL: ["helpfulness", "clarity"]
        }
        return emphasis_map.get(tone, ["helpfulness"])

    @staticmethod
    def _get_avoid_items(tone: EmotionalTone) -> List[str]:
        """Get things to avoid in response based on tone"""
        avoid_map = {
            EmotionalTone.FRUSTRATED: ["blame", "complexity", "overwhelming_options"],
            EmotionalTone.CONFUSED: ["jargon", "assumptions", "speed"],
            EmotionalTone.EXCITED: ["negativity", "lengthy_caveats"],
            EmotionalTone.STRESSED: ["lengthy_explanations", "side_topics"],
            EmotionalTone.SATISFIED: ["criticism", "unnecessary_changes"],
            EmotionalTone.NEUTRAL: ["assumptions"]
        }
        return avoid_map.get(tone, [])

    async def build_empathy_prompt_extension(
        self,
        tone: EmotionalTone,
        expertise: str
    ) -> str:
        """
        Build prompt extension with empathy instructions

        Args:
            tone: Detected emotional tone
            expertise: User expertise level

        Returns:
            Prompt extension for empathy-aware response
        """
        style = self._get_response_style(tone, expertise)
        emphasis = ", ".join(self._get_emphasis_areas(tone))
        avoid = ", ".join(self._get_avoid_items(tone))

        extension = f"""
[Response Guidelines]
- Emotional Tone: {tone.value}
- User Expertise: {expertise}
- Communication Style: {style}
- Emphasize: {emphasis}
- Avoid: {avoid}
"""
        return extension

    async def learn_from_interaction(
        self,
        pai_instance_id: str,
        user_feedback: int,
        interaction_context: Dict[str, any]
    ) -> None:
        """
        Learn from user feedback to improve personality

        Args:
            pai_instance_id: PAI instance ID
            user_feedback: Rating (1-5 stars)
            interaction_context: Context of the interaction
        """
        if not self.db_session:
            return

        instance = (
            self.db_session.query(PAIInstance)
            .filter_by(id=pai_instance_id)
            .first()
        )

        if not instance or not instance.personality_profile:
            return

        profile = instance.personality_profile

        # Adjust empathy level based on feedback
        if user_feedback >= 4:
            # User was satisfied - slightly increase empathy
            profile["empathy_level"] = min(1.0, profile.get("empathy_level", 0.8) + 0.05)
        elif user_feedback <= 2:
            # User was not satisfied - keep empathy high to compensate
            profile["empathy_level"] = max(0.5, profile.get("empathy_level", 0.8) - 0.1)

        instance.personality_profile = profile
        self.db_session.commit()


# Global personality manager instance
personality_manager: Optional[PersonalityManager] = None


def get_personality_manager(db_session: Optional[DBSession] = None) -> PersonalityManager:
    """Get or create global personality manager instance"""
    global personality_manager
    if personality_manager is None:
        personality_manager = PersonalityManager(db_session)
    return personality_manager
