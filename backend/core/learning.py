"""Self-Learning System for PAI"""
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy.orm import Session as DBSession
from backend.db.models import Learning as LearningModel, UserFeedback

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LearningRecord:
    """Record of a learning outcome"""
    id: str
    learning_type: str  # "outcome", "pattern", "preference", "skill"
    content: Dict[str, Any]
    effectiveness_score: float
    created_at: datetime


class SelfLearningSystem:
    """Self-learning system for PAI - learns from interactions"""

    def __init__(self, db_session: Optional[DBSession] = None):
        """
        Initialize self-learning system

        Args:
            db_session: Database session for persistence
        """
        self.db_session = db_session

    # Outcome Tracking

    async def record_interaction_outcome(
        self,
        pai_instance_id: str,
        interaction_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        success: bool,
        quality_score: float = 0.0
    ) -> str:
        """
        Record outcome of an interaction

        Args:
            pai_instance_id: PAI instance ID
            interaction_type: Type of interaction ("code_review", "architecture", etc.)
            input_data: Input to the interaction
            output_data: Output/result from PAI
            success: Whether interaction was successful
            quality_score: Quality score of response (0-1)

        Returns:
            learning_id: ID of recorded learning
        """
        learning_id = str(uuid.uuid4())

        learning_record = LearningModel(
            id=learning_id,
            pai_instance_id=pai_instance_id,
            learning_type="outcome",
            content={
                "interaction_type": interaction_type,
                "input_summary": str(input_data)[:500],
                "output_summary": str(output_data)[:500],
                "success": success,
                "quality_score": quality_score
            },
            effectiveness_score=quality_score if success else 0.5,
            applied_count=0,
            created_at=datetime.now(timezone.utc)
        )

        if self.db_session:
            self.db_session.add(learning_record)
            self.db_session.commit()

        return learning_id

    async def get_success_patterns(
        self,
        pai_instance_id: str,
        interaction_type: Optional[str] = None,
        limit: int = 5
    ) -> List[LearningRecord]:
        """
        Get successful patterns for an interaction type

        Note: Interaction type filtering requires PostgreSQL.
        SQLite users will get all outcome patterns without filtering.

        Args:
            pai_instance_id: PAI instance ID
            interaction_type: Filter by interaction type (optional, PostgreSQL only)
            limit: Maximum patterns to return

        Returns:
            List of successful learning records
        """
        if not self.db_session:
            return []

        query = (
            self.db_session.query(LearningModel)
            .filter(
                LearningModel.pai_instance_id == pai_instance_id,
                LearningModel.learning_type == "outcome",
                LearningModel.effectiveness_score > 0.7
            )
        )

        # Skip JSON filtering for SQLite compatibility
        # If using PostgreSQL, uncomment this:
        # if interaction_type:
        #     query = query.filter(
        #         LearningModel.content["interaction_type"].astext == interaction_type
        #     )

        records = (
            query
            .order_by(LearningModel.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            LearningRecord(
                id=r.id,
                learning_type=r.learning_type,
                content=r.content,
                effectiveness_score=r.effectiveness_score,
                created_at=r.created_at
            )
            for r in records
        ]

    # Pattern Detection

    async def detect_pattern(
        self,
        pai_instance_id: str,
        pattern_name: str,
        pattern_description: str,
        success_count: int,
        failure_count: int
    ) -> str:
        """
        Record a detected pattern

        Args:
            pai_instance_id: PAI instance ID
            pattern_name: Name of the pattern
            pattern_description: Description
            success_count: Times pattern succeeded
            failure_count: Times pattern failed

        Returns:
            learning_id: ID of pattern record
        """
        learning_id = str(uuid.uuid4())
        total = success_count + failure_count
        success_rate = success_count / total if total > 0 else 0.0

        learning_record = LearningModel(
            id=learning_id,
            pai_instance_id=pai_instance_id,
            learning_type="pattern",
            content={
                "pattern_name": pattern_name,
                "description": pattern_description,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": success_rate
            },
            effectiveness_score=success_rate,
            applied_count=0,
            created_at=datetime.now(timezone.utc)
        )

        if self.db_session:
            self.db_session.add(learning_record)
            self.db_session.commit()

        return learning_id

    async def get_effective_patterns(
        self,
        pai_instance_id: str,
        min_success_rate: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Get patterns that work effectively

        Args:
            pai_instance_id: PAI instance ID
            min_success_rate: Minimum success rate threshold

        Returns:
            List of effective patterns
        """
        if not self.db_session:
            return []

        patterns = (
            self.db_session.query(LearningModel)
            .filter(
                LearningModel.pai_instance_id == pai_instance_id,
                LearningModel.learning_type == "pattern",
                LearningModel.effectiveness_score >= min_success_rate
            )
            .order_by(LearningModel.effectiveness_score.desc())
            .all()
        )

        return [p.content for p in patterns]

    # Preference Learning

    async def learn_user_preference(
        self,
        pai_instance_id: str,
        preference_name: str,
        preference_value: str,
        confidence: float = 0.8
    ) -> str:
        """
        Learn a user preference

        Args:
            pai_instance_id: PAI instance ID
            preference_name: Name of preference (e.g., "communication_style")
            preference_value: Value of preference (e.g., "detailed")
            confidence: Confidence in learning (0-1)

        Returns:
            learning_id: ID of preference record
        """
        learning_id = str(uuid.uuid4())

        learning_record = LearningModel(
            id=learning_id,
            pai_instance_id=pai_instance_id,
            learning_type="preference",
            content={
                "preference_name": preference_name,
                "preference_value": preference_value,
                "confidence": confidence
            },
            effectiveness_score=confidence,
            applied_count=0,
            created_at=datetime.now(timezone.utc)
        )

        if self.db_session:
            self.db_session.add(learning_record)
            self.db_session.commit()

        return learning_id

    async def get_learned_preferences(
        self,
        pai_instance_id: str,
        min_confidence: float = 0.6
    ) -> Dict[str, str]:
        """
        Get all learned preferences for a PAI instance

        Args:
            pai_instance_id: PAI instance ID
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary of preferences
        """
        if not self.db_session:
            return {}

        preferences = (
            self.db_session.query(LearningModel)
            .filter(
                LearningModel.pai_instance_id == pai_instance_id,
                LearningModel.learning_type == "preference",
                LearningModel.effectiveness_score >= min_confidence
            )
            .all()
        )

        result = {}
        for pref in preferences:
            name = pref.content.get("preference_name")
            value = pref.content.get("preference_value")
            if name and value:
                result[name] = value

        return result

    # Feedback Processing

    async def process_user_feedback(
        self,
        pai_instance_id: str,
        message_id: str,
        rating: int,
        feedback_text: Optional[str] = None
    ) -> None:
        """
        Process user feedback and extract learnings

        Args:
            pai_instance_id: PAI instance ID
            message_id: ID of message being rated
            rating: User rating (1-5 stars)
            feedback_text: Optional feedback text
        """
        # Rate quality based on star rating
        quality_map = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}
        quality_score = quality_map.get(rating, 0.5)

        # Record feedback
        if self.db_session:
            feedback = UserFeedback(
                id=str(uuid.uuid4()),
                message_id=message_id,
                rating=rating,
                feedback_text=feedback_text,
                quality_score=quality_score,
                created_at=datetime.now(timezone.utc)
            )
            self.db_session.add(feedback)

            # Update related learning records
            if rating >= 4:  # Good feedback
                # Learn from positive feedback - reinforce successful patterns
                if feedback_text:
                    await self.learn_user_preference(
                        pai_instance_id,
                        "positive_feedback_pattern",
                        feedback_text,
                        confidence=0.9
                    )
            elif rating <= 2:  # Poor feedback
                # Learn from negative feedback
                if feedback_text:
                    await self.learn_user_preference(
                        pai_instance_id,
                        "correction_from_feedback",
                        feedback_text,
                        confidence=0.6
                    )
            else:  # Neutral feedback (rating 3)
                # Mixed feedback - learn areas for improvement
                if feedback_text:
                    await self.learn_user_preference(
                        pai_instance_id,
                        "improvement_area",
                        feedback_text,
                        confidence=0.7
                    )

            self.db_session.commit()

    async def extract_skill_from_interaction(
        self,
        pai_instance_id: str,
        skill_name: str,
        skill_steps: List[str],
        success_rate: float
    ) -> str:
        """
        Extract and record a new skill from successful interaction patterns

        Args:
            pai_instance_id: PAI instance ID
            skill_name: Name of new skill
            skill_steps: Steps to perform the skill
            success_rate: Success rate of this skill

        Returns:
            learning_id: ID of skill record
        """
        learning_id = str(uuid.uuid4())

        learning_record = LearningModel(
            id=learning_id,
            pai_instance_id=pai_instance_id,
            learning_type="skill",
            content={
                "skill_name": skill_name,
                "skill_steps": skill_steps,
                "success_rate": success_rate
            },
            effectiveness_score=success_rate,
            applied_count=0,
            created_at=datetime.now(timezone.utc)
        )

        if self.db_session:
            self.db_session.add(learning_record)
            self.db_session.commit()

        return learning_id

    # Learning Application

    async def increment_skill_usage(self, learning_id: str) -> None:
        """
        Increment the number of times a learned skill has been applied

        Args:
            learning_id: Learning record ID
        """
        if not self.db_session:
            return

        learning = self.db_session.query(LearningModel).filter_by(id=learning_id).first()
        if learning:
            learning.applied_count += 1
            self.db_session.commit()

    async def get_learning_effectiveness_report(
        self,
        pai_instance_id: str
    ) -> Dict[str, Any]:
        """
        Get summary of learning effectiveness

        Args:
            pai_instance_id: PAI instance ID

        Returns:
            Dictionary with effectiveness metrics
        """
        if not self.db_session:
            return {}

        all_learnings = (
            self.db_session.query(LearningModel)
            .filter(LearningModel.pai_instance_id == pai_instance_id)
            .all()
        )

        if not all_learnings:
            return {"message": "No learnings recorded yet"}

        avg_effectiveness = sum(l.effectiveness_score for l in all_learnings) / len(all_learnings)
        total_applied = sum(l.applied_count for l in all_learnings)

        by_type = {}
        for learning in all_learnings:
            ltype = learning.learning_type
            if ltype not in by_type:
                by_type[ltype] = {"count": 0, "avg_score": 0, "total": 0}
            by_type[ltype]["count"] += 1
            by_type[ltype]["total"] += learning.effectiveness_score

        for ltype in by_type:
            by_type[ltype]["avg_score"] = by_type[ltype]["total"] / by_type[ltype]["count"]

        return {
            "pai_instance_id": pai_instance_id,
            "total_learnings": len(all_learnings),
            "average_effectiveness": avg_effectiveness,
            "total_times_applied": total_applied,
            "by_type": by_type
        }


# Global self-learning system instance
learning_system: Optional[SelfLearningSystem] = None


def get_learning_system(db_session: Optional[DBSession] = None) -> SelfLearningSystem:
    """Get or create global learning system instance"""
    global learning_system
    if learning_system is None:
        learning_system = SelfLearningSystem(db_session)
    return learning_system
