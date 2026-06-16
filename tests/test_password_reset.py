from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.dependencies import get_user_repository
from app.config import Settings
from app.main import create_app
from app.repositories.memory_user_repo import MemoryUserRepository


def _make_app(user_repo: MemoryUserRepository):
    settings = Settings(config_db_uri="", config_db_name="test")
    _app = create_app(settings=settings)
    _app.dependency_overrides[get_user_repository] = lambda: user_repo
    return _app


class TestPasswordReset:

    def _signup(self, client, email="user@example.com"):
        client.post(
            "/test-product/auth/signup",
            json={"email": email, "password": "strongpass"},
        )

    def test_request_reset_success(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        resp = client.post(
            "/test-product/auth/password-reset/request",
            json={"email": "user@example.com"},
        )
        assert resp.status_code == 204

        user = repo._store["user@example.com"]
        assert user.reset_token is not None
        assert user.reset_token_expires is not None

    def test_request_reset_unknown_email(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/password-reset/request",
            json={"email": "unknown@example.com"},
        )
        assert resp.status_code == 204

    def test_confirm_reset_success(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        client.post(
            "/test-product/auth/password-reset/request",
            json={"email": "user@example.com"},
        )
        token = repo._store["user@example.com"].reset_token

        resp = client.post(
            "/test-product/auth/password-reset/confirm",
            json={"token": token, "new_password": "newstrongpass"},
        )
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Password reset successful"

        user = repo._store["user@example.com"]
        assert user.reset_token is None
        assert user.reset_token_expires is None

        login_resp = client.post(
            "/test-product/auth/login",
            json={
                "email": "user@example.com",
                "password": "newstrongpass",
            },
        )
        assert login_resp.status_code == 200

    def test_confirm_reset_expired_token(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        user = repo._store["user@example.com"]
        user.reset_token = "expired-token"
        user.reset_token_expires = datetime.now(UTC) - timedelta(hours=1)

        resp = client.post(
            "/test-product/auth/password-reset/confirm",
            json={"token": "expired-token", "new_password": "newstrongpass"},
        )
        assert resp.status_code == 400
        assert "expired" in resp.text

    def test_confirm_reset_invalid_token(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/password-reset/confirm",
            json={"token": "bogus-token", "new_password": "newstrongpass"},
        )
        assert resp.status_code == 400

    def test_confirm_reset_weak_password(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        client.post(
            "/test-product/auth/password-reset/request",
            json={"email": "user@example.com"},
        )
        token = repo._store["user@example.com"].reset_token

        resp = client.post(
            "/test-product/auth/password-reset/confirm",
            json={"token": token, "new_password": "short"},
        )
        assert resp.status_code == 422
