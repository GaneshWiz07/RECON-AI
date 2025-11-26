# 🔍 RECON - AI-Powered OSINT & Continuous Cyber Risk Monitoring Platform

**LIVE** : [https://recon-osint.netlify.app/](https://recon-osint.netlify.app/)

An intelligent Open Source Intelligence (OSINT) platform that combines automated asset discovery with machine learning-based risk assessment. Discover, monitor, and protect your digital infrastructure with real-time threat detection, vulnerability scanning, and comprehensive security analytics.

## ✨ Features

### 🎯 Asset Discovery & Intelligence

- **Multi-Source Discovery**: Automatically discover domains, subdomains, IPs, and exposed services
- **Deep Reconnaissance**: DNS enumeration, port scanning, and service fingerprinting
- **Enrichment Pipeline**: SSL certificate analysis, HTTP header inspection, and technology detection
- **Real-time Monitoring**: Continuous scanning with configurable intervals
- **Export Capabilities**: Export asset data in CSV/JSON formats

### 🤖 AI-Powered Risk Assessment

- **Machine Learning Models**: Trained risk scoring using scikit-learn
- **Threat Classification**: Automatic categorization of security risks
- **Predictive Analytics**: Identify potential vulnerabilities before exploitation
- **Risk Trending**: Track risk scores over time with historical analysis
- **Dynamic Scoring**: Real-time risk recalculation based on new findings

### 🔐 Security & Compliance

- **Firebase Authentication**: Secure Google Sign-In and email/password auth
- **Multi-User Isolation**: Complete data separation between users
- **Role-Based Access**: Subscription-tier based feature access
- **API Rate Limiting**: Protection against abuse and overuse
- **Stripe Integration**: Secure payment processing for Pro tier

### 📊 Analytics & Reporting

- **Interactive Dashboard**: Real-time statistics and visualizations
- **Risk Distribution**: Visual breakdown of asset risk levels
- **Trend Analysis**: Historical risk data with time-series charts
- **Top Risky Assets**: Prioritized list of high-risk infrastructure
- **Usage Metrics**: API call tracking and scan credit monitoring

### 🔔 Detection & Alerts

- **Security Headers**: Detect missing or misconfigured HTTP headers
- **SSL/TLS Inspector**: Certificate validation and expiry warnings
- **Open Directory Detection**: Identify exposed file listings
- **Cloud Bucket Scanning**: Find misconfigured AWS S3, Azure, GCP buckets
- **DNS Misconfigurations**: Detect dangling DNS records and takeover risks

## 🚀 Tech Stack

### Backend

- **FastAPI** - High-performance async Python web framework
- **Motor** - Async MongoDB driver for Python
- **MongoDB Atlas** - Cloud database with free tier
- **Firebase Admin SDK** - User authentication and management
- **scikit-learn** - Machine learning for risk prediction
- **Uvicorn** - Lightning-fast ASGI server
- **Stripe API** - Payment processing and subscriptions
- **Redis Queue** - Background job processing (optional)

### Frontend

- **React 18** - Modern component-based UI framework
- **Vite** - Next-generation frontend tooling
- **TailwindCSS** - Utility-first styling framework
- **Lucide Icons** - Beautiful, consistent icon system
- **Axios** - HTTP client for API communication
- **React Router** - Client-side routing
- **Context API** - Global state management

### ML & Data Science

- **scikit-learn** - Risk scoring models
- **joblib** - Model serialization and loading
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing

### DevOps & Infrastructure

- **Render** - Backend hosting and deployment
- **Netlify** - Frontend hosting and CI/CD
- **GitHub Actions** - Automated testing and deployment
- **Docker** - Containerization (optional)

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- MongoDB Atlas account (free tier available)
- Firebase account (for authentication)
- Stripe account (optional, for billing)

### 1. Clone the Repository

```bash
git clone https://github.com/GaneshWiz07/RECON-AI.git
cd RECON-AI
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Backend Environment

Create `backend/.env` file:

```bash
# MongoDB Atlas
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/reconai?retryWrites=true&w=majority

# Firebase Admin SDK (from service account JSON)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com

# Stripe (optional - for billing features)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Groq LLM (for AI-powered security recommendations)
GROQ_API_KEY=your_groq_api_key_here

# Have I Been Pwned API (optional - for breach data, higher rate limits with API key)
HIBP_API_KEY=your_hibp_api_key_here

# Application Settings
ENVIRONMENT=development
PORT=8000
CORS_ORIGINS=http://localhost:5173
```

**Train the ML model (first time setup):**

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
```

Create `frontend/.env` file:

```bash
# Backend API
VITE_API_URL=http://localhost:8000

# Firebase Web SDK
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

**Start frontend dev server:**

```bash
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)

