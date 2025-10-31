# ReconAI API Documentation

**Version:** 1.0.0  
**Base URL:** `https://api.reconai.com` (Production) | `http://localhost:8000` (Development)  
**Protocol:** HTTPS (TLS 1.2+)  
**Authentication:** Firebase JWT Bearer Token  
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Rate Limiting](#rate-limiting)
4. [Pagination](#pagination)
5. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [Assets](#assets-endpoints)
   - [Analytics](#analytics-endpoints)
   - [Billing](#billing-endpoints)
   - [System](#system-endpoints)
6. [Webhooks](#webhooks)
7. [Code Examples](#code-examples)

---

## Authentication

### Overview

ReconAI uses **Firebase Authentication** with JWT bearer tokens. All protected endpoints require a valid Firebase ID token in the `Authorization` header.

### Token Format

```
Authorization: Bearer <firebase_id_token>
```

### Token Lifecycle

- **Validity:** 1 hour (automatically refreshed by Firebase SDK)
- **Refresh:** Client-side automatic renewal before expiration
- **Revocation:** Instant via Firebase Admin SDK

### Authentication Flow

```
1. User authenticates with Firebase (email/password or OAuth)
   ├─► Firebase returns ID token + refresh token
   └─► Client stores tokens in memory (not localStorage)

2. Client makes API request with ID token
   ├─► Include token in Authorization header
   └─► Backend validates token with Firebase Admin SDK

3. Backend extracts user info from token
   ├─► User ID (uid)
   ├─► Email address
   └─► Email verification status

4. Backend authorizes request
   ├─► Checks user exists in database
   ├─► Verifies workspace access
   └─► Validates subscription limits
```

### Example: Obtaining a Token

```javascript
// Frontend (React)
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();

// Use token in API requests
const response = await fetch("https://api.reconai.com/api/assets", {
  headers: {
    Authorization: `Bearer ${idToken}`,
    "Content-Type": "application/json",
  },
});
```

### Public Endpoints

The following endpoints do NOT require authentication:

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /openapi.json` - OpenAPI schema
- `POST /api/billing/webhook` - Stripe webhook (verified via signature)

---

## Error Handling

### Standard Error Response

All errors return a JSON object with the following structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-10-31T12:34:56.789Z",
  "path": "/api/assets/scan",
  "request_id": "req_abc123xyz"
}
```

### HTTP Status Codes

| Code    | Meaning               | Description                             |
| ------- | --------------------- | --------------------------------------- |
| **200** | OK                    | Request succeeded                       |
| **201** | Created               | Resource created successfully           |
| **202** | Accepted              | Request accepted (async processing)     |
| **400** | Bad Request           | Invalid input or malformed request      |
| **401** | Unauthorized          | Missing or invalid authentication token |
| **402** | Payment Required      | Subscription limit reached              |
| **403** | Forbidden             | Insufficient permissions                |
| **404** | Not Found             | Resource does not exist                 |
| **409** | Conflict              | Resource already exists                 |
| **422** | Unprocessable Entity  | Validation error                        |
| **429** | Too Many Requests     | Rate limit exceeded                     |
| **500** | Internal Server Error | Server-side error                       |
| **503** | Service Unavailable   | Temporary service disruption            |

### Common Error Codes

| Error Code            | HTTP Status | Description                          |
| --------------------- | ----------- | ------------------------------------ |
| `AUTH_TOKEN_MISSING`  | 401         | No Authorization header provided     |
| `AUTH_TOKEN_INVALID`  | 401         | Token is malformed or expired        |
| `AUTH_TOKEN_EXPIRED`  | 401         | Token has expired (refresh required) |
| `USER_NOT_FOUND`      | 404         | User does not exist in database      |
| `SCAN_LIMIT_REACHED`  | 402         | Monthly scan credits exhausted       |
| `API_LIMIT_REACHED`   | 402         | Monthly API call limit exceeded      |
| `RATE_LIMIT_EXCEEDED` | 429         | Too many requests in time window     |
| `RESOURCE_NOT_FOUND`  | 404         | Requested asset/scan not found       |
| `INVALID_DOMAIN`      | 400         | Domain format is invalid             |
| `SCAN_IN_PROGRESS`    | 409         | Scan already running for domain      |
| `PAYMENT_REQUIRED`    | 402         | Valid payment method required        |
| `VALIDATION_ERROR`    | 422         | Request data validation failed       |

### Example Error Response

```json
{
  "detail": "Manual scan limit reached (10 scans). Upgrade to Pro for unlimited manual scans and continuous monitoring.",
  "error_code": "SCAN_LIMIT_REACHED",
  "timestamp": "2025-10-31T14:23:45.678Z",
  "path": "/api/assets/scan",
  "request_id": "req_xyz789abc"
}
```

---

## Rate Limiting

### Limits by Plan

| Plan           | Requests/Hour | Requests/Day | Burst Limit |
| -------------- | ------------- | ------------ | ----------- |
| **Free**       | 100           | 1,000        | 10/minute   |
| **Pro**        | 1,000         | 10,000       | 50/minute   |
| **Enterprise** | 10,000        | 100,000      | 200/minute  |

### Rate Limit Headers

```
X-RateLimit-Limit: 100           # Total requests allowed in window
X-RateLimit-Remaining: 87        # Requests remaining
X-RateLimit-Reset: 1698768000    # Unix timestamp for reset
Retry-After: 3600                # Seconds until limit resets (when exceeded)
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Limit: 100 requests/hour. Try again in 45 minutes.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 2700,
  "limit": 100,
  "window": "1 hour"
}
```

---

## Pagination

### Query Parameters

All list endpoints support pagination via query parameters:

| Parameter | Type    | Default | Description                                 |
| --------- | ------- | ------- | ------------------------------------------- |
| `page`    | integer | 1       | Page number (1-indexed)                     |
| `limit`   | integer | 20      | Items per page (max: 100)                   |
| `sort`    | string  | varies  | Sort field (prefix with `-` for descending) |

### Pagination Response Format

```json
{
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 87,
    "items_per_page": 20,
    "has_next": true,
    "has_prev": false
  }
}
```

### Example Request

```bash
GET /api/assets?page=2&limit=50&sort=-risk_score
```

---

## API Endpoints

## Authentication Endpoints

### POST /api/auth/register

Create a new user account after Firebase signup.

**Authentication:** Required (Firebase token)  
**Rate Limit:** 10 requests/hour

#### Request

```http
POST /api/auth/register
Authorization: Bearer <firebase_id_token>
```

#### Response (201 Created)

```json
{
  "data": {
    "uid": "firebase_user_123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "photo_url": "https://example.com/photo.jpg",
    "plan": "free",
    "workspace_id": "firebase_user_123",
    "created_at": "2025-10-31T10:00:00Z"
  },
  "message": "User registered successfully"
}
```

#### Error Responses

- **409 Conflict:** User already exists

---

### POST /api/auth/login

Sync user data after Firebase login (idempotent).

**Authentication:** Required (Firebase token)

#### Request

```http
POST /api/auth/login
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "uid": "firebase_user_123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "plan": "pro",
    "last_login": "2025-10-31T10:00:00Z"
  },
  "message": "Login successful"
}
```

---

### GET /api/auth/me

Get current authenticated user profile.

**Authentication:** Required

#### Request

```http
GET /api/auth/me
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "uid": "firebase_user_123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "photo_url": "https://example.com/photo.jpg",
    "plan": "pro",
    "subscription_status": "active",
    "api_calls_used": 234,
    "api_calls_limit": 10000,
    "scan_credits_used": 12,
    "scan_credits_limit": 100,
    "usage_reset_at": "2025-11-30T00:00:00Z",
    "created_at": "2025-01-15T08:30:00Z"
  }
}
```

---

## Assets Endpoints

### POST /api/assets/scan

Start a new asset discovery scan for a domain.

**Authentication:** Required  
**Rate Limit:** Based on plan  
**Processing:** Asynchronous (returns 202)

#### Request

```http
POST /api/assets/scan
Authorization: Bearer <firebase_id_token>
Content-Type: application/json

{
  "domain": "example.com",
  "scan_subdomains": true
}
```

#### Request Body

| Field             | Type    | Required | Description                                 |
| ----------------- | ------- | -------- | ------------------------------------------- |
| `domain`          | string  | Yes      | Target domain (e.g., example.com)           |
| `scan_subdomains` | boolean | No       | Include subdomain discovery (default: true) |

#### Response (202 Accepted)

```json
{
  "scan_id": "scn_1698768000.123",
  "domain": "example.com",
  "status": "pending",
  "estimated_completion": "2-5 minutes",
  "message": "Scan started successfully. Check status at /api/assets/scans/{scan_id}"
}
```

#### Error Responses

- **400 Bad Request:** Invalid domain format
- **402 Payment Required:** Scan credit limit reached
- **409 Conflict:** Scan already in progress for this domain

---

### GET /api/assets

List all discovered assets with filtering and pagination.

**Authentication:** Required

#### Query Parameters

| Parameter    | Type    | Options                                                | Description            |
| ------------ | ------- | ------------------------------------------------------ | ---------------------- |
| `page`       | integer | 1+                                                     | Page number            |
| `limit`      | integer | 1-100                                                  | Items per page         |
| `risk_level` | string  | low, medium, high, critical                            | Filter by risk level   |
| `asset_type` | string  | domain, subdomain, ip_address                          | Filter by asset type   |
| `sort`       | string  | risk_score, -risk_score, discovered_at, -discovered_at | Sort order             |
| `search`     | string  | -                                                      | Search in asset values |

#### Request

```http
GET /api/assets?page=1&limit=20&risk_level=high&sort=-risk_score
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "asset_id": "ast_abc123",
      "asset_value": "api.example.com",
      "asset_type": "subdomain",
      "parent_domain": "example.com",
      "risk_score": 78,
      "risk_level": "high",
      "risk_factors": [
        "High-risk ports open (SSH, RDP)",
        "Missing security headers",
        "SSL certificate expires soon"
      ],
      "open_ports": [22, 80, 443, 3389],
      "technologies": ["Nginx/1.21.0", "PHP/7.4"],
      "ssl_cert_expiry": "2025-12-01T00:00:00Z",
      "ssl_cert_valid": true,
      "ssl_days_until_expiry": 31,
      "http_status": 200,
      "http_security_headers_score": 45,
      "breach_history_count": 0,
      "discovered_at": "2025-10-31T10:00:00Z",
      "last_scanned_at": "2025-10-31T14:00:00Z",
      "next_scan_at": "2025-11-01T14:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_items": 47,
    "items_per_page": 20,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### GET /api/assets/{asset_id}

Get detailed information for a specific asset.

**Authentication:** Required

#### Request

```http
GET /api/assets/ast_abc123
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "asset_id": "ast_abc123",
    "asset_value": "api.example.com",
    "asset_type": "subdomain",
    "parent_domain": "example.com",
    "risk_score": 78,
    "risk_level": "high",
    "risk_confidence": 0.89,
    "risk_factors": [
      {
        "category": "Port Exposure",
        "severity": "high",
        "description": "SSH (22) and RDP (3389) ports exposed to internet",
        "remediation": "Restrict access via firewall or VPN"
      },
      {
        "category": "Security Headers",
        "severity": "medium",
        "description": "Missing HSTS, CSP, and X-Frame-Options headers",
        "remediation": "Configure security headers in web server"
      }
    ],
    "open_ports": [22, 80, 443, 3389],
    "technologies": ["Nginx/1.21.0", "PHP/7.4"],
    "ssl_cert_info": {
      "issuer": "Let's Encrypt",
      "expiry": "2025-12-01T00:00:00Z",
      "valid": true,
      "days_until_expiry": 31,
      "is_self_signed": false
    },
    "dns_records": {
      "A": ["192.0.2.1"],
      "AAAA": ["2001:db8::1"],
      "MX": ["mail.example.com"],
      "TXT": ["v=spf1 include:_spf.google.com ~all"]
    },
    "http_info": {
      "status": 200,
      "server": "nginx/1.21.0",
      "security_headers": {
        "strict-transport-security": null,
        "content-security-policy": null,
        "x-frame-options": "DENY",
        "x-content-type-options": "nosniff"
      }
    },
    "breach_history": {
      "count": 0,
      "breaches": []
    },
    "discovered_at": "2025-10-31T10:00:00Z",
    "last_scanned_at": "2025-10-31T14:00:00Z",
    "next_scan_at": "2025-11-01T14:00:00Z"
  }
}
```

#### Error Responses

- **404 Not Found:** Asset does not exist or not owned by user

---

### DELETE /api/assets/{asset_id}

Delete a specific asset.

**Authentication:** Required

#### Request

```http
DELETE /api/assets/ast_abc123
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "message": "Asset deleted successfully",
  "asset_id": "ast_abc123"
}
```

---

### GET /api/assets/export

Export assets as CSV or JSON.

**Authentication:** Required

#### Query Parameters

| Parameter    | Type   | Required | Description                                   |
| ------------ | ------ | -------- | --------------------------------------------- |
| `format`     | string | No       | Export format: `csv` or `json` (default: csv) |
| `risk_level` | string | No       | Filter by risk level                          |

#### Request

```http
GET /api/assets/export?format=csv&risk_level=high
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

CSV format:

```
Content-Type: text/csv
Content-Disposition: attachment; filename="reconai_assets_2025-10-31.csv"

asset_value,asset_type,risk_score,risk_level,open_ports,discovered_at
api.example.com,subdomain,78,high,"22,80,443,3389",2025-10-31T10:00:00Z
...
```

---

### GET /api/assets/scans

List scan history with status tracking.

**Authentication:** Required

#### Query Parameters

| Parameter | Type    | Description                                 |
| --------- | ------- | ------------------------------------------- |
| `page`    | integer | Page number                                 |
| `limit`   | integer | Items per page                              |
| `status`  | string  | Filter: pending, running, completed, failed |

#### Request

```http
GET /api/assets/scans?status=completed&limit=10
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "scan_id": "scn_1698768000.123",
      "domain": "example.com",
      "scan_type": "full",
      "scan_status": "completed",
      "scan_subdomains": true,
      "assets_discovered": 47,
      "high_risk_assets": 8,
      "critical_risk_assets": 2,
      "created_at": "2025-10-31T10:00:00Z",
      "started_at": "2025-10-31T10:00:05Z",
      "completed_at": "2025-10-31T10:03:42Z",
      "duration_seconds": 217
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "total_items": 15
  }
}
```

---

### GET /api/assets/scans/{scan_id}

Get detailed scan status and results.

**Authentication:** Required

#### Request

```http
GET /api/assets/scans/scn_1698768000.123
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "scan_id": "scn_1698768000.123",
    "domain": "example.com",
    "scan_type": "full",
    "scan_status": "running",
    "scan_progress": 65,
    "scan_subdomains": true,
    "current_phase": "enrichment",
    "phases": {
      "discovery": "completed",
      "enrichment": "running",
      "risk_analysis": "pending"
    },
    "assets_discovered": 47,
    "created_at": "2025-10-31T10:00:00Z",
    "started_at": "2025-10-31T10:00:05Z",
    "estimated_completion": "2025-10-31T10:05:00Z"
  }
}
```

---

## Analytics Endpoints

### GET /api/analytics/dashboard

Get comprehensive dashboard statistics.

**Authentication:** Required

#### Request

```http
GET /api/analytics/dashboard
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "overall_risk_score": 67,
    "overall_risk_level": "high",
    "risk_score_change_7d": -5.2,
    "discovered_assets": 47,
    "assets_change_7d": 12.5,
    "total_scans": 8,
    "scans_change_7d": 33.3,
    "new_critical_alerts": 2,
    "open_vulnerabilities": 10,
    "assets_by_risk": {
      "low": 15,
      "medium": 22,
      "high": 8,
      "critical": 2
    }
  }
}
```

---

### GET /api/analytics/risk-trend

Get risk score trend over time.

**Authentication:** Required

#### Query Parameters

| Parameter | Type   | Options      | Description                |
| --------- | ------ | ------------ | -------------------------- |
| `period`  | string | 7d, 30d, 90d | Time period (default: 30d) |

#### Request

```http
GET /api/analytics/risk-trend?period=30d
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "date": "2025-10-01",
      "risk_score": 72,
      "asset_count": 35
    },
    {
      "date": "2025-10-08",
      "risk_score": 68,
      "asset_count": 38
    },
    {
      "date": "2025-10-15",
      "risk_score": 70,
      "asset_count": 42
    },
    {
      "date": "2025-10-22",
      "risk_score": 65,
      "asset_count": 45
    },
    {
      "date": "2025-10-29",
      "risk_score": 67,
      "asset_count": 47
    }
  ]
}
```

---

### GET /api/analytics/top-risky-assets

Get highest-risk assets.

**Authentication:** Required

#### Query Parameters

| Parameter | Type    | Description                                       |
| --------- | ------- | ------------------------------------------------- |
| `limit`   | integer | Number of assets to return (default: 10, max: 50) |

#### Request

```http
GET /api/analytics/top-risky-assets?limit=5
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "asset_id": "ast_xyz789",
      "asset_value": "admin.example.com",
      "asset_type": "subdomain",
      "risk_score": 92,
      "risk_level": "critical",
      "primary_risk": "Multiple critical vulnerabilities detected",
      "last_scanned_at": "2025-10-31T14:00:00Z"
    }
  ]
}
```

---

### GET /api/analytics/asset-distribution

Get asset distribution by type and risk level.

**Authentication:** Required

#### Request

```http
GET /api/analytics/asset-distribution
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "by_type": {
      "domain": 1,
      "subdomain": 42,
      "ip_address": 4
    },
    "by_risk": {
      "low": 15,
      "medium": 22,
      "high": 8,
      "critical": 2
    },
    "risk_by_type": {
      "subdomain": {
        "low": 14,
        "medium": 20,
        "high": 7,
        "critical": 1
      },
      "ip_address": {
        "low": 1,
        "medium": 2,
        "high": 1,
        "critical": 0
      }
    }
  }
}
```

---

## Billing Endpoints

### GET /api/billing/subscription

Get current subscription details.

**Authentication:** Required

#### Request

```http
GET /api/billing/subscription
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "plan": "pro",
    "subscription_status": "active",
    "stripe_customer_id": "cus_abc123",
    "stripe_subscription_id": "sub_xyz789",
    "current_period_end": 1701388800,
    "cancel_at_period_end": false,
    "payment_method": {
      "brand": "visa",
      "last4": "4242",
      "exp_month": 12,
      "exp_year": 2026
    }
  }
}
```

---

### POST /api/billing/create-checkout

Create Stripe checkout session for subscription upgrade.

**Authentication:** Required

#### Request

```http
POST /api/billing/create-checkout
Authorization: Bearer <firebase_id_token>
Content-Type: application/json

{
  "plan": "pro"
}
```

#### Request Body

| Field  | Type   | Required | Options         | Description                   |
| ------ | ------ | -------- | --------------- | ----------------------------- |
| `plan` | string | Yes      | pro, enterprise | Subscription plan to purchase |

#### Response (200 OK)

```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_abc123...",
  "session_id": "cs_test_abc123xyz"
}
```

---

### POST /api/billing/cancel-subscription

Cancel current subscription (at period end).

**Authentication:** Required

#### Request

```http
POST /api/billing/cancel-subscription
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "message": "Subscription will be canceled at period end",
  "cancel_at_period_end": true,
  "period_end": "2025-11-30T23:59:59Z"
}
```

---

### GET /api/billing/usage

Get current usage statistics for billing period.

**Authentication:** Required

#### Request

```http
GET /api/billing/usage
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": {
    "billing_period": {
      "start": "2025-10-01T00:00:00Z",
      "end": "2025-10-31T23:59:59Z"
    },
    "api_calls": {
      "used": 1234,
      "limit": 10000,
      "percentage": 12.34
    },
    "scan_credits": {
      "used": 23,
      "limit": 100,
      "percentage": 23.0
    },
    "usage_reset_at": "2025-11-01T00:00:00Z"
  }
}
```

---

### GET /api/billing/history

Get billing event history.

**Authentication:** Required

#### Query Parameters

| Parameter | Type    | Description              |
| --------- | ------- | ------------------------ |
| `page`    | integer | Page number              |
| `limit`   | integer | Items per page (max: 50) |

#### Request

```http
GET /api/billing/history?page=1&limit=20
Authorization: Bearer <firebase_id_token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "event_id": "evt_abc123",
      "event_type": "payment_succeeded",
      "amount": 9900,
      "currency": "usd",
      "description": "Pro Plan - Monthly",
      "status": "succeeded",
      "created_at": "2025-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 5
  }
}
```

---

## System Endpoints

### GET /health

Health check endpoint (public, no authentication required).

#### Request

```http
GET /health
```

#### Response (200 OK)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2025-10-31T14:30:00Z",
  "dependencies": {
    "database": "healthy",
    "firebase": "healthy",
    "ml_model": "loaded"
  }
}
```

---

### GET /docs

Interactive API documentation (Swagger UI) - public endpoint.

#### Request

```http
GET /docs
```

Returns HTML page with interactive API explorer.

---

### GET /openapi.json

OpenAPI 3.0 schema specification - public endpoint.

#### Request

```http
GET /openapi.json
```

Returns OpenAPI JSON schema.

---

## Webhooks

### Stripe Webhook

**Endpoint:** `POST /api/billing/webhook`  
**Authentication:** Stripe signature verification  
**Method:** POST

#### Webhook Events

| Event                           | Description           | Action               |
| ------------------------------- | --------------------- | -------------------- |
| `customer.subscription.created` | New subscription      | Update user plan     |
| `customer.subscription.updated` | Subscription changed  | Update user plan     |
| `customer.subscription.deleted` | Subscription canceled | Downgrade to free    |
| `invoice.payment_succeeded`     | Payment successful    | Record billing event |
| `invoice.payment_failed`        | Payment failed        | Send notification    |

#### Webhook Signature Verification

```python
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Verify webhook signature
try:
    event = stripe.Webhook.construct_event(
        payload=request_body,
        sig_header=request.headers.get("Stripe-Signature"),
        secret=webhook_secret
    )
except ValueError:
    # Invalid payload
    return 400
except stripe.error.SignatureVerificationError:
    # Invalid signature
    return 400
```

---

## Code Examples

### Python (requests)

```python
import requests

# Configuration
API_BASE_URL = "https://api.reconai.com"
FIREBASE_TOKEN = "your_firebase_id_token"

# Headers
headers = {
    "Authorization": f"Bearer {FIREBASE_TOKEN}",
    "Content-Type": "application/json"
}

# Start a scan
response = requests.post(
    f"{API_BASE_URL}/api/assets/scan",
    headers=headers,
    json={
        "domain": "example.com",
        "scan_subdomains": True
    }
)

scan_data = response.json()
scan_id = scan_data["scan_id"]
print(f"Scan started: {scan_id}")

# Check scan status
status_response = requests.get(
    f"{API_BASE_URL}/api/assets/scans/{scan_id}",
    headers=headers
)

print(status_response.json())
```

### JavaScript (Axios)

```javascript
import axios from "axios";

const API_BASE_URL = "https://api.reconai.com";
const firebaseToken = "your_firebase_id_token";

// Create API client
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Authorization: `Bearer ${firebaseToken}`,
    "Content-Type": "application/json",
  },
});

// Start a scan
async function startScan(domain) {
  try {
    const response = await apiClient.post("/api/assets/scan", {
      domain: domain,
      scan_subdomains: true,
    });

    console.log("Scan started:", response.data.scan_id);
    return response.data;
  } catch (error) {
    console.error("Scan failed:", error.response.data);
    throw error;
  }
}

// Get assets
async function getAssets(riskLevel = null) {
  try {
    const params = riskLevel ? { risk_level: riskLevel } : {};
    const response = await apiClient.get("/api/assets", { params });

    return response.data;
  } catch (error) {
    console.error("Failed to fetch assets:", error.response.data);
    throw error;
  }
}

// Usage
await startScan("example.com");
const assets = await getAssets("high");
```

### cURL

```bash
# Start a scan
curl -X POST https://api.reconai.com/api/assets/scan \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "scan_subdomains": true
  }'

