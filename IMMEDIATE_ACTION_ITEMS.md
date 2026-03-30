# PAI Audit - Immediate Action Items

**Generated**: March 30, 2026
**Priority**: CRITICAL → HIGH → MEDIUM

---

## CRITICAL - DO THIS NOW (Today)

### 1. Fix Python Environment for CI/CD

**File to Modify**: `.github/workflows/ci.yml`

**Location**: Line 79 in backend-tests job

**Current Code**:
```yaml
- name: Install dependencies
  working-directory: backend
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

**Updated Code**:
```yaml
- name: Install dependencies
  working-directory: backend
  run: |
    python -m pip install --upgrade pip
    pip install --no-binary cryptography cryptography==41.0.7
    pip install -r requirements.txt
```

**Why**: The cffi module dependency in cryptography fails to build. Using `--no-binary` forces pip to use prebuilt wheels.

**Expected Result**: Backend tests will execute without ModuleNotFoundError

**Verification**:
```bash
# Test locally after fix:
cd backend
pip install --no-binary cryptography cryptography==41.0.7
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

---

### 2. Run Full Test Suite

**Backend Tests**:
```bash
cd /home/user/PAI/backend
python -m pytest tests/ -v --tb=short --cov=. --cov-report=html
```

**Expected**: All 52 test functions pass
**Time**: ~5-10 minutes

**Frontend Tests**:
```bash
cd /home/user/PAI/frontend/web
npm test -- --coverage --watchAll=false
```

**Expected**: All 6 test files pass
**Time**: ~3-5 minutes

**Verification Steps**:
1. Run backend tests
2. Check coverage report (target: 70%+)
3. Run frontend tests
4. Verify no console errors
5. Document results

---

### 3. Create Production Environment Configuration

**File**: Create `/home/user/PAI/.env.production.example`

**Content**:
```env
# ==========================================
# PRODUCTION CONFIGURATION TEMPLATE
# ==========================================

# FRONTEND (Vercel)
NEXT_PUBLIC_API_URL=https://api.pai.example.com/api/v1
NEXT_PUBLIC_DEBUG=false

# BACKEND (Cloud Run)
API_HOST=0.0.0.0
API_PORT=8080
API_SECRET_KEY=[GENERATE: openssl rand -hex 32]

# DATABASE (PostgreSQL - Production)
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/pai_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# JWT (Update secret)
JWT_SECRET=[GENERATE: openssl rand -hex 32]
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ANTHROPIC
ANTHROPIC_API_KEY=sk-ant-[from console.anthropic.com]
ANTHROPIC_MODEL=claude-opus-4-6

# GITHUB
GITHUB_TOKEN=ghp_[from GitHub settings]
GITHUB_API_URL=https://api.github.com

# LOGGING
LOG_LEVEL=WARNING
DEBUG=false

# SESSIONS
SESSION_TIMEOUT_MINUTES=30
MAX_SESSIONS_PER_USER=10

# RATE LIMITING (Stricter in production)
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW_MINUTES=1

# REDIS (Required for production scaling)
REDIS_URL=redis://[USER:PASSWORD@]HOST:PORT/DB

# FILES
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIRECTORY=/var/uploads

# ENVIRONMENT
ENVIRONMENT=production

# GCP (Cloud Run)
GCP_PROJECT_ID=[from GCP console]
GCP_REGION=us-central1

# VERCEL
VERCEL_ENV=production
```

**Instructions**:
1. Create file with content above
2. Document where to get each secret (GCP, Anthropic, GitHub, etc.)
3. Add to docs/deployment.md with production setup instructions
4. Do NOT commit actual secret values

---

## HIGH PRIORITY - This Week

### 4. Verify Streaming Endpoint Response Format

**Test the endpoint**:
```bash
# Start the API
cd /home/user/PAI/backend
python -m uvicorn backend.api.main:app --reload --port 8000

# In another terminal, test streaming
curl -v http://localhost:8000/api/v1/stream/sessions/test-session-id/messages
```

**Expected Response Headers**:
```
Content-Type: text/event-stream
Transfer-Encoding: chunked
```

