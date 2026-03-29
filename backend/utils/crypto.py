"""Cryptographic utilities for token encryption and credential management"""

import os
import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# Get encryption key from environment or use a default (NOT SECURE for production)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    logger.warning(
        "ENCRYPTION_KEY not set in environment. Using development key. "
        "SET ENCRYPTION_KEY for production!"
    )
    # Default key (ONLY for development)
    ENCRYPTION_KEY = base64.urlsafe_b64encode(
        PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"pai-dev-salt",
            iterations=100000,
            backend=default_backend()
        ).derive(b"pai-development-key")
    ).decode()

# Initialize Fernet cipher
try:
    cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Failed to initialize encryption cipher: {str(e)}")
    cipher = None


def encrypt_token(token: str) -> str:
    """Encrypt a token (API key, password, etc.)

    Args:
        token: Token to encrypt

    Returns:
        Encrypted token as string

    Raises:
        RuntimeError: If cipher not initialized
    """
    if not cipher:
        raise RuntimeError("Encryption cipher not initialized")

    try:
        encrypted = cipher.encrypt(token.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {str(e)}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token

    Args:
        encrypted_token: Encrypted token string

    Returns:
        Decrypted token

    Raises:
        RuntimeError: If cipher not initialized
        ValueError: If decryption fails
    """
    if not cipher:
        raise RuntimeError("Encryption cipher not initialized")

    try:
        encrypted = base64.b64decode(encrypted_token.encode())
        decrypted = cipher.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {str(e)}")
        raise ValueError("Failed to decrypt token") from e


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hash a password using PBKDF2

    Args:
        password: Password to hash
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (hashed_password, salt) both as base64 strings
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    hashed = kdf.derive(password.encode())
    return (
        base64.b64encode(hashed).decode(),
        base64.b64encode(salt).decode()
    )


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify a password against its hash

    Args:
        password: Password to verify
        hashed_password: Previously hashed password (base64)
        salt: Salt used for hashing (base64)

    Returns:
        True if password matches, False otherwise
    """
    try:
        decoded_salt = base64.b64decode(salt)
        decoded_hash = base64.b64decode(hashed_password)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=decoded_salt,
            iterations=100000,
            backend=default_backend()
        )

        kdf.verify(password.encode(), decoded_hash)
        return True
    except Exception as e:
        logger.debug(f"Password verification failed: {str(e)}")
        return False


def generate_random_token(length: int = 32) -> str:
    """Generate a random token

    Args:
        length: Length of token in bytes

    Returns:
        Random token as base64 string
    """
    random_bytes = os.urandom(length)
    return base64.b64encode(random_bytes).decode()