# Get assets
curl -X GET "https://api.reconai.com/api/assets?risk_level=high&limit=10" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"

# Export assets as CSV
curl -X GET "https://api.reconai.com/api/assets/export?format=csv" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  --output assets.csv
```

---

## Best Practices

### Security

1. **Never expose tokens**: Store Firebase tokens securely, never in version control
2. **Use HTTPS**: Always use HTTPS in production
3. **Token refresh**: Implement automatic token refresh before expiration
4. **Error handling**: Check for 401 errors and prompt re-authentication

### Performance

1. **Pagination**: Use pagination for large result sets
2. **Filtering**: Apply filters server-side to reduce payload size
3. **Caching**: Cache responses when appropriate (respect `Cache-Control` headers)
4. **Retry logic**: Implement exponential backoff for rate-limited requests

### Rate Limiting

1. **Monitor headers**: Check `X-RateLimit-Remaining` before making requests
2. **Handle 429**: Respect `Retry-After` header when rate limited
3. **Batch operations**: Group multiple operations when possible
4. **Upgrade plan**: Consider upgrading for higher rate limits

---

## Support

- **Documentation:** [https://docs.reconai.com](https://docs.reconai.com)
- **API Status:** [https://status.reconai.com](https://status.reconai.com)
- **Support Email:** support@reconai.com
- **GitHub Issues:** [https://github.com/GaneshWiz07/RECON-AI/issues](https://github.com/GaneshWiz07/RECON-AI/issues)

---

**Last Updated:** October 31, 2025  
**API Version:** 1.0.0
