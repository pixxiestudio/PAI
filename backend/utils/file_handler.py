"""File upload handler for PAI - manages file storage and validation"""

import os
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class FileUploadHandler:
    """Handle file uploads with validation and storage"""

    # File size limits
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILES_PER_REQUEST = 5

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'md', 'rtf',
        # Data
        'json', 'csv', 'xml', 'yaml', 'yml',
        # Code
        'py', 'js', 'ts', 'tsx', 'jsx', 'java', 'cpp', 'c', 'go', 'rs',
        # Archives
        'zip', 'tar', 'gz', 'rar',
    }

    def __init__(self, upload_dir: str = "./uploads"):
        """Initialize file upload handler

        Args:
            upload_dir: Directory to store uploaded files
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"File upload handler initialized: {self.upload_dir}")

    def validate_file(
        self,
        filename: str,
        file_size: int,
        file_content: bytes
    ) -> Tuple[bool, Optional[str]]:
        """Validate file before upload

        Args:
            filename: Original filename
            file_size: File size in bytes
            file_content: File content bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check filename
        if not filename or len(filename.strip()) == 0:
            return False, "Filename cannot be empty"

        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"

        # Check extension
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if not file_ext or file_ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed: {file_ext}"

        # Check file size
        if file_size == 0:
            return False, "File is empty"

        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large (max {self.MAX_FILE_SIZE / 1024 / 1024}MB)"

        # Check for malicious content (basic checks)
        try:
            # Check for null bytes (potential exploit)
            if b'\x00' in file_content[:512]:
                return False, "File contains null bytes (potential exploit)"

            # For text files, check encoding
            if file_ext in ['txt', 'md', 'json', 'csv', 'xml', 'yaml', 'yml']:
                try:
                    file_content[:1024].decode('utf-8')
                except UnicodeDecodeError:
                    return False, "File is not valid UTF-8 text"

        except Exception as e:
            logger.warning(f"Error during file validation: {str(e)}")

        return True, None

    def save_file(
        self,
        filename: str,
        file_content: bytes,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Save file to disk

        Args:
            filename: Original filename
            file_content: File content bytes
            user_id: User ID for directory organization
            session_id: Optional session ID for further organization

        Returns:
            Tuple of (success, error_message, file_path)
        """
        try:
            # Create user directory
            user_dir = self.upload_dir / user_id
            if session_id:
                user_dir = user_dir / session_id
            user_dir.mkdir(parents=True, exist_ok=True)

            # Generate safe filename with UUID to avoid collisions
            original_name = filename.rsplit('.', 1)[0]
            file_ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
            safe_filename = f"{uuid4().hex}_{original_name}.{file_ext}"

            file_path = user_dir / safe_filename

            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)

            logger.info(f"File saved: {file_path}")
            return True, None, str(file_path)

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return False, f"Failed to save file: {str(e)}", None

    def get_file_metadata(
        self,
        file_path: str,
        filename: str,
        file_content: bytes
    ) -> dict:
        """Generate file metadata

        Args:
            file_path: Path to saved file
            filename: Original filename
            file_content: File content bytes

        Returns:
            Metadata dictionary
        """
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Get file extension
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'

        return {
            "original_name": filename,
            "stored_path": file_path,
            "file_size": len(file_content),
            "file_type": file_ext,
            "file_hash": file_hash,
            "uploaded_at": datetime.utcnow().isoformat(),
            "mime_type": self._get_mime_type(file_ext)
        }

    def delete_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Delete a file

        Args:
            file_path: Path to file to delete

        Returns:
            Tuple of (success, error_message)
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True, None
            else:
                return False, "File not found"

        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False, f"Failed to delete file: {str(e)}"

    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Delete files older than specified days

        Args:
            days_old: Delete files older than this many days

        Returns:
            Number of files deleted
        """
        try:
            deleted_count = 0
            now = datetime.utcnow().timestamp()
            cutoff_time = now - (days_old * 24 * 60 * 60)

            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            return 0

    @staticmethod
    def _get_mime_type(file_ext: str) -> str:
        """Get MIME type for file extension

        Args:
            file_ext: File extension

        Returns:
            MIME type
        """
        mime_types = {
            # Images
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
            'gif': 'image/gif', 'webp': 'image/webp', 'svg': 'image/svg+xml',
            # Documents
            'pdf': 'application/pdf', 'txt': 'text/plain', 'md': 'text/markdown',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            # Data
            'json': 'application/json', 'csv': 'text/csv', 'xml': 'application/xml',
            'yaml': 'text/yaml', 'yml': 'text/yaml',
            # Code
            'py': 'text/x-python', 'js': 'text/javascript', 'ts': 'text/typescript',
            # Archives
            'zip': 'application/zip', 'tar': 'application/x-tar',
            'gz': 'application/gzip', 'rar': 'application/x-rar-compressed',
        }
        return mime_types.get(file_ext.lower(), 'application/octet-stream')
