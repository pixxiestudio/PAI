# PAI PROJECT - TECHNOLOGY STACK
**Date**: March 30, 2026
**Status**: Production Ready
**Last Updated**: Comprehensive review complete

---

## 🏗️ OVERALL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                  PAI Platform                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend (Web)          Backend (API)      Infra      │
│  ───────────────         ─────────────      ─────      │
│  • Next.js 14            • FastAPI          • Docker   │
│  • React 18              • Python 3.11      • GitHub   │
│  • TypeScript            • SQLAlchemy       │ Actions  │
│  • Tailwind CSS          • PostgreSQL/SQLite│ • Vercel │
│  • React Query           • Asyncio          │ • Google │
│                                             │   Cloud  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 FRONTEND TECHNOLOGY STACK

### Core Framework & Runtime
```
Node.js             v18+ LTS
npm                 v9+
TypeScript          v5+
Next.js             v14.0+ (App Router)
React               v18+ (Hooks)
```

### Styling & UI
```
Tailwind CSS        v3.4+
shadcn/ui          (Component library)
  ├─ Button
  ├─ Card
  ├─ Input
  ├─ Badge
  ├─ Textarea
  ├─ Dialog
  ├─ Dropdown
  ├─ Alert
  ├─ Toast
  ├─ Sidebar
  ├─ Spinner
  ├─ Tabs
  ├─ Form
  ├─ Checkbox
  ├─ Select
  └─ And 10+ more components

CSS Modules         (Local styling)
PostCSS             (CSS processing)
```

### State Management & Data Fetching
```
React Context API   (User context, theme)
@tanstack/react-query v5.0.0+ (TanStack Query)
  ├─ useQuery (data fetching)
  ├─ useMutation (updates)
  ├─ useInfiniteQuery (pagination)
  └─ QueryClient (caching)

localStorage API    (Client-side persistence)
```

### Custom Hooks
```
useAuth             (JWT token management)
useChat             (Session + message management)
useMemory           (Memory CRUD operations)
useLearning         (Learning data retrieval)
useFileUpload       (File upload handling)
useStreaming        (SSE EventSource)
useAsyncOperation   (Async state tracking)
```

### Testing & Quality
```
Jest                v29.7.0 (Unit testing)
@testing-library/react  v14.1.0 (Component testing)
@testing-library/jest-dom v6.1.5 (DOM matchers)
ts-jest             v29.1.1 (TypeScript support)
Mock Service Worker (MSW) (API mocking)
```

### Code Quality & Formatting
```
ESLint              (Linting)
  ├─ Strict mode enabled
  ├─ Next.js plugin
  └─ React best practices

Prettier            (Code formatting)
TypeScript          (Type checking)
  ├─ Strict mode: true
  ├─ No implicit any
  └─ Full type coverage
```

### Build & Optimization
```
Webpack             (Built into Next.js)
SWC                 (Compilation)
Terser              (Minification)
```

### API Client & Networking
```
Fetch API           (HTTP requests)
  ├─ Custom authenticated-api-client.ts
  ├─ JWT injection
  ├─ 401 error handling
  ├─ Retry logic (exponential backoff)
  └─ Request/response logging

EventSource API     (SSE streaming)
FormData API        (File upload)
```

### Environment & Configuration
```
.env.local          (Local variables)
NEXT_PUBLIC_*       (Public variables)
process.env         (Runtime configuration)
```

### Deployment Targets
```
Vercel              (Frontend hosting)
  ├─ CDN delivery
  ├─ Edge functions
  ├─ Environment variables
  ├─ SSL/TLS
  └─ Auto-deployment on push
```

### Browser Support
```
Modern browsers:    Chrome, Firefox, Safari, Edge
JavaScript ES2020+ (Target)
CSS Grid & Flexbox  (Layout)
```

---

## 🔧 BACKEND TECHNOLOGY STACK

### Core Framework & Runtime
```
Python              v3.11+
pip                 v23+
FastAPI             v0.104.1+ (Web framework)
Uvicorn             v0.24.0+ (ASGI server)
Starlette           (Underlying framework)
```

