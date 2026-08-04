# MoveIQ — Sports Injury Risk Analysis Platform

> AI-powered biomechanics analysis platform for athletes and coaches. Upload a movement video, get instant injury risk scores, AI-generated rehab recommendations, and real-time coaching insights.

---

## ✨ Features

### For Athletes
- **Video Analysis** — Upload squat/jump/sprint videos for automated pose extraction using MediaPipe
- **Injury Risk Scoring** — Overall Health Score, Final Risk Score, Biomechanical Efficiency, and Movement Quality
- **AI Recommendations** — Personalised rehab, mobility, and training protocols powered by Google Gemini AI
- **Analysis History** — Track personal biomechanics trends over time
- **PDF Reports** — Download comprehensive session reports with charts and metrics
- **Real-Time Notifications** — Instant in-app alerts for analysis completion and coach messages

### For Coaches
- **Athlete Roster Management** — Add, remove, and monitor assigned athletes
- **Team Management** — Create and manage training groups
- **Risk Dashboard** — Aggregated risk distribution view across all athletes
- **Session Review** — Access any athlete's latest analysis and notes
- **Real-Time Chat** — Direct messaging with athletes including read receipts and unread badges

### Platform
- **Google OAuth** — Sign in with Google for athletes and coaches
- **OTP Email Verification** — Secure signup and password reset via emailed OTPs
- **WebSocket Notifications** — Live push notifications via Redis Pub/Sub (no polling)
- **WebSocket Chat** — Real-time bidirectional messaging with blue tick read receipts
- **Webhook System** — External event delivery for third-party integrations
- **Admin Panel** — User management, role control, and platform analytics
- **Collapsible Sidebar** — Responsive navigation with icons for both dashboards
- **Dark Mode Support** — Premium UI supporting light and dark themes

---

## 🏗️ Architecture (5 Layers)

```
[Browser / Mobile]
      ↕ HTTP + WebSocket
[Next.js 16 Frontend]         ← Presentation Layer
      ↕ REST API + WS
[FastAPI Routers]             ← API Layer
      ↕
[Business Logic / Celery]     ← Logic Layer (ML, AI, Workers)
      ↕
[database/ utils]             ← Data Access Layer
      ↕            ↕             ↕           ↕
[PostgreSQL]   [MongoDB]   [Redis]   [Cloudinary]   ← DB & Storage Layer
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React, TypeScript, Vanilla CSS, Lucide Icons, Recharts |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI / ML** | Google Gemini AI, MediaPipe, OpenCV |
| **Relational DB** | PostgreSQL (Supabase) / MySQL (local dev) |
| **Document DB** | MongoDB Atlas |
| **Cache / Pub-Sub** | Redis (Upstash for production) |
| **File Storage** | Cloudinary |
| **Background Tasks** | Celery + Redis broker |
| **Auth** | JWT (HS256), Google OAuth 2.0, Bcrypt |
| **Email** | SMTP via Celery tasks |

---

## ⚙️ Prerequisites

- **Node.js** v18+
- **Python** 3.10+
- **Redis** (local or Upstash cloud)
- **PostgreSQL** (local or Supabase) OR **MySQL** (local dev)
- **MongoDB** (local or MongoDB Atlas)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Debabrata7719/MoveIQ.git
cd MoveIQ
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Database Setup
```bash
# Run this once to create all PostgreSQL tables:
python scripts/setup_coach_db.py

# Seed your admin account:
python api/scripts/seed_admin.py
```

---

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# --- SQL Database (pick one) ---
DATABASE_URL=postgresql://user:password@host:5432/moveiq
USE_LOCAL_DB=false              # Set to true to use MySQL instead

# MySQL (only if USE_LOCAL_DB=true)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=sports_injury_detection

# --- MongoDB ---
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGO_DB_NAME=moveiq_db

# --- Redis ---
REDIS_URL=redis://localhost:6379  # or Upstash: rediss://...

# --- JWT Auth ---
SECRET_KEY=your_super_secret_jwt_key_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# --- AI / ML ---
GEMINI_API_KEY=your_google_gemini_api_key

# --- Google OAuth ---
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# --- Cloudinary (Video Storage) ---
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# --- Email (SMTP) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# --- App ---
FRONTEND_URL=http://localhost:3000
```

---

## ▶️ Running the App

**Terminal 1 — Backend API:**
```bash
uvicorn api.server:app --reload --port 8000
```

**Terminal 2 — Celery Worker (background tasks/emails):**
```bash
celery -A src.worker.celery_app worker --loglevel=info -Q high_priority,default
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 📁 Project Structure

```
MoveIQ/
├── api/
│   ├── routers/              # FastAPI route handlers
│   │   ├── auth_router.py    # Auth, registration, Google OAuth
│   │   ├── chat_router.py    # REST chat endpoints + unread counts
│   │   ├── coach_router.py   # Coach-athlete management
│   │   ├── sessions_router.py# Video upload and analysis
│   │   ├── ws_router.py      # WebSocket: chat, notifications, progress
│   │   ├── notifications_router.py
│   │   └── webhook_router.py
│   ├── auth/                 # JWT handler, password utils
│   ├── utils/                # Redis utils, helpers
│   ├── scripts/
│   │   └── seed_admin.py     # Create admin account from CLI
│   └── server.py             # FastAPI app entry point
│
├── database/
│   ├── postgres_utils.py     # All PostgreSQL query functions
│   ├── mysql_utils.py        # All MySQL query functions (local dev)
│   ├── mongo_utils.py        # All MongoDB query functions
│   ├── sql_utils.py          # Auto-selects Postgres or MySQL
│   └── cloud_storage.py      # Cloudinary integration
│
├── src/
│   ├── worker/               # Celery tasks (email, analysis)
│   └── ...                   # ML pipeline, pose estimation
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx      # Main dashboard router
│   │   ├── components/ui/
│   │   │   ├── ChatWidget.tsx # Real-time chat panel (portal-based)
│   │   │   ├── sidebar.tsx    # Collapsible navigation sidebar
│   │   │   └── ...
│   │   └── hooks/
│   │       └── useChatSocket.ts # WebSocket chat hook
│   └── public/
│
├── scripts/
│   ├── list_users.py         # CLI: list all registered users
│   ├── setup_coach_db.py     # DB migration: create all tables
│   ├── setup_supabase.py     # DB migration: Supabase setup
│   └── setup_webhooks_db.py  # DB migration: webhooks table
│
├── Docs/
│   ├── db schema design/
│   │   ├── postgresql_schema.sql  # Full PostgreSQL schema backup
│   │   └── mysql_schema.sql       # Full MySQL schema backup
│   └── Scaling&Bugs/
│       ├── 1_Presentation_Layer.md
│       ├── 2_API_Layer.md
│       ├── 3_Business_Logic_Layer.md
│       ├── 4_Data_Access_Layer.md
│       └── 5_Database_Storage_Layer.md
│
├── requirements.txt
├── API.md                    # Full API endpoint reference
└── README.md                 # This file
```

---

## 🔒 Security Notes

Before deploying to production, review `Docs/Scaling&Bugs/2_API_Layer.md` for critical security fixes including:
- Restricting CORS origins
- Adding rate limiting to auth endpoints
- Upgrading OTP to 6 digits with secure random generation
- Moving JWT tokens out of OAuth redirect URLs

---

## 📖 API Documentation

See [API.md](./API.md) for full endpoint reference, or visit `http://localhost:8000/docs` for the interactive Swagger UI.