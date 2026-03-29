# Phase 2 Integration Guide: FastAPI REST API Layer

**Status**: Phase 1 Foundation Complete - Ready for Phase 2 REST API Implementation
**Last Updated**: 2026-03-29
**Author**: Claude Code

---

## Overview

Phase 1 has established a robust foundation with:
- ✅ Claude Code Agent SDK integration
- ✅ 3-Layer Memory System (Session/Semantic/Episodic)
- ✅ Self-Learning System (outcome tracking, pattern detection)
- ✅ Empathy & Personality Adaptation
- ✅ Extensible Skill/Plugin System
- ✅ Dependency Injection Container pattern
- ✅ Strong typing with Pydantic models
- ✅ Custom exception hierarchy with HTTP status mapping
- ✅ Timezone-aware datetimes throughout
- ✅ PAI Instance association with sessions

Phase 2 will expose this foundation through a FastAPI REST API layer, enabling:
- HTTP clients to interact with PAI
- Web dashboard integration
- Telegram bot integration (Phase 3)
- CLI client integration
- Multi-instance management

---

## Critical Dependencies Between Phase 1 & Phase 2

### 1. **ConversationContext & PAI Instance Mapping**

**Phase 1 Delivers**:
```python
@dataclass
class ConversationContext:
    session_id: str
    pai_instance_id: str           # ← NEW: Maps to PAIInstance
    messages: List[Dict[str, str]]
    model: str
    max_tokens: int
```

**Phase 2 Requirements**:
- All session creation MUST specify `pai_instance_id`
- Database has FK constraint: `Session.pai_instance_id → PAIInstance.id`
- Cannot create a session without a valid PAI instance
- Query sessions by `pai_instance_id` for per-instance analytics

**Example Phase 2 Code**:
```python
@app.post("/api/v1/sessions")
async def create_session(
    request: CreateSessionRequest,
    container: ServiceContainer = Depends(get_container)
):
    engine = container.get_engine()

    # Specify which PAI handles this session
    session_id = await engine.create_session(
        user_id=request.user_id,
        pai_instance_id=request.pai_instance_id or "default",
        session_type="chat"
    )

    return SessionResponse(
        session_id=session_id,
        user_id=request.user_id,
        created_at=datetime.now(timezone.utc),
        session_type="chat"
    )
```

### 2. **Exception Hierarchy & HTTP Status Mapping**

**Phase 1 Delivers**:
```python
class SessionNotFoundError(SessionException):
    http_status_code = 404
    error_code = "SESSION_NOT_FOUND"

class InvalidMessageError(ValidationException):
    http_status_code = 400
    error_code = "INVALID_MESSAGE"
```

**Phase 2 Implementation**:
```python
from backend.core.exceptions import PAIException

@app.exception_handler(PAIException)
async def pai_exception_handler(request: Request, exc: PAIException):
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": exc.error_code,
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
```

### 3. **ServiceContainer Dependency Injection**

**Phase 1 Delivers**:
```python
class ServiceContainer:
    def __init__(self, db_session: Optional[DBSession] = None):
        self._engine: Optional[PAIEngine] = None
        self._memory_system: Optional[MemorySystem] = None
        self._learning_system: Optional[SelfLearningSystem] = None
        ...

    def get_engine(self) -> PAIEngine: ...
    def get_memory_system(self) -> MemorySystem: ...
    def get_learning_system(self) -> SelfLearningSystem: ...
```

**Phase 2 FastAPI Integration**:
```python
from fastapi import FastAPI, Depends
from backend.core.container import get_container, ServiceContainer

app = FastAPI()

# Create container on app startup
container: Optional[ServiceContainer] = None

@app.on_event("startup")
async def startup_event():
    global container
    # Initialize database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    # Create container with DB session
    container = ServiceContainer(db_session=db_session)

@app.on_event("shutdown")
async def shutdown_event():
    if container:
        await container.shutdown()

# All endpoints use container dependency
@app.post("/api/v1/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    container: ServiceContainer = Depends(lambda: globals()['container'])
):
    engine = container.get_engine()
    response = await engine.send_message(
        session_id=session_id,
        user_message=request.message
    )
    return SendMessageResponse(
        session_id=session_id,
        response=response,
        timestamp=datetime.now(timezone.utc)
    )
```

