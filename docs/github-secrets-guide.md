# GitHub Actions Secrets Configuration Guide

## Overview
GitHub Actions requires secrets to be configured for the CI/CD pipeline to work. These are used in:
- `.github/workflows/ci.yml` - Testing and building
- `.github/workflows/deploy.yml` - Production deployment

## Required Secrets

### 1. **GCP_SA_KEY** (Required for Cloud Run deployment)
**Purpose**: Google Cloud Platform service account credentials
**Where to get it**:
1. Go to Google Cloud Console
2. Create a service account in your GCP project
3. Generate a JSON key for the service account
4. Copy the entire JSON content

**Value**: (JSON blob - entire service account key file)

---

### 2. **GCP_PROJECT_ID** (Required for Cloud Run)
**Purpose**: Google Cloud Project ID
**Where to get it**:
1. Go to https://console.cloud.google.com/
2. Look at the top of the page - it shows your project ID
3. Example: `my-pai-project-12345`

**Value**: Your GCP project ID

---

### 3. **ANTHROPIC_API_KEY** (Required for backend)
**Purpose**: Claude API key for AI functionality
**Where to get it**:
1. Go to https://console.anthropic.com/
2. Generate an API key
3. Starts with `sk-ant-`

**Value**: `sk-ant-xxxxxxxxxxxxx`

---

### 4. **GITHUB_TOKEN** (Optional, for GitHub integration)
**Purpose**: GitHub Personal Access Token for actions
**Where to get it**:
1. GitHub Settings → Developer settings → Personal access tokens
2. Create a "Classic" token with:
   - `repo` (full control of private repositories)
   - `read:user` (read user profile data)
3. Save the token immediately (can't view again)

**Value**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 5. **JWT_SECRET** (Required for backend)
**Purpose**: Secret key for JWT token signing
**How to generate**:
```bash
# Generate a random 32-character string
openssl rand -hex 16
# Or use Python
python3 -c "import secrets; print(secrets.token_hex(16))"
```

**Value**: Random 32-character hex string (e.g., `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

---

### 6. **VERCEL_TOKEN** (Required for frontend deployment)
**Purpose**: Vercel authentication token
**Where to get it**:
1. Go to https://vercel.com/account/tokens
2. Create a new token
3. Select "Full Account" scope
4. Copy immediately (can't view again)

**Value**: Token starting with `vercel_xxx`

---

### 7. **VERCEL_ORG_ID** (Required for frontend deployment)
**Purpose**: Vercel organization/team ID
**Where to get it**:
1. Go to https://vercel.com/account/settings/team (or personal account)
2. Look for "Team ID" in the settings
3. Or: `vercel whoami` in CLI

**Value**: Organization/team ID (hex string)

---

## How to Add Secrets to GitHub

### Via GitHub Web UI (Easy)
1. Go to your repository on GitHub
2. Click **Settings** (top right)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: Enter the secret name (e.g., `ANTHROPIC_API_KEY`)
6. Secret: Paste the value
7. Click **Add secret**
8. Repeat for each secret

### Via GitHub CLI (Fast)
```bash
# Install gh CLI if not already done
gh auth login

# Navigate to your repository
cd /path/to/PAI

# Add secrets
gh secret set ANTHROPIC_API_KEY --body "sk-ant-xxxxx"
gh secret set JWT_SECRET --body "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
gh secret set GCP_PROJECT_ID --body "my-project-12345"
gh secret set VERCEL_TOKEN --body "vercel_xxxxx"
gh secret set VERCEL_ORG_ID --body "team_xxxxx"
# For GCP_SA_KEY (JSON file):
gh secret set GCP_SA_KEY --body "$(cat /path/to/gcp-key.json)"
```

---

## Secrets Checklist

### Tier 1: Critical (Required for CI/CD to run)
- [ ] `ANTHROPIC_API_KEY` - Claude API key
- [ ] `JWT_SECRET` - Random 32-char string

### Tier 2: Backend Deployment (Required for Cloud Run)
- [ ] `GCP_SA_KEY` - GCP service account JSON
- [ ] `GCP_PROJECT_ID` - GCP project ID

### Tier 3: Frontend Deployment (Required for Vercel)
- [ ] `VERCEL_TOKEN` - Vercel auth token
- [ ] `VERCEL_ORG_ID` - Vercel org/team ID

### Tier 4: Optional (Nice to have)
- [ ] `GITHUB_TOKEN` - GitHub PAT (for GitHub integration)

---

## Verification

After adding secrets, you can verify they're set:
```bash
gh secret list
```

Or check in GitHub web UI: Settings → Secrets and variables → Actions

---

## Security Notes

⚠️ **IMPORTANT**:
- Never commit secrets to git
- Regenerate any secrets accidentally exposed
- Use strong random values (minimum 32 characters)
- Rotate secrets periodically (quarterly recommended)
- Each environment (dev, staging, prod) should have separate secrets
- GitHub masks secret values in logs automatically

---

## Troubleshooting

### CI/CD fails with "401 Unauthorized"
**Cause**: Missing or invalid ANTHROPIC_API_KEY
**Fix**: Verify API key is valid at console.anthropic.com

### Deployment fails to Cloud Run
**Cause**: Missing or invalid GCP_SA_KEY or GCP_PROJECT_ID
**Fix**:
1. Verify GCP project exists
2. Create service account with Cloud Run admin permissions
3. Regenerate JSON key

### Vercel deployment fails
**Cause**: Invalid VERCEL_TOKEN or VERCEL_ORG_ID
**Fix**:
1. Regenerate token at vercel.com/account/tokens
2. Get correct org/team ID from settings

---

## Next Steps After Adding Secrets

1. Add all 7 secrets to GitHub
2. Verify with `gh secret list`
3. Push a commit to main branch to trigger CI/CD
4. Check Actions tab to see if pipeline runs
5. Monitor deployment logs

---

## Reference: Where Secrets Are Used

**ci.yml**:
- `ANTHROPIC_API_KEY` - Backend environment setup
- `CODECOV_TOKEN` - Coverage reporting (optional)

**deploy.yml**:
- `GCP_SA_KEY` - Authenticate to Google Cloud
- `GCP_PROJECT_ID` - Deploy to correct GCP project
- `ANTHROPIC_API_KEY` - Backend environment
- `GITHUB_TOKEN` - GitHub API interactions
- `JWT_SECRET` - Backend JWT configuration
- `VERCEL_TOKEN` - Authenticate to Vercel
- `VERCEL_ORG_ID` - Deploy to correct Vercel org

---

## Cost Considerations

### Free Tier Limits
- **GitHub Actions**: 2,000 minutes/month free (public repos unlimited)
- **Google Cloud Run**: 2M invocations/month free, 360M seconds compute
- **Vercel**: Unlimited free deployments

### Potential Costs
- GCP Cloud Run: After free tier (~$0.40 per 1M requests)
- Vercel: Free for hobby usage
- GitHub Actions: Paid for private repos after free tier

---

**Status**: Ready to configure
**Time to complete**: ~10 minutes
**Difficulty**: Easy
