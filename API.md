# API Reference

This document outlines the core RESTful API endpoints available in the MoveIQ backend.

## Base URL
All endpoints are relative to the following base URL during local development:
`http://localhost:8000/api`

## Authentication
Most API endpoints require authentication via JSON Web Tokens (JWT). 
When making a request to a protected endpoint, you must include the token in the `Authorization` header as a Bearer token.

**Format:**
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. User Registration
Register a new coach or athlete account.

**Method & Path:** 
`POST /auth/register`

**Description:** 
Creates a new user and returns a JWT access token.

**Request Body:** (JSON)
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "role": "athlete" // or "coach"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "full_name": "John Doe", "role": "athlete"}'
```

**Example Response:** (201 Created)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-1234",
    "email": "user@example.com",
    "role": "athlete"
  }
}
```

**Status/Error Codes:**
- `201 Created` - User registered successfully.
- `400 Bad Request` - Email already registered or invalid data.

---

### 2. User Login
Authenticate a user and retrieve a JWT.

**Method & Path:** 
`POST /auth/login`

**Description:** 
Validates credentials and returns an access token.

**Request Body:** (JSON or Form Data)
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Example Response:** (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer"
}
```

**Status/Error Codes:**
- `200 OK` - Login successful.
- `401 Unauthorized` - Incorrect email or password.

---

### 3. Upload Video for Analysis
Upload a video of an athletic movement for AI biomechanical analysis.

**Method & Path:** 
`POST /analyze/upload`

**Description:** 
Accepts a video file, runs MediaPipe pose extraction, generates a risk assessment, and returns the analysis ID.

**Authentication:** 
Required (Bearer Token)

**Request Body:** (multipart/form-data)
- `file`: The video file (.mp4, .mov)
- `movement_type`: (String) e.g., "Squat", "Jump"

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/analyze/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/video.mp4" \
  -F "movement_type=Squat"
```

**Example Response:** (200 OK)
```json
{
  "session_id": "session-uuid-5678",
  "status": "processing",
  "message": "Video uploaded successfully and analysis has started."
}
```

**Status/Error Codes:**
- `200 OK` - Upload successful.
- `401 Unauthorized` - Missing or invalid token.
- `403 Forbidden` - User requires a Pro subscription to upload more videos.
- `415 Unsupported Media Type` - Invalid file format.

---

### 4. Stripe Webhook
Receive asynchronous events from Stripe regarding subscription status.

**Method & Path:** 
`POST /webhooks/stripe`

**Description:** 
Listens for the `checkout.session.completed` event to upgrade a user's account to Pro.

**Authentication:** 
None (Validates using Stripe Signature Header)

**Request Body:** (Raw JSON payload from Stripe)

**Example Request:**
(Sent automatically by Stripe)

**Example Response:** (200 OK)
```json
{
  "status": "success",
  "message": "Webhook processed successfully"
}
```

**Status/Error Codes:**
- `200 OK` - Event received and processed.
- `400 Bad Request` - Invalid signature or unhandled event type.

---

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request. When an error occurs, the API will typically return a JSON object containing a `detail` message explaining the error.

### Common Error Codes

| Code | Meaning | Description |
| :--- | :--- | :--- |
| **400** | Bad Request | The request was malformed, missing required parameters, or failed validation. |
| **401** | Unauthorized | Authentication failed or a valid JWT token was not provided in the `Authorization` header. |
| **403** | Forbidden | The authenticated user does not have permission to perform this action (e.g., an Athlete trying to access Coach data, or hitting a paywall limit). |
| **404** | Not Found | The requested resource (user, session, analysis) could not be found. |
| **415** | Unsupported Media Type | The uploaded file type is not supported. |
| **422** | Unprocessable Entity | The request body failed Pydantic validation (e.g., passing a string where an integer is expected). |
| **500** | Internal Server Error | An unexpected error occurred on the server (e.g., database failure or AI processing failure). |

**Example Error Response:**
```json
{
  "detail": "Invalid credentials provided."
}
```
