"""SQLAlchemy models for PAI database"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


Base = declarative_base()


class Session(Base):
    """User conversation session"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(255), index=True)
    pai_instance_id = Column(String(255), index=True)
    session_type = Column(String(50))  # "chat", "skill_execution", "debate", "learning"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="session")
    activities = relationship("Activity", back_populates="session")


class Message(Base):
    """Individual messages in a session"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("sessions.id"), index=True)
    sender = Column(String(50), index=True)  # "user", "pai", "subagent"
    sender_id = Column(String(255), nullable=True)  # PAI or subagent ID
    content = Column(Text)
    role = Column(String(50))  # "user", "assistant", "system"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("Session", back_populates="messages")
    feedback = relationship("UserFeedback", back_populates="message", uselist=False)


class Activity(Base):
    """Activity log for sessions"""
    __tablename__ = "activities"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("sessions.id"), index=True)
    activity_type = Column(String(100), index=True)  # "message", "subagent_spawn", "skill_invoke", etc.
    activity_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="activities")


class Memory(Base):
    """Layer 1 & 2 Memory storage"""
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True, index=True)
    user_id = Column(String(255), index=True)
    memory_type = Column(String(50), index=True)  # "session", "semantic", "episodic"
    content = Column(Text)
    importance = Column(Float, default=1.0, index=True)  # For time decay calculation
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=1)


class Skill(Base):
    """Plugin/Skill registry"""
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), unique=True, index=True)
    version = Column(String(20))
    description = Column(Text)
    path = Column(String(500))  # File path to skill
    enabled = Column(Boolean, default=True, index=True)
    parameters = Column(JSON)  # Required parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    executions = relationship("SkillExecution", back_populates="skill")


class SkillExecution(Base):
    """Track skill execution history"""
    __tablename__ = "skill_executions"

    id = Column(String(36), primary_key=True)  # UUID
    skill_id = Column(String(36), ForeignKey("skills.id"), index=True)  # Use UUID FK
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True, index=True)
    pai_instance_id = Column(String(255), index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time = Column(Float)  # seconds
    cost = Column(Float, nullable=True)  # API cost
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    skill = relationship("Skill", back_populates="executions")


class Integration(Base):
    """Integration credentials and configuration"""
    __tablename__ = "integrations"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(255), index=True)
    integration_type = Column(String(100), index=True)  # "github", "telegram", etc.
    config_data = Column(JSON)  # Encrypted credentials
    enabled = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PAIInstance(Base):
    """PAI instance configuration"""
    __tablename__ = "pai_instances"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), unique=True, index=True)
    specialization = Column(String(100), index=True)  # "code", "creative", "critic", "mentor"
    base_model = Column(String(100))
    enabled = Column(Boolean, default=True, index=True)
    personality_profile = Column(JSON)  # Personality traits and preferences
    knowledge_domains = Column(JSON)  # Domain restrictions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    learnings = relationship("Learning", back_populates="pai_instance")


class Learning(Base):
    """Learning outcomes and patterns"""
    __tablename__ = "learning"

    id = Column(String(36), primary_key=True)  # UUID
    pai_instance_id = Column(String(255), ForeignKey("pai_instances.id"), index=True)
    learning_type = Column(String(50), index=True)  # "outcome", "pattern", "preference", "skill"
    content = Column(JSON)
    effectiveness_score = Column(Float, index=True)  # How effective is this learning?
    applied_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    pai_instance = relationship("PAIInstance", back_populates="learnings")


class UserFeedback(Base):
    """User feedback on responses"""
    __tablename__ = "user_feedback"

    id = Column(String(36), primary_key=True)  # UUID
    message_id = Column(String(36), ForeignKey("messages.id"), index=True)
    rating = Column(Integer)  # 1-5 stars
    feedback_text = Column(Text, nullable=True)
    quality_score = Column(Float)  # Computed quality score
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    message = relationship("Message", back_populates="feedback")


class DebateRecord(Base):
    """Multi-PAI debate records"""
    __tablename__ = "debate_records"

    id = Column(String(36), primary_key=True)  # UUID
    topic = Column(String(500))
    participating_pais = Column(JSON)  # List of PAI instance IDs
    positions = Column(JSON)  # Each PAI's position/solution
    votes = Column(JSON)  # Vote records
    consensus_score = Column(Float)
    winner = Column(String(255), nullable=True)  # Consensus solution
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
