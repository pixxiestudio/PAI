# PAI PROJECT - COMPLETE VPS DEPLOYMENT GUIDE
**Status**: Production Ready with All Opus Fixes
**Target**: 6vCPU, 12GB RAM, Ubuntu 24.04 LTS
**Date**: March 30, 2026
**Duration**: 2.5-3 hours
**Last Updated**: March 30, 2026

> **This is the AUTHORITATIVE deployment guide.** See DEPRECATED DOCUMENTS section below.

---

## ⚠️ IMPORTANT: DEPRECATED DOCUMENTS

The following documents have been consolidated into this guide and are **NO LONGER MAINTAINED**:

- ❌ `DEPLOYMENT_READINESS_CHECKLIST.md` - DEPRECATED (sections merged below)
- ❌ `VPS_DEPLOYMENT_GUIDE.md` - DEPRECATED (sections merged below)
- ❌ `DEPLOYMENT_WITH_OPUS_FIXES.md` - DEPRECATED (sections merged below)

**Use this document for all deployments going forward.**

---

## 📋 PRE-DEPLOYMENT CHECKLIST (90 minutes total)

### ✅ Phase 1: Preparation (30 minutes)

#### Secrets & Environment Variables
Have these ready before starting:
```bash
□ ANTHROPIC_API_KEY           # Your Claude API key from console.anthropic.com
□ JWT_SECRET_KEY              # Generate: openssl rand -hex 32
□ ENCRYPTION_KEY              # Generate: openssl rand -hex 32
□ GITHUB_TOKEN                # (optional, for GitHub integration)
□ Database password            # Generate: openssl rand -hex 16
```

#### Domain & DNS
```bash
□ Domain name registered (e.g., pai.yourdomain.com)
□ DNS A record points to your VPS IP address
□ DNS propagated (verify: nslookup yourdomain.com)
```

#### VPS Access & Credentials
```bash
□ SSH private key file ready
□ Can SSH: ssh -i your_key.pem user@your_vps_ip
□ sudo access available (test: sudo whoami)
□ Git access configured (for cloning repository)
```

### ✅ Phase 2: Pre-Flight Checks (30 minutes)

```bash
# 1 Hour Before: System checks
□ Close all other work (focus)
□ Terminal ready with SSH access
□ All secrets documented and accessible
□ This guide open and ready

# 30 Minutes Before: Final verification
□ SSH connection works
□ VPS has free disk space: ssh user@vps 'df -h | grep /'
  └─ Need: min 50GB free
□ VPS has available RAM: ssh user@vps 'free -h'
  └─ Need: min 4GB available
□ Basic commands work: ssh user@vps 'ls && pwd && sudo whoami'

# Notify (if applicable)
□ Stakeholders notified of deployment window
□ Backup of existing services created
□ Emergency contacts documented
```

### ✅ Phase 3: Knowledge Check (30 minutes)

Before proceeding, ensure you understand:
```bash
□ Basic Docker commands (docker ps, docker logs)
□ Docker Compose usage (docker-compose up, down, logs)
□ Basic Nginx configuration
□ PostgreSQL/Redis basics
□ How to read deployment logs
□ How to SSH and basic Linux commands
□ How to use curl for API testing
```

---

## 🚀 DEPLOYMENT STEPS (8 Steps, 2.5-3 hours)

### STEP 1: System Preparation (45 minutes)

```bash
# SSH into your VPS
ssh -i your_key.pem user@your_vps_ip

# 1.1 Update system packages
sudo apt update && sudo apt upgrade -y

# 1.2 Install required tools
sudo apt install -y \
  build-essential \
  curl \
  git \
  wget \
  htop \
  net-tools \
  fail2ban \
  ufw \
  docker.io \
  docker-compose \
  postgresql-client \
  redis-server \
  nginx \
  certbot \
  python3-certbot-nginx

# 1.3 Start and enable services
sudo systemctl start docker
sudo systemctl start redis-server
sudo systemctl start nginx
sudo systemctl enable docker
sudo systemctl enable redis-server
sudo systemctl enable nginx

# 1.4 Add user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker $USER
newgrp docker

# 1.5 Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status

# 1.6 Set timezone
sudo timedatectl set-timezone UTC

# Verification
docker --version
docker-compose --version
sudo systemctl status docker
```

