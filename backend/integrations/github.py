"""GitHub integration skill for PAI

Provides GitHub API interactions:
- Repository listing and details
- Issue and PR management
- Code search
- Credential management
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp
from backend.integrations.skills.base import Skill, SkillResult
from backend.utils.crypto import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


class GitHubSkill(Skill):
    """GitHub integration skill for repository and issue management"""

    def __init__(self, api_token: Optional[str] = None):
        """Initialize GitHub skill

        Args:
            api_token: GitHub Personal Access Token (optional, can be set later)
        """
        super().__init__(
            name="github",
            version="1.0.0",
            description="GitHub repository and issue management"
        )
        self.api_token = api_token
        self.api_base_url = "https://api.github.com"
        self.headers = self._build_headers()

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for GitHub API requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PAI-GitHub-Integration/1.0"
        }
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"
        return headers

    def set_token(self, api_token: str) -> None:
        """Set or update GitHub API token

        Args:
            api_token: GitHub Personal Access Token
        """
        self.api_token = api_token
        self.headers = self._build_headers()
        logger.info("GitHub token updated")

    async def validate_token(self) -> bool:
        """Validate GitHub API token by making test request

        Returns:
            True if token is valid, False otherwise
        """
        if not self.api_token:
            logger.warning("No GitHub token provided")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/user",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("GitHub token validation successful")
                        return True
                    else:
                        logger.warning(f"GitHub token validation failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error validating GitHub token: {str(e)}")
            return False

    async def list_repositories(
        self,
        username: Optional[str] = None,
        limit: int = 30
    ) -> SkillResult:
        """List repositories

        Args:
            username: GitHub username (if None, lists authenticated user's repos)
            limit: Max number of repos to return

        Returns:
            SkillResult with list of repositories
        """
        try:
            if not self.api_token:
                return SkillResult(
                    success=False,
                    output={"error": "GitHub token not configured"},
                    error="No API token available"
                )

            async with aiohttp.ClientSession() as session:
                if username:
                    url = f"{self.api_base_url}/users/{username}/repos"
                else:
                    url = f"{self.api_base_url}/user/repos"

                async with session.get(
                    url,
                    headers=self.headers,
                    params={"per_page": limit, "sort": "updated"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return SkillResult(
                            success=False,
                            output={"error": f"GitHub API error: {response.status}"},
                            error=f"API returned status {response.status}"
                        )

                    repos = await response.json()
                    return SkillResult(
                        success=True,
                        output={
                            "repositories": [
                                {
                                    "name": repo["name"],
                                    "url": repo["html_url"],
                                    "description": repo["description"],
                                    "stars": repo["stargazers_count"],
                                    "language": repo["language"],
                                    "updated_at": repo["updated_at"]
                                }
                                for repo in repos
                            ],
                            "count": len(repos)
                        }
                    )

        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                output={"error": "Request timeout"},
                error="GitHub API request timed out"
            )
        except Exception as e:
            logger.error(f"Error listing repositories: {str(e)}")
            return SkillResult(
                success=False,
                output={"error": str(e)},
                error=str(e)
            )

    async def get_repository(
        self,
        owner: str,
        repo: str
    ) -> SkillResult:
        """Get repository details

        Args:
            owner: Repository owner (username or org)
            repo: Repository name

        Returns:
            SkillResult with repository details
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/repos/{owner}/{repo}"
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 404:
                        return SkillResult(
                            success=False,
                            output={"error": "Repository not found"},
                            error="404 Not Found"
                        )
                    elif response.status != 200:
                        return SkillResult(
                            success=False,
                            output={"error": f"GitHub API error: {response.status}"},
                            error=f"API returned status {response.status}"
                        )

                    repo_data = await response.json()
                    return SkillResult(
                        success=True,
                        output={
                            "name": repo_data["name"],
                            "url": repo_data["html_url"],
                            "description": repo_data["description"],
                            "owner": repo_data["owner"]["login"],
                            "stars": repo_data["stargazers_count"],
                            "forks": repo_data["forks_count"],
                            "open_issues": repo_data["open_issues_count"],
                            "language": repo_data["language"],
                            "created_at": repo_data["created_at"],
                            "updated_at": repo_data["updated_at"],
                            "topics": repo_data.get("topics", [])
                        }
                    )

        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                output={"error": "Request timeout"},
                error="GitHub API request timed out"
            )
        except Exception as e:
            logger.error(f"Error getting repository: {str(e)}")
            return SkillResult(
                success=False,
                output={"error": str(e)},
                error=str(e)
            )

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 30
    ) -> SkillResult:
        """List issues in a repository

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            limit: Max number of issues to return

        Returns:
            SkillResult with list of issues
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/repos/{owner}/{repo}/issues"
                async with session.get(
                    url,
                    headers=self.headers,
                    params={"state": state, "per_page": limit, "sort": "updated"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return SkillResult(
                            success=False,
                            output={"error": f"GitHub API error: {response.status}"},
                            error=f"API returned status {response.status}"
                        )

                    issues = await response.json()
                    return SkillResult(
                        success=True,
                        output={
                            "issues": [
                                {
                                    "number": issue["number"],
                                    "title": issue["title"],
                                    "state": issue["state"],
                                    "url": issue["html_url"],
                                    "author": issue["user"]["login"],
                                    "created_at": issue["created_at"],
                                    "updated_at": issue["updated_at"],
                                    "labels": [label["name"] for label in issue.get("labels", [])]
                                }
                                for issue in issues
                                if "pull_request" not in issue  # Exclude PRs from issues list
                            ],
                            "count": len([i for i in issues if "pull_request" not in i])
                        }
                    )

        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                output={"error": "Request timeout"},
                error="GitHub API request timed out"
            )
        except Exception as e:
            logger.error(f"Error listing issues: {str(e)}")
            return SkillResult(
                success=False,
                output={"error": str(e)},
                error=str(e)
            )

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 30
    ) -> SkillResult:
        """List pull requests in a repository

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            limit: Max number of PRs to return

        Returns:
            SkillResult with list of pull requests
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
                async with session.get(
                    url,
                    headers=self.headers,
                    params={"state": state, "per_page": limit, "sort": "updated"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return SkillResult(
                            success=False,
                            output={"error": f"GitHub API error: {response.status}"},
                            error=f"API returned status {response.status}"
                        )

                    prs = await response.json()
                    return SkillResult(
                        success=True,
                        output={
                            "pull_requests": [
                                {
                                    "number": pr["number"],
                                    "title": pr["title"],
                                    "state": pr["state"],
                                    "url": pr["html_url"],
                                    "author": pr["user"]["login"],
                                    "branch": pr["head"]["ref"],
                                    "created_at": pr["created_at"],
                                    "updated_at": pr["updated_at"]
                                }
                                for pr in prs
                            ],
                            "count": len(prs)
                        }
                    )

        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                output={"error": "Request timeout"},
                error="GitHub API request timed out"
            )
        except Exception as e:
            logger.error(f"Error listing PRs: {str(e)}")
            return SkillResult(
                success=False,
                output={"error": str(e)},
                error=str(e)
            )

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        """Execute GitHub skill based on context action

        Args:
            context: Execution context with 'action' and parameters

        Returns:
            SkillResult with execution output
        """
        action = context.get("action", "list_repos")

        try:
            if action == "list_repos":
                return await self.list_repositories(
                    username=context.get("username"),
                    limit=context.get("limit", 30)
                )

            elif action == "get_repo":
                return await self.get_repository(
                    owner=context.get("owner"),
                    repo=context.get("repo")
                )

            elif action == "list_issues":
                return await self.list_issues(
                    owner=context.get("owner"),
                    repo=context.get("repo"),
                    state=context.get("state", "open"),
                    limit=context.get("limit", 30)
                )

            elif action == "list_prs":
                return await self.list_pull_requests(
                    owner=context.get("owner"),
                    repo=context.get("repo"),
                    state=context.get("state", "open"),
                    limit=context.get("limit", 30)
                )

            else:
                return SkillResult(
                    success=False,
                    output={"error": f"Unknown action: {action}"},
                    error=f"Action '{action}' not supported"
                )

        except Exception as e:
            logger.error(f"Error executing GitHub skill: {str(e)}")
            return SkillResult(
                success=False,
                output={"error": str(e)},
                error=str(e)
            )

    async def cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("GitHub skill cleanup completed")
