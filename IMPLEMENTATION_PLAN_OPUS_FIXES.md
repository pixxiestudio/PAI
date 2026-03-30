# PAI PROJECT: IMPLEMENTATION PLAN FOR OPUS FIXES
**Created**: March 30, 2026
**Priority**: Critical & High-Priority Items
**Timeline**: 3-4 days for critical fixes + testing
**Total Effort**: 34-48 hours

---

## OVERVIEW

This document provides a step-by-step implementation plan for all Opus-recommended fixes, organized by priority and effort.

### Fix Categories
- 🔴 **CRITICAL** (3 items, 5.75 hours) - Must complete before deploy
- 🟠 **HIGH** (3 items, 13-18 hours) - Complete before launch
- 🟡 **MEDIUM** (2 items, 12-20 hours) - Complete within 30 days

---

## 🔴 CRITICAL FIXES (5.75 hours total)

### FIX #1: CONNECTION POOL SIZING ⏱️ 15 minutes
**Priority**: CRITICAL - Quick Win
**Risk**: Database connection exhaustion at 50+ concurrent users
**Current State**: Default pool_size=5 (SQLAlchemy default)

#### Step 1.1: Update Configuration
**File**: `backend/utils/config.py`

**Current Code**:
```python
DATABASE_URL = settings.database_url
```

**New Code**:
```python
# Database connection pool configuration
DATABASE_POOL_CONFIG = {
    'pool_size': 20,           # Increase from default 5
    'max_overflow': 0,         # Reject connections above pool_size
    'pool_pre_ping': True,     # Verify connections before use
    'pool_recycle': 3600,      # Recycle connections hourly (avoid stale connections)
}
```

#### Step 1.2: Update API Server
**File**: `backend/api/main.py`

**Current Code** (around line 57):
```python
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo
)
```

**New Code**:
```python
from backend.utils.config import DATABASE_POOL_CONFIG

# Create database engine with optimized pool configuration
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=DATABASE_POOL_CONFIG['pool_size'],
    max_overflow=DATABASE_POOL_CONFIG['max_overflow'],
    pool_pre_ping=DATABASE_POOL_CONFIG['pool_pre_ping'],
    pool_recycle=DATABASE_POOL_CONFIG['pool_recycle']
)
```

#### Step 1.3: Verification
```bash
# Test: Run with debug logging
# Connection pool should show pool_size=20 in startup logs
# Expected in logs: "CREATE pool <QueuePool object at 0x...>, size=20"
```

**Completion**: ✅ When pool_size=20 verified in logs

---

### FIX #2: DATABASE INDEXES ⏱️ 1 hour
**Priority**: CRITICAL - Performance Critical
**Risk**: Message queries timeout at 1M+ rows
**Current State**: No indexes on common query patterns

#### Step 2.1: Create Indexes - Option A (SQL Migration)
**File**: Create `backend/db/migrations/001_add_indexes.sql`

```sql
-- Index for querying messages by session (most common query)
CREATE INDEX idx_messages_session_created
ON messages(session_id, created_at DESC);

-- Index for querying learning outcomes by user
CREATE INDEX idx_learning_user_created
ON learning(user_id, created_at DESC);

-- Index for querying memory by user and type
CREATE INDEX idx_memory_user_type
ON memory(user_id, memory_type);
```

#### Step 2.2: Create Indexes - Option B (SQLAlchemy Models)
**File**: `backend/db/models.py`

**Add to Message model**:
```python
from sqlalchemy import Index

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # ... other columns ...

    # Add composite index for query optimization
    __table_args__ = (
        Index('idx_messages_session_created', 'session_id', 'created_at'),
    )
```

**Add to Learning model**:
```python
class Learning(Base):
    __tablename__ = "learning"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # ... other columns ...

    __table_args__ = (
        Index('idx_learning_user_created', 'user_id', 'created_at'),
    )
```

**Add to Memory model**:
```python
class Memory(Base):
    __tablename__ = "memory"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    memory_type = Column(String, nullable=False)
    # ... other columns ...

    __table_args__ = (
        Index('idx_memory_user_type', 'user_id', 'memory_type'),
    )
```

