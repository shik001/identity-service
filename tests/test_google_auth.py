from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_google_auth_service,
    get_user_repository,
)
from app.config import Settings
from app.main import create_app
from app.repositories.memory_user_repo import MemoryUserRepository
from app.services.google_auth import GoogleAuthService


def _make_mock_service(valid: bool = True, domain: str = ""):
    mock = MagicMock(spec=GoogleAuthService)
    if valid:
        mock.verify_id_token.return_value = {
            "sub": "google-sub-123",
            "email": "alice@example.com",
            "email_verified": True,
        }
    else:
        mock.verify_id_token.side_effect = ValueError(
            "Invalid token"
        )
    return mock


def _make_app(
    user_repo: MemoryUserRepository | None = None,
    mock_service: MagicMock | None = None,
) -> FastAPI:
    settings = Settings(config_db_uri="", config_db_name="test")
    _app = create_app(settings=settings)
    if user_repo is not None:
        _app.dependency_overrides[
            get_user_repository
        ] = lambda: user_repo
    if mock_service is not None:
        _app.dependency_overrides[
            get_google_auth_service
        ] = lambda: mock_service
    return _app


class TestGoogleAuth:

    def _get_client(self, mock_service):
        user_repo = MemoryUserRepository()
        app = _make_app(
            user_repo=user_repo, mock_service=mock_service
        )
        return TestClient(app), user_repo

    def test_google_signup_new_user(self):
        mock = _make_mock_service(valid=True)
        client, repo = self._get_client(mock)

        resp = client.post(
            "/test-product/auth/google",
            json={"id_token": "valid-token"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["email_verified"] is True

        user = repo._store["alice@example.com"]
        assert user.google_sub == "google-sub-123"
        assert user.auth_provider == "google"
        assert user.email_verified is True

    def test_google_login_existing_user(self):
        mock = _make_mock_service(valid=True)
        client, repo = self._get_client(mock)

        client.post(
            "/test-product/auth/google",
            json={"id_token": "valid-token"},
        )

        resp = client.post(
            "/test-product/auth/google",
            json={"id_token": "valid-token"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "alice@example.com"

    def test_google_account_linking(self):
        mock = _make_mock_service(valid=True)
        user_repo = MemoryUserRepository()
        app = _make_app(
            user_repo=user_repo, mock_service=mock
        )
        client = TestClient(app)

        client.post(
            "/test-product/auth/signup",
            json={
                "email": "alice@example.com",
                "password": "strongpass",
            },
        )

        user = user_repo._store["alice@example.com"]
        assert user.google_sub is None
        assert user.auth_provider == "email"

        resp = client.post(
            "/test-product/auth/google",
            json={"id_token": "valid-token"},
        )

        assert resp.status_code == 200
        user = user_repo._store["alice@example.com"]
        assert user.google_sub == "google-sub-123"
        assert user.auth_provider == "google"

    def test_google_invalid_token(self):
        mock = _make_mock_service(valid=False)
        client, repo = self._get_client(mock)

        resp = client.post(
            "/test-product/auth/google",
            json={"id_token": "bad-token"},
        )

        assert resp.status_code == 401

    def test_google_user_cannot_login_with_password(self):
        mock = _make_mock_service(valid=True)
        client, repo = self._get_client(mock)

        client.post(
            "/test-product/auth/google",
            json={"id_token": "valid-token"},
        )

        resp = client.post(
            "/test-product/auth/login",
            json={
                "email": "alice@example.com",
                "password": "any-password",
            },
        )

        assert resp.status_code == 401

    def test_google_domain_restriction(self):
        mock = _make_mock_service(valid=True, domain="company.com")
        mock.verify_id_token.side_effect = ValueError(
            "Email domain not allowed"
        )
        client, repo = self._get_client(mock)

        resp = client.post(
            "/test-product/auth/google",
            json={"id_token": "valid-token"},
        )

        assert resp.status_code == 401