### 4. **Pydantic Models for API Responses**

**Phase 1 Delivers** (backend/core/models.py):
```python
class SendMessageResponse(BaseModel):
    session_id: str = Field(...)
    response: str = Field(...)
    timestamp: datetime = Field(...)
    tokens_used: Optional[int] = Field(None)

class ErrorResponse(BaseModel):
    error_code: str = Field(...)
    message: str = Field(...)
    http_status_code: int = Field(...)
```

**Phase 2 Usage**:
```python
@app.post("/api/v1/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(...):
    # Response automatically validated against SendMessageResponse
    return SendMessageResponse(...)

# Errors automatically mapped to ErrorResponse
@app.exception_handler(InvalidMessageError)
async def handle_invalid_message(request: Request, exc: InvalidMessageError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code="INVALID_MESSAGE",
            message=str(exc),
            http_status_code=400,
            timestamp=datetime.now(timezone.utc)
        ).dict()
    )
```

### 5. **Timezone-Aware Datetimes**

**Phase 1 Delivers**:
- All `datetime.utcnow()` → `datetime.now(timezone.utc)`
- All database defaults use `_utc_now()` function
- Consistent UTC timezone throughout

**Phase 2 Requirement**:
```python
from datetime import datetime, timezone

# ALL timestamp fields must be timezone-aware
timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# NO naive datetimes
# WRONG: datetime.utcnow()
# RIGHT: datetime.now(timezone.utc)
```

### 6. **Memory System Integration**

**Phase 1 Delivers**:
```python
class MemorySystem:
    async def save_message(self, session_id, user_id, content) -> str: ...
    async def get_session_context(self, session_id) -> str: ...
    async def get_relevant_memories(self, user_id) -> List[MemoryEntry]: ...
    async def build_injection_context(self, session_id, user_id) -> str: ...
```

**Phase 2 Usage Pattern**:
```python
@app.post("/api/v1/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    container: ServiceContainer = Depends(get_container)
):
    engine = container.get_engine()
    memory_system = container.get_memory_system()

    # Save user message to memory
    await memory_system.save_message(
        session_id=session_id,
        user_id=request.user_id,
        content=request.message,
        sender="user"
    )

    # Get context for injection
    context = await memory_system.build_injection_context(
        session_id=session_id,
        user_id=request.user_id
    )

    # Send message with context
    response = await engine.send_message(
        session_id=session_id,
        user_message=request.message,
        context_injection=context
    )

    # Save AI response to memory
    await memory_system.save_message(
        session_id=session_id,
        user_id=request.user_id,
        content=response,
        sender="assistant"
    )

    return SendMessageResponse(
        session_id=session_id,
        response=response,
        timestamp=datetime.now(timezone.utc)
    )
```

---

## API Endpoint Blueprint

### Session Management

```
POST   /api/v1/sessions
       Create new session for user
       Request: { user_id, pai_instance_id }
       Response: SessionResponse

GET    /api/v1/sessions/{session_id}
       Get session details
       Response: SessionResponse

DELETE /api/v1/sessions/{session_id}
       End session
       Response: { status: "ended" }
```

### Messaging

```
POST   /api/v1/sessions/{session_id}/messages
       Send message and get response
       Request: SendMessageRequest
       Response: SendMessageResponse

GET    /api/v1/sessions/{session_id}/history
       Get conversation history
       Response: SessionHistoryResponse

GET    /api/v1/sessions/{session_id}/messages?limit=20
       Get paginated message history
       Response: PaginatedMessages
```

### Memory Management

```
GET    /api/v1/users/{user_id}/memories
       Get user's memories
       Response: GetMemoriesResponse

POST   /api/v1/users/{user_id}/memories
       Save new memory
       Request: SaveMemoryRequest
       Response: SaveMemoryResponse

PUT    /api/v1/memories/{memory_id}
       Update memory (importance)
       Request: { importance: 0-1 }
       Response: { success: bool }
```

### Learning & Feedback