### ORM & Database
```
SQLAlchemy          v2.0.23+ (ORM)
SQLite              v3 (Development)
PostgreSQL          (Production ready)
Alembic             (Migrations - optional)
```

### API & Request Handling
```
Pydantic            v2+ (Data validation)
  ├─ BaseModel (validation)
  ├─ ValidationError (error handling)
  └─ Type checking

FastAPI routing:
  ├─ Path parameters
  ├─ Query parameters
  ├─ Request body validation
  ├─ Response models
  └─ Status codes
```

### Async & Concurrency
```
asyncio             (Async runtime)
aiohttp             (Async HTTP client)
async/await         (Syntax)
```

### Authentication & Security
```
PyJWT               v2.12.1+ (JSON Web Tokens)
cryptography        v41+ (Encryption)
  ├─ Fernet (symmetric encryption)
  ├─ RSA (asymmetric)
  └─ PBKDF2 (password hashing)

hashlib             (Hashing - SHA256)
secrets             (Random token generation)
```

### Middleware & Handlers
```
CORS middleware     (Cross-Origin Resource Sharing)
Rate limiting       (Token bucket algorithm)
Error handling      (Custom exception mapping)
Request logging     (Structured logging)
```

### Claude API Integration
```
Anthropic SDK       (Claude API client)
  ├─ Messages API
  ├─ Streaming responses
  ├─ Token counting
  └─ Model selection

anthropic-sdk       v0.25+ (Python SDK)
```

### GitHub Integration
```
PyGithub            v2.0+ (GitHub API)
  ├─ Repository operations
  ├─ Issues management
  ├─ Pull request handling
  └─ Code search

GitHub OAuth        (Token-based auth)
github_api          (Direct REST calls)
```

### File Handling
```
python-multipart    (File upload parsing)
python-magic        (MIME type detection)
pathlib             (Path manipulation)
os/shutil           (File operations)
uuid                (Unique file naming)
hashlib             (File hash generation)
```

### Streaming & Real-time
```
SSE (Server-Sent Events)  (Real-time data)
NDJSON              (Newline-delimited JSON)
async generators    (Stream generation)
```

### Testing & Quality
```
pytest              v7.4.3+ (Testing framework)
pytest-asyncio      v0.21.1+ (Async test support)
pytest-cov          (Coverage reporting)
pytest-mock         (Mocking support)

Coverage            (Code coverage analysis)
  ├─ HTML reports
  ├─ XML reports
  └─ Terminal reports
```

### Code Quality
```
Type hints          (Python typing)
  ├─ Type annotations
  ├─ Generic types
  └─ Protocol support

mypy                (Type checking - optional)
black               (Code formatting)
flake8              (Linting)
```

### Logging & Monitoring
```
logging             (Python standard library)
structlog           (Structured logging)
sys                 (System operations)
```

### Configuration & Environment
```
python-dotenv       (Environment variables)
os.environ          (Environment access)
ConfigParser        (Config files)
```

### Deployment Targets
```
Google Cloud Run    (Backend hosting)
  ├─ Containerization
  ├─ Auto-scaling
  ├─ Load balancing
  ├─ Health checks
  └─ Environment variables

Docker              (Containerization)
```

### Requirements Management
```
requirements.txt    (Dependency specification)
  ├─ FastAPI==0.104.1
  ├─ Uvicorn==0.24.0
  ├─ SQLAlchemy==2.0.23
  ├─ Pydantic==2.5.0
  ├─ PyJWT==2.12.1
  ├─ cryptography==41.0.7
  ├─ python-multipart==0.0.6
  ├─ python-magic==0.4.27
  ├─ pytest==7.4.3
  ├─ pytest-asyncio==0.21.1
  ├─ anthropic==0.25.0+
  ├─ PyGithub==2.1.1
  └─ And more...
```

---

## 🗄️ DATABASE TECHNOLOGY

