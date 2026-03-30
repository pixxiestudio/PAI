# Anthropic API Key OAuth Subscription Setup
**Configuration System**: Similar to Claude Code's `settings.json`

---

## 📋 Overview

Users get access to Anthropic API via **OAuth subscription** instead of managing their own API keys.

### How It Works:
1. **User clicks "Login with Anthropic"**
2. **OAuth redirect** → User authorizes your app
3. **Backend validates** subscription tier (free/pro/enterprise)
4. **Backend proxies** API requests using pool API key
5. **Usage tracked** per user for billing

---

## 🔧 Configuration File

**Location**: `backend/config/anthropic_oauth_config.json`

Similar to Claude Code's `settings.json`, this is the **source of truth** for OAuth settings.

### Key Sections:

#### 1. OAuth Provider
```json
"oauth_config": {
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "http://localhost:3000/api/auth/callback",
  "auth_url": "https://api.anthropic.com/oauth/authorize",
  "token_url": "https://api.anthropic.com/oauth/token"
}
```

#### 2. Subscription Tiers
```json
"subscription_tiers": {
  "free": {
    "monthly_requests": 1000,
    "max_tokens_per_request": 4096,
    "concurrent_requests": 5,
    "features": ["basic-chat", "simple-memory"],
    "cost": 0
  },
  "pro": {
    "monthly_requests": 50000,
    "max_tokens_per_request": 100000,
    "concurrent_requests": 50,
    "features": ["advanced-chat", "memory-system", "learning"],
    "cost": 29.99
  }
}
```

#### 3. API Strategy (Choose One)
```json
"api_key_management": {
  "strategy": "backend_proxy"
}
```

**Options**:
- `backend_proxy` - Single API key, backend proxies all requests
- `user_temporary_keys` - Issue temporary keys to each user
- `hybrid` - Free users use proxy, paid users get own keys

#### 4. Rate Limiting
```json
"rate_limiting": {
  "per_user": {
    "requests_per_minute": 60,
    "tokens_per_hour": 1000000
  }
}
```

#### 5. Billing
```json
"billing": {
  "provider": "stripe",
  "enabled": true,
  "webhook_url": "http://localhost:8000/api/v1/billing/webhook"
}
```

---

## 🚀 Setup Steps

### Step 1: Get OAuth Credentials from Anthropic

Contact Anthropic to register your OAuth app:
- Get `client_id` and `client_secret`
- Register redirect URI: `https://yourdomain.com/api/auth/callback`

### Step 2: Update Configuration (Like settings.json)

Edit `backend/config/anthropic_oauth_config.json`:

```json
{
  "anthropic_oauth": {
    "enabled": true,
    "oauth_config": {
      "client_id": "your_actual_client_id",
      "client_secret": "your_actual_client_secret",
      "redirect_uri": "https://yourdomain.com/api/auth/callback"
    },
    "billing": {
      "enabled": true,
      "provider": "stripe",
      "webhook_secret": "whsec_..."
    }
  }
}
```

### Step 3: Set Environment Variables

```bash
# For production (or sensitive values)
export ANTHROPIC_OAUTH_CLIENT_ID="your_client_id"
export ANTHROPIC_OAUTH_CLIENT_SECRET="your_client_secret"
export ANTHROPIC_API_KEY="your_backend_pool_key"  # For proxy strategy
export STRIPE_SECRET_KEY="sk_live_..."
```

### Step 4: Initialize Database Tables

```bash
python backend/scripts/init_db.py
# Creates: users, subscriptions, api_usage, billing_history tables
```

### Step 5: Start Backend

```bash
python -m uvicorn backend.api.main:app --reload
```

---

## 📡 API Endpoints

### Get OAuth Login URL
```bash
GET /api/v1/oauth/login
```

**Response**:
```json
{
  "login_url": "https://api.anthropic.com/oauth/authorize?client_id=...&redirect_uri=..."
}
```

### OAuth Callback (After User Authorizes)
```bash
POST /api/v1/oauth/callback
```

**Request**:
```json
{
  "code": "auth_code_from_anthropic"
}
```

**Response**:
```json
{
  "access_token": "token_xxx",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "user_123",
  "subscription_tier": "free"
}
```

### Get Subscription Status
```bash
GET /api/v1/oauth/subscription/{user_id}
```

**Response**:
```json
{
  "user_id": "user_123",
  "tier": "pro",
  "status": "active",
  "billing_cycle_start": "2026-03-01",
  "billing_cycle_end": "2026-04-01",
  "usage_this_month": {
    "requests": 2500,
    "tokens": 1250000
  },
  "limits": {
    "monthly_requests": 50000,
    "max_tokens_per_request": 100000
  },
  "features": ["advanced-chat", "memory-system", "learning"]
}
```