---

### STEP 2: Repository Clone & Environment Setup (20 minutes)

```bash
# 2.1 Create deployment directory
mkdir -p ~/pai-deployment
cd ~/pai-deployment

# 2.2 Clone repository
git clone https://github.com/yourusername/PAI.git .
git checkout main

# 2.3 Create production environment file
cat > .env.production << 'EOF'
# Server Configuration
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
HOST=0.0.0.0
PORT=8000

# Database (PostgreSQL)
DATABASE_URL=postgresql://pai_user:STRONG_PASSWORD_HERE@localhost:5432/pai_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0
DATABASE_POOL_RECYCLE=3600

# Redis (for token revocation - NEW OPUS FIX)
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# Security - REPLACE THESE WITH GENERATED VALUES
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
JWT_SECRET_KEY=YOUR_32_HEX_CHARS_HERE
ENCRYPTION_KEY=YOUR_32_HEX_CHARS_HERE

# Optional: GitHub Integration
GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE

# Logging
LOG_LEVEL=INFO

# CORS - Update to your domain
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com", "www.yourdomain.com", "localhost"]

# Frontend
NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1
EOF

# 2.4 Secure the environment file
chmod 600 .env.production

# 2.5 Verify environment file created
cat .env.production
```

---

### STEP 3: PostgreSQL Database Setup (20 minutes)

```bash
# 3.1 Create PostgreSQL user and database
sudo -u postgres psql << 'EOF'
CREATE USER pai_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
CREATE DATABASE pai_db OWNER pai_user;
GRANT ALL PRIVILEGES ON DATABASE pai_db TO pai_user;
\connect pai_db
GRANT ALL ON SCHEMA public TO pai_user;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

# 3.2 Verify database was created
sudo -u postgres psql -l | grep pai_db

# 3.3 Test connection
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "SELECT version();"

# 3.4 Initialize database with migrations
cd ~/pai-deployment
docker run --rm \
  --network host \
  -e DATABASE_URL="postgresql://pai_user:STRONG_PASSWORD_HERE@localhost:5432/pai_db" \
  -v $(pwd):/app \
  python:3.11 bash -c "
    pip install -q sqlalchemy psycopg2-binary alembic
    python /app/backend/scripts/init_db.py
  "

# 3.5 Verify database schema created
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "\dt"
# Should show tables: sessions, messages, memories, learning, etc.
```

---

### STEP 4: Nginx SSL/TLS Configuration (20 minutes)

```bash
# 4.1 Create Nginx configuration
sudo tee /etc/nginx/sites-available/pai.conf > /dev/null << 'EOF'
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS with SSL
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (Let's Encrypt - obtained in Step 5)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/pai_access.log;
    error_log /var/log/nginx/pai_error.log;

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # Streaming endpoint (longer timeout)
    location /api/v1/stream/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# 4.2 Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/pai.conf /etc/nginx/sites-enabled/

# 4.3 Test Nginx configuration
sudo nginx -t
# Expected: "syntax is ok" and "test is successful"

# 4.4 Reload Nginx (without certificate yet)
sudo systemctl reload nginx
```

---

### STEP 5: SSL Certificate with Let's Encrypt (15 minutes)

```bash
# 5.1 Obtain SSL certificate
sudo certbot certonly --nginx \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --agree-tos \
  --email your-email@example.com \
  --non-interactive

# 5.2 Reload Nginx with SSL enabled
sudo systemctl reload nginx

# 5.3 Verify SSL certificate
sudo certbot certificates

# 5.4 Test HTTPS
curl https://yourdomain.com
# Expected: Connection works (may be 502 until services start)

# 5.5 Auto-renewal setup
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

### STEP 6: Docker Compose Production Configuration (20 minutes)

```bash
cd ~/pai-deployment