### Database Engine
```
SQLite              (Development)
  ├─ File-based
  ├─ No setup required
  └─ Full SQL support

PostgreSQL          (Production ready)
  ├─ Scalable
  ├─ ACID compliant
  ├─ Advanced features
  └─ Easy migration path
```

### ORM & Migrations
```
SQLAlchemy          v2.0.23+
  ├─ Declarative base
  ├─ Relationships
  ├─ Foreign keys
  ├─ Constraints
  └─ Query builder

Alembic             (Migrations - optional)
  ├─ Version control
  ├─ Auto-generation
  └─ Downgrade support
```

### Database Models
```
User                (User authentication)
Session             (Chat sessions)
Message             (Chat messages)
Memory              (User memories)
Learning            (Learning patterns)
Skill               (Skill metadata)
Integration         (API integrations)
FileMetadata        (File information)
RateLimitBucket     (Rate limit tracking)
```

---

## 📦 CI/CD & DEPLOYMENT STACK

### Version Control
```
Git                 (Version control)
GitHub              (Repository hosting)
  ├─ GitHub Actions
  ├─ GitHub Secrets
  ├─ Webhooks
  └─ Status checks
```

### CI/CD Pipeline
```
GitHub Actions      (Automation)
  ├─ Workflow files (.yml)
  ├─ Actions (pre-built)
  ├─ Environment variables
  └─ Secrets management

Workflows:
  ├─ ci.yml (Testing & build verification)
  │   ├─ Backend: pytest (169 tests)
  │   ├─ Frontend: Jest (87+ tests)
  │   ├─ Code quality: ESLint, TypeScript
  │   └─ Coverage reporting
  │
  └─ deploy.yml (Deployment)
      ├─ Backend: Docker → Cloud Run
      ├─ Frontend: Next.js → Vercel
      ├─ Health checks
      └─ Notifications
```

### Containerization
```
Docker              v24+
  ├─ Backend Dockerfile
  ├─ Multi-stage builds
  ├─ Health checks
  └─ Environment variables

Docker Compose      (Local development)
  ├─ Backend service
  ├─ Database service
  ├─ Frontend service
  ├─ Reverse proxy (Nginx)
  └─ Network setup
```

### Container Registry
```
Google Container Registry (GCR)
  ├─ Image hosting
  ├─ Access control
  └─ Deployment source
```

### Frontend Deployment
```
Vercel              (Next.js platform)
  ├─ Git-connected deployment
  ├─ Preview deployments
  ├─ Environment variables
  ├─ Edge functions
  ├─ CDN acceleration
  ├─ SSL/TLS
  ├─ Custom domains
  └─ Analytics
```

### Backend Deployment
```
Google Cloud Run    (Serverless platform)
  ├─ Container hosting
  ├─ Auto-scaling
  ├─ Load balancing
  ├─ Health checks
  ├─ Environment variables
  ├─ Logs & monitoring
  ├─ Secrets Manager
  └─ Custom domains
```

### Infrastructure
```
Google Cloud Platform (GCP)
  ├─ Cloud Run (backend)
  ├─ Cloud Storage (files)
  ├─ Cloud Logging (logs)
  ├─ Secret Manager (secrets)
  ├─ Cloud SQL (PostgreSQL ready)
  └─ Load Balancer

Vercel Edge Network (Frontend)
  ├─ Global CDN
  ├─ Edge functions
  ├─ Serverless functions
  └─ Analytics
```

---

## 🔐 SECURITY & SECRETS STACK

### Authentication
```
JWT (JSON Web Tokens)
  ├─ Algorithm: HS256
  ├─ Expiration: 24 hours
  ├─ Refresh logic: On 401
  └─ Validation: Signature check

Token Storage:
  ├─ localStorage (frontend)
  ├─ Environment variables (backend)
  └─ GitHub Secrets (CI/CD)
```

### Encryption
```
Fernet Cipher       (Symmetric encryption)
  ├─ Token encryption
  ├─ Credential storage
  └─ Secure token rotation

PBKDF2             (Password hashing)
  ├─ Algorithm: SHA256
  ├─ Iterations: 100,000
  └─ Salted hashes

RSA                (Asymmetric - optional)
  └─ For future OAuth
```