**Expected Response Body Format** (one of):
```
# Option 1: Server-Sent Events (SSE)
data: {"content": "chunk of text", ...}
data: [DONE]

# Option 2: Regular chunked transfer
chunk of text
[DONE]
```

**If Issue Found**:
1. Check `/backend/api/v1/streaming.py` line 21-80
2. Verify response format in `stream_ai_response()` generator
3. Ensure proper SSE headers are set
4. Add test case to verify format

---

### 5. Code Review: authenticated-api-client.ts

**File**: `/frontend/web/lib/authenticated-api-client.ts`

**Review Checklist**:
- [ ] File exists at correct path
- [ ] Imports authenticated token from useAuth
- [ ] Adds Authorization header to requests
- [ ] Handles 401 responses (token expired)
- [ ] Implements retry logic with exponential backoff
- [ ] Has timeout configuration (30s recommended)
- [ ] Proper error handling for network failures
- [ ] Proxy routing to /api/proxy/* works

**Action if issues found**:
1. Document any API differences from hooks
2. Create ticket for frontend fixes
3. Update hook implementations if needed

---

### 6. Test File Upload End-to-End

**Steps**:
1. Start backend API
2. Start frontend: `npm run dev` in frontend/web
3. Navigate to Memory page
4. Upload a test file (< 10MB)
5. Verify:
   - File appears in upload list
   - Progress bar shows
   - Success message displays
   - File metadata saved to database

**Test Cases**:
- [ ] Small text file (.txt)
- [ ] Image file (.png/.jpg)
- [ ] Multiple files simultaneously
- [ ] File larger than limit
- [ ] Invalid file type (if restricted)
- [ ] Network error during upload

**Expected Behavior**:
- ✅ Files upload successfully
- ✅ Progress tracked per file
- ✅ Errors handled gracefully
- ✅ Success callbacks fire
- ✅ Memory page updates with file reference

---

### 7. Test Chat with Streaming

**Steps**:
1. Navigate to Chat page
2. Create new chat session
3. Send a message
4. Observe streaming response:
   - Text appears chunk-by-chunk
   - Not all at once
   - Completes with [DONE] sentinel
5. Verify message saves in database

**Test Cases**:
- [ ] Short message (< 100 chars)
- [ ] Long message (> 1000 chars)
- [ ] Stop streaming mid-response
- [ ] Network interruption recovery
- [ ] Multiple rapid messages

**Expected Behavior**:
- ✅ Response streams in real-time
- ✅ UI updates as chunks arrive
- ✅ Final message saves correctly
- ✅ Error handling works

---

## MEDIUM PRIORITY - Next 2 Weeks

### 8. Add E2E Integration Test

**File**: Create `/backend/tests/test_e2e_integration.py`

**Test Cases**:
```python
# 1. Complete authentication flow
def test_auth_login_logout():
    # POST /auth/token → get JWT
    # Verify token in response
    # Verify expiration timestamp

# 2. Chat session flow
def test_chat_session_creation():
    # POST /sessions → create session
    # POST /sessions/{id}/messages → send message
    # GET /sessions/{id}/messages → retrieve history

# 3. File upload flow
def test_file_upload_to_memory():
    # POST /files/upload → upload file
    # Verify file metadata
    # Verify file accessible in memory

# 4. Memory operations
def test_memory_crud():
    # POST /users/{id}/memories → save memory
    # GET /users/{id}/memories → retrieve
    # PUT /users/{id}/memories/{id} → update importance
    # DELETE /users/{id}/memories/{id} → delete

# 5. Streaming response
def test_streaming_response():
    # GET /stream/sessions/{id}/messages → stream response
    # Verify SSE format
    # Verify [DONE] sentinel
```

**Expected Coverage**: >80% of happy paths

---

### 9. Performance Testing

**Test Setup**:
```bash
# Install loadtest tool
npm install -g loadtest

# Test backend API capacity
loadtest -c 10 -n 1000 http://localhost:8000/api/v1/health
```

**Success Criteria**:
- [ ] Handle 10 concurrent requests
- [ ] Response time < 500ms (p95)
- [ ] No errors under load
- [ ] Memory usage < 500MB
- [ ] CPU usage < 80%

**If Issues Found**:
1. Check database connection pooling
2. Verify rate limiting not too aggressive
3. Check for memory leaks
4. Profile slow endpoints

---

### 10. Security Audit

**Checklist**:
- [ ] No hardcoded secrets in code
- [ ] All environment variables documented
- [ ] CORS properly configured (not *)
- [ ] Rate limiting enabled
- [ ] JWT secret sufficiently random
- [ ] Password hashing for any passwords (N/A for JWT-only)
- [ ] HTTPS required in production
- [ ] SQL injection protection (SQLAlchemy)
- [ ] XSS protection (Next.js built-in)

**Tool**:
```bash
# Run secret scanner
cd /home/user/PAI
git log -p | grep -i "password\|secret\|token" || echo "✅ No secrets found"

# Or use truffleHog
docker run -it trufflesecurity/trufflehog filesystem /home/user/PAI
```

---

## MEDIUM PRIORITY - This Month

### 11. Documentation Enhancements

**Needed Documentation**:
1. [ ] Production deployment step-by-step guide
2. [ ] Troubleshooting guide (common errors + fixes)
3. [ ] API endpoint reference with curl examples
4. [ ] Database schema diagram (mermaid)
5. [ ] Architecture diagram (mermaid)
6. [ ] Frontend component library documentation
7. [ ] Backend service layer documentation

**Example Addition** - Add to `docs/API_REFERENCE.md`:
```markdown
## GET /sessions/{sessionId}/messages

### Description
Retrieve paginated message history for a session

### Authentication
Required: Bearer token

### Parameters
- sessionId (path): Session UUID
- skip (query, default=0): Number of messages to skip
- limit (query, default=20): Number of messages to return (max=100)

### Response
```json
{
  "total": 45,
  "messages": [
    {
      "id": "msg-123",
      "session_id": "sess-456",
      "sender": "user",
      "content": "Hello",
      "role": "user",
      "created_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

### Example
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/sessions/sess-123/messages?skip=0&limit=10
```
```

---

## FOLLOW-UP VERIFICATION

### After Applying Critical Fixes

**Verification Checklist** (1 hour):
```bash
# 1. Fix Python environment and run tests
cd /home/user/PAI/backend
pip install --no-binary cryptography cryptography==41.0.7
pip install -r requirements.txt
pytest tests/ -v --tb=short -x

# 2. Verify frontend tests
cd /home/user/PAI/frontend/web
npm test -- --coverage --watchAll=false

# 3. Verify API starts
cd /home/user/PAI/backend
python -m uvicorn backend.api.main:app --port 8000

# 4. Verify frontend starts
cd /home/user/PAI/frontend/web
npm run dev

# 5. Smoke tests
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/
```

**Expected Results**:
- ✅ All pytest pass
- ✅ All npm tests pass
- ✅ Backend starts without errors
- ✅ Frontend starts without errors
- ✅ Health endpoint returns 200

---

## SIGN-OFF CHECKLIST

After completing all CRITICAL items, verify:

- [ ] Python environment fix applied to CI/CD
- [ ] Backend tests pass (52/52)
- [ ] Frontend tests pass (all tests)
- [ ] Streaming endpoint returns correct format
- [ ] File upload works end-to-end
- [ ] Chat streaming works end-to-end
- [ ] Production environment template created
- [ ] No hardcoded secrets found
- [ ] All dependencies up to date

**Expected Timeline**:
- CRITICAL items: 2-4 hours
- HIGH items: 1-2 days
- MEDIUM items: 1-2 weeks

**Success Criteria**:
✅ All tests pass
✅ All features work end-to-end
✅ No blocking issues
✅ Ready for Phase 3.4

---

## NEXT PHASE (Phase 3.4)

After completing the above:

1. **Plan Phase 3.4 work**:
   - Enhanced monitoring
   - Performance optimization
   - Security hardening
   - Scalability improvements

2. **Prepare for production**:
   - Final security audit
   - Load testing
   - Deployment checklist
   - Runbook documentation

3. **Team coordination**:
   - Code review final changes
   - Test coverage assessment
   - Performance baseline
   - Deployment plan

---

**Document Version**: 1.0
**Last Updated**: March 30, 2026
**Next Review**: After CRITICAL items completed
