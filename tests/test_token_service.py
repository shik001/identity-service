import time

import pytest

from app.config import Settings
from app.services.token_service import TokenService


@pytest.fixture
def service():
    settings = Settings(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        config_db_uri="",
    )
    return TokenService(settings)


class TestTokenService:

    def test_create_and_decode_access_token(self, service):
        token = service.create_access_token(
            email="user@example.com", product_id="test-product"
        )
        payload = service.decode_token(token)
        assert payload.type == "access"
        assert payload.sub == "user@example.com"
        assert payload.product_id == "test-product"

    def test_create_and_decode_refresh_token(self, service):
        token = service.create_refresh_token(
            email="user@example.com", product_id="test-product"
        )
        payload = service.decode_token(token)
        assert payload.type == "refresh"
        assert payload.sub == "user@example.com"
        assert payload.product_id == "test-product"
        assert payload.jti is not None

    def test_token_pair_contains_both(self, service):
        pair = service.create_token_pair(
            email="user@example.com", product_id="test-product"
        )
        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"

        access = service.decode_token(pair.access_token)
        assert access.type == "access"

        refresh = service.decode_token(pair.refresh_token)
        assert refresh.type == "refresh"

    def test_invalid_token_raises(self, service):
        with pytest.raises(ValueError, match="Invalid or expired token"):
            service.decode_token("not-a-valid-jwt")

    def test_expired_token_raises(self, service):
        settings = Settings(
            jwt_secret="test-secret",
            access_token_expire_minutes=-1,
            refresh_token_expire_days=0,
            config_db_uri="",
        )
        expired_service = TokenService(settings)
        token = expired_service.create_access_token(
            email="user@example.com", product_id="test-product"
        )
        time.sleep(0.1)
        with pytest.raises(ValueError, match="Invalid or expired token"):
            expired_service.decode_token(token)
