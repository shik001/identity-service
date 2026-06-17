# Identity Service — Usage Guide

A reusable authentication service that validates users against per-product databases via a central product registry.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Quick Setup](#quick-setup)
- [Registering Your Product](#1-register-your-product)
- [Authentication Flow](#2-authentication-flow)
- [Password Reset](#3-password-reset)
- [Email Verification](#4-email-verification)
- [Integrating with Your App](#5-integrating-with-your-app)
- [Postman Collection Guide](#postman-collection-guide)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## How It Works

```
                    ┌──────────────────────┐
                    │   Config Database     │
                    │  (identity_config)    │
                    │                       │
                    │  products:            │
                    │   - _id (ObjectId)    │
                    │   - name              │
                    │   - mongo_uri         │
                    │   - db_name           │
                    └──────────┬────────────┘
                               │
                  ┌────────────┴────────────┐
                  │     Identity Service     │
                  │                          │
                  │  POST /{id}/auth/signup  │
                  │  POST /{id}/auth/login   │
                  │  POST /{id}/auth/refresh │
                  │  POST /{id}/auth/logout  │
                  │                          │
                  │  CRUD /admin/products    │
                  └────┬──────────────┬──────┘
                       │              │
              ┌────────┴───┐   ┌─────┴────────┐
              │  Product A │   │  Product B   │
              │  Database  │   │  Database    │
              │            │   │              │
              │  users     │   │  users       │
              │  tokens    │   │  tokens      │
              └────────────┘   └──────────────┘
```

Each product gets its **own MongoDB database**. The config database stores connection details for every registered product. When a request comes in with a product's MongoDB `_id` in the URL, the service looks up the product in the config DB, connects to that product's database, and performs auth operations there.

---

## Quick Setup

### Prerequisites

- Python 3.11+
- MongoDB (Atlas or local)
- Docker (optional)

### 1. Clone and install

```bash
git clone <repo-url> identity-service
cd identity-service
make install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
CONFIG_DB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
JWT_SECRET=your-secret-key-keep-it-safe
```

### 3. Start the service

```bash
make run
```

The API will be available at `http://localhost:8000`.

### 4. Verify it works

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

---

## 1. Register Your Product

Before any user can sign up, you must register your product. This tells Identity Service where to store your users.

### Request

**POST** `http://localhost:8000/admin/products`

```json
{
  "name": "My App",
  "mongo_uri": "mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0",
  "db_name": "my_app_users"
}
```

| Field | Description |
|---|---|
| `name` | Human-readable name for your product |
| `mongo_uri` | MongoDB connection string for **your product's database** |
| `db_name` | Database name within that MongoDB instance for your users |

You can use the **same MongoDB instance** as the config DB, but with a **different database name** to keep things isolated.

### Response

```json
{
  "data": {
    "id": "6a31251b3ea64a86cb4be650",
    "name": "My App",
    "mongo_uri": "mongodb+srv://...",
    "db_name": "my_app_users",
    "created_at": "2026-06-16T10:00:00",
    "updated_at": "2026-06-16T10:00:00"
  }
}
```

**Save the `id` field** — this is your product identifier. You'll use it in every auth endpoint URL (e.g., `/{id}/auth/login`).

### Subsequent requests

Now you can list, update, or delete your product:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/products` | List all products |
| GET | `/admin/products/{id}` | Get a single product |
| PUT | `/admin/products/{id}` | Update name / mongo_uri / db_name |
| DELETE | `/admin/products/{id}` | Remove a product |

---

## 2. Authentication Flow

All auth endpoints are prefixed with `/{product_id}/auth/`, where `{product_id}` is the MongoDB `_id` returned when you registered the product.

### Signup

**POST** `/{product_id}/auth/signup`

```json
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}
```

**Success (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "email": "alice@example.com",
    "email_verified": false
  }
}
```

**Errors:** `409` if email already registered, `422` if email is invalid or password < 8 characters.

### Login

**POST** `/{product_id}/auth/login`

```json
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}
```

**Success (200):** Same response shape as signup — returns `access_token`, `refresh_token`, and user info.

**Error (401):**
```json
{
  "detail": "Invalid credentials"
}
```

### Refresh Token

Access tokens expire after 30 minutes (configurable). Use the refresh token to get a new pair without requiring login again.

**POST** `/{product_id}/auth/refresh`

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Success (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Note:** Each refresh invalidates the previous refresh token (it gets blacklisted).

### Logout

**POST** `/{product_id}/auth/logout`

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `204 No Content`

After logout, the refresh token is blacklisted and cannot be used again.

### Using the Access Token

Include it in the `Authorization` header for protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

The access token is a **JWT** containing:

```json
{
  "sub": "alice@example.com",      // user email
  "product_id": "6a31251b3ea64a86cb4be650",
  "exp": 1718534400,               // expiry timestamp
  "jti": "550e8400-e29b-41d4-a716-446655440000"  // unique token ID
}
```

You can decode it with any JWT library (e.g., [jwt.io](https://jwt.io/)) using your `JWT_SECRET`.

---

## 3. Password Reset

### Step 1: Request a reset

**POST** `/{product_id}/auth/password-reset/request`

```json
{
  "email": "alice@example.com"
}
```

**Response:** `204 No Content` (always — prevents email enumeration).

The service stores a reset token and expiry in the user's database document. In production, you would email this token to the user.

### Step 2: Get the reset token

The reset token is stored in the user's document in your product's MongoDB database. Query it directly:

```
use my_app_users
db.users.findOne({email: "alice@example.com"})
// → { "reset_token": "abc123...", "reset_token_expires": ISODate("...") }
```

Copy the `reset_token` value.

### Step 3: Confirm the reset

**POST** `/{product_id}/auth/password-reset/confirm`

```json
{
  "token": "abc123def456...",
  "new_password": "NewSecurePass456!"
}
```

**Success (200):**
```json
{
  "detail": "Password reset successful"
}
```

**Errors:** `400` if token is invalid or expired, `422` if new password < 8 characters.

After successful reset, the token is consumed (cleared from the user document) and the password hash is updated. Login with the old password will fail.

---

## 4. Email Verification

### Step 1: Get the verification token

When a user signs up, a `verification_token` is stored in their user document. Query your product's database:

```
use my_app_users
db.users.findOne({email: "alice@example.com"})
// → { "verification_token": "xyz789..." }
```

In production, you would email this token as a verification link.

### Step 2: Verify the email

**POST** `/{product_id}/auth/verify-email`

```json
{
  "token": "xyz789..."
}
```

**Success (200):**
```json
{
  "detail": "Email verified successfully"
}
```

If already verified:
```json
{
  "detail": "Email already verified"
}
```

**Error (400):** Invalid token.

### Resend verification

If the user needs a new token:

**POST** `/{product_id}/auth/verify-email/resend`

```json
{
  "email": "alice@example.com"
}
```

**Response:** `204 No Content` (always).

This generates a new `verification_token` and overwrites the old one.

---

## 5. Integrating with Your App

### Backend integration (Python example)

```python
import requests

BASE_URL = "http://localhost:8000"
PRODUCT_ID = "6a31251b3ea64a86cb4be650"  # from product registration

# Signup
resp = requests.post(f"{BASE_URL}/{PRODUCT_ID}/auth/signup", json={
    "email": "alice@example.com",
    "password": "SecurePass123!",
})
data = resp.json()
access_token = data["access_token"]
refresh_token = data["refresh_token"]

# Authenticated request to your own API
headers = {"Authorization": f"Bearer {access_token}"}
resp = requests.get("https://api.myapp.com/protected", headers=headers)

# When access token expires, refresh it
resp = requests.post(f"{BASE_URL}/{PRODUCT_ID}/auth/refresh", json={
    "refresh_token": refresh_token,
})
data = resp.json()
access_token = data["access_token"]           # new
refresh_token = data["refresh_token"]         # new (old one is blacklisted)
```

### JWT verification in your app

Decode and verify the JWT in your own API to authenticate users:

```python
from jose import jwt

JWT_SECRET = "your-secret-key"  # must match Identity Service config

def verify_token(token: str) -> dict:
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    # payload contains: sub (email), product_id, exp, jti
    return payload
```

### Token lifecycle summary

| Token | Lifetime | Stored on client? | Can be refreshed? |
|---|---|---|---|
| Access token | 30 min (configurable) | Yes (in-memory / HTTP header) | No (get a new one via refresh) |
| Refresh token | 7 days (configurable) | Yes (secure httpOnly cookie / local storage) | Yes (old one is blacklisted) |

---

## Postman Collection Guide

### Importing

1. Open Postman
2. Click **File → Import**
3. Select `identity-service.postman_collection.json` from the project root
4. Click **Import**

### Collection Variables

The collection comes with these variables (edit them to match your setup):

| Variable | Default | Description |
|---|---|---|
| `base_url` | `http://localhost:8000` | Your Identity Service URL |
| `product_id` | _(empty)_ | Auto-populated after Creating a Product |
| `email` | `alice@example.com` | User email for signup/login |
| `password` | `SecurePass123!` | User password |
| `new_password` | `NewSecurePass456!` | Used in password reset |
| `verification_token` | _(empty)_ | Paste from MongoDB (see step 4) |
| `reset_token` | _(empty)_ | Paste from MongoDB (see step 7) |

### Running the flow step-by-step

#### Step 0: Start the service

```bash
make run
```

#### Step 1: Create a Product

Open **Admin — Products → Create Product**. Edit the JSON body to use your MongoDB connection string and click **Send**.

The response's `data.id` is **automatically saved** into the `product_id` variable by the Tests script.

#### Step 2: Signup

Open **Auth Flow → 1. Signup** and click **Send**.

The Tests script automatically saves `access_token` and `refresh_token` into collection variables.

#### Step 3: Login

Open **Auth Flow → 2. Login** and click **Send**.

Tokens are updated in collection variables.

#### Step 4: Refresh Token

Open **Auth Flow → 3. Refresh Token** and click **Send**.

#### Step 5: Verify Email

The `verification_token` is stored in your product's MongoDB. To get it:

1. Open MongoDB Compass or shell
2. Connect to your product's MongoDB
3. Find the user document:
   ```javascript
   use my_app_users
   db.users.findOne({email: "alice@example.com"})
   ```
4. Copy the `verification_token` value
5. Paste it into Postman's `verification_token` collection variable
6. Open **Auth Flow → 4. Verify Email** and click **Send**

#### Step 6: Password Reset

1. Open **Auth Flow → 6. Password Reset — Request** and click **Send** (204 No Content)
2. Get the `reset_token` from MongoDB (same place as verification token)
3. Paste it into Postman's `reset_token` collection variable
4. Open **Auth Flow → 7. Password Reset — Confirm** and click **Send**
5. The Tests script updates the `password` variable to the `new_password` value

#### Step 7: Logout

Open **Auth Flow → 8. Logout** and click **Send** (204 No Content).

The refresh token is now blacklisted. Trying **3. Refresh Token** again with the same token will return **401**.

### Google Sign-In

The service supports Google Sign-In via ID tokens. When a user authenticates with Google on your frontend (using the Google Sign-In SDK), you get an ID token. Send that token to this endpoint:

**POST** `/{product_id}/auth/google`

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Success (200):** Same response shape as login — returns `access_token`, `refresh_token`, and user info.

**How it works:**
1. The service verifies the ID token using Google's public keys (JWKS)
2. If the user already exists with that email (email/password user), their account is **linked** — they can now sign in with either method
3. If the user already exists with that `google_sub`, a new token pair is returned
4. If neither exists, a new user is created with `auth_provider: "google"`

**Prerequisites:**
- Set `GOOGLE_CLIENT_ID` in `.env` (your Google OAuth 2.0 client ID)
- Optionally set `ALLOWED_EMAIL_DOMAIN` to restrict sign-ins to a specific domain (e.g., `yourcompany.com`)
- The frontend must use the Google Sign-In SDK to obtain an ID token

### Testing Google Sign-In from Postman

Getting a real Google ID token requires OAuth flow. Here are two approaches:

#### Option A: Use a test Google ID token (sandbox)

Not possible — Google's JWKS verification requires a real signed token.

#### Option B: Generate an ID token via OAuth playground

1. Go to https://developers.google.com/oauthplayground
2. Click the gear icon (⚙️) → check **"Use your own OAuth credentials"**
3. Enter your **Client ID** and **Client Secret** from Google Cloud Console
4. In the left panel, scroll to **"Google OAuth2 API v2"** → select **"https://www.googleapis.com/auth/userinfo.email"** and **"https://www.googleapis.com/auth/userinfo.profile"**
5. Click **Authorize APIs** → sign in with your Google account
6. Click **Exchange authorization code for tokens**
7. Copy the **id_token** value
8. Paste it into Postman's `google_id_token` collection variable
9. Run **9. Google Sign-In** in the Auth Flow folder

#### Option C: Frontend-first approach

Build a simple HTML page that uses the Google Sign-In SDK, logs the ID token to the console, then paste it into Postman:

```html
<!-- Save as google-signin-test.html, open in browser -->
<html>
<body>
<script src="https://accounts.google.com/gsi/client" async></script>
<script>
function handleCredentialResponse(response) {
  console.log("ID Token:", response.credential);
  alert("Copy the ID token from the console (F12 → Console)");
}
</script>
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID"
     data-callback="handleCredentialResponse">
</div>
<div class="g_id_signin" data-type="standard"></div>
</body>
</html>
```

After getting the ID token, paste it into Postman's `google_id_token` variable and run **9. Google Sign-In**.

#### Option D: Skip Google verification for Postman testing

If you want to test the endpoint without a real Google token, you can temporarily monkey-patch the service in tests (not recommended for production). The existing test suite uses a mock `GoogleAuthService` to test the endpoint logic without real tokens.

---

### Chaining requests

The collection is designed so that Steps 1–3 and Step 8 can be run sequentially without manual intervention — tokens flow automatically via collection variables. Steps 5 and 7 require you to paste tokens from MongoDB.

---

## API Reference

### Admin — Product Registry

| Method | Endpoint | Request Body | Response |
|---|---|---|---|
| POST | `/admin/products` | `{name, mongo_uri, db_name}` | 201 — product with auto-generated `id` |
| GET | `/admin/products` | — | 200 — array of products |
| GET | `/admin/products/{id}` | — | 200 — single product |
| PUT | `/admin/products/{id}` | `{name?, mongo_uri?, db_name?}` | 200 — updated product |
| DELETE | `/admin/products/{id}` | — | 204 — no content |

### Auth

| Method | Endpoint | Request Body | Response |
|---|---|---|---|
| POST | `/{id}/auth/signup` | `{email, password}` | 201 — tokens + user |
| POST | `/{id}/auth/login` | `{email, password}` | 200 — tokens + user |
| POST | `/{id}/auth/refresh` | `{refresh_token}` | 200 — new token pair |
| POST | `/{id}/auth/logout` | `{refresh_token}` | 204 — no content |
| POST | `/{id}/auth/google` | `{id_token}` | 200 — tokens + user |
| POST | `/{id}/auth/password-reset/request` | `{email}` | 204 — no content |
| POST | `/{id}/auth/password-reset/confirm` | `{token, new_password}` | 200 — success message |
| POST | `/{id}/auth/verify-email` | `{token}` | 200 — success message |
| POST | `/{id}/auth/verify-email/resend` | `{email}` | 204 — no content |

### Health

| Method | Endpoint | Response |
|---|---|---|
| GET | `/health` | `{"status": "ok", "version": "0.1.0"}` |

---

## Troubleshooting

### "Product not found"

You're probably using a custom `product_id` string instead of the MongoDB `_id`. Make sure to:

1. Create the product via `POST /admin/products`
2. Use the `id` from the response (e.g., `6a31251b3ea64a86cb4be650`)

### "Email already registered"

The email exists in your product's database. Use a different email or use the password reset flow.

### `401 Unauthorized` on refresh

The refresh token has been blacklisted (by a previous refresh or logout). The client needs to re-authenticate via login.

### "Can't compare offset-naive and offset-aware datetimes"

If you see this error, ensure you're running the latest version of the service. This was a bug that has been fixed.

### Rate limiting

The service does not currently implement rate limiting. In production, add a reverse proxy (e.g., Nginx) or use Redis-based rate limiting.

### JWT secret rotation

If you change `JWT_SECRET` in `.env`:
- All existing tokens become invalid
- All users will need to log in again

Keep the secret stable in production.

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `CONFIG_DB_URI` | `mongodb://localhost:27017` | MongoDB connection string for config database |
| `CONFIG_DB_NAME` | `identity_config` | Config database name |
| `JWT_SECRET` | `change-me-in-production` | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `CORS_ORIGINS` | `*` | Comma-separated CORS origins (e.g., `https://app.com,https://admin.com`) |