#### Step 2.3: Apply Indexes to Database
```bash
# If using SQLAlchemy models approach:
python -c "from backend.db.models import Base; from backend.utils.config import settings; from sqlalchemy import create_engine; engine = create_engine(settings.database_url); Base.metadata.create_all(engine)"

# Or run SQL directly:
sqlite3 your_database.db < backend/db/migrations/001_add_indexes.sql
```

#### Step 2.4: Verification
```bash
# Verify indexes exist:
# For SQLite:
sqlite3 your_database.db ".indices"

# For PostgreSQL:
psql -c "SELECT indexname FROM pg_indexes WHERE schemaname = 'public';"

# Should show:
# idx_messages_session_created
# idx_learning_user_created
# idx_memory_user_type
```

**Completion**: ✅ When all 3 indexes verified to exist

---

### FIX #3: TOKEN REVOCATION SYSTEM ⏱️ 4-6 hours
**Priority**: CRITICAL - Security Critical
**Risk**: Compromised tokens valid until 24h expiration
**Current State**: No token blacklist/revocation mechanism

#### Step 3.1: Add Redis to Dependencies
**File**: `requirements.txt`

**Add**:
```
redis==5.0.1
```

#### Step 3.2: Update Configuration
**File**: `backend/utils/config.py`

**Add to settings**:
```python
# Redis configuration for token revocation
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

# Token revocation TTL (24 hours = 86400 seconds)
TOKEN_REVOCATION_TTL = 86400
```

#### Step 3.3: Create TokenRevocationService
**File**: Create `backend/core/token_revocation.py`

```python
"""Token revocation service for JWT token blacklisting"""

import redis
import logging
from typing import Optional
from backend.utils.config import settings

logger = logging.getLogger(__name__)


class TokenRevocationService:
    """Service for revoking JWT tokens (blacklisting)"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize token revocation service

        Args:
            redis_client: Redis client instance (if None, disabled)
        """
        self.redis = redis_client
        self.enabled = redis_client is not None

    def revoke_token(self, token: str, expires_in: int = 86400) -> bool:
        """
        Revoke (blacklist) a JWT token

        Args:
            token: JWT token to revoke
            expires_in: TTL in seconds (default 24 hours)

        Returns:
            True if revocation successful, False if service disabled
        """
        if not self.enabled:
            logger.warning("Token revocation requested but Redis disabled")
            return False

        try:
            key = f"revoked_token:{token}"
            self.redis.setex(key, expires_in, "1")
            logger.info(f"Token revoked (TTL: {expires_in}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def is_revoked(self, token: str) -> bool:
        """
        Check if a JWT token has been revoked

        Args:
            token: JWT token to check

        Returns:
            True if token is revoked, False if valid or service disabled
        """
        if not self.enabled:
            return False  # If Redis disabled, assume token not revoked

        try:
            key = f"revoked_token:{token}"
            return self.redis.exists(key) == 1
        except Exception as e:
            logger.error(f"Failed to check token revocation: {e}")
            return False  # On error, assume valid (fail open)

    def clear_revocation(self, token: str) -> bool:
        """
        Clear revocation for a token (rarely used)

        Args:
            token: JWT token to un-revoke

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            key = f"revoked_token:{token}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to clear token revocation: {e}")
            return False
```

#### Step 3.4: Update ServiceContainer
**File**: `backend/core/container.py`

**Add Redis client initialization**:
```python
import redis
from backend.core.token_revocation import TokenRevocationService

class ServiceContainer:
    def __init__(self, db_session=None):
        """Initialize service container with all dependencies"""

        # ... existing code ...

        # Initialize Redis client for token revocation
        try:
            if settings.REDIS_ENABLED:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                # Test connection
                self.redis_client.ping()
                self.revocation_service = TokenRevocationService(self.redis_client)
                logger.info("Redis token revocation service initialized")
            else:
                logger.warning("Redis disabled - token revocation will not work")
                self.revocation_service = TokenRevocationService(None)
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.revocation_service = TokenRevocationService(None)

    async def shutdown(self):
        """Shutdown service container"""
        # ... existing code ...
        if hasattr(self, 'redis_client'):
            self.redis_client.close()
```

#### Step 3.5: Update JWTHandler in auth.py
**File**: `backend/core/auth.py`

