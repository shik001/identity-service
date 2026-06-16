import pytest
from pydantic import ValidationError

from app.models.product import ProductConfig, ProductCreate, ProductUpdate


class TestProductConfig:

    def test_create_product(self):
        p = ProductConfig(
            name="KOL Intelligence",
            mongo_uri="mongodb://localhost",
            db_name="kol_intelligence",
        )
        assert p.name == "KOL Intelligence"
        assert p.id == ""

    def test_create_with_id(self):
        p = ProductConfig(
            id="abc123",
            name="Test",
            mongo_uri="mongodb://localhost",
            db_name="test",
        )
        assert p.id == "abc123"


class TestProductCreate:

    def test_valid_create(self):
        data = ProductCreate(
            name="Test",
            mongo_uri="mongodb://localhost",
            db_name="test",
        )
        assert data.name == "Test"

    def test_requires_name(self):
        with pytest.raises(ValidationError):
            ProductCreate(mongo_uri="mongodb://localhost", db_name="test")

    def test_requires_mongo_uri(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="Test", db_name="test")

    def test_requires_db_name(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="Test", mongo_uri="mongodb://localhost")


class TestProductUpdate:

    def test_all_optional(self):
        data = ProductUpdate()
        assert data.name is None
        assert data.mongo_uri is None
        assert data.db_name is None

    def test_partial_update(self):
        data = ProductUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.mongo_uri is None
