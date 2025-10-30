# ReconAI - OSINT Platform

**Automated Intelligence, Proactive Security.**

ReconAI is a comprehensive Micro-SaaS platform that discovers, enriches, and analyzes exposed assets across the internet. It scores assets for security risk using machine learning and provides a secure multi-tenant dashboard with Firebase authentication.

![ReconAI Platform](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18.2-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)

## 🌟 Features

### Core Capabilities
- **Asset Discovery**: Automated discovery using Censys and Shodan APIs
- **Risk Scoring**: ML-powered risk assessment (0-100 scale)
- **Real-time Dashboard**: Interactive analytics with trend visualization
- **Multi-tenant Architecture**: Secure workspace isolation
- **Firebase Authentication**: Email/password + Google OAuth 2.0
- **Subscription Management**: Stripe-powered billing (Free & Pro tiers)
- **Automated Rescans**: Scheduled asset monitoring
- **REST API**: Full-featured API with OpenAPI documentation

### Security Features
- DNS enumeration and validation
- HTTP security header analysis
- Breach history checking (HaveIBeenPwned)
- Outdated software detection
- SSL/TLS certificate validation
- Port exposure analysis

## 🏗️ Architecture

```
User → React (Firebase SDK) → FastAPI API (Firebase token verified) → MongoDB / Redis / ML / Stripe
```

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+, async/await)
- MongoDB Atlas (user data, assets, risk scores)
- Redis (rate limiting, task queue, caching)
- scikit-learn (Logistic Regression for risk scoring)
- Firebase Admin SDK (authentication)

**Frontend:**
- React 18 + Vite
- TailwindCSS (dark theme)
- Recharts (data visualization)
- Firebase Web SDK
- Axios (API client)

**External APIs:**
- Censys (asset discovery)
- Shodan (asset discovery)
- HaveIBeenPwned (breach history)
- Stripe (payments)

**Hosting:**
- Backend: Render
- Frontend: Netlify
- Database: MongoDB Atlas
- Cache/Queue: Redis Cloud

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
│   │   ├── collectors/         # External API collectors
│   │   │   ├── censys_collector.py
│   │   │   ├── shodan_collector.py
│   │   │   ├── merger.py       # Result merging
│   │   │   └── enrichers.py    # Data enrichment
│   │   ├── core/               # Core infrastructure
│   │   │   ├── firebase.py     # Firebase Admin SDK
│   │   │   ├── database.py     # MongoDB connection
│   │   │   └── redis_client.py # Redis connection
│   │   ├── middleware/         # Middleware
│   │   │   └── auth.py         # Firebase auth middleware
│   │   ├── ml/                 # Machine learning
│   │   │   ├── train_model.py  # Model training
│   │   │   └── models/         # Trained models
│   │   ├── tasks/              # Background workers
│   │   │   ├── scan_worker.py  # Scan executor
│   │   │   └── scheduler.py    # Rescan scheduler
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
- Redis instance (local or cloud)
- Firebase project (with Authentication enabled)
- Censys API credentials
- Shodan API key
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

### 3. Redis Setup

**Option A: Local Redis**
```bash
# Install Redis (macOS)
brew install redis
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:latest
```

**Option B: Redis Cloud**
- Sign up at [https://redis.com/try-free/](https://redis.com/try-free/)
- Create a database and get connection URL

### 4. Backend Setup

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

# Redis
REDIS_URL=redis://localhost:6379  # or your Redis Cloud URL

# Censys API (get from https://search.censys.io/account/api)
CENSYS_API_ID=your_censys_id
CENSYS_API_SECRET=your_censys_secret

# Shodan API (get from https://account.shodan.io/)
SHODAN_API_KEY=your_shodan_key

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

**Start background worker (separate terminal):**
```bash
rq worker scan_queue --with-scheduler
```

### 5. Frontend Setup

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

## 📚 API Documentation

### Authentication

All protected routes require Firebase ID token in Authorization header:
```
Authorization: Bearer <firebase_id_token>
```

### Key Endpoints

**Authentication:**
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Sync user data
- `GET /api/auth/me` - Get current user

**Asset Discovery:**
- `POST /api/assets/scan` - Start new scan
- `GET /api/assets` - List assets (with pagination & filters)
- `GET /api/assets/{asset_id}` - Get asset details

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

Full API documentation available at `/docs` when running the backend.

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
- Redis uses authentication
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

**"Redis connection refused"**
- Ensure Redis server is running (local or cloud)
- Check `REDIS_URL` format

**"Collector returns no results"**
- Verify Censys and Shodan API credentials
- Check API quotas (free tiers have limits)
- Test credentials directly with API documentation

**"Frontend can't connect to backend"**
- Ensure backend is running on correct port
- Check `VITE_API_URL` in frontend `.env`
- Verify CORS is configured correctly

## 📧 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Email: support@reconai.com (example)
- Documentation: [https://docs.reconai.com](https://docs.reconai.com) (example)

## 🙏 Acknowledgments

- Firebase for authentication infrastructure
- Censys and Shodan for asset discovery data
- MongoDB Atlas for database hosting
- Stripe for payment processing
- Open source community for amazing libraries

---

**Made with ❤️ for the security community**