**Modify verify_token method**:
```python
def verify_token(self, token: str, revocation_service=None) -> Dict[str, Any]:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string to verify
        revocation_service: Optional TokenRevocationService for checking revocation

    Returns:
        Decoded token payload

    Raises:
        TokenInvalidError: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

        # Check if token is revoked (if service provided)
        if revocation_service and revocation_service.is_revoked(token):
            logger.warning(f"Attempt to use revoked token")
            raise TokenInvalidError("Token has been revoked")

        logger.info(f"JWT token verified for user {payload.get('user_id')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token")
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise TokenInvalidError(f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {e}")
        raise TokenInvalidError(f"Error verifying token: {e}")
```

#### Step 3.6: Update API Endpoint for Logout
**File**: `backend/api/v1/auth.py`

**Add logout endpoint**:
```python
from fastapi import APIRouter, Depends, HTTPException
from backend.core.container import get_container

router = APIRouter(prefix="/api/v1", tags=["auth"])

@router.post("/logout")
async def logout(token: str = Depends(get_token_from_header)):
    """
    Logout user by revoking their token

    Args:
        token: JWT token from Authorization header

    Returns:
        Success message
    """
    container = get_container()

    if container.revocation_service.revoke_token(token):
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to process logout"
        )
```

#### Step 3.7: Add Tests
**File**: Create `backend/tests/test_token_revocation.py`

```python
import pytest
import redis
from backend.core.token_revocation import TokenRevocationService
from backend.core.auth import JWTHandler


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    return redis.Redis(host='localhost', port=6379, db=1)


@pytest.fixture
def revocation_service(mock_redis):
    """Create token revocation service"""
    return TokenRevocationService(mock_redis)


@pytest.fixture
def jwt_handler():
    """Create JWT handler"""
    return JWTHandler()


async def test_revoke_and_check_token(jwt_handler, revocation_service):
    """Test token revocation"""
    # Create token
    token = jwt_handler.create_token("user123")

    # Verify not revoked initially
    assert not revocation_service.is_revoked(token)

    # Revoke token
    assert revocation_service.revoke_token(token)

    # Verify now revoked
    assert revocation_service.is_revoked(token)


async def test_revocation_ttl(revocation_service):
    """Test that revoked tokens expire after TTL"""
    token = "test_token"

    # Revoke with 1 second TTL
    revocation_service.revoke_token(token, expires_in=1)
    assert revocation_service.is_revoked(token)

    # Wait for expiration
    import time
    time.sleep(2)

    # Should no longer be revoked
    assert not revocation_service.is_revoked(token)
```

#### Step 3.8: Environment Configuration
**File**: `.env.example`

**Add**:
```
# Redis configuration for token revocation
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

#### Step 3.9: Verification
```bash
# Start Redis (if not running):
redis-server

# Run tests:
pytest backend/tests/test_token_revocation.py -v