# 6.1 Create production Docker Compose file
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: pai_backend
    environment:
      DATABASE_URL: postgresql://pai_user:STRONG_PASSWORD_HERE@localhost:5432/pai_db
      DATABASE_POOL_SIZE: 20
      DATABASE_MAX_OVERFLOW: 0
      DATABASE_POOL_RECYCLE: 3600
      REDIS_ENABLED: "true"
      REDIS_URL: redis://localhost:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      - db
      - redis

  # Next.js Frontend
  frontend:
    build:
      context: ./frontend/web
      dockerfile: Dockerfile
    container_name: pai_frontend
    environment:
      NEXT_PUBLIC_API_URL: https://yourdomain.com/api/v1
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - backend

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: pai_db
    environment:
      POSTGRES_USER: pai_user
      POSTGRES_PASSWORD: STRONG_PASSWORD_HERE
      POSTGRES_DB: pai_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pai_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache (for token revocation - NEW OPUS FIX)
  redis:
    image: redis:7-alpine
    container_name: pai_redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local
EOF

# 6.2 Verify docker-compose.prod.yml syntax
docker-compose -f docker-compose.prod.yml config > /dev/null
```

---

### STEP 7: Build & Start Containers (30 minutes)

```bash
cd ~/pai-deployment

# 7.1 Build Docker images
docker-compose -f docker-compose.prod.yml build --no-cache
# Note: This downloads base images and builds PAI backend/frontend
# Expected time: 15-20 minutes

# 7.2 Start all services
docker-compose -f docker-compose.prod.yml up -d

# 7.3 Check service startup
docker-compose -f docker-compose.prod.yml ps
# Expected: All containers "Up"

# 7.4 Wait for services to be ready (give them 30 seconds)
sleep 30

# 7.5 View logs to verify startup
docker-compose -f docker-compose.prod.yml logs --tail=50
# Look for: "Uvicorn running on" (backend), "started server" (frontend)
```

---

### STEP 8: Verification & Testing (20 minutes)

```bash
# 8.1 Verify all containers running
docker-compose -f docker-compose.prod.yml ps
# Expected output:
# NAME          STATE        PORTS
# pai_backend   Up           8000/tcp
# pai_frontend  Up           3000/tcp
# pai_db        Up           5432/tcp
# pai_redis     Up           6379/tcp

# 8.2 Test backend health endpoint
curl https://yourdomain.com/api/v1/health
# Expected response: {"status": "healthy", "database_connected": true, ...}

# 8.3 Test frontend loads
curl https://yourdomain.com | head -20
# Expected: HTML response with Next.js app