```
POST   /api/v1/sessions/{session_id}/feedback
       Submit quality feedback on response
       Request: { rating: 1-5, feedback_text }
       Response: { processed: bool }

GET    /api/v1/pai/{pai_instance_id}/learning
       Get learning progress
       Response: LearningReportResponse
```

### Skills Management

```
GET    /api/v1/pai/{pai_instance_id}/skills
       List available skills
       Response: { skills: [SkillInfo] }

POST   /api/v1/pai/{pai_instance_id}/skills/{skill_name}/execute
       Execute a skill
       Request: ExecuteSkillRequest
       Response: SkillExecutionResult
```

---

## Database Integrity Constraints

### Foreign Key Relationships

**Session → PAIInstance**:
```sql
ALTER TABLE sessions
ADD CONSTRAINT fk_session_pai
FOREIGN KEY (pai_instance_id)
REFERENCES pai_instances(id)
ON DELETE RESTRICT;
```

Implication: Cannot delete a PAI instance if sessions exist.

**Learning → PAIInstance**:
```sql
ALTER TABLE learning
ADD CONSTRAINT fk_learning_pai
FOREIGN KEY (pai_instance_id)
REFERENCES pai_instances(id)
ON DELETE CASCADE;
```

Implication: Deleting PAI instance cascades to delete its learning records.

**SkillExecution → Session**:
```sql
ALTER TABLE skill_executions
ADD CONSTRAINT fk_skillexec_session
FOREIGN KEY (session_id)
REFERENCES sessions(id)
ON DELETE CASCADE;
```

---

## Performance Considerations for Phase 2

### 1. Session Lookup

**Current**: Dictionary lookup (O(1) in-memory)
**Phase 2 Concern**: With multiple workers, sessions are per-worker
**Solution**: Move to Redis-backed session store for distributed deployments

```python
# Phase 2 upgrade
class RedisSessionStore:
    async def get_context(self, session_id: str) -> ConversationContext:
        data = await redis.get(f"session:{session_id}")
        return ConversationContext.parse_obj(json.loads(data))

    async def save_context(self, context: ConversationContext):
        await redis.setex(
            f"session:{context.session_id}",
            3600,  # 1 hour TTL
            context.json()
        )
```

### 2. Memory Queries

**Current**: Linear scan of all memories
**Phase 2 Optimization**: Add vector embeddings for semantic search

```python
# Phase 2 upgrade
async def get_relevant_memories_semantic(
    self,
    user_id: str,
    query: str,
    limit: int = 5
) -> List[MemoryEntry]:
    # Use embedding model to find semantically similar memories
    query_embedding = await embed(query)
    memories = await self.semantic_search(user_id, query_embedding, limit)
    return memories
```

### 3. Concurrent Message Handling

**Current**: Sequential processing in engine.send_message()
**Phase 2 Consideration**: May need queue-based processing for high throughput

```python
# Consider for Phase 2+
class MessageQueue:
    async def enqueue_message(self, session_id, message):
        await queue.put({
            'session_id': session_id,
            'message': message,
            'timestamp': datetime.now(timezone.utc)
        })

    async def process_messages(self):
        while True:
            msg = await queue.get()
            await self.handle_message(msg)
```

---

## Testing Strategy for Phase 2

### Unit Tests

```python
# tests/unit/test_api_endpoints.py
@pytest.mark.asyncio
async def test_send_message_endpoint(client, container):
    # Create session
    session_response = await client.post(
        "/api/v1/sessions",
        json={"user_id": "test-user", "pai_instance_id": "default"}
    )
    session_id = session_response.json()["session_id"]

    # Send message
    message_response = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "Hello PAI"}
    )

    assert message_response.status_code == 200
    assert "response" in message_response.json()

@pytest.mark.asyncio
async def test_invalid_session_error(client):
    response = await client.post(
        "/api/v1/sessions/invalid-session-id/messages",
        json={"message": "test"}
    )

    assert response.status_code == 404
    assert response.json()["error"] == "SESSION_NOT_FOUND"
```

### Integration Tests

