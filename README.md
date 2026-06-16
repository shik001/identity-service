# Identity Service

A reusable authentication service built with FastAPI and MongoDB. Validates users against per-product databases via a central product registry.

## Architecture

```
                      ┌──────────────────────┐
                      │   Config Database     │
                      │  (identity_config)    │
                      │                      │
                      │  products:           │
                      │   - product_id       │
                      │   - mongo_uri        │
                      │   - db_name          │
                      └──────────┬───────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      Identity Service    │
                    │                          │
                    │  POST /{pid}/auth/signup │
                    │  POST /{pid}/auth/login  │
                    │  POST /{pid}/auth/refresh│
                    │  POST /{pid}/auth/logout │
                    │  POST /{pid}/auth/password-reset/*
                    │  POST /{pid}/auth/verify-email/*
                    │                          │
                    │  CRUD /admin/products    │
                    └────┬──────────────┬──────┘
                         │              │
                ┌────────┴───┐   ┌─────┴────────┐
                │ Product A  │   │  Product B   │
                │ Database   │   │  Database    │
                │            │   │              │
                │ users      │   │ users        │
                │ tokens     │   │ tokens       │
                └────────────┘   └──────────────┘
```

Each product gets its own database. The config database stores the connection details for every registered product. When a request comes in with a `product_id` URL prefix, the service looks up the product in the config DB, connects to the product's database, and performs auth operations there.

## Prerequisites

- Python 3.11+
- MongoDB (Atlas or local)
- Docker (optional, for containerized deployment)

## Quick Start

```bash
# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and JWT secret

# Run the service
make run
```

The API will be available at `http://localhost:8000`.

## Configuration

All configuration is via environment variables (loaded from `.env`):

| Variable | Default | Description |
|---|---|---|
| `CONFIG_DB_URI` | `mongodb://localhost:27017` | MongoDB connection string for config database |
| `CONFIG_DB_NAME` | `identity_config` | Config database name |
| `JWT_SECRET` | `change-me-in-production` | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `CORS_ORIGINS` | `*` | Comma-separated CORS origins |

## API Reference

### Admin — Product Registry

| Method | Path | Description | Status |
|---|---|---|---|
| GET | `/admin/products` | List all registered products | 200 |
| POST | `/admin/products` | Register a new product | 201 |
| GET | `/admin/products/{product_id}` | Get product details | 200 |
| PUT | `/admin/products/{product_id}` | Update product config | 200 |
| DELETE | `/admin/products/{product_id}` | Remove a product | 204 |

### Auth

| Method | Path | Description | Status |
|---|---|---|---|
| POST | `/{product_id}/auth/signup` | Register a new user | 201 |
| POST | `/{product_id}/auth/login` | Authenticate and get tokens | 200 |
| POST | `/{product_id}/auth/refresh` | Refresh access token | 200 |
| POST | `/{product_id}/auth/logout` | Revoke refresh token | 204 |
| POST | `/{product_id}/auth/password-reset/request` | Request password reset | 204 |
| POST | `/{product_id}/auth/password-reset/confirm` | Complete password reset | 200 |
| POST | `/{product_id}/auth/verify-email` | Verify email address | 200 |
| POST | `/{product_id}/auth/verify-email/resend` | Resend verification email | 204 |

### Health

| Method | Path | Description | Status |
|---|---|---|---|
| GET | `/health` | Service health check | 200 |

## Development

```bash
# Run unit tests (no MongoDB required)
make test

# Run integration tests (requires MongoDB at CONFIG_DB_URI)
make integration-test

# Lint and type checking
make lint
make typecheck

# Format code
make format
```

### Docker

```bash
# Build image
make docker-build

# Run with Docker Compose
make docker-run
```

## Project Structure

```
app/
├── api/            # Route handlers
│   ├── admin.py    # Product CRUD endpoints
│   ├── auth.py     # Authentication endpoints
│   └── dependencies.py  # FastAPI dependency injection
├── models/         # Pydantic models
├── repositories/   # Data access layer (Mongo + Memory)
├── services/       # Business logic (password, JWT)
├── config.py       # Settings via pydantic-settings
├── database.py     # MongoDB client factory
├── main.py         # FastAPI app factory
└── middleware.py   # Request ID middleware
tests/
└── test_*.py       # Unit and integration tests
```