### Secrets Management
```
GitHub Secrets      (7 required)
  ├─ ANTHROPIC_API_KEY
  ├─ JWT_SECRET
  ├─ GCP_SA_KEY
  ├─ GCP_PROJECT_ID
  ├─ VERCEL_TOKEN
  ├─ VERCEL_ORG_ID
  └─ GITHUB_TOKEN

Google Secret Manager (Production)
  ├─ Encrypted storage
  ├─ Access control
  ├─ Audit logging
  └─ Automatic rotation (optional)

.env files          (Local development)
  ├─ .env.local (ignored)
  ├─ .env.example (template)
  └─ Never commit secrets
```

### Security Protocols
```
HTTPS/TLS 1.3       (Transport security)
CORS                (Cross-origin)
CSP                 (Content Security Policy)
HSTS                (Strict Transport Security)
Rate Limiting       (Token bucket)
Input Validation    (Pydantic)
SQL Injection       (Parameterized queries)
XSS Prevention      (Content encoding)
```

---

## 📊 MONITORING & LOGGING STACK

### Logging
```
Python logging      (Backend)
  ├─ Structured logs
  ├─ Request tracking
  ├─ Error logging
  └─ Debug mode

Console logging     (Frontend)
  ├─ Error tracking
  ├─ Network requests
  └─ State changes

Cloud Logging       (Google Cloud)
  ├─ Centralized logging
  ├─ Filtering
  ├─ Dashboards
  └─ Alerts
```

### Monitoring & Alerts
```
Health Checks       (Built-in)
  ├─ Frontend: GET /
  ├─ Backend: GET /api/v1/health
  └─ Detailed: GET /api/v1/health/detailed

Google Cloud Monitoring
  ├─ Metrics collection
  ├─ Custom dashboards
  ├─ Alert policies
  └─ Performance tracking

Error Tracking      (Sentry - ready to integrate)
  ├─ Error aggregation
  ├─ Stack traces
  ├─ Release tracking
  └─ Alerts
```

### Performance Monitoring
```
Lighthouse         (Frontend)
  ├─ Performance score
  ├─ Accessibility
  ├─ Best practices
  └─ SEO

APM Metrics        (Optional - ready to add)
  ├─ Request latency
  ├─ Database queries
  ├─ API response times
  └─ Resource usage
```

---

## 🛠️ DEVELOPMENT TOOLS & UTILITIES

### Development Environment
```
VSCode              (Recommended editor)
  ├─ Extensions (ESLint, Prettier, TypeScript)
  └─ Debug configurations

Terminal/CLI        (Command line)
  ├─ git
  ├─ npm
  ├─ python/pip
  └─ docker
```

### Package Management
```
npm                 (Frontend packages)
  ├─ package.json
  ├─ package-lock.json
  └─ Workspace protocol

pip                 (Backend packages)
  ├─ requirements.txt
  ├─ Virtual environment
  └─ Dependency pinning
```

### Build & Run Scripts
```
npm scripts:
  ├─ npm run dev (development)
  ├─ npm run build (production build)
  ├─ npm start (production run)
  ├─ npm test (run tests)
  ├─ npm run test:ci (CI tests)
  ├─ npm run test:coverage (coverage)
  └─ npm run format (prettier)

Python scripts:
  ├─ python -m uvicorn main:app (dev server)
  ├─ pytest (run tests)
  ├─ pytest --cov (coverage)
  └─ python scripts/*.py (utilities)
```

### Local Development
```
Docker Compose      (Local environment)
  ├─ Backend service
  ├─ Database
  ├─ Frontend service
  └─ Reverse proxy

Environment Setup:
  ├─ Python 3.11+ venv
  ├─ Node.js 18+ nvm
  ├─ Docker + Docker Compose
  └─ Git
```

---

## 📚 DOCUMENTATION TOOLS

