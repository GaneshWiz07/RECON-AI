# ReconAI - Enterprise OSINT Platform

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](https://github.com/GaneshWiz07/RECON-AI)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-13AA52)](https://www.mongodb.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth-FFA000)](https://firebase.google.com/)

**Automated Intelligence, Proactive Security** — Enterprise-grade Open Source Intelligence (OSINT) platform for continuous attack surface monitoring, threat intelligence, and security posture management.

ReconAI is a production-ready, scalable SaaS platform that automates the discovery, enrichment, and analysis of exposed digital assets across the internet. Leveraging machine learning for intelligent risk scoring, multi-tenant architecture for secure workspace isolation, and real-time analytics for actionable security insights — ReconAI empowers security teams to stay ahead of threats.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#️-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Security](#-security)
- [Subscription Tiers](#-subscription-tiers)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Features

### Core Platform Capabilities

#### 🎯 Intelligent Asset Discovery

- **Automated Reconnaissance**: Multi-source asset discovery with configurable scan depths
- **Domain & Subdomain Enumeration**: Comprehensive DNS reconnaissance with recursive subdomain discovery
- **IP Address Intelligence**: Geolocation, ASN mapping, and network ownership analysis
- **Technology Stack Detection**: Identify web servers, frameworks, CMS, and third-party services
- **Certificate Transparency Monitoring**: SSL/TLS certificate discovery and validation
- **Real-time Scan Orchestration**: Background job processing with status tracking and progress monitoring

#### 🤖 Machine Learning-Powered Risk Intelligence

- **Predictive Risk Scoring**: ML-based risk assessment (0-100 scale) using Logistic Regression
- **Multi-dimensional Feature Analysis**: 11+ security indicators including port exposure, SSL health, breach history
- **Risk Classification**: Automated categorization (Low, Medium, High, Critical)
- **Confidence Scoring**: Model confidence levels for prediction transparency
- **Continuous Learning**: Model retraining capabilities with new threat intelligence

#### � Real-Time Analytics & Insights

- **Executive Dashboard**: KPI cards with 7-day trend analysis and risk aggregation
- **Risk Trend Visualization**: Time-series analysis with interactive charts (Recharts)
- **Asset Distribution Analytics**: Risk-based asset categorization and filtering
- **Scan History Tracking**: Complete audit trail with success/failure metrics
- **Custom Reporting**: Data export capabilities (CSV, JSON) for compliance and integration

#### 🔐 Enterprise Security & Authentication

- **Firebase Authentication**: Email/password + Google OAuth 2.0 social login
- **JWT Token-Based Authorization**: Stateless authentication with automatic token refresh
- **Multi-Tenant Architecture**: Complete workspace isolation with user-specific data partitioning
- **Role-Based Access Control (RBAC)**: Granular permission management (foundation for team features)
- **Audit Logging**: Comprehensive activity tracking for compliance requirements
- **Data Encryption**: At-rest and in-transit encryption for sensitive information

#### 💳 Subscription & Billing Management

- **Stripe Payment Integration**: PCI-compliant payment processing
- **Tiered Subscription Plans**: Free, Pro, and Enterprise tiers with usage-based limits
- **Usage Metering**: Real-time tracking of API calls and scan credits
- **Automatic Billing Cycles**: Subscription renewals with prorated upgrades/downgrades
- **Webhook-Driven Updates**: Real-time subscription status synchronization
- **Payment History**: Complete billing event tracking and invoice generation

#### � Advanced Security Detectors

- **DNS Misconfiguration Detection**: SPF, DMARC, DKIM validation; missing/duplicate records
- **HTTP Security Header Analysis**: HSTS, CSP, X-Frame-Options, and 15+ header checks
- **SSL/TLS Certificate Inspector**: Certificate expiry monitoring, self-signed detection, weak cipher identification
- **Port Exposure Assessment**: Dangerous port detection (SSH, RDP, database services)
- **Breach History Intelligence**: Email breach lookup with HaveIBeenPwned integration
- **Open Directory Detector**: Exposed file listings and sensitive data exposure
- **Cloud Bucket Security**: S3, Azure Blob, GCS misconfiguration scanning (foundation)

#### 🔌 RESTful API & Integration

- **OpenAPI 3.0 Documentation**: Interactive Swagger UI at `/docs`
- **Versioned API Endpoints**: Stable, backward-compatible API contracts
- **Rate Limiting**: Request throttling to prevent abuse (configurable by plan)
- **Pagination & Filtering**: Efficient data retrieval with query parameter support
- **Webhook Support**: Real-time event notifications for external integrations
- **CORS Configuration**: Secure cross-origin resource sharing for web clients

### Technical Excellence

#### ⚡ Performance & Scalability

- **Asynchronous Architecture**: Python `asyncio` for non-blocking I/O operations
- **Connection Pooling**: MongoDB connection reuse for optimal database performance
- **Background Task Processing**: Celery-compatible async job execution
- **Horizontal Scalability**: Stateless API design for load balancing and auto-scaling
- **Response Caching**: Strategic caching for frequently accessed data (Redis-ready)

#### 🧪 Quality & Reliability

- **Comprehensive Test Coverage**: Unit and integration tests with pytest
- **Health Check Endpoints**: `/health` monitoring for uptime and dependency status
- **Structured Logging**: JSON-formatted logs for centralized log aggregation
- **Error Handling**: Graceful degradation with user-friendly error messages
- **Database Indexing**: Optimized queries with compound indexes for sub-second responses

---

## 🏗️ Architecture

ReconAI follows a modern microservices-inspired architecture with clear separation of concerns and event-driven async processing.

### High-Level Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Web Client    │◄───────►│   API Gateway    │◄───────►│   Auth Service  │
│  (React + PWA)  │  HTTPS  │   (FastAPI)      │  Admin  │   (Firebase)    │
└─────────────────┘         └──────────────────┘   SDK   └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
          ┌─────────────────┐ ┌──────────┐  ┌─────────────────┐
          │  ML Risk Engine  │ │ Database │  │  Task Queue     │
          │  (scikit-learn)  │ │ (MongoDB)│  │  (Async Jobs)   │
          └─────────────────┘ └──────────┘  └─────────────────┘
                    │                                  │
                    │         External APIs            │
                    └──────────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │   Stripe     │    │   DNS/WHOIS  │    │ HaveIBeenPwned│
      │   Billing    │    │  Collectors  │    │     API       │
      └──────────────┘    └──────────────┘    └──────────────┘
```

### Component Architecture

```
Backend (FastAPI)
├── API Layer                 # REST endpoints, request validation
│   ├── Auth Routes          # Registration, login, user management
│   ├── Asset Routes         # Asset CRUD, scanning, export
│   ├── Analytics Routes     # Dashboard stats, trends, insights
│   └── Billing Routes       # Stripe checkout, webhooks, usage
│
├── Business Logic Layer      # Core application logic
│   ├── Collectors           # Asset discovery and data collection
│   │   ├── Base Collector   # Abstract collector interface
│   │   ├── Free Collector   # Free/open-source data collection
│   │   └── Enrichers        # Data enhancement modules
│   │
│   ├── Detectors            # Security analysis modules
│   │   ├── DNS Misconfig    # SPF, DMARC, zone validation
│   │   ├── SSL Inspector    # Certificate health checks
│   │   ├── Header Analyzer  # HTTP security headers
│   │   ├── Port Scanner     # Open port risk assessment
│   │   └── Cloud Bucket     # S3/Azure/GCS exposure checks
│   │
│   ├── ML Engine            # Machine learning pipeline
│   │   ├── Feature Extract  # Asset -> feature vector
│   │   ├── Model Inference  # Risk prediction
│   │   └── Model Training   # Retraining pipeline
│   │
│   └── Tasks                # Background job processing
│       ├── Scan Worker      # Async scan execution
│       └── Email Alerts     # Notification system
│
├── Infrastructure Layer      # Cross-cutting concerns
│   ├── Middleware           # Auth, CORS, rate limiting
│   ├── Core Services        # Firebase, MongoDB connections
│   └── Database Schema      # ODM models and indexes
│
└── External Integrations     # Third-party services
    ├── Firebase Admin SDK   # Authentication verification
    ├── Stripe SDK           # Payment processing
    └── OSINT APIs           # Data collection sources

Frontend (React)
├── Pages                     # Route components
│   ├── Dashboard            # Main analytics view
│   ├── Assets               # Asset management table
│   ├── Billing              # Subscription management
│   └── Auth (Login/Signup)  # Authentication flows
│
├── Components                # Reusable UI components
│   ├── UI Library           # Buttons, cards, inputs
│   ├── Navigation           # Header, sidebar
│   └── Auth Guards          # Protected route wrappers
│
├── Services                  # API client layer
│   └── API Client           # Axios-based HTTP client
│
└── State Management          # Application state
    └── Auth Context         # Firebase auth state
```

### Data Flow: Asset Scan Lifecycle

```
1. User Initiates Scan
   ├─► Frontend: Click "New Scan" → POST /api/assets/scan
   └─► Backend: Validate auth token, check scan credits

2. Scan Initialization
   ├─► Create scan record in MongoDB (status: pending)
   ├─► Decrement scan credits (Free plan only)
   └─► Spawn async background task

3. Asset Discovery Phase
   ├─► DNS enumeration (subdomains, records)
   ├─► Certificate transparency search
   ├─► IP address resolution
   └─► Technology fingerprinting

4. Data Enrichment Phase
   ├─► SSL/TLS certificate analysis
   ├─► HTTP security header inspection
   ├─► Port scanning and service detection
   ├─► Breach history lookup
   └─► DNS misconfiguration detection

5. Risk Scoring Phase
   ├─► Extract 11+ features from asset data
   ├─► Scale features using trained StandardScaler
   ├─► ML model inference (Logistic Regression)
   └─► Assign risk level (Low/Medium/High/Critical)

6. Persistence & Notification
   ├─► Store assets in MongoDB with indexes
   ├─► Update scan status to "completed"
   ├─► Send email alert (if high/critical risks)
   └─► WebSocket notification (future enhancement)

7. Frontend Updates
   ├─► Poll scan status endpoint
   ├─► Refresh asset table on completion
   └─► Update dashboard analytics
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed technical architecture documentation.

---

## 🛠 Tech Stack

### Backend

| Technology             | Purpose              | Version |
| ---------------------- | -------------------- | ------- |
| **FastAPI**            | Async web framework  | 0.115.0 |
| **Python**             | Primary language     | 3.11+   |
| **Motor**              | Async MongoDB driver | 3.3.2   |
| **MongoDB Atlas**      | NoSQL database       | Cloud   |
| **Firebase Admin SDK** | Authentication       | 6.3.0   |
| **scikit-learn**       | Machine learning     | 1.3.2   |
| **Stripe**             | Payment processing   | 7.8.0   |
| **Pydantic**           | Data validation      | 2.9.2   |
| **Uvicorn**            | ASGI server          | 0.32.0  |
| **pytest**             | Testing framework    | 7.4.3   |

### Frontend

| Technology       | Purpose             | Version |
| ---------------- | ------------------- | ------- |
| **React**        | UI framework        | 18.2    |
| **Vite**         | Build tool          | 5.x     |
| **TailwindCSS**  | Utility-first CSS   | 3.x     |
| **Firebase SDK** | Authentication      | 10.x    |
| **Recharts**     | Data visualization  | 2.x     |
| **Axios**        | HTTP client         | 1.x     |
| **React Router** | Client-side routing | 6.x     |

### Infrastructure & DevOps

| Service            | Purpose                    |
| ------------------ | -------------------------- |
| **Render**         | Backend hosting (Docker)   |
| **Netlify**        | Frontend hosting (CDN)     |
| **MongoDB Atlas**  | Database (multi-region)    |
| **Firebase**       | Authentication service     |
| **Stripe**         | Billing & subscriptions    |
| **GitHub Actions** | CI/CD pipelines (optional) |

### External APIs & Services

| API                          | Purpose           | Cost      |
| ---------------------------- | ----------------- | --------- |
| **DNS Resolvers**            | DNS enumeration   | Free      |
| **Certificate Transparency** | SSL/TLS discovery | Free      |
| **HaveIBeenPwned**           | Breach history    | Free      |
| **IP Geolocation**           | Location data     | Free tier |
| **Censys**                   | Advanced OSINT    | Optional  |

---

## 📦 Project Structure

```
RECON-AI/
├── backend/
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   │   ├── auth.py         # Authentication routes
│   │   │   ├── assets.py       # Asset management
│   │   │   ├── analytics.py    # Dashboard analytics
│   │   │   └── billing.py      # Stripe integration
│   │   ├── collectors/         # Data collectors
│   │   │   ├── censys_collector.py  # Censys API integration
│   │   │   └── enrichers.py         # Data enrichment
│   │   ├── core/               # Core infrastructure
│   │   │   ├── firebase.py     # Firebase Admin SDK
│   │   │   └── database.py     # MongoDB connection
│   │   ├── middleware/         # Middleware
│   │   │   └── auth.py         # Firebase auth middleware
│   │   ├── ml/                 # Machine learning
│   │   │   ├── train_model.py  # Model training
│   │   │   └── models/         # Trained models
│   │   ├── tasks/              # Background workers
│   │   │   └── scan_worker.py  # Scan executor
│   │   └── main.py             # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── auth/           # Authentication
│   │   │   ├── layout/         # Layout components
│   │   │   └── ui/             # Reusable UI
│   │   ├── pages/              # Page components
│   │   │   ├── Login.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── context/            # React context
│   │   │   └── AuthContext.jsx
│   │   ├── services/           # API services
│   │   │   └── api.js
│   │   ├── config/             # Configuration
│   │   │   └── firebase.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas account
- Firebase project (with Authentication enabled)
- Censys API credentials (optional)
- Stripe account (for billing)

### 1. Firebase Setup

1. Create a Firebase project at [https://console.firebase.google.com](https://console.firebase.google.com)

2. Enable Authentication:

   - Go to Authentication > Sign-in method
   - Enable Email/Password
   - Enable Google

3. Generate service account key:

   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Download the JSON file

4. Get Web SDK config:
   - Go to Project Settings > General
   - Under "Your apps", add a Web app
   - Copy the Firebase config object

### 2. MongoDB Setup

1. Create a MongoDB Atlas cluster at [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)

2. Create a database user and get connection string

3. Whitelist your IP address (or use 0.0.0.0/0 for testing)

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required environment variables:**

```bash
# MongoDB
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/reconai

# Firebase Admin SDK (from service account JSON)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com

# Stripe (get from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Application
ENVIRONMENT=development
PORT=8000
CORS_ORIGINS=http://localhost:5173
```

**Train ML model:**

```bash
python -m app.ml.train_model
```

**Start backend server:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env with your Firebase config
nano .env
```

**Required environment variables:**

```bash
# API
VITE_API_URL=http://localhost:8000

# Firebase Web SDK (from Firebase Console)
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

**Start frontend dev server:**

```bash
npm run dev
```

### 6. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📚 Documentation

### Comprehensive Guides

- **[API Documentation](./API.md)**: Complete REST API reference with examples, authentication, rate limiting, and code samples
- **[Architecture Documentation](./ARCHITECTURE.md)**: System design, component architecture, data models, ML pipeline, and deployment patterns

### Quick API Reference

#### Authentication

All protected routes require Firebase ID token in Authorization header:

```
Authorization: Bearer <firebase_id_token>
```

#### Key Endpoints

**Authentication:**

- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Sync user data
- `GET /api/auth/me` - Get current user

**Asset Discovery:**

- `POST /api/assets/scan` - Start new scan
- `GET /api/assets` - List assets (with pagination & filters)
- `GET /api/assets/{asset_id}` - Get asset details
- `GET /api/assets/export` - Export assets as CSV/JSON

**Analytics:**

- `GET /api/analytics/dashboard` - Dashboard statistics
- `GET /api/analytics/risk-trend` - Risk score over time
- `GET /api/analytics/top-risky-assets` - Highest risk assets

**Billing:**

- `GET /api/billing/subscription` - Current subscription
- `POST /api/billing/create-checkout` - Create Stripe checkout
- `GET /api/billing/usage` - Current usage stats

**System:**

- `GET /health` - Health check (public)
- `GET /docs` - Interactive API documentation (public)

📖 **For detailed API documentation with request/response examples, see [API.md](./API.md)**

---

## 🔒 Security

### Authentication Flow

1. User signs up/logs in with Firebase (email/password or Google)
2. Frontend receives Firebase ID token
3. Frontend includes token in all API requests
4. Backend validates token with Firebase Admin SDK
5. User info attached to request for authorization

### Data Isolation

- Each user has a unique workspace (workspace_id = Firebase UID)
- All database queries filtered by user_id
- No cross-user data access possible

### Best Practices

- Firebase tokens refresh automatically every hour
- Tokens stored in memory only (not localStorage)
- HTTPS required in production
- MongoDB connection uses TLS
- Stripe webhook signature verification
- Rate limiting on all API endpoints

## 💳 Subscription Tiers

### Free Tier

- 100 API calls/month
- 10 scan credits/month
- Basic reporting
- Email support

### Pro Tier ($99/month)

- 10,000 API calls/month
- 100 scan credits/month
- Advanced reporting
- Priority support
- Automated rescans
- Risk alerts

## 🧪 Testing

**Backend tests:**

```bash
cd backend
pytest tests/ -v --cov=app
```

**Frontend tests:**

```bash
cd frontend
npm test
```

## 🚢 Deployment

### Backend (Render)

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repository
4. Configure:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables
5. Deploy

**Background Worker (Render):**

- Create Background Worker service
- Start Command: `rq worker scan_queue --with-scheduler`
- Use same environment variables

**Scheduler (Render Cron Job):**

- Schedule: `0 * * * *` (every hour)
- Command: `python -m backend.app.tasks.scheduler`

### Frontend (Netlify)

1. Push code to GitHub
2. Create new site on Netlify
3. Configure:
   - Base directory: `frontend/`
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`
   - Add environment variables
4. Deploy

## 📊 Database Schema

### Collections

**users** - User profiles and subscription data

- Indexed on: uid (unique), email (unique)

**assets** - Discovered assets

- Indexed on: user_id + asset_value (compound unique), risk_score, next_scan_at

**scans** - Scan history

- Indexed on: asset_id + created_at, user_id, scan_status

**billing_events** - Billing history

- Indexed on: user_id + created_at, stripe_event_id (unique)

**api_usage_logs** - API call tracking with TTL (90 days)

- Indexed on: user_id + timestamp, timestamp (TTL)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**"Firebase credentials not found"**

- Ensure `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, and `FIREBASE_CLIENT_EMAIL` are set
- Private key must have `\\n` replaced with actual newlines

**"MongoDB connection failed"**

- Check your MongoDB Atlas IP whitelist
- Verify connection string is correct
- Ensure database user has read/write permissions

**"Collector returns no results"**

- Verify Censys API credentials are correct
- Check API quotas (free tier has limits)
- Ensure domain has exposed services/certificates

**"Frontend can't connect to backend"**

- Ensure backend is running on correct port
- Check `VITE_API_URL` in frontend `.env`
- Verify CORS is configured correctly

## 📧 Support

For issues, questions, or feature requests:

- **GitHub Issues**: [https://github.com/GaneshWiz07/RECON-AI/issues](https://github.com/GaneshWiz07/RECON-AI/issues)
- **Email**: support@reconai.com
- **Documentation**: See [API.md](./API.md) and [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 📖 Additional Resources

### Documentation

- **[API Reference](./API.md)** - Complete REST API documentation with authentication, endpoints, examples, and best practices
- **[Architecture Guide](./ARCHITECTURE.md)** - System design, component architecture, data models, security, scalability, and ML pipeline

### Useful Links

- **Interactive API Docs**: http://localhost:8000/docs (when running locally)
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Repository**: [https://github.com/GaneshWiz07/RECON-AI](https://github.com/GaneshWiz07/RECON-AI)

---

## 🙏 Acknowledgments

- **Firebase** for authentication infrastructure
- **MongoDB Atlas** for database hosting
- **Stripe** for payment processing
- **FastAPI** for the excellent web framework
- **scikit-learn** for machine learning capabilities
- **React** and **TailwindCSS** for frontend development
- Open source community for amazing libraries and tools

---

<div align="center">

**Made with ❤️ for the security community**

[![GitHub stars](https://img.shields.io/github/stars/GaneshWiz07/RECON-AI?style=social)](https://github.com/GaneshWiz07/RECON-AI)
[![GitHub forks](https://img.shields.io/github/forks/GaneshWiz07/RECON-AI?style=social)](https://github.com/GaneshWiz07/RECON-AI)
[![GitHub issues](https://img.shields.io/github/issues/GaneshWiz07/RECON-AI)](https://github.com/GaneshWiz07/RECON-AI/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>
