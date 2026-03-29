"""Skill registry and loader for PAI"""
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session as DBSession

from backend.integrations.skills.base import Skill, SkillResult
from backend.db.models import Skill as SkillModel

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Registry and loader for PAI skills

    Manages skill lifecycle:
    - Registration of new skills
    - Execution of loaded skills
    - Skill discovery and listing
    - Persistence in database
    """

    def __init__(self, db_session: Optional[DBSession] = None):
        """
        Initialize skill registry

        Args:
            db_session: Database session for skill persistence
        """
        self.db_session = db_session
        self.loaded_skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """
        Register a skill in memory and optionally save to database

        Args:
            skill: Skill instance to register
        """
        self.loaded_skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name} v{skill.version}")

        # Persist to database
        if self.db_session:
            self._save_skill_to_db(skill)

    def unregister(self, skill_name: str) -> None:
        """
        Unregister a skill from memory

        Args:
            skill_name: Name of skill to unregister
        """
        if skill_name in self.loaded_skills:
            skill = self.loaded_skills[skill_name]
            # Allow skill to cleanup
            import asyncio
            try:
                asyncio.run(skill.cleanup())
            except RuntimeError:
                # If already in event loop, skip cleanup
                pass

            del self.loaded_skills[skill_name]
            logger.info(f"Unregistered skill: {skill_name}")

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """
        Get a registered skill by name

        Args:
            skill_name: Name of skill to retrieve

        Returns:
            Skill instance if found, None otherwise
        """
        return self.loaded_skills.get(skill_name)

    def list_skills(self) -> Dict[str, str]:
        """
        List all registered skills with descriptions

        Returns:
            Dict mapping skill names to descriptions
        """
        return {
            name: skill.description
            for name, skill in self.loaded_skills.items()
        }

    async def execute(
        self,
        skill_name: str,
        **kwargs
    ) -> SkillResult:
        """
        Execute a registered skill

        Args:
            skill_name: Name of skill to execute
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult with execution outcome

        Raises:
            ValueError: If skill not found or validation fails
        """
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found")

        # Validate parameters
        if not await skill.validate_parameters(**kwargs):
            raise ValueError(
                f"Invalid parameters for skill '{skill_name}'. "
                f"Expected: {list(skill.parameters.keys())}"
            )

        try:
            result = await skill.execute(**kwargs)
            logger.debug(f"Skill '{skill_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing skill '{skill_name}': {str(e)}")
            return SkillResult(
                success=False,
                data=None,
                error=str(e)
            )

    def is_available(self, skill_name: str) -> bool:
        """
        Check if a skill is available and enabled

        Args:
            skill_name: Name of skill to check

        Returns:
            True if skill is registered and available
        """
        return skill_name in self.loaded_skills

    def _save_skill_to_db(self, skill: Skill) -> None:
        """
        Save skill metadata to database

        Args:
            skill: Skill instance to save
        """
        if not self.db_session:
            return

        # Check if skill already exists
        existing = self.db_session.query(SkillModel).filter_by(
            name=skill.name
        ).first()

        skill_record = SkillModel(
            id=skill.name,  # Use skill name as ID
            name=skill.name,
            version=skill.version,
            description=skill.description,
            path=skill.__class__.__module__,
            enabled=True,
            parameters={
                name: {
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default
                }
                for name, param in skill.parameters.items()
            }
        )

        if existing:
            # Update existing skill
            for key, value in skill_record.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            self.db_session.commit()
            logger.debug(f"Updated skill in database: {skill.name}")
        else:
            # Create new skill record
            self.db_session.add(skill_record)
            self.db_session.commit()
            logger.debug(f"Saved skill to database: {skill.name}")

    def load_from_database(self) -> List[str]:
        """
        Load skill metadata from database (for persistence)

        Note: This loads metadata only. Actual skill classes must be
        registered separately via register() method.

        Returns:
            List of skill names loaded from database
        """
        if not self.db_session:
            return []

        skills = self.db_session.query(SkillModel).filter_by(enabled=True).all()
        return [skill.name for skill in skills]
