"""Custom exception hierarchy for PAI

This module defines all custom exceptions used throughout PAI.
Each exception is mapped to appropriate HTTP status codes for REST API layer.

Exception Hierarchy:
    PAIException (base)
    ├── SessionException
    │   ├── SessionNotFoundError (404)
    │   └── InvalidSessionError (400)
    ├── MemoryException
    │   └── MemoryOperationError (500)
    ├── LearningException
    │   └── LearningError (500)
    ├── SkillException
    │   ├── SkillNotFoundError (404)
    │   ├── SkillValidationError (400)
    │   └── SkillExecutionError (500)
    ├── APIException
    │   ├── APIKeyError (401)
    │   ├── APIRateLimitError (429)
    │   └── APIConnectionError (502)
    ├── ValidationException
    │   ├── InvalidParametersError (400)
    │   └── InvalidMessageError (400)
    └── DatabaseException
        └── DatabaseError (500)
"""


class PAIException(Exception):
    """Base exception for all PAI errors

    All PAI exceptions inherit from this base class for unified error handling.
    Each exception can map to an appropriate HTTP status code.

    Attributes:
        http_status_code: HTTP status code for REST API responses
        error_code: Machine-readable error code for clients
        message: Human-readable error message
    """
    http_status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, error_code: str = None):
        """Initialize exception

        Args:
            message: Human-readable error message
            error_code: Optional override for error code
        """
        self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses

        Returns:
            Dict with error_code, message, and http_status_code
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "http_status_code": self.http_status_code
        }


# Session Exceptions

class SessionException(PAIException):
    """Base exception for session-related errors"""
    http_status_code = 500
    error_code = "SESSION_ERROR"


class SessionNotFoundError(SessionException):
    """Session doesn't exist (404)"""
    http_status_code = 404
    error_code = "SESSION_NOT_FOUND"


class InvalidSessionError(SessionException):
    """Session ID format invalid (400)"""
    http_status_code = 400
    error_code = "INVALID_SESSION"


class SessionEndedError(SessionException):
    """Session has been ended (400)"""
    http_status_code = 400
    error_code = "SESSION_ENDED"


# Memory Exceptions

class MemoryException(PAIException):
    """Base exception for memory system errors"""
    http_status_code = 500
    error_code = "MEMORY_ERROR"


class MemoryOperationError(MemoryException):
    """Memory operation failed (500)"""
    http_status_code = 500
    error_code = "MEMORY_OPERATION_FAILED"


# Learning Exceptions

class LearningException(PAIException):
    """Base exception for learning system errors"""
    http_status_code = 500
    error_code = "LEARNING_ERROR"


class LearningError(LearningException):
    """Learning operation failed (500)"""
    http_status_code = 500
    error_code = "LEARNING_OPERATION_FAILED"


# Skill Exceptions

class SkillException(PAIException):
    """Base exception for skill system errors"""
    http_status_code = 500
    error_code = "SKILL_ERROR"


class SkillNotFoundError(SkillException):
    """Skill not registered (404)"""
    http_status_code = 404
    error_code = "SKILL_NOT_FOUND"


class SkillValidationError(SkillException):
    """Skill parameters invalid (400)"""
    http_status_code = 400
    error_code = "SKILL_VALIDATION_FAILED"


class SkillExecutionError(SkillException):
    """Skill execution failed (500)"""
    http_status_code = 500
    error_code = "SKILL_EXECUTION_FAILED"


class SkillNotAvailableError(SkillException):
    """Skill exists but is disabled (503)"""
    http_status_code = 503
    error_code = "SKILL_NOT_AVAILABLE"


# API Exceptions

class APIException(PAIException):
    """Base exception for external API errors"""
    http_status_code = 502
    error_code = "API_ERROR"


class APIKeyError(APIException):
    """API key is invalid or missing (401)"""
    http_status_code = 401
    error_code = "INVALID_API_KEY"


class APIRateLimitError(APIException):
    """API rate limit exceeded (429)"""
    http_status_code = 429
    error_code = "RATE_LIMITED"


class APIConnectionError(APIException):
    """Cannot connect to API (502)"""
    http_status_code = 502
    error_code = "API_UNAVAILABLE"


class APIQuotaExceededError(APIException):
    """API quota exceeded (429)"""
    http_status_code = 429
    error_code = "QUOTA_EXCEEDED"


# Validation Exceptions

class ValidationException(PAIException):
    """Base exception for validation errors"""
    http_status_code = 400
    error_code = "VALIDATION_ERROR"


class InvalidParametersError(ValidationException):
    """Function parameters are invalid (400)"""
    http_status_code = 400
    error_code = "INVALID_PARAMETERS"


class InvalidMessageError(ValidationException):
    """Message content is invalid (400)"""
    http_status_code = 400
    error_code = "INVALID_MESSAGE"


class MessageTooLongError(ValidationException):
    """Message exceeds maximum length (400)"""
    http_status_code = 400
    error_code = "MESSAGE_TOO_LONG"


# Database Exceptions

class DatabaseException(PAIException):
    """Base exception for database errors"""
    http_status_code = 500
    error_code = "DATABASE_ERROR"


class DatabaseConnectionError(DatabaseException):
    """Cannot connect to database (500)"""
    http_status_code = 500
    error_code = "DATABASE_CONNECTION_FAILED"


class DatabaseOperationError(DatabaseException):
    """Database operation failed (500)"""
    http_status_code = 500
    error_code = "DATABASE_OPERATION_FAILED"


class DataIntegrityError(DatabaseException):
    """Data integrity constraint violated (500)"""
    http_status_code = 500
    error_code = "DATA_INTEGRITY_VIOLATION"


# Personality Exceptions

class PersonalityException(PAIException):
    """Base exception for personality system errors"""
    http_status_code = 500
    error_code = "PERSONALITY_ERROR"


class PersonalityLoadError(PersonalityException):
    """Failed to load personality profile (500)"""
    http_status_code = 500
    error_code = "PERSONALITY_LOAD_FAILED"


# Configuration Exceptions

class ConfigurationException(PAIException):
    """Base exception for configuration errors"""
    http_status_code = 500
    error_code = "CONFIGURATION_ERROR"


class MissingConfigurationError(ConfigurationException):
    """Required configuration is missing (500)"""
    http_status_code = 500
    error_code = "MISSING_CONFIGURATION"


class InvalidConfigurationError(ConfigurationException):
    """Configuration value is invalid (500)"""
    http_status_code = 500
    error_code = "INVALID_CONFIGURATION"