### Check Rate Limit
```bash
GET /api/v1/oauth/rate-limit/{user_id}
```

**Response**:
```json
{
  "allowed": true,
  "remaining_requests": 24750,
  "reset_at": "2026-04-01T00:00:00Z"
}
```

### Get Available Tiers
```bash
GET /api/v1/oauth/tiers
```

**Response**:
```json
{
  "tiers": {
    "free": {
      "name": "Free",
      "monthly_requests": 1000,
      "cost": 0,
      "features": ["basic-chat"]
    },
    "pro": {
      "name": "Pro",
      "monthly_requests": 50000,
      "cost": 29.99,
      "features": ["advanced-chat", "learning"]
    }
  }
}
```

---

## 🔐 Security

### API Key Encryption
Keys are encrypted before storing in database:

```python
from cryptography.fernet import Fernet

cipher = Fernet(encryption_key)
encrypted_key = cipher.encrypt(api_key.encode())
```

### Token Security
- Access tokens expire after 24 hours
- Refresh tokens valid for 30 days
- HTTPS required in production

### Rate Limiting
- Per-user: 60 requests/minute
- Global: 100 concurrent requests
- Queue timeout: 30 seconds

---

## 💰 Billing Integration (Stripe)

### Webhook Handler
```bash
POST /api/v1/billing/webhook
```

**Events Handled**:
- `payment_intent.succeeded` - Upgrade subscription
- `customer.subscription.deleted` - Downgrade/cancel
- `invoice.payment_failed` - Payment retry

### Usage Tracking
Every API call tracked:
```python
await service.track_usage(
    user_id="user_123",
    tokens_used=1500,
    cost=0.03
)
```

---

## 🛠️ Updating Configuration (Like settings.json)

### Python API
```python
from backend.core.anthropic_oauth_service import get_oauth_config

config = get_oauth_config()

# Read
print(config.client_id)
print(config.get_tier_limits(SubscriptionTier.PRO))

# Update in memory
config.update_config({"enabled": False})

# Save to disk
config.save_config()
```

### Via API
```bash
# Update config via admin endpoint (future)
PATCH /api/v1/admin/oauth/config
```

---

## 🧪 Testing

### Mock OAuth Flow
```python
import pytest
from backend.core.anthropic_oauth_service import get_oauth_service

async def test_oauth_flow():
    service = get_oauth_service()

    # Test token exchange
    auth_result = await service.authenticate_user("test_code")
    assert "access_token" in auth_result

    # Test subscription check
    sub_status = await service.get_subscription_status("user_123")
    assert sub_status["tier"] in ["free", "pro", "enterprise"]

    # Test rate limits
    rate_limit = await service.check_rate_limit("user_123", SubscriptionTier.FREE)
    assert rate_limit["allowed"] == True
```

---

## 📊 Database Schema

### users
```sql
CREATE TABLE users (
  id VARCHAR(255) PRIMARY KEY,
  oauth_id VARCHAR(255) UNIQUE,
  email VARCHAR(255),
  created_at TIMESTAMP,
  last_login TIMESTAMP
);
```

### subscriptions
```sql
CREATE TABLE subscriptions (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(id),
  tier VARCHAR(50),  -- free, pro, enterprise
  status VARCHAR(50),  -- active, canceled, overdue
  billing_cycle_start DATE,
  billing_cycle_end DATE,
  stripe_customer_id VARCHAR(255),
  stripe_subscription_id VARCHAR(255)
);
```

### api_usage
```sql
CREATE TABLE api_usage (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(id),
  requests_count INT,
  tokens_used INT,
  cost DECIMAL(10, 4),
  created_at TIMESTAMP
);
```

### billing_history
```sql
CREATE TABLE billing_history (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(id),
  invoice_amount DECIMAL(10, 2),
  invoice_date TIMESTAMP,
  status VARCHAR(50),  -- paid, failed, pending
  stripe_invoice_id VARCHAR(255)
);
```

---

## ✅ Checklist

- [ ] Get OAuth credentials from Anthropic
- [ ] Update `anthropic_oauth_config.json`
- [ ] Set environment variables
- [ ] Initialize database
- [ ] Test OAuth flow: `/api/v1/oauth/login`
- [ ] Test callback: `/api/v1/oauth/callback?code=...`
- [ ] Test subscription: `/api/v1/oauth/subscription/{user_id}`
- [ ] Set up Stripe webhook
- [ ] Deploy to production

---

## 🚀 Next Steps

1. **Contact Anthropic** for OAuth app registration
2. **Update config** with your credentials
3. **Test locally** with mock OAuth flow
4. **Deploy** to production
5. **Monitor usage** and billing

---

**Configuration is similar to Claude Code's settings.json** — edit it, save it, and the backend loads the new settings automatically!
