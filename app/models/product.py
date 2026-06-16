import re
from datetime import UTC, datetime

from pydantic import BaseModel, field_validator


class ProductConfig(BaseModel):
    product_id: str
    name: str
    mongo_uri: str
    db_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "product_id must contain only letters, numbers, "
                "hyphens, and underscores"
            )
        return v


class ProductCreate(BaseModel):
    product_id: str
    name: str
    mongo_uri: str
    db_name: str


class ProductUpdate(BaseModel):
    name: str | None = None
    mongo_uri: str | None = None
    db_name: str | None = None


def now_utc() -> datetime:
    return datetime.now(UTC)