```python
# tests/integration/test_api_flow.py
@pytest.mark.asyncio
async def test_full_conversation_flow(client, container):
    # 1. Create session
    session_id = await create_test_session(client)

    # 2. Send multiple messages
    responses = []
    for msg in ["Hello", "How are you?", "Tell me a joke"]:
        resp = await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": msg}
        )
        responses.append(resp.json()["response"])

    # 3. Verify context is building
    history = await client.get(f"/api/v1/sessions/{session_id}/history")
    assert len(history.json()["messages"]) >= 6  # 3 user + 3 AI

    # 4. Verify memories are saved
    memories = await client.get("/api/v1/users/test-user/memories")
    assert len(memories.json()["memories"]) > 0

    # 5. Submit feedback
    feedback = await client.post(
        f"/api/v1/sessions/{session_id}/feedback",
        json={"rating": 5, "feedback_text": "Great!"}
    )
    assert feedback.status_code == 200
```

---

## Migration Path: Phase 1 → Phase 2

### What Stays the Same
- ✅ ConversationContext structure
- ✅ Memory System API
- ✅ Engine.send_message() signature
- ✅ Exception hierarchy
- ✅ Pydantic models
- ✅ Database models

### What's Added
- 🆕 FastAPI REST API layer
- 🆕 Request/Response serialization
- 🆕 Error handling middleware
- 🆕 Authentication (basic/OAuth)
- 🆕 Rate limiting
- 🆕 CORS configuration

### What's Refactored (Minimal)
- Session storage: in-memory dict → optional Redis
- Message handling: direct calls → potential queue-based (Phase 3)
- Timezone handling: already completed in Phase 1

---

## Known Limitations (Phase 1)

These are documented limitations that Phase 2 will address:

1. **Session Storage**: In-memory dictionary not thread-safe for multi-worker deployments
   - **Phase 2 Fix**: Use Redis or sticky sessions

2. **No Authentication**: API has no user authentication
   - **Phase 2 Fix**: Add JWT/OAuth middleware

3. **No Rate Limiting**: No protection against abuse
   - **Phase 2 Fix**: Add rate limit middleware

4. **Single Database**: SQLite cannot handle concurrent writes well
   - **Phase 2 Fix**: Upgrade to PostgreSQL

5. **Memory Search**: Linear scan through all memories
   - **Phase 2 Fix**: Add vector embeddings, semantic search index

6. **No Caching**: Every request queries database fresh
   - **Phase 2 Fix**: Add Redis caching layer

---

## Checklist for Phase 2 Kickoff

Before starting Phase 2 REST API implementation, verify:

- [ ] All Phase 1 tests pass (41 tests, 0 failures)
- [ ] pai_instance_id properly maps ConversationContext → Database
- [ ] All datetimes are timezone-aware
- [ ] SkillRegistry.unregister() is async-compatible
- [ ] Foreign keys documented in database models
- [ ] Exception hierarchy fully mapped to HTTP status codes
- [ ] ServiceContainer ready for FastAPI Depends() integration
- [ ] All Pydantic models included in models.py
- [ ] No hardcoded datetime.utcnow() calls remaining
- [ ] Memory system tested with context injection

---

## Reference: Key Files Modified in Phase 1

**Core Engine & Memory**:
- `backend/core/engine.py` - Added pai_instance_id to ConversationContext
- `backend/core/memory.py` - Configurable memory decay
- `backend/core/learning.py` - Self-learning system
- `backend/core/exceptions.py` - Exception hierarchy
- `backend/core/container.py` - Dependency injection
- `backend/core/models.py` - Pydantic response models

**Database**:
- `backend/db/models.py` - Added timezone-aware defaults, FK constraints

**Configuration**:
- `backend/utils/config.py` - Configurable memory decay lambda

**Skills**:
- `backend/integrations/skills/registry.py` - Fixed async unregister

---

## Next Steps

1. ✅ Phase 1 implementation complete
2. 📋 Phase 2: Implement FastAPI REST API layer
   - Create endpoint handlers for all routes
   - Implement exception middleware
   - Add authentication
   - Add rate limiting
3. 🧪 Phase 2: Write comprehensive API tests
4. 🚀 Phase 2: Docker setup for local development
5. 📱 Phase 3: Telegram bot integration
6. 🌐 Phase 3: Web dashboard (React)

