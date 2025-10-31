# ReconAI

ReconAI is a compact OSINT platform that helps you discover, monitor, and assess internet-facing assets. It includes asset discovery, basic enrichment, ML-based risk scoring, and a simple dashboard.

This repository contains a backend (FastAPI + MongoDB) and a frontend (React + Vite).

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

## Key features

- Asset discovery (domains, subdomains, IPs)
- Basic enrichment (SSL, headers, ports)
- ML risk scoring (simple model and thresholds)
- REST API with OpenAPI docs
- React frontend with dashboard

## Quick start

1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
# edit .env with MONGO_URI and FIREBASE_* values
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

- Update `backend/.env` from `backend/.env.example` (MongoDB, Firebase, Stripe)
- Update `frontend/.env` (VITE*API_URL, VITE_FIREBASE*\* keys)

## Docs

- API reference: `API.md`
- Architecture: `ARCHITECTURE.md`

## License

MIT — see LICENSE

---

Simple and focused. For full technical details see `API.md` and `ARCHITECTURE.md`.

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

````

**Train ML model:**

```bash
python -m app.ml.train_model
````

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

# ReconAI — Simple README

ReconAI is an OSINT tool for discovering and scoring internet-facing assets.

Quick start

Backend:

```
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# edit backend/.env with MONGO_URI and FIREBASE_* values
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```
cd frontend
npm install
npm run dev
```

Notes

- Copy environment variables from `.env.example` and do not commit your `.env` files.
- API docs available at `http://localhost:8000/docs` when the backend is running.

Links

- API reference: `API.md`
- Architecture: `ARCHITECTURE.md`

License: MIT