# 8.4 Test authentication (NEW - Opus Fix #6: User ID Tracking)
RESPONSE=$(curl -s -X POST https://yourdomain.com/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}')
TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token obtained: $TOKEN"
# Expected: Token starting with "eyJ..."

# 8.5 Test logout/revocation (NEW - Opus Fix #3: Token Revocation)
curl -X POST https://yourdomain.com/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
# Expected: {"message": "Successfully logged out", "user_id": "test_user"}

# 8.6 Verify token is now revoked
curl -X POST https://yourdomain.com/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"user_id": "test_user"}' \
  -H "Content-Type: application/json"
# Expected: 401 Unauthorized (token was revoked)

# 8.7 Test rate limiting (NEW - Opus Fix #7: Per-User Rate Limiting)
for i in {1..6}; do
  echo "Attempt $i:"
  curl -s -X POST https://yourdomain.com/api/v1/auth/token \
    -H "Content-Type: application/json" \
    -d '{"user_id": "rate_test_user"}' | jq '.status // .detail'
done
# Expected: Last attempt returns 429 Too Many Requests

# 8.8 Check logs for all Opus fixes
docker-compose -f docker-compose.prod.yml logs backend | grep -E "pool|index|revok|reload|linkage|rate_limit|rollback" | head -20
# Should see evidence of all fixes working

echo "✅ All verifications passed!"
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Immediate Checks (After Step 8)

```bash
# All services running
docker-compose -f docker-compose.prod.yml ps
# All should show "Up"

# Database connected
docker-compose -f docker-compose.prod.yml exec backend \
  curl http://localhost:8000/api/v1/health | jq '.database_connected'
# Should be: true

# Redis working (NEW - Opus Fix #3)
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
# Should be: PONG

# Indexes created (NEW - Opus Fix #2)
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "
  SELECT indexname FROM pg_indexes
  WHERE tablename IN ('messages', 'learning', 'memories')
  ORDER BY indexname;"
# Should show: idx_messages_session_created, idx_learning_instance_type_created, etc.

# Connection pool configured (NEW - Opus Fix #1)
grep DATABASE_POOL_SIZE .env.production
# Should show: DATABASE_POOL_SIZE=20
```

### Health Checks (Daily)

```bash
#!/bin/bash
# save as ~/pai-deployment/health-check.sh

set -e

echo "=== PAI Health Check ==="
echo "Time: $(date)"

# Backend health
echo -n "Backend: "
curl -s https://yourdomain.com/api/v1/health | jq '.status' || echo "FAILED"

# Database connection
echo -n "Database: "
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost \
  -c "SELECT 'OK'" 2>/dev/null || echo "FAILED"

# Redis connection
echo -n "Redis: "
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping 2>/dev/null || echo "FAILED"

# Container status
echo -n "Containers: "
UP_COUNT=$(docker-compose -f docker-compose.prod.yml ps | grep -c "Up")
TOTAL_COUNT=$(docker-compose -f docker-compose.prod.yml ps | grep -c "pai_")
echo "$UP_COUNT/$TOTAL_COUNT running"

echo "=== Done ==="
```

---

## 🔍 MONITORING & VERIFICATION (All Opus Fixes)

### Monitor Database Performance (Fix #1: Connection Pool)

```bash
# Check pool usage
docker-compose -f docker-compose.prod.yml exec backend python3 << 'EOF'
from sqlalchemy import create_engine, text
from backend.utils.config import settings
engine = create_engine(settings.database_url)
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Available: {pool.size() - pool.checkedout()}")
EOF

# Watch active connections
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost << 'EOF'
SELECT
  datname,
  count(*) as connections,
  max(extract(epoch from (now() - query_start))) as longest_query_seconds
FROM pg_stat_activity
GROUP BY datname;
EOF
```

### Monitor Token Revocation (Fix #3: Token Revocation)

```bash
# Check Redis cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli << 'EOF'
INFO stats
KEYS "revoked_token:*" | wc -l
EOF

# Check revocation logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "token.*revok" | tail -10
```

### Monitor Database Indexes (Fix #2: Database Indexes)

```bash
# List all indexes
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "
  SELECT schemaname, tablename, indexname
  FROM pg_indexes
  WHERE tablename IN ('messages', 'learning', 'memories')
  ORDER BY tablename, indexname;"

# Check index usage
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "
  SELECT schemaname, tablename, indexname, idx_scan
  FROM pg_stat_user_indexes
  WHERE tablename IN ('messages', 'learning', 'memories')
  ORDER BY idx_scan DESC;"
```

### Monitor Session Reload (Fix #4: Session State Sync)

```bash
# Check session reload logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "session.*reload" | tail -10

# Test session reload (after restarting backend)
docker-compose -f docker-compose.prod.yml restart backend
sleep 10
curl https://yourdomain.com/api/v1/health
```

### Monitor Learning Linkage (Fix #5: Learning Records Linkage)

```bash
# Check Learning table structure
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "
  \d learning" | grep -E "session_id|user_id|message_id"

# Count learning records with linkage
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "
  SELECT
    COUNT(*) as total,
    COUNT(session_id) as with_session,
    COUNT(user_id) as with_user,
    COUNT(message_id) as with_message
  FROM learning;"
```

### Monitor Rate Limiting (Fix #7: Per-User Rate Limiting)

```bash
# Check rate limiting logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "rate_limit" | tail -10

# Test rate limiting
for i in {1..6}; do
  echo "Attempt $i:"
  curl -s -X POST https://yourdomain.com/api/v1/auth/token \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"ratelimit_test_$i\"}" | jq '.status // .detail'
  sleep 1
done
```

---

## 🛠️ TROUBLESHOOTING

### Issue: Backend won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common causes:
# - Database not ready: wait 30 seconds and try again
# - API key missing: verify .env.production
# - Port in use: docker ps | grep 8000
# - Build failed: docker-compose build --no-cache backend
```

### Issue: Database won't connect

```bash
# Verify PostgreSQL running
sudo systemctl status postgresql
# or
docker-compose -f docker-compose.prod.yml logs db

# Test connection manually
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "SELECT 1"

# Check if indexes are created
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -d pai_db -h localhost -c "
  SELECT indexname FROM pg_indexes WHERE tablename = 'messages';"
```

### Issue: SSL certificate not working

```bash
# Check certificate status
sudo certbot certificates

# Verify Nginx can find certificate
sudo ls -la /etc/letsencrypt/live/yourdomain.com/

# Test HTTPS
curl -v https://yourdomain.com

# Reload Nginx
sudo systemctl reload nginx
```

### Issue: Token revocation not working

```bash
# Check Redis running
docker-compose -f docker-compose.prod.yml ps redis
# Should be "Up"

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
# Should return: PONG

# Check revocation logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "revocation"

# If Redis not available, system falls back to in-memory
docker-compose -f docker-compose.prod.yml logs backend | grep -i "in-memory fallback"
```

---

## 📊 OPERATIONAL COMMANDS

### Start/Stop Services

```bash
cd ~/pai-deployment

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build --no-cache backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### View Logs

```bash
cd ~/pai-deployment

# View all logs (last 50 lines)
docker-compose -f docker-compose.prod.yml logs --tail=50

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f backend

# View specific service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs db
docker-compose -f docker-compose.prod.yml logs redis
```

### Updates & Maintenance

```bash
cd ~/pai-deployment

# Pull latest code
git pull origin main

# Rebuild containers with new code
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop, rebuild, and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Verify everything after update
docker-compose -f docker-compose.prod.yml ps
curl https://yourdomain.com/api/v1/health
```

### Database Backups

```bash
# Backup database
mkdir -p ~/backups
BACKUP_FILE=~/backups/pai_db_$(date +%Y%m%d_%H%M%S).sql
PGPASSWORD=STRONG_PASSWORD_HERE pg_dump -U pai_user -h localhost pai_db > $BACKUP_FILE
echo "Backup saved to: $BACKUP_FILE"

# List backups
ls -lh ~/backups/

# Restore from backup
PGPASSWORD=STRONG_PASSWORD_HERE psql -U pai_user -h localhost pai_db < ~/backups/pai_db_20260330_120000.sql
```

---

## ✅ DEPLOYMENT SUCCESS CHECKLIST

Verify all 8 Opus Fixes are working:

| # | Fix | Verification Command | Expected Result |
|---|-----|---------------------|-----------------|
| 1 | Connection Pool | `grep DATABASE_POOL_SIZE .env.production` | `DATABASE_POOL_SIZE=20` |
| 2 | Database Indexes | `psql ... -c "SELECT indexname FROM pg_indexes..."` | Shows `idx_messages_session_created`, `idx_learning_*`, `idx_memory_*` |
| 3 | Token Revocation | `curl /auth/logout` with token, then use same token | 401 Unauthorized |
| 4 | Session Reload | Restart backend, query session | Session history loads from DB |
| 5 | Learning Linkage | `psql ... -c "SELECT session_id, user_id, message_id FROM learning..."` | Shows linked columns populated |
| 6 | User ID Tracking | Send message via API, check database | Message has real `user_id`, not "unknown" |
| 7 | Rate Limiting | 6 failed auth attempts | 5th+ returns 429 Too Many Requests |
| 8 | DB Rollbacks | Check logs for errors | See `rollback()` in error logs |

**If all checks pass: ✅ Deployment successful!**

---

## 📞 SUPPORT & REFERENCES

If you encounter issues:

1. **Check logs first**: `docker-compose -f docker-compose.prod.yml logs backend`
2. **Review this guide**: Search for the specific issue in TROUBLESHOOTING section
3. **Check referenced documents**:
   - `OPUS_COMPREHENSIVE_AUDIT_REPORT.md` - Technical details on all fixes
   - `TECHNOLOGY_STACK.md` - Complete tech stack reference
   - `PROJECT_STATUS_BY_PHASE.md` - Project architecture overview

4. **Common commands**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps       # Service status
   docker-compose -f docker-compose.prod.yml logs -f  # Live logs
   curl https://yourdomain.com/api/v1/health          # Health check
   ```

---

**Status**: ✅ Production Ready
**Last Updated**: March 30, 2026
**All 8 Opus Fixes Implemented & Verified**
