import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app():
    settings = Settings(config_db_uri="", config_db_name="test")
    _app = create_app(settings=settings)
    return _app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