# Expected output:
# test_revoke_and_check_token PASSED
# test_revocation_ttl PASSED
```

**Completion**: ✅ When logout endpoint works and tests pass

---

## 🟠 HIGH-PRIORITY FIXES (13-18 hours total)

### FIX #4: PER-USER RATE LIMITING ⏱️ 3-4 hours
**Priority**: HIGH - Security (prevents account enumeration)
**Risk**: Attackers can enumerate accounts
**Current State**: Rate limiting by IP only

#### Step 4.1: Create Per-User Rate Limiter
**File**: Create `backend/core/user_rate_limiter.py`

```python
"""Per-user rate limiting to prevent account enumeration"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class PerUserRateLimiter:
    """Track rate limits per user for security endpoints"""

    def __init__(self):
        """Initialize in-memory rate limit tracker"""
        # Format: {"user_id": [(timestamp, action), ...]}
        self.attempts: Dict[str, list] = {}
        self.max_attempts = 5  # Max failed attempts
        self.window_seconds = 3600  # 1 hour window

    def record_failed_attempt(self, user_id: str, action: str = "login") -> None:
        """
        Record a failed authentication attempt for a user

        Args:
            user_id: User identifier
            action: Type of action (login, password_reset, etc.)
        """
        now = datetime.now(timezone.utc)

        if user_id not in self.attempts:
            self.attempts[user_id] = []

        self.attempts[user_id].append((now, action))
        logger.warning(f"Failed {action} attempt for user {user_id}")

    def is_rate_limited(self, user_id: str, action: str = "login") -> bool:
        """
        Check if user is rate limited

        Args:
            user_id: User identifier
            action: Type of action

        Returns:
            True if user exceeded rate limit, False otherwise
        """
        if user_id not in self.attempts:
            return False

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        # Remove old attempts outside window
        self.attempts[user_id] = [
            (timestamp, act) for timestamp, act in self.attempts[user_id]
            if timestamp > window_start and act == action
        ]

        # Check if exceeded limit
        if len(self.attempts[user_id]) >= self.max_attempts:
            logger.warning(f"User {user_id} rate limited for {action}")
            return True

        return False

    def reset_attempts(self, user_id: str, action: str = "login") -> None:
        """
        Reset rate limit for user (on successful login)

        Args:
            user_id: User identifier
            action: Type of action
        """
        if user_id in self.attempts:
            self.attempts[user_id] = [
                (ts, act) for ts, act in self.attempts[user_id]
                if act != action
            ]
```

#### Step 4.2: Update Auth Endpoint
**File**: `backend/api/v1/auth.py`

```python
from backend.core.user_rate_limiter import PerUserRateLimiter

rate_limiter = PerUserRateLimiter()

@router.post("/login")
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT token

    Args:
        credentials: Username and password

    Returns:
        JWT token and user info
    """
    # Check if user is rate limited
    if rate_limiter.is_rate_limited(credentials.username, action="login"):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Try again in 1 hour."
        )

    # Verify credentials
    user = authenticate_user(credentials.username, credentials.password)

    if not user:
        # Record failed attempt
        rate_limiter.record_failed_attempt(credentials.username, action="login")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Success - reset rate limit
    rate_limiter.reset_attempts(credentials.username, action="login")

    # Create token
    token = jwt_handler.create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
```

#### Step 4.3: Tests
**File**: Create `backend/tests/test_user_rate_limiter.py`

```python
import pytest
from backend.core.user_rate_limiter import PerUserRateLimiter


@pytest.fixture
def limiter():
    return PerUserRateLimiter()


async def test_rate_limit_after_max_attempts(limiter):
    """Test that user is rate limited after max attempts"""
    user_id = "test_user"

    # Record max attempts
    for i in range(limiter.max_attempts):
        assert not limiter.is_rate_limited(user_id)
        limiter.record_failed_attempt(user_id)

    # Next attempt should be rate limited
    assert limiter.is_rate_limited(user_id)


async def test_reset_after_success(limiter):
    """Test that rate limit resets after successful login"""
    user_id = "test_user"

    # Record some attempts
    for i in range(3):
        limiter.record_failed_attempt(user_id)

    # Reset
    limiter.reset_attempts(user_id)

    # Should not be rate limited
    assert not limiter.is_rate_limited(user_id)
```

**Completion**: ✅ When rate limiting works and blocks after 5 failures

---

### FIX #5: MESSAGE ARCHIVAL STRATEGY ⏱️ 6-8 hours
**Priority**: HIGH - Data Persistence (prevents unbounded growth)
**Risk**: Table grows to 100M+ rows, performance degrades
**Current State**: No retention policy

#### Step 5.1: Create Archive Job
**File**: Create `backend/jobs/archive_messages.py`

```python
"""Archive old messages to cold storage"""

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_
from backend.db.models import Message

logger = logging.getLogger(__name__)


