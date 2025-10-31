# ReconAI Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** October 31, 2025  
**Status:** Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [High-Level Architecture](#high-level-architecture)
4. [Component Architecture](#component-architecture)
5. [Data Architecture](#data-architecture)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Scalability & Performance](#scalability--performance)
9. [Machine Learning Pipeline](#machine-learning-pipeline)
10. [API Design](#api-design)
11. [Future Enhancements](#future-enhancements)

---

## System Overview

### Purpose

ReconAI is an enterprise-grade Open Source Intelligence (OSINT) platform designed for:

- **Continuous Attack Surface Monitoring**: Automated discovery and tracking of exposed digital assets
- **Threat Intelligence**: ML-powered risk assessment and vulnerability detection
- **Security Posture Management**: Real-time analytics and actionable insights
- **Compliance & Reporting**: Audit trails and exportable security reports

### Key Characteristics

| Attribute              | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| **Architecture Style** | Microservices-inspired, event-driven, async-first     |
| **Deployment Model**   | Cloud-native SaaS (multi-tenant)                      |
| **Scalability**        | Horizontal scaling with stateless API design          |
| **Availability**       | 99.9% uptime target with health monitoring            |
| **Security**           | Zero-trust, JWT-based auth, data encryption           |
| **Performance**        | Sub-second API responses, async background processing |

---

## Architecture Principles

### 1. Separation of Concerns

- **API Layer**: Request handling, validation, authentication
- **Business Logic**: Core domain logic, security detectors, collectors
- **Data Layer**: Database interactions, caching, persistence
- **Infrastructure**: Cross-cutting concerns (logging, monitoring, auth)

### 2. Asynchronous-First Design

- **Non-blocking I/O**: All database and external API calls use `async/await`
- **Background Tasks**: Long-running operations (scans) run asynchronously
- **Event-Driven**: Task queue for decoupled job processing

### 3. Stateless API Design

- **No Server-Side Sessions**: JWT tokens for authentication
- **Horizontal Scalability**: Any instance can handle any request
- **Load Balancer Friendly**: No sticky sessions required

### 4. Multi-Tenancy

- **Workspace Isolation**: Each user has a dedicated workspace (workspace_id = Firebase UID)
- **Data Partitioning**: All database queries filtered by `user_id`
- **Resource Quotas**: Per-user rate limiting and usage tracking

### 5. Security-First Approach

- **Defense in Depth**: Multiple layers of security controls
- **Zero Trust**: All requests authenticated and authorized
- **Data Encryption**: At-rest (MongoDB encryption) and in-transit (TLS 1.2+)
- **Audit Logging**: Comprehensive activity tracking

### 6. API-Driven Architecture

- **RESTful Design**: Standard HTTP methods and status codes
- **OpenAPI Documentation**: Auto-generated interactive docs
- **Versioning**: Path-based versioning for backward compatibility
- **Developer Experience**: Consistent responses, clear error messages

---

## High-Level Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ReconAI Platform                             │
│                                                                       │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────┐  │
│  │   End Users  │◄────────►│   Web App    │◄────────►│   API    │  │
│  │  (Security   │  HTTPS   │   (React)    │  REST/   │ (FastAPI)│  │
│  │   Teams)     │          │              │  JSON    │          │  │
│  └──────────────┘          └──────────────┘          └─────┬────┘  │
│                                                               │       │
│                              ┌────────────────────────────────┘       │
│                              │                                        │
│                ┌─────────────┼────────────────────┐                  │
│                │             │                    │                  │
│         ┌──────▼─────┐ ┌────▼────┐  ┌───────────▼──────┐           │
│         │  ML Engine │ │Database │  │   Task Queue     │           │
│         │ (sklearn)  │ │(MongoDB)│  │  (Async Jobs)    │           │
│         └────────────┘ └─────────┘  └──────────────────┘           │
│                                                                       │
└───────────────────────────┬───────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────▼──────┐ ┌───▼───┐  ┌──────▼──────┐
       │   Firebase  │ │Stripe │  │   OSINT     │
       │    Auth     │ │Billing│  │   APIs      │
       └─────────────┘ └───────┘  └─────────────┘
```

### Request Flow: Typical Scan Lifecycle

```
┌────────┐                                                      ┌──────────┐
│ Client │                                                      │ Firebase │
└───┬────┘                                                      └────┬─────┘
    │                                                                │
    │ 1. User Authenticates (Email/Password or OAuth)               │
    ├──────────────────────────────────────────────────────────────►│
    │◄─────────────────────────────────────────────────────────────┤
    │                   Firebase ID Token                           │
    │                                                                │
    │                                                                │
┌───▼────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 2. POST /api/assets/scan (with Firebase token)              │ │
│  │    - Middleware validates token with Firebase Admin SDK     │ │
│  │    - Extract user_id from token                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                           │                                        │
│  ┌────────────────────────▼──────────────────────────────────────┐ │
│  │ 3. Business Logic                                            │ │
│  │    - Check user subscription & scan credits                 │ │
│  │    - Validate domain format                                 │ │
│  │    - Create scan record in MongoDB                          │ │
│  │    - Decrement scan credits (if Free plan)                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                           │                                        │
│  ┌────────────────────────▼──────────────────────────────────────┐ │
│  │ 4. Async Task Spawning                                       │ │
│  │    - Create background task (asyncio.create_task)           │ │
│  │    - Return 202 Accepted immediately                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                           │                                        │
└───────────────────────────┼────────────────────────────────────────┘
                            │
    ┌───────────────────────▼───────────────────────────┐
    │     Background Task (Scan Worker)                 │
    │                                                    │
    │  5. Asset Discovery Phase                         │
    │     - DNS enumeration (subdomains, records)       │
    │     - Certificate transparency logs               │
    │     - IP resolution & geolocation                 │
    │     - Technology fingerprinting                   │
    │                                                    │
    │  6. Data Enrichment Phase                         │
    │     - SSL/TLS certificate analysis                │
    │     - HTTP security header inspection             │
    │     - Port scanning (service detection)           │
    │     - Breach history lookup (HaveIBeenPwned)      │
    │     - DNS misconfiguration detection              │
    │                                                    │
    │  7. ML Risk Scoring                               │
    │     - Extract 11+ features from asset data        │
    │     - Feature scaling (StandardScaler)            │
    │     - Model inference (Logistic Regression)       │
    │     - Risk classification (Low/Med/High/Crit)     │
    │                                                    │
    │  8. Persistence                                   │
    │     - Store assets in MongoDB                     │
    │     - Update scan status to "completed"           │
    │     - Trigger email alerts (if critical risks)    │
    │                                                    │
    └────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Backend Architecture (FastAPI)

```
backend/
│
├── app/
│   ├── main.py                    # Application entry point, ASGI app
│   │
│   ├── api/                       # API Layer (Presentation)
│   │   ├── routes/
│   │   │   ├── auth.py           # User registration, login, profile
│   │   │   ├── assets.py         # Asset CRUD, scanning, export
│   │   │   ├── analytics.py      # Dashboard stats, trends
│   │   │   └── billing.py        # Stripe integration, webhooks
│   │   └── __init__.py
│   │
│   ├── collectors/                # Data Collection Layer
│   │   ├── base_collector.py    # Abstract collector interface
│   │   ├── free_collector.py    # Free/open-source data sources
│   │   └── enrichers.py          # Data enrichment modules
│   │
│   ├── detectors/                 # Security Analysis Layer
│   │   ├── dns_misconfig_detector.py     # SPF, DMARC, zone checks
│   │   ├── ssl_inspector.py              # Certificate health
│   │   ├── web_header_analyzer.py        # HTTP security headers
│   │   ├── open_directory_detector.py    # Exposed directories
│   │   ├── cloud_bucket_checker.py       # S3/Azure/GCS exposure
│   │   └── security_file_checker.py      # Sensitive file detection
│   │
│   ├── ml/                        # Machine Learning Layer
│   │   ├── predict.py            # Model inference engine
│   │   ├── train_model.py        # Training pipeline
│   │   └── models/
│   │       ├── risk_model.joblib        # Trained model
│   │       └── scaler.joblib            # Feature scaler
│   │
│   ├── tasks/                     # Background Job Processing
│   │   ├── scan_worker.py        # Async scan execution
│   │   └── email_alerts.py       # Notification system
│   │
│   ├── core/                      # Infrastructure Layer
│   │   ├── database.py           # MongoDB connection & ODM
│   │   └── firebase.py           # Firebase Admin SDK wrapper
│   │
│   ├── middleware/                # Cross-Cutting Concerns
│   │   └── auth.py               # JWT validation middleware
│   │
│   ├── services/                  # External Service Integrations
│   │   └── email_service.py      # SendGrid email client
│   │
│   └── tests/                     # Test Suite
│       ├── test_auth.py
│       ├── test_assets.py
│       └── test_ml.py
│
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment variables template
```

### Component Responsibilities

#### 1. API Layer (`api/routes/`)

**Responsibility**: HTTP request handling, input validation, response formatting

- **Request Parsing**: Pydantic models for request/response validation
- **Authentication**: Middleware validates Firebase JWT tokens
- **Authorization**: Check user permissions and subscription limits
- **Error Handling**: Convert exceptions to HTTP error responses
- **Documentation**: OpenAPI schema generation via FastAPI decorators

**Example: Asset Scan Endpoint**

```python
@router.post("/scan", response_model=ScanResponse, status_code=202)
async def start_asset_scan(request: Request, scan_request: ScanRequest):
    """
    Start new asset discovery scan.

    1. Extract user from validated JWT
    2. Check scan credits
    3. Create scan record
    4. Spawn background task
    5. Return 202 Accepted
    """
    user = get_current_user(request)  # From middleware

    # Business logic delegation
    scan_id = await scan_service.initiate_scan(
        user_id=user["uid"],
        domain=scan_request.domain,
        scan_subdomains=scan_request.scan_subdomains
    )

    return {"scan_id": scan_id, "status": "pending"}
```

#### 2. Data Collection Layer (`collectors/`)

**Responsibility**: External data acquisition and normalization

- **Base Collector**: Abstract interface defining standard asset format
- **Free Collector**: DNS, WHOIS, Certificate Transparency (100% free)
- **Enrichers**: Additional data enhancement (breach history, geolocation)

**Data Flow**:

```
Raw External Data → Collector → Normalized Asset Dict → Database
```

**Standard Asset Format**:

```python
{
    "asset_value": "api.example.com",
    "asset_type": "subdomain",  # domain, subdomain, ip_address
    "parent_domain": "example.com",
    "open_ports": [80, 443],
    "technologies": ["Nginx/1.21.0"],
    "ssl_cert_expiry": "2026-05-15T00:00:00Z",
    "dns_records": {"A": ["192.0.2.1"], "MX": [...]},
    "discovered_via": "dns_enumeration",
    "raw_metadata": {...}
}
```

#### 3. Security Detectors (`detectors/`)

**Responsibility**: Vulnerability and misconfiguration detection

Each detector is a self-contained module that:

1. Takes asset data as input
2. Performs specific security checks
3. Returns findings with severity levels

**Example: DNS Misconfiguration Detector**

```python
async def detect_dns_misconfig(asset: dict) -> List[Finding]:
    findings = []

    # Check SPF record
    spf_record = await check_spf_record(asset["asset_value"])
    if not spf_record:
        findings.append({
            "category": "DNS Misconfiguration",
            "severity": "medium",
            "description": "Missing SPF record",
            "remediation": "Add SPF record to prevent email spoofing"
        })

    # Check DMARC
    dmarc_record = await check_dmarc_record(asset["parent_domain"])
    if not dmarc_record:
        findings.append({
            "category": "DNS Misconfiguration",
            "severity": "medium",
            "description": "Missing DMARC record",
            "remediation": "Configure DMARC for email authentication"
        })

    return findings
```

#### 4. Machine Learning Layer (`ml/`)

**Responsibility**: Risk prediction and model management

**Architecture**:

```
Asset Data → Feature Extraction → Feature Scaling → Model Inference → Risk Score
```

**Feature Engineering** (11+ features):

- `open_ports_count`: Number of exposed ports
- `has_ssh_open`: SSH port (22) exposed (boolean)
- `has_rdp_open`: RDP port (3389) exposed (boolean)
- `has_database_ports_open`: MySQL, PostgreSQL, MongoDB, Redis ports
- `ssl_days_until_expiry`: Days until certificate expires
- `ssl_cert_is_self_signed`: Self-signed certificate (boolean)
- `outdated_software_count`: Number of outdated technologies
- `breach_history_count`: Number of breaches found
- `http_security_headers_score`: 0-100 based on header presence
- `exposure_type_score`: 1-5 based on asset exposure level
- `dns_misconfig_count`: Number of DNS issues

**Model Details**:

- **Algorithm**: Logistic Regression (scikit-learn)
- **Output**: Risk probability (0.0 - 1.0) → Risk score (0-100)
- **Training Data**: Synthetic dataset + real-world patterns
- **Retraining**: On-demand via `train_model.py`

**Risk Classification**:

```python
if risk_score >= 86:
    risk_level = "critical"  # Immediate action required
elif risk_score >= 61:
    risk_level = "high"      # Urgent attention needed
elif risk_score >= 31:
    risk_level = "medium"    # Monitor closely
else:
    risk_level = "low"       # Acceptable risk
```

#### 5. Background Task Processing (`tasks/`)

**Responsibility**: Asynchronous job execution

**Scan Worker Lifecycle**:

```python
async def _execute_scan_async(scan_id: str, domain: str, user_id: str):
    """
    Async scan execution pipeline.

    1. Discovery Phase: Find assets
    2. Enrichment Phase: Gather details
    3. Analysis Phase: Run detectors
    4. ML Phase: Risk scoring
    5. Persistence: Save to database
    6. Notification: Alert user if critical
    """
    try:
        # Update scan status
        await update_scan_status(scan_id, "running")

        # Phase 1: Discovery
        raw_assets = await discover_assets(domain)

        # Phase 2: Enrichment
        enriched_assets = []
        for asset in raw_assets:
            enriched = await enrich_asset(asset)
            enriched_assets.append(enriched)

        # Phase 3: Security Analysis
        for asset in enriched_assets:
            findings = await run_all_detectors(asset)
            asset["security_findings"] = findings

        # Phase 4: ML Risk Scoring
        for asset in enriched_assets:
            risk_data = await predict_risk(asset)
            asset["risk_score"] = risk_data["risk_score"]
            asset["risk_level"] = risk_data["risk_level"]

        # Phase 5: Save to database
        await save_assets(enriched_assets, user_id)

        # Phase 6: Complete scan
        await update_scan_status(scan_id, "completed")

        # Phase 7: Send alerts
        critical_assets = [a for a in enriched_assets if a["risk_level"] == "critical"]
        if critical_assets:
            await send_email_alert(user_id, critical_assets)

    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        await update_scan_status(scan_id, "failed", error=str(e))
```

#### 6. Infrastructure Layer (`core/`)

**Responsibility**: Database, authentication, external service clients

**Database Module** (`core/database.py`):

- MongoDB connection pooling via Motor (async driver)
- Collection getters with type hints
- Health check functionality
- Index management

```python
# Singleton database instance
_db_client: Optional[AsyncIOMotorClient] = None

async def connect_to_mongodb():
    """Initialize MongoDB connection with retry logic."""
    global _db_client
    _db_client = AsyncIOMotorClient(MONGO_URI, maxPoolSize=10)
    await _db_client.admin.command('ping')
    logger.info("Connected to MongoDB")

def get_collection(name: str):
    """Get collection by name with type safety."""
    return _db_client[DB_NAME][name]
```

**Firebase Module** (`core/firebase.py`):

- Firebase Admin SDK initialization
- JWT token verification
- User info extraction

```python
async def verify_firebase_token(token: str) -> dict:
    """
    Verify Firebase ID token and extract user info.

    Returns:
        dict: {"uid": "...", "email": "...", "name": "..."}

    Raises:
        HTTPException: 401 if token invalid
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
```

---

## Data Architecture

### Database Schema (MongoDB)

#### Collections Overview

| Collection       | Purpose                       | Size Estimate | Indexes                                                           |
| ---------------- | ----------------------------- | ------------- | ----------------------------------------------------------------- |
| `users`          | User profiles, subscriptions  | ~10KB/doc     | uid (unique), email (unique)                                      |
| `assets`         | Discovered assets, risk data  | ~5KB/doc      | user_id + asset_value (compound unique), risk_score, next_scan_at |
| `scans`          | Scan history, status tracking | ~2KB/doc      | user_id + created_at, scan_status                                 |
| `billing_events` | Payment history               | ~1KB/doc      | user_id + created_at, stripe_event_id (unique)                    |
| `api_usage_logs` | API call tracking (TTL)       | ~500B/doc     | user_id + timestamp, timestamp (TTL: 90 days)                     |

#### Schema: Users Collection

```javascript
{
  "_id": ObjectId("..."),
  "uid": "firebase_user_abc123",              // Firebase User ID (unique)
  "email": "user@example.com",                // Email address (unique)
  "display_name": "John Doe",                 // Display name
  "photo_url": "https://...",                 // Profile photo URL
  "email_verified": true,                     // Email verification status

  // Workspace (1:1 relationship with user)
  "workspace_id": "firebase_user_abc123",     // Same as uid

  // Subscription & Billing
  "plan": "pro",                              // free, pro, enterprise
  "subscription_status": "active",            // active, canceled, past_due
  "stripe_customer_id": "cus_xyz789",         // Stripe customer ID
  "stripe_subscription_id": "sub_abc123",     // Stripe subscription ID

  // Usage Tracking
  "api_calls_used": 1234,                     // API calls in current period
  "api_calls_limit": 10000,                   // API calls limit per period
  "scan_credits_used": 23,                    // Scans in current period
  "scan_credits_limit": 100,                  // Scan limit per period
  "usage_reset_at": ISODate("2025-11-01"),    // Next reset date

  // Timestamps
  "created_at": ISODate("2025-01-15T08:30:00Z"),
  "last_login": ISODate("2025-10-31T10:00:00Z"),
  "updated_at": ISODate("2025-10-31T10:00:00Z")
}
```

**Indexes**:

```javascript
db.users.createIndex({ uid: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ stripe_customer_id: 1 });
```

#### Schema: Assets Collection

```javascript
{
  "_id": ObjectId("..."),
  "asset_id": "ast_xyz789abc123",             // Unique asset identifier
  "user_id": "firebase_user_abc123",          // Owner (Firebase UID)
  "workspace_id": "firebase_user_abc123",     // Workspace (same as user_id)

  // Asset Identity
  "asset_value": "api.example.com",           // Domain, subdomain, or IP
  "asset_type": "subdomain",                  // domain, subdomain, ip_address
  "parent_domain": "example.com",             // Root domain

  // Risk Assessment (ML-generated)
  "risk_score": 78,                           // 0-100 (ML model output)
  "risk_level": "high",                       // low, medium, high, critical
  "risk_confidence": 0.89,                    // Model confidence (0.0-1.0)
  "risk_factors": [                           // Human-readable risk reasons
    {
      "category": "Port Exposure",
      "severity": "high",
      "description": "SSH and RDP ports exposed",
      "remediation": "Restrict access via firewall"
    }
  ],

  // Network Information
  "open_ports": [22, 80, 443, 3389],          // Detected open ports
  "ip_addresses": ["192.0.2.1"],             // Resolved IP addresses
  "ip_geolocation": {
    "country": "US",
    "city": "San Francisco",
    "latitude": 37.7749,
    "longitude": -122.4194
  },

  // Technology Stack
  "technologies": [                           // Detected software/frameworks
    "Nginx/1.21.0",
    "PHP/7.4",
    "WordPress/5.8"
  ],
  "server_header": "nginx/1.21.0",

  // SSL/TLS Certificate
  "ssl_cert_info": {
    "issuer": "Let's Encrypt",
    "subject": "api.example.com",
    "expiry": ISODate("2025-12-01"),
    "valid": true,
    "is_self_signed": false,
    "days_until_expiry": 31
  },

  // DNS Records
  "dns_records": {
    "A": ["192.0.2.1"],
    "AAAA": ["2001:db8::1"],
    "MX": ["mail.example.com"],
    "TXT": ["v=spf1 include:_spf.google.com ~all"],
    "NS": ["ns1.example.com", "ns2.example.com"]
  },

  // HTTP Information
  "http_status": 200,                         // Last HTTP status code
  "http_redirect_chain": [],                  // Redirect history
  "http_security_headers": {                  // Security header presence
    "strict-transport-security": null,
    "content-security-policy": null,
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff"
  },
  "http_security_headers_score": 45,          // 0-100 based on headers

  // Breach Intelligence
  "breach_history": {
    "count": 2,
    "breaches": [
      {
        "name": "Example Breach 2023",
        "date": "2023-05-15",
        "compromised_data": ["Emails", "Passwords"]
      }
    ]
  },

  // Security Findings (from detectors)
  "security_findings": [
    {
      "detector": "dns_misconfig_detector",
      "category": "DNS Misconfiguration",
      "severity": "medium",
      "description": "Missing DMARC record",
      "remediation": "Configure DMARC policy"
    }
  ],

  // Discovery Metadata
  "discovered_via": "dns_enumeration",        // Collection method
  "discovered_at": ISODate("2025-10-31T10:00:00Z"),
  "last_scanned_at": ISODate("2025-10-31T14:00:00Z"),
  "next_scan_at": ISODate("2025-11-01T14:00:00Z"),  // For automated rescans
  "scan_frequency_hours": 24,                 // Rescan interval

  // Timestamps
  "created_at": ISODate("2025-10-31T10:00:00Z"),
  "updated_at": ISODate("2025-10-31T14:00:00Z")
}
```

**Indexes**:

```javascript
// Prevent duplicate assets per user
db.assets.createIndex({ user_id: 1, asset_value: 1 }, { unique: true });

// Query by risk level
db.assets.createIndex({ user_id: 1, risk_level: 1 });

// Sort by risk score
db.assets.createIndex({ user_id: 1, risk_score: -1 });

// Automated rescan scheduling
db.assets.createIndex({ next_scan_at: 1 });

// Search by asset type
db.assets.createIndex({ user_id: 1, asset_type: 1 });
```

#### Schema: Scans Collection

```javascript
{
  "_id": ObjectId("..."),
  "scan_id": "scn_1698768000.123",            // Unique scan identifier
  "user_id": "firebase_user_abc123",          // Owner
  "workspace_id": "firebase_user_abc123",     // Workspace

  // Scan Configuration
  "domain": "example.com",                    // Target domain
  "scan_type": "full",                        // full, quick, rescan
  "scan_subdomains": true,                    // Include subdomains

  // Scan Status
  "scan_status": "completed",                 // pending, running, completed, failed
  "scan_progress": 100,                       // 0-100 percentage
  "current_phase": "completed",               // discovery, enrichment, analysis, completed

  // Scan Results
  "assets_discovered": 47,                    // Total assets found
  "high_risk_assets": 8,                      // High-risk asset count
  "critical_risk_assets": 2,                  // Critical-risk asset count

  // Error Handling
  "error_message": null,                      // Error details if failed
  "retry_count": 0,                           // Number of retries

  // Timestamps
  "created_at": ISODate("2025-10-31T10:00:00Z"),     // Scan requested
  "started_at": ISODate("2025-10-31T10:00:05Z"),     // Execution started
  "completed_at": ISODate("2025-10-31T10:03:42Z"),   // Execution finished
  "duration_seconds": 217                     // Total execution time
}
```

**Indexes**:

```javascript
db.scans.createIndex({ user_id: 1, created_at: -1 });
db.scans.createIndex({ scan_status: 1 });
db.scans.createIndex({ scan_id: 1 }, { unique: true });
```

### Data Flow Diagrams

#### Write Path: New Asset Discovery

```
User Request (POST /api/assets/scan)
    │
    ▼
Validate JWT & Check Credits
    │
    ▼
Create Scan Record (MongoDB)
    │
    ▼
Spawn Background Task
    │
    ├──► Return 202 Accepted to user
    │
    ▼
Background Task Execution:
    │
    ├──► Phase 1: DNS enumeration (external APIs)
    ├──► Phase 2: SSL/TLS checks (external APIs)
    ├──► Phase 3: HTTP analysis (external APIs)
    ├──► Phase 4: Breach lookup (HaveIBeenPwned API)
    ├──► Phase 5: ML risk scoring (in-memory model)
    │
    ▼
Batch Insert Assets (MongoDB with upsert)
    │
    ▼
Update Scan Status (MongoDB)
    │
    ▼
Send Email Alert (if critical risks via SendGrid)
```

#### Read Path: Dashboard Analytics

```
User Request (GET /api/analytics/dashboard)
    │
    ▼
Validate JWT
    │
    ▼
MongoDB Aggregation Pipeline:
    │
    ├──► Count total assets (filtered by user_id)
    ├──► Group by risk_level (aggregation)
    ├──► Calculate average risk_score (aggregation)
    ├──► Count scans (filtered by user_id)
    │
    ▼
Format Response
    │
    ▼
Return JSON to client
```

---

## Security Architecture

### Authentication & Authorization

#### Authentication Flow

```
┌──────────┐                                    ┌──────────┐
│  Client  │                                    │ Firebase │
└────┬─────┘                                    └────┬─────┘
     │                                                │
     │ 1. User enters email/password                 │
     ├───────────────────────────────────────────────►
     │                                                │
     │ 2. Firebase verifies credentials              │
     │                                                │
     │◄───────────────────────────────────────────────┤
     │       Firebase ID Token (JWT)                 │
     │                                                │
     │                                                │
     │ 3. Client includes token in API request       │
     │    Authorization: Bearer <token>              │
     ├──────────────────────────────────────────────────────►
     │                                                │       │
     │                                                │   ┌───▼────┐
     │                                                │   │FastAPI │
     │                                                │   └───┬────┘
     │                                                │       │
     │                                                │       │ 4. Middleware
     │                                                │       │    extracts token
     │                                                │       │
     │                                                │◄──────┤
     │                                                │   5. Verify token
     │                                                │
     │                                                ├──────►
     │                                                │   6. Return user info
     │                                                │
     │                                                │       │
     │                                                │       │ 7. Attach user
     │                                                │       │    to request
     │                                                │       │
     │                                                │       │ 8. Route handler
     │                                                │       │    accesses user
     │                                                │       │
     │◄────────────────────────────────────────────────────────
     │           API Response                         │
```

#### JWT Token Structure

```json
{
  "iss": "https://securetoken.google.com/reconai-prod",
  "aud": "reconai-prod",
  "auth_time": 1698768000,
  "user_id": "firebase_user_abc123",
  "sub": "firebase_user_abc123",
  "iat": 1698768000,
  "exp": 1698771600,
  "email": "user@example.com",
  "email_verified": true,
  "firebase": {
    "identities": {
      "email": ["user@example.com"]
    },
    "sign_in_provider": "password"
  }
}
```

#### Authorization Middleware

```python
# middleware/auth.py

async def firebase_auth_middleware(request: Request, call_next):
    """
    Middleware to validate Firebase JWT tokens.

    1. Extract token from Authorization header
    2. Verify token with Firebase Admin SDK
    3. Attach user info to request state
    4. Proceed to route handler
    """
    # Skip auth for public routes
    if request.url.path in PUBLIC_ROUTES:
        return await call_next(request)

    # Extract token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No authentication token")

    token = auth_header.split("Bearer ", 1)[1]

    # Verify with Firebase
    try:
        user_info = await verify_firebase_token(token)
        request.state.user = user_info  # Attach to request
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)
```

### Data Security

#### Encryption

| Layer               | Method                | Details                                |
| ------------------- | --------------------- | -------------------------------------- |
| **In-Transit**      | TLS 1.2+              | All API traffic over HTTPS             |
| **At-Rest**         | MongoDB Encryption    | Database-level encryption (Atlas)      |
| **Application**     | Environment Variables | Secrets stored in `.env` (not in code) |
| **Firebase Tokens** | JWT Signature         | RSA-256 signed by Firebase             |
| **Stripe Webhooks** | HMAC Signature        | Webhook signature verification         |

#### Multi-Tenancy Isolation

**Data Isolation Strategy**:

- Every database query MUST filter by `user_id`
- `workspace_id` always equals `user_id` (1:1 relationship)
- No cross-user data access possible

**Example Query**:

```python
# CORRECT: Filtered by user_id
assets = await assets_collection.find({"user_id": user_id}).to_list(length=100)

# WRONG: Would leak data across users (NEVER DO THIS)
assets = await assets_collection.find({}).to_list(length=100)
```

**Database-Level Enforcement**:

- Compound unique indexes include `user_id`
- Application-level checks in all route handlers
- Middleware ensures `user_id` is always from verified JWT

#### Input Validation

**Pydantic Models** for all request bodies:

```python
from pydantic import BaseModel, validator

class ScanRequest(BaseModel):
    domain: str
    scan_subdomains: bool = True

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format and prevent injection."""
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$', v):
            raise ValueError('Invalid domain format')
        if len(v) > 253:
            raise ValueError('Domain too long')
        return v.lower()
```

### Rate Limiting & Abuse Prevention

**Per-User Rate Limits**:

```python
# Stored in user document
{
  "api_calls_used": 1234,
  "api_calls_limit": 10000,
  "usage_reset_at": "2025-11-01T00:00:00Z"
}

# Check before processing request
if user["api_calls_used"] >= user["api_calls_limit"]:
    raise HTTPException(status_code=402, detail="API limit reached")

# Increment after successful request
await users.update_one(
    {"uid": user_id},
    {"$inc": {"api_calls_used": 1}}
)
```

**IP-Based Rate Limiting** (future enhancement):

- Redis-based sliding window counter
- 100 requests/minute per IP (unauthenticated)

---

## Deployment Architecture

### Production Deployment (Render + Netlify)

```
┌────────────────────────────────────────────────────────────┐
│                     Internet (HTTPS)                        │
└────────────────────┬───────────────────┬───────────────────┘
                     │                   │
         ┌───────────▼──────────┐   ┌────▼────────────┐
         │   Netlify CDN        │   │  Render.com     │
         │   (Frontend)         │   │  (Backend API)  │
         │                      │   │                 │
         │  - React SPA         │   │  - Docker       │
         │  - TailwindCSS       │   │  - FastAPI      │
         │  - Global CDN        │   │  - Auto-scaling │
         │  - SSL Certs         │   │  - Health checks│
         └──────────────────────┘   └────┬────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
            ┌───────▼────────┐   ┌────────▼───────┐   ┌────────▼──────┐
            │  MongoDB Atlas │   │    Firebase    │   │    Stripe     │
            │   (Database)   │   │  (Auth Service)│   │   (Billing)   │
            │                │   │                │   │               │
            │  - M10 Cluster │   │  - Auth tokens │   │  - Payments   │
            │  - Multi-AZ    │   │  - User mgmt   │   │  - Webhooks   │
            │  - Auto-backup │   │                │   │               │
            └────────────────┘   └────────────────┘   └───────────────┘
```

### Container Architecture (Docker)

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./backend/*.py ./

# Train ML model
RUN python -m app.ml.train_model

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

**Environment Variables** (`.env`):

```bash
# Application
ENVIRONMENT=production
PORT=8000
CORS_ORIGINS=https://reconai.com

# Database
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/reconai

# Firebase Admin SDK
FIREBASE_PROJECT_ID=reconai-prod
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@reconai-prod.iam.gserviceaccount.com

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_ENTERPRISE=price_...

# Email
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=noreply@reconai.com

# External APIs (Optional)
CENSYS_API_ID=...
CENSYS_API_SECRET=...
```

---

## Scalability & Performance

### Horizontal Scaling

**Stateless API Design**:

- No server-side sessions
- JWT tokens carry all auth info
- Any instance can handle any request

**Load Balancing** (Render):

```
User Request → Render Load Balancer → [Instance 1, Instance 2, Instance 3]
```

**Database Connection Pooling**:

```python
# Motor connection pool (max 10 connections per instance)
client = AsyncIOMotorClient(MONGO_URI, maxPoolSize=10)
```

### Performance Optimizations

#### 1. Database Indexes

All high-frequency queries have supporting indexes:

```javascript
// User lookup by Firebase UID (O(1) with index)
db.users.find({ uid: "..." });

// Asset listing with pagination and sorting
db.assets.find({ user_id: "..." }).sort({ risk_score: -1 }).limit(20);

// Compound index supports both filter and sort
db.assets.createIndex({ user_id: 1, risk_score: -1 });
```

#### 2. Async/Await Throughout

All I/O operations are non-blocking:

```python
# Multiple external API calls in parallel
results = await asyncio.gather(
    check_dns_records(domain),
    check_ssl_certificate(domain),
    check_http_headers(domain),
    lookup_breach_history(domain)
)
```

#### 3. Pagination

All list endpoints return paginated results:

```python
# Limit result set size
assets = await collection.find(query).skip(skip).limit(limit).to_list(length=limit)
```

#### 4. Selective Field Projection

Only fetch needed fields:

```python
# Only return necessary fields
users = await collection.find(
    {"uid": user_id},
    {"_id": 0, "uid": 1, "email": 1, "plan": 1}
)
```

### Monitoring & Observability

**Health Check Endpoint**:

```python
@app.get("/health")
async def health_check():
    """
    Check system health.

    - API: Always healthy (this endpoint responding)
    - Database: Ping MongoDB
    - ML Model: Check if loaded
    """
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "dependencies": {}
    }

    # Check MongoDB
    try:
        await db_client.admin.command('ping')
        health_status["dependencies"]["database"] = "healthy"
    except:
        health_status["dependencies"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check ML model
    model, scaler = load_model()
    if model and scaler:
        health_status["dependencies"]["ml_model"] = "loaded"
    else:
        health_status["dependencies"]["ml_model"] = "not_loaded"

    return health_status
```

**Structured Logging**:

```python
import logging

logger = logging.getLogger(__name__)
logger.info(
    "Scan completed",
    extra={
        "scan_id": scan_id,
        "user_id": user_id,
        "assets_found": len(assets),
        "duration_seconds": duration
    }
)
```

---

## Machine Learning Pipeline

### Training Pipeline

**Synthetic Dataset Generation**:

```python
# app/ml/train_model.py

def generate_training_data(n_samples=1000):
    """
    Generate synthetic training data based on security patterns.

    High-risk indicators:
    - SSH/RDP ports open
    - Expired/self-signed SSL
    - Missing security headers
    - Breach history
    - Many open ports
    """
    X = []  # Features
    y = []  # Labels (0=low risk, 1=high risk)

    for _ in range(n_samples):
        features = {
            "open_ports_count": random.randint(0, 20),
            "has_ssh_open": random.choice([0, 1]),
            "has_rdp_open": random.choice([0, 1]),
            # ... 11 total features
        }

        # Risk scoring logic
        risk_score = calculate_risk_score(features)
        label = 1 if risk_score >= 60 else 0

        X.append(list(features.values()))
        y.append(label)

    return np.array(X), np.array(y)
```

**Model Training**:

```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Generate data
X, y = generate_training_data(n_samples=5000)

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Feature scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
accuracy = model.score(X_test_scaled, y_test)
print(f"Model accuracy: {accuracy:.2%}")

# Save model and scaler
joblib.dump(model, "models/risk_model.joblib")
joblib.dump(scaler, "models/scaler.joblib")
```

### Inference Pipeline

```python
# app/ml/predict.py

async def predict_risk(asset: dict) -> dict:
    """
    Predict risk score and level for an asset.

    1. Extract features from asset data
    2. Scale features using trained scaler
    3. Predict risk probability with model
    4. Convert to 0-100 risk score
    5. Classify into risk level
    """
    # Load model
    model, scaler = load_model()
    if not model:
        # Fallback to rule-based scoring
        return rule_based_risk_score(asset)

    # Extract features
    features = extract_features(asset)
    feature_vector = np.array([list(features.values())])

    # Scale features
    feature_vector_scaled = scaler.transform(feature_vector)

    # Predict risk probability
    risk_probability = model.predict_proba(feature_vector_scaled)[0][1]

    # Convert to 0-100 score
    risk_score = int(risk_probability * 100)

    # Classify risk level
    if risk_score >= 86:
        risk_level = "critical"
    elif risk_score >= 61:
        risk_level = "high"
    elif risk_score >= 31:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_confidence": float(risk_probability)
    }
```

---

## API Design

### RESTful Principles

| HTTP Method | CRUD Operation | Idempotent | Safe |
| ----------- | -------------- | ---------- | ---- |
| GET         | Read           | Yes        | Yes  |
| POST        | Create         | No         | No   |
| PUT         | Update/Replace | Yes        | No   |
| PATCH       | Partial Update | No         | No   |
| DELETE      | Delete         | Yes        | No   |

### Status Code Usage

| Code    | Usage                        | Example                                 |
| ------- | ---------------------------- | --------------------------------------- |
| **200** | Successful GET/PUT/PATCH     | `GET /api/assets`                       |
| **201** | Resource created             | `POST /api/auth/register`               |
| **202** | Accepted (async processing)  | `POST /api/assets/scan`                 |
| **204** | Success, no content          | `DELETE /api/assets/{id}` (alternative) |
| **400** | Client error (bad input)     | Invalid domain format                   |
| **401** | Unauthenticated              | Missing/invalid JWT                     |
| **402** | Payment required             | Scan limit reached                      |
| **403** | Unauthorized (no permission) | Access denied                           |
| **404** | Resource not found           | Asset doesn't exist                     |
| **409** | Conflict                     | User already exists                     |
| **422** | Validation error             | Pydantic validation failed              |
| **429** | Rate limit exceeded          | Too many requests                       |
| **500** | Server error                 | Unhandled exception                     |

### Response Format Consistency

**Success Response**:

```json
{
  "data": {...},           // Or array
  "message": "Success",    // Optional
  "pagination": {...}      // If list endpoint
}
```

**Error Response**:

```json
{
  "detail": "Human-readable error message",
  "error_code": "SPECIFIC_CODE",
  "timestamp": "2025-10-31T12:00:00Z",
  "path": "/api/endpoint"
}
```

---

## Future Enhancements

### Planned Features

#### 1. Real-Time Notifications

- **WebSocket Integration**: Live scan progress updates
- **Browser Push Notifications**: Critical alert delivery
- **Slack/Discord Webhooks**: Team collaboration integrations

#### 2. Team Collaboration

- **Multi-User Workspaces**: Invite team members
- **Role-Based Access Control**: Admin, Member, Viewer roles
- **Shared Assets**: Collaborative asset management
- **Activity Feed**: Team audit log

#### 3. Advanced Analytics

- **Custom Dashboards**: Drag-and-drop widgets
- **Scheduled Reports**: Automated PDF/email reports
- **Data Export API**: Programmatic data access
- **Historical Trending**: Long-term risk analysis

#### 4. Enhanced ML Models

- **Deep Learning**: Neural networks for complex patterns
- **Anomaly Detection**: Unsupervised learning for outliers
- **Threat Intelligence**: Integration with CVE databases
- **Model Explainability**: SHAP values for risk factor importance

#### 5. API Enhancements

- **GraphQL API**: Flexible data querying
- **gRPC API**: High-performance service-to-service
- **Bulk Operations**: Batch asset management
- **Versioned APIs**: v1, v2 with deprecation strategy

#### 6. Infrastructure Improvements

- **Redis Caching**: Response caching for performance
- **Celery Task Queue**: Distributed task processing
- **Kubernetes**: Container orchestration for auto-scaling
- **Multi-Region Deployment**: Global CDN and database replication

---

## Appendix

### Glossary

| Term               | Definition                                                    |
| ------------------ | ------------------------------------------------------------- |
| **OSINT**          | Open Source Intelligence - publicly available data collection |
| **Attack Surface** | All possible entry points an attacker could exploit           |
| **Asset**          | Any discoverable digital resource (domain, subdomain, IP)     |
| **Risk Score**     | 0-100 numerical value indicating security risk                |
| **Multi-Tenancy**  | Single platform serving multiple isolated customers           |
| **JWT**            | JSON Web Token - compact token format for authentication      |
| **Async/Await**    | Python pattern for non-blocking concurrent operations         |

### References

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **MongoDB Best Practices**: https://www.mongodb.com/docs/manual/administration/production-notes/
- **Firebase Admin SDK**: https://firebase.google.com/docs/admin/setup
- **Stripe API**: https://stripe.com/docs/api
- **scikit-learn**: https://scikit-learn.org/stable/

---

**Document Version:** 1.0.0  
**Last Updated:** October 31, 2025  
**Maintainer:** GaneshWiz07  
**Repository:** https://github.com/GaneshWiz07/RECON-AI
