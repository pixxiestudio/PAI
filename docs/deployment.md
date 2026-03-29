# PAI Deployment Guide

This guide covers deploying PAI in different environments: local development, Docker, and production (Vercel + Cloud Run).

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [Backend Deployment (Cloud Run)](#backend-deployment-cloud-run)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites
- Node.js 18+ (`node --version`)
- Python 3.11+ (`python --version`)
- pip (`pip --version`)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/pixxiestudio/pai.git
   cd pai
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your credentials
   ```

3. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   # API will run at http://localhost:8000
   ```

4. **Frontend Setup** (in another terminal)
   ```bash
   cd frontend/web
   npm install
   npm run dev
   # Frontend will run at http://localhost:3000
   ```

5. **Access the application**
   - Dashboard: http://localhost:3000
   - API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Prerequisites
- Docker (`docker --version`)
- Docker Compose (`docker-compose --version`)

### Quick Start

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Build and run**
   ```bash
   docker-compose up -d
   ```

3. **Check status**
   ```bash
   docker-compose ps
   docker-compose logs -f api
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

### Docker Compose Services

- **api**: FastAPI backend on port 8000
- **redis**: Redis cache on port 6379

### Health Checks

The API includes a health check endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

### Persisting Data

- Database: `./pai.db` (SQLite, mounted as volume)
- Redis: `redis-data` (Docker volume)

### Custom Configuration

Override environment variables:
```bash
ANTHROPIC_API_KEY=sk-ant-xxx docker-compose up
```

---

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (https://vercel.com)
- GitHub repository connected

### Deployment Steps

1. **Connect GitHub Repository**
   - Visit https://vercel.com/new
   - Import your PAI GitHub repository
   - Select `frontend/web` as the root directory

2. **Configure Environment Variables**
   In Vercel dashboard, add:
   - `NEXT_PUBLIC_API_URL`: Production API URL (e.g., https://api.pai.example.com)

3. **Deploy**
   - Vercel will automatically detect Next.js
   - Build: `npm run build`
   - Install: `npm install`
   - Start: `npm start`

4. **Custom Domain**
   - Go to project settings → Domains
   - Add your custom domain (e.g., app.pai.example.com)

### Environment by Branch

- `main` → Production
- `develop` → Preview
- Feature branches → Preview deployments

### Build & Deployment Settings

```
Framework: Next.js
Build Command: npm run build
Output Directory: .next
Install Command: npm ci
Start Command: npm start
Node.js Version: 18.x
```

### Monitoring

- Performance: https://vercel.com/analytics
- Real-time logs: https://vercel.com/logs
- Deployment history: Project → Deployments

---

## Backend Deployment (Cloud Run)

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Project with enabled APIs:
  - Cloud Run
  - Artifact Registry
  - Cloud Build

### Deployment Steps

1. **Authenticate with Google Cloud**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build Docker Image**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pai-api:latest
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy pai-api \
     --image gcr.io/YOUR_PROJECT_ID/pai-api:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 1Gi \
     --cpu 1 \
     --timeout 3600 \
     --max-instances 100
   ```

4. **Set Environment Variables**
   ```bash
   gcloud run services update pai-api \
     --set-env-vars "ANTHROPIC_API_KEY=sk-ant-xxx" \
     --region us-central1
   ```

5. **View Deployment**
   ```bash
   gcloud run services describe pai-api --region us-central1
   ```

### Cloud SQL Database (Optional)

For production, use Cloud SQL instead of SQLite:

1. **Create Cloud SQL instance**
   ```bash
   gcloud sql instances create pai-db --database-version=POSTGRES_14
   ```

2. **Update CONNECTION_NAME**
   ```bash
   gcloud sql instances describe pai-db --format='value(connectionName)'
   ```

3. **Set environment variable**
   ```bash
   DATABASE_URL=postgresql+psycopg2://user:password@/pai_db?unix_sock=/cloudsql/CONNECTION_NAME
   ```

### Monitoring

- Logs: Google Cloud Console → Cloud Run → pai-api → Logs
- Metrics: Cloud Monitoring dashboard
- Alerts: Set up alerts for high error rates

---

## Environment Configuration

### Frontend Environment Variables

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Optional
NEXT_PUBLIC_DEBUG=false
```

### Backend Environment Variables

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///./pai.db
# OR for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/pai_db

# Authentication
JWT_SECRET=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Claude API
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-6

# GitHub (for GitHub integration)
GITHUB_TOKEN=ghp_...
GITHUB_API_URL=https://api.github.com

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

### Sensitive Variables

⚠️ **Never commit `.env` to git!**

Store secrets in:
- **Development**: `.env.local` (gitignored)
- **Vercel**: Environment variables in dashboard
- **Cloud Run**: Secret Manager integration
- **Docker**: Use `.env` file (not in git)

---

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'anthropic'`

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend API calls failing

**Error**: `CORS error` or `Failed to fetch`

**Solution**:
1. Check `NEXT_PUBLIC_API_URL` is set correctly
2. Verify backend is running: `curl http://localhost:8000/api/v1/health`
3. Check CORS headers in backend

### Docker container exits immediately

**Error**: Container stops after starting

**Solution**:
```bash
docker-compose logs api  # View error logs
docker-compose ps       # Check status
```

### Vercel build fails

**Error**: `Build failed`

**Solution**:
1. Check build logs in Vercel dashboard
2. Verify `npm run build` works locally
3. Check environment variables are set
4. Ensure working directory is set to `frontend/web`

### GitHub Actions CI fails

**Error**: Tests fail in CI but pass locally

**Solution**:
1. Check Node/Python versions match locally
2. Ensure test database is configured
3. Check for hardcoded paths (use relative paths)
4. Verify secrets are configured in GitHub Actions

---

## Scaling Considerations

### Load Balancing
- Vercel: Automatic geographic distribution
- Cloud Run: Automatic scaling based on traffic

### Database
- SQLite: Single-instance only (local/Docker)
- Cloud SQL: Multi-instance, automatic backups

### Caching
- Redis: Enabled in docker-compose
- Browser caching: Set via HTTP headers

### Monitoring
- Error tracking: Sentry integration (future)
- Performance: Vercel Analytics
- API: Cloud Run metrics

---

## Rollback Procedure

### Vercel
1. Go to Deployments
2. Click on previous deployment
3. Select "Promote to Production"

### Cloud Run
```bash
gcloud run deploy pai-api \
  --image gcr.io/YOUR_PROJECT_ID/pai-api:PREVIOUS_VERSION
```

### Docker
```bash
docker-compose down
# Check docker images for previous version
docker images | grep pai-api
# Run with previous image tag
```

---

## Support

For deployment issues:
1. Check logs: `docker-compose logs -f` or Vercel/Cloud Run dashboard
2. Verify environment variables: `docker-compose config`
3. Test connectivity: `curl http://localhost:8000/api/v1/health`
4. Review GitHub Issues: https://github.com/pixxiestudio/pai/issues