async def archive_old_messages(
    db_session,
    retention_days: int = 365,
    batch_size: int = 1000
):
    """
    Archive messages older than retention period

    Args:
        db_session: Database session
        retention_days: Days to keep in hot storage (default 1 year)
        batch_size: How many messages to archive per batch
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    try:
        # Find old messages
        old_messages = db_session.query(Message).filter(
            Message.created_at < cutoff_date
        ).limit(batch_size).all()

        if not old_messages:
            logger.info("No old messages to archive")
            return

        # Archive to cold storage (e.g., S3, GCS)
        archive_path = await backup_to_cloud(old_messages)

        # Delete from hot database
        for msg in old_messages:
            db_session.delete(msg)

        db_session.commit()

        logger.info(f"Archived {len(old_messages)} messages to {archive_path}")

    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to archive messages: {e}")
        raise


async def backup_to_cloud(messages: list) -> str:
    """
    Backup messages to cloud storage (S3, GCS, etc.)

    Args:
        messages: List of Message objects to archive

    Returns:
        Path where backed up
    """
    # Implementation depends on your cloud provider
    # Example with S3:
    import boto3
    import json

    s3 = boto3.client('s3')

    # Serialize messages
    data = json.dumps([
        {
            "id": msg.id,
            "session_id": msg.session_id,
            "created_at": msg.created_at.isoformat(),
            "content": msg.content
        }
        for msg in messages
    ])

    # Upload to S3
    timestamp = datetime.now(timezone.utc).isoformat()
    key = f"archived_messages/{timestamp}.json.gz"

    s3.put_object(
        Bucket="pai-message-archive",
        Key=key,
        Body=data,
        ServerSideEncryption="AES256"
    )

    return f"s3://pai-message-archive/{key}"
```

#### Step 5.2: Schedule Archive Job
**File**: Create `backend/jobs/scheduler.py`

```python
"""Schedule recurring archive jobs"""

import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


async def setup_scheduler(db_session):
    """Setup APScheduler for recurring jobs"""

    scheduler = AsyncIOScheduler()

    # Archive old messages daily at 2 AM
    scheduler.add_job(
        func=archive_old_messages,
        trigger="cron",
        hour=2,
        minute=0,
        args=(db_session,),
        id="archive_messages",
        name="Archive messages older than 365 days",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Message archive scheduler started")

    return scheduler
```

#### Step 5.3: Add to Dependencies
**File**: `requirements.txt`

**Add**:
```
apscheduler==3.10.4
```

#### Step 5.4: Integration with Startup
**File**: `backend/api/main.py`

```python
from backend.jobs.scheduler import setup_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""

    # Startup
    logger.info("Starting up...")

    # ... existing startup code ...

    # Start archive scheduler
    scheduler = await setup_scheduler(db_session)

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown()

    # ... existing shutdown code ...
```

**Completion**: ✅ When archive job runs and removes old messages

---

### FIX #6: MONITORING & ALERTING ⏱️ 4-6 hours
**Priority**: HIGH - Operations (detect issues automatically)
**Risk**: Silent failures, undetected issues
**Current State**: No monitoring alerts configured

#### Step 6.1: Add Prometheus Metrics
**File**: Create `backend/core/metrics.py`

```python
"""Prometheus metrics for monitoring"""

from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Database metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# Token metrics
tokens_revoked_total = Counter(
    'tokens_revoked_total',
    'Total tokens revoked'
)

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['limiter_type']
)
```

#### Step 6.2: Setup Prometheus
**File**: Create `docker-compose.prometheus.yml`

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerting_rules.yml:/etc/prometheus/alerting_rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
```

#### Step 6.3: Prometheus Config
**File**: Create `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'pai-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

rule_files:
  - 'alerting_rules.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

#### Step 6.4: Alert Rules
**File**: Create `alerting_rules.yml`

```yaml
groups:
  - name: pai_alerts
    rules:
      # Error rate alert
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.01  # > 1% error rate
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected ({{ $value | humanizePercentage }})"

      # Response time alert
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times detected (p95: {{ $value }}s)"

      # Database connections alert
      - alert: HighDatabaseConnections
        expr: database_connections_active > 18
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High database connection usage ({{ $value }} of 20)"

      # Memory alert (via system metrics)
      - alert: HighMemoryUsage
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage above 80%"
```

**Completion**: ✅ When metrics are being collected and alerts trigger

---

## 🟡 MEDIUM-PRIORITY FIXES (12-20 hours)

### FIX #7: LOAD TESTING FRAMEWORK ⏱️ 4-6 hours
**Priority**: MEDIUM - Validation
**Risk**: Unknown performance under load

**File**: Create `tests/load/locustfile.py`

```python
"""Load testing with Locust"""

from locust import HttpUser, task, between
import random


class PAIUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    @task(3)
    def chat_message(self):
        """Send chat message (weighted 3)"""
        session_id = getattr(self, 'session_id', None)
        if not session_id:
            # Create session first
            response = self.client.post(
                "/api/v1/sessions",
                json={"user_id": f"user_{random.randint(1, 1000)}"}
            )
            if response.status_code == 200:
                self.session_id = response.json()['session_id']

        if session_id:
            self.client.post(
                f"/api/v1/messages/{session_id}",
                json={"message": "Hello, how are you?"}
            )

    @task(1)
    def get_memory(self):
        """Get user memory (weighted 1)"""
        self.client.get(
            "/api/v1/memory",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def get_learning(self):
        """Get user learning (weighted 1)"""
        self.client.get(
            "/api/v1/learning",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    def on_start(self):
        """Called when user starts"""
        # Login to get token
        response = self.client.post(
            "/api/v1/login",
            json={
                "username": f"user_{random.randint(1, 1000)}",
                "password": "password"
            }
        )
        if response.status_code == 200:
            self.token = response.json()['access_token']
```

**Run load test**:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 300 --spawn-rate 10 --run-time 10m
```

**Success Criteria**:
- ✅ 300 concurrent users without errors
- ✅ Response time p95 < 2s
- ✅ Memory stable (no growth)
- ✅ CPU < 70%

---

### FIX #8: REDIS CACHING LAYER ⏱️ 8-10 hours
**Priority**: MEDIUM - Performance (for 500+ concurrent)

**File**: Create `backend/core/cache.py`

```python
"""Redis-backed caching layer"""

import redis
import json
import logging
from typing import Optional, Any
from functools import wraps
from backend.utils.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching service"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.enabled = redis_client is not None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None

        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.enabled:
            return

        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def delete(self, key: str):
        """Delete value from cache"""
        if not self.enabled:
            return

        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")


def cached(ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            cache_service.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

**Usage**:
```python
# In API endpoint
@cached(ttl=300)  # Cache for 5 minutes
async def get_user_memory(user_id: str):
    return db_session.query(Memory).filter(Memory.user_id == user_id).all()
```

**Completion**: ✅ When caching reduces database load

---

## IMPLEMENTATION SCHEDULE

### Week 1: Critical Fixes
```
Monday:
  - Connection Pool (15 min)
  - Database Indexes (1 hour)
  - Total: 1.25 hours

Tuesday-Wednesday:
  - Token Revocation (4-6 hours)
  - Testing & verification (2-3 hours)
  - Total: 6-9 hours

Thursday-Friday:
  - Load Testing (4-6 hours)
  - Security validation (2 hours)
  - Total: 6-8 hours

Subtotal: ~13-18 hours (ready for deployment)
```

### Week 2: High-Priority Fixes
```
Monday-Tuesday:
  - Per-User Rate Limiting (3-4 hours)
  - Monitoring Setup (4-6 hours)
  - Total: 7-10 hours

Wednesday-Friday:
  - Message Archival (6-8 hours)
  - Testing & verification (3-4 hours)
  - Total: 9-12 hours

Subtotal: ~16-22 hours
```

### Week 3-4: Medium-Priority & Optimization
```
- Load Testing Framework (4-6 hours)
- Redis Caching (8-10 hours)
- Documentation & runbooks (4-6 hours)
- Total: 16-22 hours
```

---

## SUCCESS CRITERIA

### Critical Fixes Validation
- ✅ Connection pool shows size=20
- ✅ 3 database indexes exist and improve query performance
- ✅ Token revocation works (logout invalidates tokens)
- ✅ Load test with 300 concurrent users passes

### High-Priority Fixes Validation
- ✅ Rate limiting blocks after 5 failed attempts
- ✅ Messages older than 1 year automatically archived
- ✅ Prometheus metrics collecting
- ✅ Alerts firing correctly on threshold breaches

### Medium-Priority Fixes Validation
- ✅ Load test framework running successfully
- ✅ Redis cache reducing database queries
- ✅ Cache invalidation working correctly

---

## ROLLBACK PLAN

If any fix causes issues:

```bash
# Revert connection pool changes
git revert <commit_hash>

# Restore database from backup
sqlite3 backup.db ".restore pai.db"

# Restart services
docker-compose restart

# Verify health
curl http://localhost:8000/api/v1/health
```

---

**Ready to implement?** Start with FIX #1 (Connection Pool - takes 15 minutes)