### Documentation Generation
```
Markdown           (Content format)
  ├─ .md files
  ├─ GitHub Flavored Markdown
  └─ Code blocks with syntax highlighting

Documentation Files:
  ├─ API documentation
  ├─ Deployment guides
  ├─ Architecture diagrams
  ├─ Configuration guides
  ├─ Audit reports
  ├─ Status documents
  └─ Roadmaps
```

### Diagrams & Visualization
```
ASCII Diagrams     (Text-based)
Markdown Tables    (Data presentation)
Flow Diagrams      (Process flows)
Architecture Diagrams (System design)
```

---

## 📋 COMPLETE DEPENDENCY LIST

### Frontend (package.json)
```
Runtime Dependencies:
  • next@14.0.0+
  • react@18.0.0+
  • react-dom@18.0.0+
  • @tanstack/react-query@5.0.0+
  • typescript@5.0.0+
  • tailwindcss@3.4.0+

Dev Dependencies:
  • @types/node@^20.0.0
  • @types/react@^18.0.0
  • @types/react-dom@^18.0.0
  • @testing-library/react@14.1.0
  • @testing-library/jest-dom@6.1.5
  • jest@29.7.0
  • ts-jest@29.1.1
  • eslint@8.0.0+
  • prettier@3.0.0+
  • typescript-eslint@^6.0.0
```

### Backend (requirements.txt)
```
Core Framework:
  • fastapi==0.104.1
  • uvicorn==0.24.0
  • starlette==0.27.0
  • pydantic==2.5.0

Database:
  • sqlalchemy==2.0.23
  • alembic==1.13.0

Authentication & Security:
  • PyJWT==2.12.1
  • cryptography==41.0.7
  • python-multipart==0.0.6

API & HTTP:
  • aiohttp==3.9.1
  • requests==2.31.0

Integrations:
  • anthropic==0.25.0+
  • PyGithub==2.1.1
  • python-magic==0.4.27

Testing:
  • pytest==7.4.3
  • pytest-asyncio==0.21.1
  • pytest-cov==4.1.0
  • pytest-mock==3.12.0

Development:
  • python-dotenv==1.0.0
  • black==23.12.0
  • flake8==6.1.0
```

---

## 🎯 TECHNOLOGY DECISIONS & RATIONALE

### Why These Choices?

| Technology | Category | Why Chosen | Alternatives Considered |
|-----------|----------|-----------|------------------------|
| **Next.js 14** | Frontend | Built-in React, SSR, API routes | React + Create React App, Remix |
| **FastAPI** | Backend | Async, auto-docs, validation | Flask, Django, Starlette |
| **SQLAlchemy** | ORM | Flexible, mature, type-safe | Django ORM, Tortoise-ORM |
| **React Query** | State Mgmt | Powerful caching, synchronization | Redux, Zustand, Jotai |
| **Tailwind CSS** | Styling | Utility-first, performant | Material-UI, Chakra, styled-components |
| **PyJWT** | Authentication | Simple, lightweight, standard | OAuth, Okta, Auth0 |
| **Fernet** | Encryption | Symmetric, secure by default | RSA, AES (cryptography) |
| **Docker** | Deployment | Consistent, isolated environments | Systemd, Virtual Machines |
| **GitHub Actions** | CI/CD | Native to GitHub, free | Jenkins, GitLab CI, CircleCI |
| **Vercel** | Frontend Deploy | Next.js optimization, fast | Netlify, AWS Amplify, Heroku |
| **Cloud Run** | Backend Deploy | Serverless, auto-scaling, cost | EC2, App Engine, Lambda |

---

## 🔄 TECHNOLOGY INTEGRATION POINTS

### Frontend ↔ Backend
```
HTTP/REST API       (30+ endpoints)
  ├─ JSON payloads
  ├─ JWT authentication
  ├─ Error handling
  └─ SSE streaming

API Client:
  ├─ Fetch API
  ├─ Automatic token injection
  ├─ Retry logic
  └─ Error classification
```

