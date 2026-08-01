# Sports Injury Risk Detection (MoveIQ) — API Reference

This document provides a comprehensive specification of the RESTful API built with **FastAPI** to connect the web frontend with the core Python computer vision, biomechanics, and AI recommendation engines.

---

## 🚀 Server Launch & Interactive Documentation

Start the API server locally using Uvicorn:
```bash
uvicorn api.server:app --reload --port 8000
```

Once running, interactive Swagger API documentation with live testing capabilities is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`

---

## 🔒 Authentication & Security Architecture

All protected endpoints require a valid **JSON Web Token (JWT)** passed in the HTTP Authorization header:
```http
Authorization: Bearer <your_jwt_access_token>
```

### Security & Identity Rules:
1. **Stateless Identity Extraction**: The backend strictly ignores any `athlete_id` or user identifier passed in request bodies or query strings for authorization. The authenticated user's identity and role are derived mathematically from the verified JWT payload.
2. **Role-Based Access Control (RBAC)**: The API enforces three primary user roles:
   - **`athlete`**: Can upload videos, view personal session history, update own profile, and generate personal rehab recommendations.
   - **`coach`**: Can access assigned athletes' profiles, review session histories, and attach coach feedback notes.
   - **`ops_admin`**: Granted system-wide access to administrative diagnostics, real-time telemetry, audit logs, and user account management.

---

## 🔗 Endpoint Groups

### 1. Authentication & Account Management (`/api/auth`)
Manages user registration, login, JWT token issuance, and account profile updates using MySQL / Supabase PostgreSQL and `bcrypt` password hashing.

- **`POST /api/auth/register`**
  - **Description**: Registers a new user account in the SQL database.
  - **Request Body**:
    ```json
    {
      "email": "athlete@example.com",
      "password": "SecurePassword123!",
      "full_name": "Alex Morgan",
      "role": "athlete"
    }
    ```
  - **Response**: `201 Created` — `{"message": "User created successfully", "user_id": 1}`

- **`POST /api/auth/login`**
  - **Description**: Authenticates user credentials and issues a JWT access token.
  - **Request Body**:
    ```json
    {
      "email": "athlete@example.com",
      "password": "SecurePassword123!"
    }
    ```
  - **Response**: `200 OK` — `{"access_token": "eyJhbGciOi...", "token_type": "bearer", "user": {"id": 1, "email": "...", "role": "athlete"}}`

- **`GET /api/auth/me`** *(Requires JWT)*
  - **Description**: Returns the decoded profile information and role of the currently authenticated user.
  - **Response**: `200 OK` — `{"id": 1, "email": "athlete@example.com", "full_name": "Alex Morgan", "role": "athlete"}`

- **`PUT /api/auth/account`** *(Requires JWT)*
  - **Description**: Updates the authenticated user's display name and email address.
  - **Request Body**: `{"full_name": "Alex M. Morgan", "email": "alex.new@example.com"}`
  - **Response**: `200 OK` — `{"message": "Account updated successfully"}`

- **`PUT /api/auth/password`** *(Requires JWT)*
  - **Description**: Securely changes the user's password after verifying their current password.
  - **Request Body**: `{"old_password": "OldPassword123!", "new_password": "NewSecurePassword456!"}`
  - **Response**: `200 OK` — `{"message": "Password updated successfully"}`

---

### 2. Athlete Historical Profiles (`/api/profile`)
Handles reading and upserting athlete historical and demographic data stored in MongoDB. Demographics are critical as they act as baseline multipliers in the Stage 3 Risk Scoring Engine.

- **`GET /api/profile`** *(Requires JWT)*
  - **Description**: Retrieves the authenticated athlete's demographic and injury history profile from MongoDB (`athlete_profiles` collection).
  - **Response**: `200 OK`
    ```json
    {
      "athlete_id": "athlete_001",
      "age": 24,
      "gender": "Female",
      "height": 170,
      "weight": 65,
      "sport": "Soccer",
      "has_previous_injury": "Yes",
      "previous_injury_type": "Ankle Sprain",
      "injury_recency": "3 months ago",
      "training_intensity": "High",
      "weekly_training_sessions": 4
    }
    ```

- **`POST /api/profile`** | **`PUT /api/profile`** *(Requires JWT)*
  - **Description**: Creates or updates the athlete's demographic and training history profile in MongoDB.
  - **Request Body**: Matches the JSON structure returned in `GET /api/profile`.
  - **Response**: `200 OK` — `{"message": "Profile updated successfully"}`

---

### 3. Video Sessions & AI Analysis (`/api/sessions`)
Bridges the web frontend to the core Python computer vision and biomechanical analysis pipeline (`src.main`).

- **`POST /api/sessions/upload-and-analyze`** *(Requires JWT)*
  - **Description**: Accepts a raw video upload, generates a unique UUID session, executes the MediaPipe pose extractor and biomechanical analyzer, stores frame-by-frame data in MongoDB, extracts Base64 key-moment frames, and deletes local temporary files.
  - **Payload**: `multipart/form-data` with form field `video` containing the MP4/MOV file.
  - **Response**: `200 OK`
    ```json
    {
      "session_id": "c597-4c20-9be9-380e354b36fb",
      "video_name": "squat_test",
      "status": "completed",
      "video_url": "https://res.cloudinary.com/.../squat_test.mp4",
      "risk_data": {
        "overall_health_score": 78.5,
        "risk_category": "Low Risk",
        "flagged_issues": "Minor asymmetry in ankle dorsiflexion"
      }
    }
    ```

- **`GET /api/sessions/history`** *(Requires JWT)*
  - **Description**: Fetches all historical analysis sessions associated with the authenticated user (sorted newest to oldest).
  - **Response**: `200 OK` — Array of session summary objects.

- **`GET /api/sessions/{session_id}`** *(Requires JWT)*
  - **Description**: Retrieves full metadata, joint angle charts, and key-moment frames for a specific analysis session. Enforces strict ownership checks unless requested by an authorized coach or admin.
  - **Response**: `200 OK` — Full session document including `biomechanics` and `risk_scores` sub-objects.

---

### 4. AI Recommendation Engine (`/api/recommendations`)
Integrates with LangGraph and Groq LLMs to generate personalized rehabilitation and training programs based on detected biomechanical flaws.

- **`POST /api/recommendations/{session_id}/generate`** *(Requires JWT)*
  - **Description**: Triggers `src.recommendations.engine` to analyze the session's risk score and flagged issues, formulating a structured exercise plan and plain-English diagnostic summary.
  - **Response**: `200 OK` — `{"message": "Recommendations generated successfully", "summary": "..."}`

- **`GET /api/recommendations/{session_id}`** *(Requires JWT)*
  - **Description**: Retrieves the structured recommendation report from MongoDB (`recommendations` collection).
  - **Response**: `200 OK`
    ```json
    {
      "session_id": "c597-4c20-9be9-380e354b36fb",
      "structured_summary": {
        "one_line_summary": "Overall good squat mechanics with mild right knee inward collapse during ascent.",
        "key_findings": ["Knee valgus angle reached 14° on right leg", "Good hip flexion depth maintained"],
        "action_plan": "Focus on glute medius strengthening and neuromuscular knee alignment cues."
      },
      "recommended_exercises": {
        "Knee Stability": [
          {"name": "Banded Clamshells", "sets": "3 sets of 15 reps", "notes": "Keep feet together and control descent"}
        ],
        "Hip Mobility": [
          {"name": "90/90 Hip Stretch", "sets": "2 sets of 60s per side", "notes": "Maintain upright torso"}
        ]
      }
    }
    ```

---

### 5. Operations & Admin Telemetry (`/api/ops`)
Protected endpoints reserved for users with the `ops_admin` role. Power the real-time Operations Portal dashboard.

- **`GET /api/ops/diagnostics`** *(Requires `ops_admin` role)*
  - **Description**: Returns live system telemetry, health checks, and connection latency for MongoDB, MySQL, and cloud storage.
  - **Response**: `200 OK`
    ```json
    {
      "status": "healthy",
      "timestamp": "2026-07-26T16:30:00Z",
      "databases": {
        "mongodb": {"status": "connected", "latency_ms": 14.2, "db_name": "sports_injury_db"},
        "mysql": {"status": "connected", "latency_ms": 5.8}
      },
      "system": {
        "cpu_usage_pct": 12.4,
        "memory_usage_pct": 45.1,
        "disk_free_gb": 112.5
      }
    }
    ```

- **`GET /api/ops/analytics`** *(Requires `ops_admin` role)*
  - **Description**: Aggregates system-wide usage metrics, total sessions processed, risk category distributions, and athlete demographic summaries.
  - **Response**: `200 OK` — Aggregated analytics statistics for chart rendering.

- **`GET /api/ops/audit-logs`** *(Requires `ops_admin` role)*
  - **Description**: Retrieves chronological security and system audit logs (logins, role changes, error spikes, pipeline failures).
  - **Query Parameters**: `?limit=50&offset=0`
  - **Response**: `200 OK` — Array of audit log entry objects.

- **`GET /api/ops/users`** | **`PUT /api/ops/users/{user_id}/role`** *(Requires `ops_admin` role)*
  - **Description**: Allows administrators to inspect registered accounts and modify user roles (e.g., promoting an athlete to coach or admin).
  - **Request Body (PUT)**: `{"role": "coach"}`
  - **Response**: `200 OK` — `{"message": "User role updated successfully"}`

---

### 6. Coach & Athlete Monitoring (`/api/coach`)
Allows coaches to monitor assigned athletes and attach professional feedback.

- **`GET /api/coach/athletes`** *(Requires `coach` or `ops_admin` role)*
  - **Description**: Retrieves a list of all athletes assigned to the authenticated coach.
  - **Response**: `200 OK` — Array of athlete profile summaries.

- **`POST /api/coach/sessions/{session_id}/notes`** *(Requires `coach` role)*
  - **Description**: Attaches coach feedback notes or customized rehab modifications to an athlete's session analysis.
  - **Request Body**: `{"coach_notes": "Great improvement on squat depth! Continue focusing on keeping knees tracking over toes."}`
  - **Response**: `200 OK` — `{"message": "Coach notes saved successfully"}`

---

### 7. Cloudinary Media Management (`/api/cloudinary`)
Handles direct media interactions and signature generation for frontend CDN optimization.

- **`DELETE /api/cloudinary/video/{public_id}`** *(Requires JWT)*
  - **Description**: Deletes a hosted video asset from Cloudinary storage upon session deletion.
  - **Response**: `200 OK` — `{"message": "Media deleted successfully"}`

---

## 📄 Client-Side PDF Generation Note
To maximize server performance and maintain stateless backend execution, the API no longer compiles PDF documents on the server. Instead, the backend serves structured JSON data from `/api/recommendations/{session_id}`. The Next.js frontend uses React components styled as A4 reports, capturing them into high-resolution canvases via `html-to-image` and generating downloadable PDFs natively in the user's browser using `jsPDF`.
