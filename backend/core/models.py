"""Pydantic models for PAI API responses and type safety

These models provide strong typing for API responses and ensure
consistent data structures across Phase 2+ REST API layer.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# Enums

class EmotionalToneEnum(str, Enum):
    """Emotional tone enumeration"""
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    EXCITED = "excited"
    STRESSED = "stressed"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"


class MemoryTypeEnum(str, Enum):
    """Memory type enumeration"""
    SESSION = "session"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"


class SkillStatusEnum(str, Enum):
    """Skill execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


# Session Models

class Message(BaseModel):
    """Single message in conversation"""
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="When message was sent")


class SessionResponse(BaseModel):
    """Session creation/info response"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    session_type: str = Field(default="chat", description="Session type")


class SessionHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: str = Field(..., description="Session identifier")
    messages: List[Message] = Field(..., description="Conversation messages")
    message_count: int = Field(..., description="Total message count")


class SendMessageRequest(BaseModel):
    """Request to send message"""
    message: str = Field(..., description="User message")
    context_injection: Optional[str] = Field(None, description="Optional context")
    model: Optional[str] = Field(None, description="Optional model override")


class SendMessageResponse(BaseModel):
    """Response to message"""
    session_id: str = Field(..., description="Session ID")
    response: str = Field(..., description="AI response")
    timestamp: datetime = Field(..., description="Response timestamp")
    tokens_used: Optional[int] = Field(None, description="Approximate tokens used")


# Memory Models

class MemoryEntryResponse(BaseModel):
    """Memory entry in response"""
    id: str = Field(..., description="Memory identifier")
    content: str = Field(..., description="Memory content")
    memory_type: MemoryTypeEnum = Field(..., description="Type of memory")
    importance: float = Field(..., ge=0, le=1, description="Current importance (0-1)")
    created_at: datetime = Field(..., description="Creation timestamp")
    accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    access_count: int = Field(..., description="Number of times accessed")


class GetMemoriesResponse(BaseModel):
    """Get memories response"""
    user_id: str = Field(..., description="User identifier")
    memories: List[MemoryEntryResponse] = Field(..., description="Retrieved memories")
    total_count: int = Field(..., description="Total memory count")


class SaveMemoryRequest(BaseModel):
    """Save memory request"""
    content: str = Field(..., description="Memory content")
    memory_type: MemoryTypeEnum = Field(..., description="Memory type")
    importance: float = Field(default=1.0, ge=0, le=1, description="Importance (0-1)")


class SaveMemoryResponse(BaseModel):
    """Save memory response"""
    memory_id: str = Field(..., description="Created memory ID")
    created_at: datetime = Field(..., description="Creation timestamp")


# Learning Models

class LearningRecordResponse(BaseModel):
    """Learning record"""
    id: str = Field(..., description="Learning record ID")
    learning_type: str = Field(..., description="Type of learning")
    content: Dict[str, Any] = Field(..., description="Learning content")
    effectiveness_score: float = Field(..., ge=0, le=1, description="Effectiveness (0-1)")
    created_at: datetime = Field(..., description="Creation timestamp")


class LearningReportResponse(BaseModel):
    """Learning effectiveness report"""
    pai_instance_id: str = Field(..., description="PAI instance ID")
    total_learnings: int = Field(..., description="Total learning records")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate")
    average_quality: float = Field(..., ge=0, le=1, description="Average quality")
    patterns_detected: int = Field(..., description="Number of patterns detected")


# Skill Models

class SkillParameterDefinition(BaseModel):
    """Skill parameter definition"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, int, float, bool, json)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(..., description="Is parameter required")
    default: Optional[Any] = Field(None, description="Default value")


class SkillInfo(BaseModel):
    """Information about a skill"""
    name: str = Field(..., description="Skill name")
    version: str = Field(..., description="Skill version")
    description: str = Field(..., description="Skill description")
    parameters: Dict[str, SkillParameterDefinition] = Field(..., description="Required parameters")
    enabled: bool = Field(..., description="Is skill enabled")


class ExecuteSkillRequest(BaseModel):
    """Request to execute skill"""
    skill_name: str = Field(..., description="Name of skill to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")


class SkillExecutionResult(BaseModel):
    """Result of skill execution"""
    success: bool = Field(..., description="Did execution succeed")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


# Personality Models

class PersonalityAdaptationResponse(BaseModel):
    """Personality adaptation guidance"""
    emotional_tone: EmotionalToneEnum = Field(..., description="Detected emotion")
    estimated_expertise: str = Field(..., description="Estimated expertise level")
    response_style: str = Field(..., description="Recommended response style")
    empathy_guidance: str = Field(..., description="Empathy guidance for response")


# Error Models

class ErrorResponse(BaseModel):
    """Error response"""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    http_status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(..., description="When error occurred")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


# Health Models

class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="'healthy' or 'unhealthy'")
    timestamp: datetime = Field(..., description="Check timestamp")
    database_connected: bool = Field(..., description="Is database connected")
    api_key_configured: bool = Field(..., description="Is API key configured")
