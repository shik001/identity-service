import pytest
from pydantic import ValidationError

from app.models.product import ProductConfig, ProductCreate, ProductUpdate


class TestProductConfig:

    def test_valid_product_id(self):
        p = ProductConfig(
            product_id="kol-intelligence",
            name="KOL Intelligence",
            mongo_uri="mongodb://localhost",
            db_name="kol_intelligence",
        )
        assert p.product_id == "kol-intelligence"

    def test_invalid_product_id_with_spaces(self):
        with pytest.raises(ValidationError):
            ProductConfig(
                product_id="kol intelligence",
                name="KOL Intelligence",
                mongo_uri="mongodb://localhost",
                db_name="kol_intelligence",
            )

    def test_invalid_product_id_with_special_chars(self):
        with pytest.raises(ValidationError):
            ProductConfig(
                product_id="kol@intelligence!",
                name="KOL Intelligence",
                mongo_uri="mongodb://localhost",
                db_name="kol_intelligence",
            )

    def test_valid_product_id_with_underscore(self):
        p = ProductConfig(
            product_id="kol_intelligence",
            name="KOL Intelligence",
            mongo_uri="mongodb://localhost",
            db_name="kol_intelligence",
        )
        assert p.product_id == "kol_intelligence"


class TestProductCreate:

    def test_valid_create(self):
        data = ProductCreate(
            product_id="test-product",
            name="Test",
            mongo_uri="mongodb://localhost",
            db_name="test",
        )
        assert data.product_id == "test-product"


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
