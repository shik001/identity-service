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


class TestEmailVerification:

    def _signup(self, client, email="user@example.com"):
        client.post(
            "/test-product/auth/signup",
            json={"email": email, "password": "strongpass"},
        )

    def test_verify_success(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        token = repo._store["user@example.com"].verification_token

        resp = client.post(
            "/test-product/auth/verify-email",
            json={"token": token},
        )
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Email verified successfully"

        user = repo._store["user@example.com"]
        assert user.email_verified is True
        assert user.verification_token is None

    def test_verify_invalid_token(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/verify-email",
            json={"token": "bogus-token"},
        )
        assert resp.status_code == 400

    def test_verify_already_verified(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        token = repo._store["user@example.com"].verification_token
        client.post(
            "/test-product/auth/verify-email",
            json={"token": token},
        )

        resp = client.post(
            "/test-product/auth/verify-email",
            json={"token": token},
        )
        assert resp.status_code == 400

    def test_resend_success(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        old_token = repo._store["user@example.com"].verification_token

        resp = client.post(
            "/test-product/auth/verify-email/resend",
            json={"email": "user@example.com"},
        )
        assert resp.status_code == 204

        new_token = repo._store["user@example.com"].verification_token
        assert new_token is not None
        assert new_token != old_token

    def test_resend_unknown_email(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))

        resp = client.post(
            "/test-product/auth/verify-email/resend",
            json={"email": "unknown@example.com"},
        )
        assert resp.status_code == 204

    def test_resend_already_verified(self):
        repo = MemoryUserRepository()
        client = TestClient(_make_app(repo))
        self._signup(client)

        token = repo._store["user@example.com"].verification_token
        client.post(
            "/test-product/auth/verify-email",
            json={"token": token},
        )

        resp = client.post(
            "/test-product/auth/verify-email/resend",
            json={"email": "user@example.com"},
        )
        assert resp.status_code == 204

        user = repo._store["user@example.com"]
        assert user.verification_token is None
