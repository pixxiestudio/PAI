"""GitHub API endpoints for repository and issue management"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.integrations.github import GitHubSkill
from backend.integrations.github_config import GitHubConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])


def get_github_skill(container: ServiceContainer = Depends(get_container)) -> GitHubSkill:
    """Get GitHub skill instance from container

    Args:
        container: Service container

    Returns:
        GitHub skill instance
    """
    return GitHubSkill()


@router.post("/auth/token")
async def set_github_token(
    token: str,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Configure GitHub API token for user

    Args:
        token: GitHub Personal Access Token
        container: Service container
        db: Database session

    Returns:
        Success message
    """
    try:
        if not token or not token.strip():
            raise HTTPException(status_code=400, detail="Token cannot be empty")

        # For now, we'll use a hardcoded user_id since we don't have full auth context
        user_id = "current-user"

        config = GitHubConfig(db)
        success = config.save_credentials(user_id, token)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save GitHub credentials"
            )

        # Validate token
        skill = GitHubSkill(api_token=token)
        is_valid = await skill.validate_token()

        return {
            "message": "GitHub token configured",
            "valid": is_valid
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting GitHub token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error setting token: {str(e)}"
        )


@router.get("/auth/validate")
async def validate_github_token(
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Validate configured GitHub token

    Returns:
        Validation result
    """
    try:
        user_id = "current-user"
        config = GitHubConfig(db)
        token = config.get_credentials(user_id)

        if not token:
            raise HTTPException(
                status_code=401,
                detail="GitHub token not configured"
            )

        skill = GitHubSkill(api_token=token)
        is_valid = await skill.validate_token()

        return {
            "valid": is_valid,
            "configured": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating GitHub token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validating token: {str(e)}"
        )


@router.get("/repositories")
async def list_repositories(
    username: Optional[str] = Query(None, description="GitHub username"),
    limit: int = Query(30, ge=1, le=100, description="Max repositories to return"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """List GitHub repositories

    Args:
        username: GitHub username (optional)
        limit: Max number of repositories
        container: Service container
        db: Database session

    Returns:
        List of repositories
    """
    try:
        user_id = "current-user"
        config = GitHubConfig(db)
        token = config.get_credentials(user_id)

        if not token:
            raise HTTPException(
                status_code=401,
                detail="GitHub token not configured. Use /github/auth/token to configure."
            )

        skill = GitHubSkill(api_token=token)
        result = await skill.list_repositories(username=username, limit=limit)

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error
            )

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing repositories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing repositories: {str(e)}"
        )


@router.get("/repositories/{owner}/{repo}")
async def get_repository(
    owner: str,
    repo: str,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Get repository details

    Args:
        owner: Repository owner
        repo: Repository name
        container: Service container
        db: Database session

    Returns:
        Repository details
    """
    try:
        user_id = "current-user"
        config = GitHubConfig(db)
        token = config.get_credentials(user_id)

        if not token:
            raise HTTPException(
                status_code=401,
                detail="GitHub token not configured"
            )

        skill = GitHubSkill(api_token=token)
        result = await skill.get_repository(owner=owner, repo=repo)

        if not result.success:
            if "404" in result.error:
                raise HTTPException(status_code=404, detail="Repository not found")
            raise HTTPException(status_code=400, detail=result.error)

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting repository: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting repository: {str(e)}"
        )


@router.get("/repositories/{owner}/{repo}/issues")
async def list_issues(
    owner: str,
    repo: str,
    state: str = Query("open", description="Issue state: open, closed, all"),
    limit: int = Query(30, ge=1, le=100),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """List issues in repository

    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state
        limit: Max issues to return
        container: Service container
        db: Database session

    Returns:
        List of issues
    """
    try:
        user_id = "current-user"
        config = GitHubConfig(db)
        token = config.get_credentials(user_id)

        if not token:
            raise HTTPException(
                status_code=401,
                detail="GitHub token not configured"
            )

        skill = GitHubSkill(api_token=token)
        result = await skill.list_issues(
            owner=owner,
            repo=repo,
            state=state,
            limit=limit
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing issues: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing issues: {str(e)}"
        )


@router.get("/repositories/{owner}/{repo}/pulls")
async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = Query("open", description="PR state: open, closed, all"),
    limit: int = Query(30, ge=1, le=100),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """List pull requests in repository

    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state
        limit: Max PRs to return
        container: Service container
        db: Database session

    Returns:
        List of pull requests
    """
    try:
        user_id = "current-user"
        config = GitHubConfig(db)
        token = config.get_credentials(user_id)

        if not token:
            raise HTTPException(
                status_code=401,
                detail="GitHub token not configured"
            )

        skill = GitHubSkill(api_token=token)
        result = await skill.list_pull_requests(
            owner=owner,
            repo=repo,
            state=state,
            limit=limit
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing pull requests: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing pull requests: {str(e)}"
        )