## 🏃 Running Locally

### Development Mode

**Backend (with auto-reload):**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (with hot reload):**

```bash
cd frontend
npm run dev
```

Visit http://localhost:5173 to see the app in action!

### Production Mode

**Backend:**

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**

```bash
cd frontend
npm run build
npm run preview
```

## 🚀 Deployment

### Deploy Backend to Render

1. **Create Web Service**

   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Build Settings**

   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3

3. **Add Environment Variables**

   - Add all variables from `backend/.env`
   - Set `ENVIRONMENT=production`
   - Update `CORS_ORIGINS` to your frontend URL

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment

### Deploy Frontend to Netlify

1. **Connect Repository**

   - Go to [Netlify Dashboard](https://app.netlify.com/)
   - Click "Add new site" → "Import an existing project"
   - Connect your GitHub repository

2. **Configure Build Settings**

   - **Base directory**: `frontend/`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

3. **Add Environment Variables**

   - Go to Site settings → Environment variables
   - Add all `VITE_*` variables from `frontend/.env`
   - Update `VITE_API_URL` to your Render backend URL

4. **Deploy**
   - Trigger deployment
   - Your site will be live at `https://your-site.netlify.app`

## 📁 Project Structure

```
RECON-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py          # Authentication endpoints
│   │   │       ├── assets.py        # Asset management endpoints
│   │   │       ├── analytics.py     # Analytics and reporting
│   │   │       └── billing.py       # Stripe integration
│   │   ├── collectors/
│   │   │   ├── base_collector.py    # Asset discovery logic
│   │   │   ├── enrichers.py         # Data enrichment
│   │   │   └── free_collector.py    # Free-tier collectors
│   │   ├── core/
│   │   │   ├── database.py          # MongoDB connection
│   │   │   └── firebase.py          # Firebase Admin SDK
│   │   ├── detectors/
│   │   │   ├── cloud_bucket_checker.py
│   │   │   ├── dns_misconfig_detector.py
│   │   │   ├── open_directory_detector.py
│   │   │   ├── security_file_checker.py
│   │   │   ├── ssl_inspector.py
│   │   │   └── web_header_analyzer.py
│   │   ├── middleware/
│   │   │   └── auth.py              # Authentication middleware
│   │   ├── ml/
│   │   │   ├── predict.py           # Risk prediction
│   │   │   ├── train_model.py       # Model training
│   │   │   └── models/
│   │   │       ├── risk_model.joblib
│   │   │       └── scaler.joblib
│   │   ├── tasks/
│   │   │   ├── scan_worker.py       # Background scanning
│   │   │   └── email_alerts.py      # Email notifications
│   │   └── main.py                  # FastAPI application
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   └── ProtectedRoute.jsx
│   │   │   └── ui/
│   │   │       ├── Badge.jsx
│   │   │       ├── Button.jsx
│   │   │       ├── Card.jsx
│   │   │       ├── Input.jsx
│   │   │       ├── LoadingSpinner.jsx
│   │   │       ├── Logo.jsx
│   │   │       └── Navigation.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # Global auth state
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Assets.jsx
│   │   │   ├── Analytics.jsx
│   │   │   └── Billing.jsx
│   │   ├── services/
│   │   │   └── api.js               # API client
│   │   ├── config/
│   │   │   └── firebase.js          # Firebase config
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── netlify.toml
├── API.md                           # Detailed API documentation
├── ARCHITECTURE.md                  # System architecture guide
├── README.md
└── LICENSE
```

## 📚 Documentation

### Comprehensive Guides

- **[API Documentation](./API.md)** - Complete REST API reference with authentication, endpoints, request/response examples, rate limiting, and code samples in Python, JavaScript, and cURL
- **[Architecture Documentation](./ARCHITECTURE.md)** - System design, component architecture, data flow, MongoDB schemas, ML pipeline, security patterns, and deployment strategies

### Quick API Reference

#### Authentication

All protected routes require Firebase ID token:

```
Authorization: Bearer <firebase_id_token>
```

#### Core Endpoints

**Authentication:**

- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Sync user data with backend
- `GET /api/auth/me` - Get current user profile

**Asset Discovery:**

- `POST /api/assets/scan` - Start new asset scan
- `GET /api/assets` - List assets (pagination, filters)
- `GET /api/assets/{asset_id}` - Get detailed asset info
- `GET /api/assets/export` - Export as CSV/JSON

**Analytics:**

- `GET /api/analytics/dashboard` - Dashboard statistics
- `GET /api/analytics/risk-trend` - Risk score timeline
- `GET /api/analytics/top-risky-assets` - High-risk assets

**Billing:**

- `GET /api/billing/subscription` - Current plan details
- `POST /api/billing/create-checkout` - Start Stripe checkout
- `GET /api/billing/usage` - Usage and limits

**System:**

- `GET /health` - Health check (public)
- `GET /docs` - Interactive API docs (public)

📖 **For detailed API documentation with full examples, see [API.md](./API.md)**

## 🎯 Features in Detail

### Asset Discovery

- **Subdomain Enumeration**: Discover all subdomains using multiple techniques
- **IP Resolution**: Resolve domains to IP addresses with geolocation
- **Port Scanning**: Identify open ports and running services
- **Service Detection**: Fingerprint web servers, databases, and applications
- **Technology Stack**: Identify frameworks, CMS, and libraries in use

### Security Analysis

- **SSL/TLS Inspection**:

  - Certificate validity and expiration checks
  - Cipher suite analysis
  - Protocol version detection
  - Certificate chain verification

- **HTTP Header Analysis**:

  - Missing security headers (HSTS, CSP, X-Frame-Options)
  - Information disclosure in headers
  - Cookie security attributes
  - CORS configuration review

- **Cloud Bucket Detection**:

  - AWS S3 bucket enumeration
  - Azure Blob Storage scanning
  - Google Cloud Storage checks
  - Permission and ACL analysis

- **DNS Security**:
  - Dangling DNS record detection
  - Subdomain takeover vulnerabilities
  - CAA record verification
  - DNSSEC validation

### Machine Learning Risk Scoring

- **Feature Engineering**: Extract security-relevant features from asset data
- **Model Training**: Train on historical vulnerability data
- **Risk Prediction**: Real-time risk score calculation (0-100)
- **Continuous Learning**: Retrain models with new data
- **Explainability**: Understand why assets are flagged as high-risk

### Subscription Tiers

#### 🆓 Free Tier

- 10 scan credits/month
- 100 API calls/month
- Basic asset discovery
- Standard risk scoring
- Dashboard access
- Email support

#### 💎 Pro Tier ($99/month)

- 100 scan credits/month
- 10,000 API calls/month
- Advanced enrichment
- Priority scanning
- Automated re-scans
- Risk trend alerts
- Export capabilities
- Priority support
- API access

## 🔒 Security

### Authentication Flow

1. User authenticates with Firebase (Google Sign-In or email/password)
2. Firebase returns ID token
3. Frontend stores token in memory (not localStorage)
4. Token included in Authorization header for all API requests
5. Backend validates token with Firebase Admin SDK
6. User identity attached to request context

### Data Isolation

- Each user has a unique `user_id` (Firebase UID)
- All database queries filtered by `user_id`
- No cross-user data access possible
- API endpoints enforce user-scoped data access

### Best Practices

- ✅ Firebase tokens auto-refresh every hour
- ✅ HTTPS enforced in production
- ✅ MongoDB connection uses TLS 1.2+
- ✅ Stripe webhook signature verification
- ✅ Rate limiting on all endpoints
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (NoSQL)
- ✅ CORS properly configured

## 🌐 API Rate Limits

### Free Tier

- 100 requests/month
- 10 scans/month
- Rate: 10 requests/minute

### Pro Tier

- 10,000 requests/month
- 100 scans/month
- Rate: 100 requests/minute

## 🧪 Testing

**Backend tests:**

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

**Frontend tests:**

```bash
cd frontend
npm test
npm run test:coverage
```

## 📊 Database Schema

### Collections

**users** - User profiles and subscription data

- Indexed: `uid` (unique), `email` (unique), `created_at`

**assets** - Discovered assets

- Indexed: `user_id + asset_value` (compound unique), `risk_score`, `next_scan_at`, `created_at`

**scans** - Scan history and results

- Indexed: `asset_id + created_at`, `user_id`, `scan_status`, `created_at`

**billing_events** - Stripe events and subscriptions

- Indexed: `user_id + created_at`, `stripe_event_id` (unique)

**api_usage_logs** - API call tracking with 90-day TTL

- Indexed: `user_id + timestamp`, `timestamp` (TTL: 90 days)

## 🎨 Customization

### Update Branding

Edit `frontend/src/components/ui/Logo.jsx` and `frontend/src/index.css`

### Modify Risk Thresholds

Edit `backend/app/ml/predict.py`:

```python
RISK_THRESHOLDS = {
    "low": 30,
    "medium": 60,
    "high": 80
}
```

### Add New Detectors

Create new file in `backend/app/detectors/` and implement detection logic:

```python
async def detect_vulnerability(asset_data: dict) -> dict:
    # Your detection logic here
    return {"findings": [...], "severity": "high"}
```

### Customize Scan Intervals

Edit `backend/app/collectors/base_collector.py`:

```python
SCAN_INTERVALS = {
    "free": 24 * 60 * 60,    # 24 hours
    "pro": 6 * 60 * 60       # 6 hours
}
```

## 🐛 Troubleshooting

### Backend Issues

**"Firebase credentials not found"**

- Ensure `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, and `FIREBASE_CLIENT_EMAIL` are set in `.env`
- Private key must have literal `\n` characters (not actual newlines)
- Wrap private key in double quotes

**"MongoDB connection failed"**

- Check MongoDB Atlas connection string in `MONGO_URI`
- Verify IP whitelist in MongoDB Atlas (allow 0.0.0.0/0 for development)
- Ensure database user has read/write permissions

**"ML model not found"**

- Run `python -m app.ml.train_model` to generate model files
- Check that `backend/app/ml/models/` contains `risk_model.joblib` and `scaler.joblib`

### Frontend Issues

**"Network Error" or API calls failing**

- Verify `VITE_API_URL` in `frontend/.env` points to running backend
- Check browser console for CORS errors
- Ensure backend is running on the specified port

**Firebase authentication not working**

- Verify all Firebase config variables are set correctly
- Check Firebase Console that Google Sign-In is enabled
- Ensure authorized domains include localhost and production URLs

**Blank page or white screen**

- Check browser console for errors
- Verify all dependencies installed: `npm install`
- Clear browser cache and restart dev server

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed
4. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**
   - Describe your changes clearly
   - Reference any related issues

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Firebase** - For robust authentication and user management
- **MongoDB Atlas** - For reliable cloud database hosting
- **FastAPI** - For the excellent async Python web framework
- **Stripe** - For secure payment processing
- **scikit-learn** - For machine learning capabilities
- **React & Vite** - For modern frontend development
- **TailwindCSS** - For beautiful, responsive styling
- All open-source contributors and the security research community

## 📧 Contact

For questions, suggestions, or support:

- **GitHub Issues**: [Report a bug or request a feature](https://github.com/GaneshWiz07/RECON-AI/issues)
- **Email**: Open an issue for contact information
- **Documentation**: See [API.md](./API.md) and [ARCHITECTURE.md](./ARCHITECTURE.md)

---

**Made with ❤️ and 🔍 by Ganesh E**

_Secure your digital infrastructure with intelligent OSINT_
