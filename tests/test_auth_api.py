from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_token_repository, get_user_repository
from app.config import Settings
from app.main import create_app
from app.repositories.memory_token_repo import MemoryTokenRepository
from app.repositories.memory_user_repo import MemoryUserRepository


def _make_app(
    user_repo: MemoryUserRepository,
    token_repo: MemoryTokenRepository | None = None,
) -> FastAPI:
    settings = Settings(config_db_uri="", config_db_name="test")
    _app = create_app(settings=settings)
    _app.dependency_overrides[get_user_repository] = lambda: user_repo
    if token_repo is not None:
        _app.dependency_overrides[get_token_repository] = lambda: token_repo
    return _app


class TestSignup:

    def test_signup_success(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/signup",
            json={"email": "new@example.com", "password": "strongpass"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["email_verified"] is False

    def test_signup_duplicate_email(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        client.post(
            "/test-product/auth/signup",
            json={"email": "dup@example.com", "password": "strongpass"},
        )
        resp = client.post(
            "/test-product/auth/signup",
            json={"email": "dup@example.com", "password": "strongpass"},
        )
        assert resp.status_code == 409

    def test_signup_invalid_email(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/signup",
            json={"email": "not-an-email", "password": "strongpass"},
        )
        assert resp.status_code == 422

    def test_signup_weak_password(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/signup",
            json={"email": "a@b.com", "password": "short"},
        )
        assert resp.status_code == 422


class TestLogin:

    def _signup_and_get_client(self):
        user_repo = MemoryUserRepository()
        client = TestClient(_make_app(user_repo))
        client.post(
            "/test-product/auth/signup",
            json={"email": "user@example.com", "password": "strongpass"},
        )
        return client, user_repo

    def test_login_success(self):
        client, _ = self._signup_and_get_client()

        resp = client.post(
            "/test-product/auth/login",
            json={"email": "user@example.com", "password": "strongpass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "user@example.com"

    def test_login_wrong_password(self):
        client, _ = self._signup_and_get_client()

        resp = client.post(
            "/test-product/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self):
        client, _ = self._signup_and_get_client()

        resp = client.post(
            "/test-product/auth/login",
            json={
                "email": "unknown@example.com",
                "password": "strongpass",
            },
        )
        assert resp.status_code == 401


class TestRefresh:

    def test_refresh_success(self):
        user_repo = MemoryUserRepository()
        token_repo = MemoryTokenRepository()
        client = TestClient(_make_app(user_repo, token_repo))

        signup_resp = client.post(
            "/test-product/auth/signup",
            json={"email": "user@example.com", "password": "strongpass"},
        )
        refresh_token = signup_resp.json()["refresh_token"]

        resp = client.post(
            "/test-product/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["refresh_token"] != refresh_token

    def test_refresh_with_blacklisted_token(self):
        user_repo = MemoryUserRepository()
        token_repo = MemoryTokenRepository()
        client = TestClient(_make_app(user_repo, token_repo))

        signup_resp = client.post(
            "/test-product/auth/signup",
            json={"email": "user@example.com", "password": "strongpass"},
        )
        refresh_token = signup_resp.json()["refresh_token"]

        client.post(
            "/test-product/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        resp = client.post(
            "/test-product/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401

    def test_refresh_invalid_token(self):
        user_repo = MemoryUserRepository()
        token_repo = MemoryTokenRepository()
        client = TestClient(_make_app(user_repo, token_repo))

        resp = client.post(
            "/test-product/auth/refresh",
            json={"refresh_token": "not-a-valid-jwt"},
        )
        assert resp.status_code == 401


class TestLogout:

    def test_logout_success(self):
        user_repo = MemoryUserRepository()
        token_repo = MemoryTokenRepository()
        client = TestClient(_make_app(user_repo, token_repo))

        signup_resp = client.post(
            "/test-product/auth/signup",
            json={"email": "user@example.com", "password": "strongpass"},
        )
        refresh_token = signup_resp.json()["refresh_token"]

        resp = client.post(
            "/test-product/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 204

        refresh_resp = client.post(
            "/test-product/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    def test_logout_invalid_token(self):
        user_repo = MemoryUserRepository()
        token_repo = MemoryTokenRepository()
        client = TestClient(_make_app(user_repo, token_repo))

        resp = client.post(
            "/test-product/auth/logout",
            json={"refresh_token": "bad-token"},
        )
        assert resp.status_code == 401
