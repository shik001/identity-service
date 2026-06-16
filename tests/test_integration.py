"""Integration tests against a real MongoDB cluster.

These tests require a running MongoDB reachable via CONFIG_DB_URI in .env.
Test databases are created and dropped automatically.

Run with: pytest -v -m integration
"""

import asyncio
import secrets

import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings
from app.main import create_app

TEST_SUFFIX = secrets.token_hex(4)
CONFIG_DB = f"test_integration_config_{TEST_SUFFIX}"
PRODUCTS: list[tuple[str, str]] = [
    ("Integration Product A", f"test_integration_a_{TEST_SUFFIX}"),
    ("Integration Product B", f"test_integration_b_{TEST_SUFFIX}"),
]
ALL_DBS = [CONFIG_DB] + [p[1] for p in PRODUCTS]


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture(scope="module")
def settings():
    return Settings(config_db_name=CONFIG_DB)


@pytest.fixture(scope="module")
def client(settings):
    app = create_app(settings=settings)
    uri = settings.config_db_uri
    product_ids: list[str] = []
    with TestClient(app) as c:
        for name, db_name in PRODUCTS:
            resp = c.post(
                "/admin/products",
                json={
                    "name": name,
                    "mongo_uri": uri,
                    "db_name": db_name,
                },
            )
            assert resp.status_code == 201, resp.json()
            product_ids.append(resp.json()["data"]["id"])
        yield c, product_ids

    async def _cleanup():
        mc = AsyncIOMotorClient(uri)
        for db_name in ALL_DBS:
            await mc.drop_database(db_name)
        mc.close()

    _run_async(_cleanup())


def _signup(client, pid, email, password):
    resp = client.post(
        f"/{pid}/auth/signup",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201
    return resp.json()


def _get_user(settings, db_name, email):
    async def _fetch():
        mc = AsyncIOMotorClient(settings.config_db_uri)
        db = mc[db_name]
        user = await db["users"].find_one({"email": email})
        mc.close()
        return user

    return _run_async(_fetch())


@pytest.mark.integration
class TestIntegrationAuth:
    """End-to-end auth flows against a real MongoDB."""

    def test_full_auth_flow(self, client, settings):
        c, pids = client
        pid = pids[0]
        db_name = PRODUCTS[0][1]
        email = f"flow-{TEST_SUFFIX}@test.com"
        password = "Str0ng!Pass1"

        data = _signup(c, pid, email, password)
        refresh_token = data["refresh_token"]

        resp = c.post(
            f"/{pid}/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200
        data = resp.json()
        refresh_token = data["refresh_token"]

        resp = c.post(
            f"/{pid}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        refresh_token2 = data["refresh_token"]

        user = _get_user(settings, db_name, email)
        vtoken = user["verification_token"]
        resp = c.post(
            f"/{pid}/auth/verify-email",
            json={"token": vtoken},
        )
        assert resp.status_code == 200

        resp = c.post(
            f"/{pid}/auth/logout",
            json={"refresh_token": refresh_token2},
        )
        assert resp.status_code == 204

        resp = c.post(
            f"/{pid}/auth/refresh",
            json={"refresh_token": refresh_token2},
        )
        assert resp.status_code == 401

    def test_product_isolation(self, client, settings):
        c, pids = client
        pid_a, pid_b = pids[0], pids[1]
        email = f"iso-{TEST_SUFFIX}@test.com"
        password = "Str0ng!Pass2"

        _signup(c, pid_a, email, password)

        resp = c.post(
            f"/{pid_a}/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200

        resp = c.post(
            f"/{pid_b}/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 401

    def test_password_reset_flow(self, client, settings):
        c, pids = client
        pid = pids[0]
        db_name = PRODUCTS[0][1]
        email = f"reset-{TEST_SUFFIX}@test.com"
        password = "Str0ng!Pass3"
        new_password = "NewStr0ng!Pass3"

        _signup(c, pid, email, password)

        resp = c.post(
            f"/{pid}/auth/password-reset/request",
            json={"email": email},
        )
        assert resp.status_code == 204

        user = _get_user(settings, db_name, email)
        reset_token = user["reset_token"]
        assert reset_token is not None

        resp = c.post(
            f"/{pid}/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": new_password},
        )
        assert resp.status_code == 200

        resp = c.post(
            f"/{pid}/auth/login",
            json={"email": email, "password": new_password},
        )
        assert resp.status_code == 200

        resp = c.post(
            f"/{pid}/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 401