### Backend ↔ Database
```
SQLAlchemy ORM      (Object-relational mapping)
  ├─ Connection pooling
  ├─ Query optimization
  ├─ Relationship management
  └─ Transaction support

SQL Generation:
  ├─ Parameterized queries
  ├─ SQL injection prevention
  └─ Cross-database compatibility
```

### Backend ↔ External APIs
```
Claude API          (AI responses)
  ├─ Streaming support
  ├─ Token counting
  └─ Error handling

GitHub API          (Repository operations)
  ├─ OAuth tokens
  ├─ Rate limiting
  └─ Data synchronization
```

### CI/CD Integration
```
GitHub ↔ GitHub Actions
  ├─ Webhook triggers
  ├─ Secret injection
  ├─ Status checks
  └─ Build artifacts

GitHub Actions ↔ Vercel
  ├─ Environment variables
  ├─ Deployment tokens
  └─ Preview deployments

GitHub Actions ↔ Google Cloud
  ├─ Service account auth
  ├─ Container registry push
  ├─ Cloud Run deployment
  └─ Health checks
```

---

## 📈 PERFORMANCE OPTIMIZATIONS

### Frontend
```
Code Splitting      (Next.js automatic)
Lazy Loading        (Dynamic imports)
Image Optimization  (Next.js Image component)
Caching Strategy    (React Query)
Bundle Analysis     (Webpack)
```

### Backend
```
Connection Pooling  (SQLAlchemy)
Query Optimization  (Indexed fields)
Async Processing    (asyncio)
Caching Layer       (Memory - extensible)
Compression         (gzip)
```

### Deployment
```
CDN Delivery        (Vercel Edge, Google Cloud CDN)
Auto-scaling        (Cloud Run, Vercel)
Load Balancing      (Cloud Load Balancer)
Regional Redundancy (Multi-region support)
```

---

## 🔮 FUTURE TECHNOLOGY ADDITIONS (Post-MVP)

### Phase 4.0+
```
Machine Learning:
  • scikit-learn (model training)
  • numpy/pandas (data processing)
  • embeddings (sentence-transformers)

Vector Database:
  • Pinecone or Weaviate
  • Vector search
  • Semantic matching
```

### Phase 5.0+
```
Knowledge Graphs:
  • Neo4j (graph database)
  • Graph algorithms
  • Relationship mapping

Advanced Features:
  • Celery (task queue)
  • Redis (caching)
  • Elasticsearch (full-text search)
```

### Phase 7.0+
```
Enterprise:
  • Kafka (event streaming)
  • Prometheus (metrics)
  • ELK Stack (logging)
  • Grafana (dashboards)
```

---

## 📋 TECHNOLOGY MAINTENANCE SCHEDULE

### Monthly Updates
- npm security updates
- pip dependency updates
- Docker base image updates

### Quarterly Reviews
- Major version updates
- Dependency audit
- Security scanning

### Annual Planning
- Technology stack review
- Performance benchmarking
- Cost optimization

---

## ✅ TECHNOLOGY STACK VERIFICATION

**Last Verified**: March 30, 2026

| Layer | Status | Version | Notes |
|-------|--------|---------|-------|
| Frontend | ✅ | Current | Next.js 14, React 18 |
| Backend | ✅ | Current | FastAPI 0.104+, Python 3.11 |
| Database | ✅ | Current | SQLAlchemy 2.0, SQLite/PostgreSQL |
| Testing | ✅ | Current | Jest 29, pytest 7.4 |
| CI/CD | ✅ | Current | GitHub Actions |
| Deployment | ✅ | Current | Vercel, Google Cloud Run |
| Security | ✅ | Current | PyJWT, Fernet, TLS 1.3 |
| Monitoring | ✅ | Current | Cloud Logging, Health Checks |

---

**Technology Stack Status**: ✅ **PRODUCTION READY**
**Compatibility**: ✅ **All components integrated**
**Security**: ✅ **Best practices implemented**
**Performance**: ✅ **Optimized and scalable**
