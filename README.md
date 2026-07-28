# Sports Injury Risk Detection (MoveIQ)

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14%2B-black.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

An advanced, AI-assisted computer vision and biomechanical analysis platform designed to evaluate athletic movements (squats, lunges, jumps, running), calculate injury risk scores, and deliver personalized AI corrective exercise plans. Features a comprehensive web dashboard, real-time operations telemetry, and role-based access control (RBAC).

---

## 🌟 Key Features & Architecture Overview

The system operates across a multi-layered architecture combining computer vision, biomechanical math models, large language models, and enterprise-grade system operations:

### 1. 🎥 Four-Stage AI & Biomechanics Pipeline
- **Stage 1: Pose Landmark Extraction**: Utilizes MediaPipe & OpenCV to track 33 3D body landmarks frame-by-frame from uploaded videos or live webcam feeds.
- **Stage 2: Biomechanical Analysis**: Evaluates kinematic joint angles (knee flexion, hip flexion, ankle dorsiflexion), balance sway, dynamic valgus, and left-vs-right body asymmetries.
- **Stage 3: Demographics-Aware Risk Scoring**: Combines real-time kinematics with historical athlete profiles (Height, Weight/BMI, Age, Gender, Sport, Previous Injuries) stored in MongoDB to compute an overall 0–100 Health Score and Risk Category (Low, Moderate, High, Severe).
- **Stage 4: AI Recommendation Engine (LangGraph & Groq)**: Triggers an LLM orchestration workflow to translate biomechanical flaws into plain-English summaries and assign targeted corrective rehab exercises.

### 2. 🖥️ Full-Stack Web Application (Next.js & React)
- **Modern Acetternity & Tailwind UI**: Features a sleek, dynamic interface with glassmorphism, smooth animations, and interactive data visualization charts.
- **Full Theme Support (Light & Dark Mode)**: System-wide theme switcher integrated into user settings, seamlessly adapting dashboards, charts, and analysis tables.
- **Client-Side PDF Report Generation**: Dynamically renders and compiles high-resolution A4 diagnostic reports natively in the browser using React, `html-to-image`, and `jsPDF`.

### 3. 🛡️ Operations & Admin Portal (RBAC)
- **Role-Based Access Control**: Secure separation between Athletes, Coaches, and Operations Admins.
- **Real-Time System Diagnostics**: Live health telemetry tracking MongoDB/MySQL connection latency, memory utilization, API uptime, and storage health.
- **Analytics & Audit Logging**: System-wide analytics dashboards tracking risk distributions, session volume, error rates, and security audit logs.
- **Account Provisioning**: Admins can inspect users, modify roles, and monitor system-wide activity.

### 4. ☁️ Enterprise Cloud & Storage Layer
- **Stateless Server Processing**: Temporary video frames and CSVs are automatically purged after pipeline execution to ensure zero server bloat.
- **Cloudinary Media Storage**: Processed videos and key annotated moment thumbnails are uploaded directly to Cloudinary and linked via secure CDN URLs in MongoDB.
- **Dual-Database Persistence**:
  - **MySQL / Supabase PostgreSQL**: Stores user identities, hashed passwords (`bcrypt`), and authentication roles.
  - **MongoDB Atlas**: Stores flexible document schemas for athlete profiles, session metadata, frame-by-frame biomechanics, risk scores, and AI recommendation reports.

---

## 📁 Repository Structure

```text
Sports-Injury-Risk-/
├── api/                     # FastAPI backend server & REST endpoints
│   ├── auth/                # MySQL / PostgreSQL authentication & JWT handlers
│   ├── routers/             # API route controllers (auth, profile, sessions, recommendations, ops, coach, cloudinary)
│   └── utils/               # Helper utilities (email notifications, security)
├── frontend/                # Next.js 14 / Tailwind CSS Web Application
│   ├── src/app/             # App router pages (dashboard, analysis, reports, settings, ops portal)
│   └── src/components/      # Reusable UI components and visual charts
├── src/                     # Core AI & Biomechanics Python Engine
│   ├── main.py              # Pipeline execution entry point
│   ├── pose_extractor.py    # MediaPipe 3D pose extraction script
│   ├── config.py            # Global thresholds, joint limits, and directory paths
│   ├── biomechanics/        # Pure math calculators and symmetry analyzers
│   ├── risk_scoring/        # Health score algorithms and demographic multipliers
│   └── recommendations/     # LangGraph workflows and LLM prompts
├── database/                # Database connection managers (MongoDB, Cloud Storage)
├── scripts/                 # Maintenance and administrative seeding scripts
├── tests/                   # Modular component-by-component and end-to-end test suite
└── Docs/                    # Architectural and database schema documentation
```

---

## 🚀 Getting Started & Installation

### 1. Prerequisites
**Backend (AI Pipeline & API Server):**
- **Python 3.10+**
- **MongoDB Atlas** (or local MongoDB instance)
- **MySQL / Supabase PostgreSQL** database
- **Cloudinary Account** (for video storage)
- **Groq API Key** (for AI recommendations)

**Frontend (Web Dashboard):**
- **Node.js 18+** & **npm** (Only required if running the Next.js web interface in `frontend/`)

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
# Database Connections
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/sports_db
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=sports_injury_db
USE_LOCAL_DB=false

# Cloud Storage & AI Keys
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
GROQ_API_KEY=gsk_your_groq_api_key_here

# Security & JWT Auth
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Start the FastAPI backend server:
```bash
uvicorn api.server:app --reload --port 8000
```
*API Swagger Documentation will be live at: `http://localhost:8000/docs`*

### 3. Frontend Setup
Open a new terminal, navigate to the frontend directory, and start the Next.js development server:
```bash
cd frontend
npm install
npm run dev -- -p 3000
```
*The web dashboard will be accessible at: `http://localhost:3000`*

---

## 🛠️ Administrative & Maintenance Scripts

### Seeding an Operations Admin Account
To create an initial Operations Admin user for accessing the `/ops` portal:
```bash
python scripts/seed_ops_mysql.py
```
This script provisions an admin account in MySQL (Default: `debabratadey9090@gmail.com`) with role `ops_admin`, granting full access to system telemetry, analytics dashboards, and audit logs.

---

## 🧪 Testing Infrastructure

The project includes a fully modular, dependency-isolated testing suite located in `tests/`. It includes synthetic mock video generators (`mock_data.py`) so tests run cleanly without requiring external video downloads or live cloud database connections.

### Test Components:
- `test_01_pose_extractor.py`: Validates video reading and landmark CSV creation.
- `test_02_biomechanics.py`: Validates kinematic angle calculations and symmetry math.
- `test_03_risk_scoring.py`: Validates injury risk category assignment and demographic multipliers.
- `test_04_recommendations.py`: Validates LangGraph LLM workflow and structured summaries.
- `test_05_databases_and_storage.py`: Validates Cloudinary upload mocking and DB schemas.
- `test_06_end_to_end.py`: Runs the full 4-stage pipeline sequentially on synthetic video data.

To run the complete test suite:
```bash
pytest -v
```

---

## 📚 Documentation
- **API Reference**: Detailed REST endpoint documentation is available in [API.md](./API.md).
- **Admin Architecture**: System administration and telemetry details are available in [admin.md](./admin.md).
- **Database Schema**: Comprehensive database migration and collection schemas are documented in [Docs/New_DB_Schema_design.md](./Docs/New_DB_Schema_design.md).

---
*Disclaimer: This is an AI-assisted sports movement screening tool. It is designed for biomechanical evaluation and training optimization, not as a direct medical diagnosis.*