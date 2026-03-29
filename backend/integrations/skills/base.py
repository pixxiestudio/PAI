"""Base interface for PAI skills/plugins"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class SkillParameter:
    """Definition of a skill parameter"""
    name: str
    type: str  # "string", "int", "float", "bool", "json"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum_values: List[str] = field(default_factory=list)


@dataclass
class SkillResult:
    """Result of skill execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class Skill(ABC):
    """
    Base class for all PAI skills (plugins/extensions)

    Skills are modular capabilities that PAI instances can invoke.
    They handle specific tasks like code analysis, documentation generation,
    API calls, etc.

    Example:
        class CodeAnalyzerSkill(Skill):
            @property
            def name(self) -> str:
                return "code_analyzer"

            async def execute(self, code: str) -> SkillResult:
                # Analyze the code
                return SkillResult(
                    success=True,
                    data={"issues": [], "quality_score": 0.95}
                )
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for this skill

        Returns:
            Skill name (e.g., "code_analyzer", "github_api", "document_generator")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what this skill does

        Returns:
            Description string
        """
        pass

    @property
    def version(self) -> str:
        """
        Semantic version of this skill

        Returns:
            Version string (e.g., "1.0.0")
        """
        return "1.0.0"

    @property
    def parameters(self) -> Dict[str, SkillParameter]:
        """
        Parameters this skill accepts

        Returns:
            Dict mapping parameter names to SkillParameter definitions
        """
        return {}

    @property
    def required_integrations(self) -> List[str]:
        """
        External integrations required by this skill (e.g., "github", "stripe")

        Returns:
            List of integration names
        """
        return []

    @property
    def tags(self) -> List[str]:
        """
        Tags for categorizing this skill (e.g., "code", "analysis", "github")

        Returns:
            List of tag strings
        """
        return []

    async def validate_parameters(self, **kwargs) -> bool:
        """
        Validate input parameters before execution

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if parameters are valid, False otherwise
        """
        # Check required parameters
        for param_name, param_def in self.parameters.items():
            if param_def.required and param_name not in kwargs:
                return False

        return True

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill with given parameters

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult with success status and result data
        """
        pass

    async def learn_from_feedback(self, feedback: Dict[str, Any]) -> None:
        """
        Optional: Learn from user feedback to improve performance

        Args:
            feedback: User feedback (e.g., {"rating": 5, "comment": "Very helpful"})
        """
        pass

    async def cleanup(self) -> None:
        """
        Optional: Cleanup resources when skill is unloaded
        """
        pass
