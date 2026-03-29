"""Skills management endpoints

Handles skill listing and execution
"""

from fastapi import APIRouter, Depends

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import ExecuteSkillRequest, SkillExecutionResult

router = APIRouter()


@router.get("/pai/{pai_instance_id}/skills")
async def list_skills(
    pai_instance_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    List available skills for a PAI instance

    Args:
        pai_instance_id: PAI instance identifier

    Returns:
        List of available skills with metadata
    """
    skill_registry = container.get_skill_registry()

    # Get all available skills
    skills_dict = skill_registry.list_skills()

    skills = [
        {
            "name": name,
            "description": description,
            "available": skill_registry.is_available(name)
        }
        for name, description in skills_dict.items()
    ]

    return {
        "pai_instance_id": pai_instance_id,
        "skills": skills,
        "total": len(skills)
    }


@router.post("/pai/{pai_instance_id}/skills/{skill_name}/execute", response_model=SkillExecutionResult)
async def execute_skill(
    pai_instance_id: str,
    skill_name: str,
    request: ExecuteSkillRequest,
    container: ServiceContainer = Depends(get_container)
):
    """
    Execute a skill

    Args:
        pai_instance_id: PAI instance identifier
        skill_name: Name of skill to execute
        request: Execution request with parameters

    Returns:
        SkillExecutionResult with outcome
    """
    skill_registry = container.get_skill_registry()

    # Execute skill
    result = await skill_registry.execute(skill_name, **request.parameters)

    return SkillExecutionResult(
        skill_name=skill_name,
        success=result.success,
        data=result.data,
        error=result.error,
        execution_time=0.0  # Would track actual execution time
    )


@router.get("/pai/{pai_instance_id}/skills/{skill_name}")
async def get_skill_details(
    pai_instance_id: str,
    skill_name: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get detailed information about a skill

    Args:
        pai_instance_id: PAI instance identifier
        skill_name: Name of skill

    Returns:
        Skill metadata and documentation
    """
    skill_registry = container.get_skill_registry()

    # Get skill
    skill = skill_registry.get_skill(skill_name)

    if not skill:
        from backend.core.exceptions import SkillException
        raise SkillException(f"Skill '{skill_name}' not found")

    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "parameters": {
            name: {
                "type": param.type,
                "description": param.description,
                "required": param.required,
                "default": param.default
            }
            for name, param in skill.parameters.items()
        },
        "tags": skill.tags if hasattr(skill, 'tags') else []
    }
