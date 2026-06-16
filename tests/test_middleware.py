from fastapi import Depends
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.config import Settings
from app.main import create_app
from app.models.token import AccessTokenPayload
from app.services.token_service import TokenService

TEST_SECRET = "test-secret"


def _make_app(settings_override: dict | None = None):
    kwargs = {"config_db_uri": "", "config_db_name": "test", "jwt_secret": TEST_SECRET}
    if settings_override:
        kwargs.update(settings_override)
    settings = Settings(**kwargs)
    _app = create_app(settings=settings)

    @_app.get("/protected")
    async def protected(
        user: AccessTokenPayload = Depends(get_current_user),
    ):
        return {"email": user.sub, "product_id": user.product_id}

    return _app


class TestRequestID:

    def test_request_id_generated(self):
        client = TestClient(_make_app())
        resp = client.get("/health")
        assert "X-Request-ID" in resp.headers
        assert resp.headers["X-Request-ID"] != ""

    def test_request_id_propagated(self):
        client = TestClient(_make_app())
        resp = client.get(
            "/health", headers={"X-Request-ID": "my-custom-id"}
        )
        assert resp.headers["X-Request-ID"] == "my-custom-id"


class TestCORS:

    def test_cors_headers_on_options(self):
        client = TestClient(_make_app())
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in resp.headers

    def test_cors_headers_on_get(self):
        client = TestClient(_make_app())
        resp = client.get(
            "/health", headers={"Origin": "http://example.com"}
        )
        assert "access-control-allow-origin" in resp.headers


class TestCurrentUser:

    def _valid_token(self) -> str:
        settings = Settings(
            config_db_uri="", jwt_secret=TEST_SECRET
        )
        svc = TokenService(settings)
        return svc.create_access_token(
            email="user@example.com", product_id="test-product"
        )

    def test_valid_token(self):
        client = TestClient(_make_app())
        token = self._valid_token()
        resp = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@example.com"
        assert data["product_id"] == "test-product"

    def test_missing_header(self):
        client = TestClient(_make_app())
        resp = client.get("/protected")
        assert resp.status_code == 401

    def test_invalid_token(self):
        client = TestClient(_make_app())
        resp = client.get(
            "/protected",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert resp.status_code == 401

    def test_expired_token(self):
        settings = Settings(
            config_db_uri="",
            jwt_secret=TEST_SECRET,
            access_token_expire_minutes=-1,
        )
        svc = TokenService(settings)
        token = svc.create_access_token(
            email="user@example.com", product_id="test-product"
        )
        client = TestClient(_make_app())
        resp = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
