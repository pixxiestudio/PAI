"""GitHub integration configuration and credential management"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.db.models import Integration
from backend.utils.crypto import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


class GitHubConfig:
    """Manage GitHub integration credentials and configuration"""

    def __init__(self, db_session: Session):
        """Initialize GitHub config manager

        Args:
            db_session: Database session for persistence
        """
        self.db_session = db_session

    def save_credentials(
        self,
        user_id: str,
        github_token: str
    ) -> bool:
        """Save GitHub credentials encrypted to database

        Args:
            user_id: User ID
            github_token: GitHub Personal Access Token

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Check if integration already exists
            existing = self.db_session.query(Integration).filter(
                Integration.user_id == user_id,
                Integration.integration_type == "github"
            ).first()

            # Encrypt token
            encrypted_token = encrypt_token(github_token)

            if existing:
                # Update existing
                existing.config_data = {
                    "token": encrypted_token,
                    "token_type": "personal_access_token"
                }
                logger.info(f"Updated GitHub credentials for user {user_id}")
            else:
                # Create new
                integration = Integration(
                    user_id=user_id,
                    integration_type="github",
                    config_data={
                        "token": encrypted_token,
                        "token_type": "personal_access_token"
                    },
                    enabled=True
                )
                self.db_session.add(integration)
                logger.info(f"Saved GitHub credentials for user {user_id}")

            self.db_session.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving GitHub credentials: {str(e)}")
            self.db_session.rollback()
            return False

    def get_credentials(self, user_id: str) -> Optional[str]:
        """Retrieve and decrypt GitHub credentials

        Args:
            user_id: User ID

        Returns:
            GitHub token if found and valid, None otherwise
        """
        try:
            integration = self.db_session.query(Integration).filter(
                Integration.user_id == user_id,
                Integration.integration_type == "github"
            ).first()

            if not integration or not integration.enabled:
                logger.debug(f"No enabled GitHub integration for user {user_id}")
                return None

            # Decrypt token
            encrypted_token = integration.config_data.get("token")
            if not encrypted_token:
                logger.warning(f"No token found for user {user_id}")
                return None

            token = decrypt_token(encrypted_token)
            return token

        except Exception as e:
            logger.error(f"Error retrieving GitHub credentials: {str(e)}")
            return None

    def delete_credentials(self, user_id: str) -> bool:
        """Delete GitHub credentials

        Args:
            user_id: User ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            integration = self.db_session.query(Integration).filter(
                Integration.user_id == user_id,
                Integration.integration_type == "github"
            ).first()

            if integration:
                self.db_session.delete(integration)
                self.db_session.commit()
                logger.info(f"Deleted GitHub credentials for user {user_id}")
                return True

            logger.debug(f"No GitHub integration found for user {user_id}")
            return False

        except Exception as e:
            logger.error(f"Error deleting GitHub credentials: {str(e)}")
            self.db_session.rollback()
            return False

    def is_configured(self, user_id: str) -> bool:
        """Check if GitHub integration is configured for user

        Args:
            user_id: User ID

        Returns:
            True if configured and enabled, False otherwise
        """
        integration = self.db_session.query(Integration).filter(
            Integration.user_id == user_id,
            Integration.integration_type == "github",
            Integration.enabled == True
        ).first()

        return integration is not None
