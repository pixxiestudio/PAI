# PAI Phase 1 Contract & Integration Guide

**Date**: 2026-03-29
**Status**: STABLE (Plug-and-play ready for Phase 2+)
**Audience**: Phase 2 developers building REST API, web UI, and advanced features

---

## Table of Contents

1. [Overview](#overview)
2. [Core Engine Interface](#core-engine-interface)
3. [Memory System Interface](#memory-system-interface)
4. [Learning System Interface](#learning-system-interface)
5. [Personality System Interface](#personality-system-interface)
6. [Context Injection Interface](#context-injection-interface)
7. [Skill System Interface](#skill-system-interface)
8. [Database Schema](#database-schema)
9. [Error Handling](#error-handling)
10. [Configuration](#configuration)
11. [Testing Infrastructure](#testing-infrastructure)
12. [Phase 2 Integration Points](#phase-2-integration-points)
13. [Known Limitations](#known-limitations)

---

## Overview

Phase 1 provides a complete, self-contained AI engine with:
- **Session management** with conversation history
- **3-layer memory system** with semantic/episodic learning
- **Self-learning capabilities** that improve from interactions
- **Empathy & personality adaptation** based on user emotion/expertise
- **Extensible skill/plugin system** for custom capabilities
- **SQLite persistence** with async-safe operations

**Key Principle**: Phase 1 core is STABLE and does NOT need modification for Phase 2+. All extensions happen OUTSIDE Phase 1.

---

## Core Engine Interface

**File**: `backend/core/engine.py`

### Class: `PAIEngine`

#### Initialization
```python
engine = PAIEngine(db_session=None)
```

**Parameters**:
- `db_session` (Optional): SQLAlchemy session for database persistence
  - If None: Sessions exist in-memory only (ephemeral)
  - If provided: Sessions persist to database

#### Public Methods (All Async)

##### `create_session(user_id: str, session_type: str = "chat") -> str`

Create a new conversation session.

**Args**:
- `user_id`: Unique identifier for the user
- `session_type`: Type of session ("chat", "skill_execution", "debate", "learning")

**Returns**: Session ID (UUID string)

**Behavior**:
- Creates session in-memory immediately
- Persists to database if `db_session` provided
- Returns UUID identifying this conversation

**Example**:
```python
session_id = await engine.create_session("user-123", "chat")
# Returns: "550e8400-e29b-41d4-a716-446655440000"
```

---

##### `send_message(session_id: str, user_message: str, context_injection: str = "") -> str`

Send a message to PAI and get a response (blocking until complete).

**Args**:
- `session_id`: Session to send message in
- `user_message`: User's message
- `context_injection`: Optional context from memory/learning systems

**Returns**: PAI's response text

**Behavior**:
- Calls Claude API with message and context
- Stores message and response in session history
- Returns complete response text
- Blocks until response complete

**Note**: For streaming, use `stream_message()` instead

**Example**:
```python
response = await engine.send_message(
    session_id,
    "How do I optimize this Python function?",
    context_injection="Previous: User prefers concise technical explanations"
)
```

---

##### `stream_message(session_id: str, user_message: str, context_injection: str = "") -> AsyncGenerator[str, None]`

Send a message and stream the response token-by-token.

**Args**: Same as `send_message()`

**Returns**: AsyncGenerator yielding response tokens

**Behavior**:
- Calls Claude API with streaming enabled
- Yields tokens as they arrive
- Stores complete message/response after streaming complete
- Useful for real-time UI updates

**Example**:
```python
async for token in engine.stream_message(session_id, "Explain async/await..."):
    print(token, end="", flush=True)
```

---

##### `get_session_history(session_id: str) -> List[Dict]`

Get all messages in a session.

**Returns**: List of message dicts with fields: `sender`, `content`, `timestamp`

**Example**:
```python
history = await engine.get_session_history(session_id)
# [
#   {"sender": "user", "content": "Hello", "timestamp": "..."},
#   {"sender": "assistant", "content": "Hi there!", "timestamp": "..."}
# ]
```

---

##### `get_last_n_messages(session_id: str, n: int) -> List[Dict]`

Get last N messages in a session (useful for context window limits).

**Args**:
- `session_id`: Session ID
- `n`: Number of recent messages

**Returns**: Last N messages in order (oldest to newest)

---

##### `end_session(session_id: str) -> None`

Mark a session as ended.

**Behavior**:
- Removes from in-memory sessions dict
- Marks `ended_at` timestamp in database if persisted
- Messages/history are NOT deleted

---

##### `set_model(session_id: str, model: str) -> None` (SYNC)

Switch which Claude model this session uses.

**Args**:
- `session_id`: Session ID
- `model`: Model name ("claude-opus-4-6", "claude-sonnet-4-6", etc.)

**Note**: Synchronous method (doesn't need await)

---

##### `clear_history(session_id: str) -> None` (SYNC)

Clear conversation history for a session.

**Note**: Does NOT delete from database if persisted; only clears in-memory

---

### Key Behaviors

#### In-Memory vs. Persistent Sessions

**Without `db_session`**:
```python
engine = PAIEngine()  # No database
session_id = await engine.create_session("user-1")
# Session exists in memory during engine lifetime
# Lost if engine restarts
```

**With `db_session`**:
```python
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from backend.db.models import Base

db_engine = create_engine("sqlite:///pai.db")
Base.metadata.create_all(db_engine)
db_session = Session(db_engine)

pai_engine = PAIEngine(db_session=db_session)
session_id = await engine.create_session("user-1")
# Session persisted to database AND in memory
# Can be recovered after engine restart via database query
```

---

#### Model Selection

**Current Architecture**: Single model per session

**Phase 2 Extension**: Multi-model routing (e.g., Haiku for simple → Sonnet for complex)

**For Phase 2**: Use `set_model()` to switch models, or extend with routing logic

---

### Async/Await Safety

All public methods are properly async:
- ✅ Safe to call from `async def` context
- ✅ Thread pool used for Claude API calls (sync → async wrapper)
- ✅ No blocking operations in async functions
- ✅ Safe for FastAPI endpoints

---

## Memory System Interface

**File**: `backend/core/memory.py`

### Class: `MemorySystem`

#### 3-Layer Architecture

```
Layer 1 (Session): Current conversation messages
  └─ Persists during session
  └─ Cleared when session ends

Layer 2 (Semantic/Episodic): Learned patterns and facts
  └─ User preferences
  └─ Domain knowledge
  └─ Lessons learned
  └─ Persists indefinitely (with time decay)

Layer 3 (Context Injection): Smart context assembly
  └─ Combines recent messages + relevant learnings
  └─ Token-budgeted for model limits
  └─ Empathy-aware formatting
```

---

### Layer 1: Session Memory

##### `save_message(session_id: str, user_id: str, content: str, sender: str = "user") -> str`

Save a message in session memory.

**Args**:
- `session_id`: Session ID
- `user_id`: User ID
- `content`: Message content
- `sender`: "user" or "assistant"

**Returns**: Memory ID (UUID)

**Example**:
```python
msg_id = await memory_system.save_message(
    session_id,
    user_id,
    "I need help with Python",
    sender="user"
)
```

---

##### `get_session_context(session_id: str, context_count: int = 5) -> str`

Get formatted context from last N messages.

**Args**:
- `session_id`: Session ID
- `context_count`: Number of recent messages to include

**Returns**: Formatted string of recent conversation

**Behavior**:
- Returns empty string if no messages
- Formats as: "User: ...\nAssistant: ...\n..."
- Useful for context injection

---

### Layer 2: Semantic & Episodic Memory

##### `save_learning(user_id: str, content: str, memory_type: str = "semantic", importance: float = 1.0) -> str`

Save a semantic or episodic learning.

**Args**:
- `user_id`: User ID
- `content`: Learning content (text)
- `memory_type`: "semantic" (fact/concept) or "episodic" (event)
- `importance`: Initial importance (0-1)

**Returns**: Learning ID (UUID)

**Time Decay**:
```
importance_at_age = base_importance × e^(-λ × age_days)
where λ = 0.1 (configurable)
```

**Example**:
```python
learning_id = await memory_system.save_learning(
    user_id,
    "User prefers detailed step-by-step explanations",
    memory_type="semantic",
    importance=0.9
)
```

---

##### `get_relevant_memories(user_id: str, query: str = "", limit: int = 5, min_importance: float = 0.1) -> List[MemoryEntry]`

Retrieve learnings relevant to a query.

**Args**:
- `user_id`: User ID
- `query`: Search query (optional)
- `limit`: Max results
- `min_importance`: Filter by minimum importance

**Returns**: List of MemoryEntry dataclasses

**MemoryEntry Fields**:
```python
@dataclass
class MemoryEntry:
    id: str
    content: str
    memory_type: str  # "semantic" or "episodic"
    importance: float  # Current importance after decay
    accessed_at: datetime
    access_count: int
```

---

##### `update_memory_importance(memory_id: str, new_importance: float) -> None`

Update importance of a learning.

**Behavior**:
- Updates importance score
- Increments access_count
- Updates accessed_at timestamp

---

### Layer 3: Context Injection

##### `build_injection_context(session_id: str, user_id: str, token_budget: int = 2048) -> str`

Build complete context for injection into prompt.

**Args**:
- `session_id`: Session ID
- `user_id`: User ID
- `token_budget`: Max tokens for context

**Returns**: Formatted context string

**Includes**:
1. Recent session messages
2. Relevant semantic learnings
3. User preferences
4. Formatted with separators

**Example**:
```python
context = await memory_system.build_injection_context(
    session_id,
    user_id,
    token_budget=2000
)

# Use in Claude prompt:
prompt = f"""You are a helpful assistant.

CONTEXT:
{context}

User: {user_message}"""
```

---

### Memory Optimization

##### `optimize_memory(user_id: str) -> Dict[str, int]`

Clean up old, low-importance memories.

**Returns**: Dict with keys: `deleted`, `archived`, `updated`

**Criteria**:
- Age > 30 days AND importance < 0.1
- Gets cleaned up to save storage

---

## Learning System Interface

**File**: `backend/core/learning.py`

### Class: `SelfLearningSystem`

Tracks PAI's learning and improvement from interactions.

---

### Outcome Recording

##### `record_interaction_outcome(pai_instance_id: str, interaction_type: str, input_data: Dict, output_data: Dict, success: bool, quality_score: float) -> str`

Record success/failure of an interaction.

**Args**:
- `pai_instance_id`: PAI instance that interacted
- `interaction_type`: Type of task (e.g., "code_analysis", "documentation")
- `input_data`: What the task was given
- `output_data`: What the task produced
- `success`: True if outcome was good
- `quality_score`: 0-1 quality rating

**Returns**: Learning record ID

**Used By**: PAI to learn which approaches work

---

### Pattern Detection

##### `get_success_patterns(pai_instance_id: str, interaction_type: Optional[str] = None, limit: int = 5) -> List[LearningRecord]`

Get successful interaction patterns.

**Args**:
- `pai_instance_id`: PAI instance
- `interaction_type`: Optional filter
- `limit`: Max patterns

**Returns**: List of LearningRecord objects

**Note**: Interaction type filtering requires PostgreSQL. SQLite returns all patterns.

---

### Preference Learning

##### `learn_user_preference(pai_instance_id: str, preference_name: str, preference_value: str, confidence: float) -> str`

Record a learned user preference.

**Args**:
- `pai_instance_id`: PAI instance learning
- `preference_name`: Preference category (e.g., "communication_style")
- `preference_value`: The preference (e.g., "technical_and_concise")
- `confidence`: 0-1 confidence level

**Returns**: Learning record ID

---

##### `get_learned_preferences(pai_instance_id: str, min_confidence: float = 0.7) -> Dict[str, str]`

Get all learned preferences for a PAI.

**Returns**: Dict mapping preference names to values

---

### Feedback Integration

##### `process_user_feedback(pai_instance_id: str, message_id: str, rating: int, feedback_text: str = "") -> None`

Learn from user ratings (1-5 stars).

**Args**:
- `pai_instance_id`: PAI to learn from
- `message_id`: ID of message being rated
- `rating`: 1-5 star rating
- `feedback_text`: Optional comment

**Behavior**:
- Ratings 4-5: Extract and record positive patterns
- Rating 3: Note as neutral
- Ratings 1-2: Record as learning from mistakes

---

### Effectiveness Reporting

##### `get_learning_effectiveness_report(pai_instance_id: str) -> Dict`

Get summary of learning progress.

**Returns**: Dict with keys:
- `total_learnings`: Count of recorded learnings
- `success_rate`: Percentage of successful outcomes
- `average_quality`: Average quality score
- `patterns_detected`: Number of patterns learned
- `preferences_learned`: Number of preferences learned

---

## Personality System Interface

**File**: `backend/core/personality.py`

### Emotion & Expertise Detection

#### Static Method: `EmpathyDetector.detect_tone(message: str) -> Optional[EmotionalTone]`

Detect emotional tone from text.

**Returns**: EmotionalTone enum or None

**Emotional Tones**:
```python
class EmotionalTone(Enum):
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    EXCITED = "excited"
    STRESSED = "stressed"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
```

**Detection Method**: Keyword-based (limited but fast)

**Limitation**: English only (Phase 2 should extend for multilingual)

**Example**:
```python
tone = EmpathyDetector.detect_tone("I'm so frustrated with this!")
# Returns: EmotionalTone.FRUSTRATED
```

---

#### Static Method: `EmpathyDetector.extract_expertise_level(message: str) -> str`

Estimate user's expertise level in domain.

**Returns**: One of: "beginner", "intermediate", "expert"

**Detection**: Analyzes vocabulary, question complexity, etc.

---

### Personality Adaptation

#### `PersonalityManager.adapt_to_user(pai_instance_id: str, user_message: str) -> Dict`

Get adaptation recommendations based on user state.

**Returns**: Dict with:
```python
{
    "emotional_tone": EmotionalTone,
    "estimated_expertise": str,
    "response_style": str,  # "formal", "casual", "technical", etc.
    "suggested_tone": str,
    "empathy_guidance": str
}
```

**Example**:
```python
adaptations = await personality_manager.adapt_to_user(
    pai_id,
    "I've been debugging this for hours and I'm stuck!"
)
# {
#     "emotional_tone": "frustrated",
#     "estimated_expertise": "intermediate",
#     "response_style": "empathetic_and_encouraging",
#     "empathy_guidance": "Acknowledge frustration, offer step-by-step guidance..."
# }
```

---

#### `PersonalityManager.build_empathy_prompt_extension(tone: EmotionalTone, expertise: str) -> str`

Build prompt guidance for PAI based on tone + expertise.

**Returns**: String with response guidelines

**Example Output**:
```
Response Guidelines for FRUSTRATED user (intermediate):
- Acknowledge frustration and validate effort
- Provide step-by-step breakdown
- Celebrate progress made so far
- Offer preventive patterns
```

---

#### `PersonalityManager.load_personality(pai_instance_id: str) -> Optional[PersonalityProfile]`

Load personality configuration for a PAI.

**Returns**: PersonalityProfile with empathy level, communication style, etc.

---

## Context Injection Interface

**File**: `backend/core/context.py`

### Smart Context Assembly

#### `ContextManager.prepare_response_context(session_id: str, user_id: str, user_message: str) -> str`

Build full context for Claude prompt injection.

**Returns**: Multi-section context string

**Sections**:
1. **Recent Conversation**: Last 5-10 messages
2. **Empathy Guidance**: Based on detected emotion
3. **User Preferences**: Learned communication style
4. **Relevant Learnings**: Domain knowledge
5. **Context Metadata**: Session info, source documents, etc.

**Token Usage**: Carefully budgeted to leave room for response

---

#### `ContextInjector.score_context_relevance(context: str, user_query: str) -> float`

Score how relevant context is to current query (0-1).

**Used By**: Context builder to rank which memories to include

---

## Skill System Interface

**File**: `backend/integrations/skills/`

### Skill Interface

#### Base Class: `Skill(ABC)`

All skills inherit from this base class.

```python
class CodeAnalyzerSkill(Skill):
    @property
    def name(self) -> str:
        return "code_analyzer"

    @property
    def description(self) -> str:
        return "Analyzes code for quality, patterns, and issues"

    @property
    def parameters(self) -> Dict[str, SkillParameter]:
        return {
            "code": SkillParameter(
                name="code",
                type="string",
                description="Python code to analyze",
                required=True
            )
        }

    async def execute(self, **kwargs) -> SkillResult:
        code = kwargs["code"]
        # Analyze code...
        return SkillResult(
            success=True,
            data={"issues": [], "quality": 0.95}
        )
```

---

### Skill Registry

#### Class: `SkillRegistry`

Manages skill lifecycle.

**Methods**:
```python
registry.register(skill: Skill)          # Register a skill
registry.unregister(skill_name: str)     # Remove skill
registry.get_skill(skill_name: str)      # Get skill instance
registry.is_available(skill_name: str)   # Check if available
registry.list_skills()                   # List all
registry.execute(skill_name, **kwargs)   # Run skill
```

**Example**:
```python
from backend.integrations.skills import SkillRegistry, Skill

registry = SkillRegistry()
registry.register(CodeAnalyzerSkill())

result = await registry.execute(
    "code_analyzer",
    code="def hello():\n    print('hi')"
)
```

---

## Database Schema

**File**: `backend/db/models.py`

All models use:
- UUID primary keys
- UTC timestamps
- JSON columns for flexible data
- Foreign key relationships

### Key Tables

**sessions**: Conversation sessions
```sql
id (UUID), user_id, pai_instance_id, session_type, created_at, updated_at, ended_at
```

**memories**: Layer 1-2 memory storage
```sql
id, session_id (FK), user_id, memory_type, content (JSON), importance, created_at, accessed_at, access_count
```

**learning**: PAI self-learning records
```sql
id, pai_instance_id (FK), learning_type, content (JSON), effectiveness_score, created_at
```

**pai_instances**: PAI configuration
```sql
id (UUID), name, specialization, base_model, personality_profile (JSON), knowledge_domains (JSON)
```

**skills**: Registered skills
```sql
id, name, version, description, path, enabled, parameters (JSON)
```

---

## Error Handling

### Current Approach
Phase 1 uses generic exceptions: `ValueError`, `RuntimeError`

### Phase 2 Should Add
```python
class PAIException(Exception):
    """Base PAI exception"""
    pass

class SessionNotFoundError(PAIException):
    """Session doesn't exist"""
    pass

class MemoryError(PAIException):
    """Memory system error"""
    pass

class SkillError(PAIException):
    """Skill execution failed"""
    pass

class APIError(PAIException):
    """External API error"""
    pass
```

---

## Configuration

**File**: `backend/utils/config.py`

### Settings (Pydantic BaseSettings)
```python
# AI Models
default_model: str  # e.g., "claude-sonnet-4-6"
fast_model: str
powerful_model: str

# Memory
max_injection_tokens: int  # Context budget
response_reserve_tokens: int  # Leave room for response
context_reserve_tokens: int  # Cushion

# Database
database_url: str  # e.g., "sqlite:///pai.db"

# API
anthropic_api_key: str
github_token: Optional[str]

# Features
redis_url: Optional[str]  # For Phase 2
ollama_enabled: bool
ollama_endpoint: str
```

### Usage
```python
from backend.utils.config import settings

print(settings.default_model)
print(settings.max_injection_tokens)
```

---

## Testing Infrastructure

**File**: `tests/conftest.py`

### Fixtures Available

```python
test_db                    # In-memory SQLite
db_session                 # Fresh per test
pai_engine                 # Engine instance
memory_system              # Memory instance
context_manager            # Context instance
learning_system            # Learning instance
personality_manager        # Personality instance
sample_session_id          # Unique session ID
sample_user_id             # Unique user ID
sample_pai_instance_id     # Unique PAI ID
```

### Test Pattern

```python
@pytest.mark.asyncio
async def test_something(self, memory_system, sample_session_id, sample_user_id):
    # Your test here
    pass
```

---

## Phase 2 Integration Points

### Must Do Before Phase 2
1. **Define custom exception hierarchy** (Phase 2 REST layer needs this)
2. **Create ServiceContainer for DI** (FastAPI integration)
3. **Document session ↔ pai_instance_id mapping** (Learning system contract)

### Recommended Phase 2 Enhancements
1. Add exception types (block until done)
2. Create ServiceContainer pattern
3. Implement custom tone detection for other languages
4. Add async/sync boundary consideration for real DB
5. Define API versioning strategy

### Do NOT Modify Phase 1
Phase 1 core is stable. Extend outside it:
- Add REST API layer
- Add Web UI integration
- Add Telegram bot
- Add Multi-PAI network
- Add Skill implementations

---

## Known Limitations

### SQLite (Phase 1 Default)
- ✅ Perfect for development
- ❌ Can't filter Learning records by interaction_type (no .astext() support)
- ❌ Can't support parallel test execution
- ✅ Can upgrade to PostgreSQL without code changes

### Emotion Detection
- ✅ Fast keyword matching
- ❌ English only
- ❌ Misses context ("I'm not frustrated, but...")
- 🎯 Phase 2 should add semantic/ML-based detection

### Async/Sync Boundary
- ✅ Properly isolated with asyncio.to_thread()
- ⚠️ Database operations are sync
- 🎯 Phase 2 should evaluate asyncpg for true async DB

### In-Memory vs. Persistent Sessions
- ⚠️ Sessions in-memory can diverge from DB
- ✅ Can recover from DB if needed
- 🎯 Phase 2 should document recovery strategy

---

## Summary

**Phase 1 provides a solid, plug-and-play foundation for Phase 2+.**

- ✅ All core interfaces are stable
- ✅ Database schema is extension-friendly
- ✅ Async/await properly implemented
- ✅ Test infrastructure is comprehensive
- ⚠️ Phase 2 must add: exceptions, DI, documentation

**Do NOT modify Phase 1 core. Build Phase 2 around it.**

---

**Last Updated**: 2026-03-29
**Next Phase**: Phase 2 - REST API Implementation
