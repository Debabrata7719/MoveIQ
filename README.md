# Sports Injury Risk Detection (MoveIQ)

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14%2B-black.svg)
![Celery](https://img.shields.io/badge/Celery-5.3%2B-lightgreen.svg)
![Redis](https://img.shields.io/badge/Redis-7.0%2B-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

An advanced, AI-assisted computer vision and biomechanical analysis platform designed to evaluate athletic movements (squats, lunges, jumps, running), calculate injury risk scores, and deliver personalized AI corrective exercise plans. Features a comprehensive web dashboard, real-time operations telemetry, and fully asynchronous video processing.

---

## 🌟 Key Features & Architecture Overview

The system operates across a multi-layered architecture combining computer vision, biomechanical math models, large language models, and enterprise-grade system operations:

### 1. 🎥 Four-Stage AI & Biomechanics Pipeline
- **Stage 1: Pose Landmark Extraction**: Utilizes MediaPipe & OpenCV to track 33 3D body landmarks frame-by-frame from uploaded videos.
- **Stage 2: Biomechanical Analysis**: Evaluates kinematic joint angles (knee flexion, hip flexion, ankle dorsiflexion), balance sway, dynamic valgus, and left-vs-right body asymmetries.
- **Stage 3: Demographics-Aware Risk Scoring**: Combines real-time kinematics with historical athlete profiles (Height, Weight/BMI, Age, Gender, Sport, Previous Injuries) stored in MongoDB to compute an overall 0–100 Health Score and Risk Category.
- **Stage 4: AI Recommendation Engine (LangGraph & Groq)**: Triggers an LLM orchestration workflow to translate biomechanical flaws into plain-English summaries and assign targeted corrective rehab exercises.

### 2. ⚡ Asynchronous Task Queue & WebSockets (Real-time UX)
- **Celery & Redis Architecture**: Heavy video processing (MediaPipe + LLM inferencing) is offloaded to a background Celery worker cluster, ensuring the FastAPI web server remains blazing fast and unblocked.
- **WebSocket Pub/Sub**: The backend streams live processing status (e.g., "Extracting Landmarks...", "Scoring Risk...") over WebSockets to the Next.js frontend using Redis Pub/Sub, providing users with a beautiful, real-time progress bar instead of loading spinners.

### 3. 🖥️ Full-Stack Web Application (Next.js & React)
- **Modern Acetternity & Tailwind UI**: Features a sleek, dynamic interface with glassmorphism, smooth animations, and interactive data visualization charts.
- **Full Theme Support (Light & Dark Mode)**: System-wide theme switcher integrated into user settings, seamlessly adapting dashboards, charts, and analysis tables.
- **Client-Side PDF Report Generation**: Dynamically renders and compiles high-resolution A4 diagnostic reports natively in the browser using React, `html-to-image`, and `jsPDF`.


### 4. ☁️ Enterprise Cloud & Storage Layer
- **Stateless Server Processing**: Temporary video frames and CSVs are automatically purged after pipeline execution to ensure zero server bloat.
- **Multi-Environment Databases**: 
  - Easily toggle between local development databases and cloud production databases (Supabase, MongoDB Atlas, Upstash Redis) using the `USE_LOCAL_DB` environment flag.
  - **MySQL / PostgreSQL**: Stores user identities, hashed passwords (`bcrypt`), and authentication roles.
  - **MongoDB**: Stores flexible document schemas for athlete profiles, session metadata, frame-by-frame biomechanics, risk scores, and AI recommendation reports.
  - **Redis**: Acts as the Celery Message Broker, WebSocket Pub/Sub channel, and OTP verification cache.

---

## 📁 Repository Structure

```text
Sports-Injury-Risk-/
├── api/                     # FastAPI backend server & REST endpoints
│   ├── auth/                # MySQL / PostgreSQL authentication & JWT handlers
│   ├── routers/             # API controllers (auth, profiles, sessions, coach, websockets)
│   └── utils/               # Utilities (email notifications, redis url parsing, security)
├── frontend/                # Next.js 14 / Tailwind CSS Web Application
│   ├── src/app/             # App router pages (dashboard, analysis, reports, settings)
│   └── src/components/      # Reusable UI components and visual charts
├── src/                     # Core AI & Biomechanics Python Engine
│   ├── main.py              # Pipeline execution entry point
│   ├── pose_extractor.py    # MediaPipe 3D pose extraction script
│   ├── config.py            # Global thresholds, joint limits, and directory paths
│   ├── worker/              # Celery worker application & async task definitions
│   ├── biomechanics/        # Pure math calculators and symmetry analyzers
│   ├── risk_scoring/        # Health score algorithms and demographic multipliers
│   └── recommendations/     # LangGraph workflows and LLM prompts
├── database/                # Database connection managers (MongoDB, MySQL)
├── scripts/                 # Maintenance and administrative seeding scripts
├── tests/                   # Modular component-by-component and end-to-end test suite
└── Docs/                    # Architectural and database schema documentation
```

---

## 🚀 Getting Started & Installation

### 1. Prerequisites
**Backend (AI Pipeline, API Server & Worker):**
- **Python 3.10+**
- **Redis Server** (Run via Docker: `docker run -d -p 6379:6379 redis`)
- **MongoDB Atlas** (or local MongoDB instance)
- **MySQL / Supabase PostgreSQL**
- **Cloudinary Account** (for video storage)
- **Groq API Key** (for AI recommendations)

**Frontend (Web Dashboard):**
- **Node.js 18+** & **npm**

### 2. Backend Setup
Clone the repository and set up the Python virtual environment:
```bash
git clone <repository-url>
cd Sports-Injury-Risk-
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your credentials:
```env
# Multi-Environment Toggle (true = localhost, false = Cloud providers)
USE_LOCAL_DB=true

# Database Connections (MySQL & Mongo)
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/sports_db
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=sports_injury_db

# Redis Connections (Celery & WebSockets)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_CELERY_URL=rediss://default:your-cloud-pass@your-cloud-url:6379
UPSTASH_REDIS_REST_URL=https://your-upstash-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_token

# Cloud Storage & AI Keys
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
GROQ_API_KEY=gsk_your_groq_api_key_here

# Security & JWT Auth
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 3. Running the Stack (3 Terminal Setup)

To run the application, you need to spin up the API server, the background Celery worker, and the Next.js frontend.

**Terminal 1: FastAPI Server**
```bash
uvicorn api.server:app --reload --port 8000
```
*API Swagger Docs live at: `http://localhost:8000/docs`*

**Terminal 2: Celery Worker (Background Video Processor)**
```bash
# On Mac/Linux:
celery -A src.worker.celery_app worker --concurrency=4 --loglevel=info

# On Windows:
celery -A src.worker.celery_app worker --pool=solo --loglevel=info
```

**Terminal 3: Next.js Frontend**
```bash
cd frontend
npm install
npm run dev -- -p 3000
```
*Web dashboard lives at: `http://localhost:3000`*


---

## 🧪 Testing Infrastructure

The project includes a fully modular testing suite located in `tests/`. It includes synthetic mock video generators (`mock_data.py`) so tests run cleanly without requiring external video downloads or live cloud database connections.

To run the complete test suite:
```bash
pytest -v
```

---

## 📚 Documentation
- **API Reference**: Detailed REST endpoint documentation is available in [API.md](./API.md).
- **Database Schema**: Comprehensive database migration and collection schemas are documented in [Docs/New_DB_Schema_design.md](./Docs/New_DB_Schema_design.md).
- **Architecture Updates**: To read about our Celery queue and WebSockets migration, see [Walkthrough](./brain/12224a28-c597-4c20-9be9-380e354b36fb/walkthrough.md).

---
*Disclaimer: This is an AI-assisted sports movement screening tool. It is designed for biomechanical evaluation and training optimization, not as a direct medical diagnosis.*