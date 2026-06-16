from datetime import UTC, datetime

from pydantic import BaseModel


class ProductConfig(BaseModel):
    id: str = ""
    name: str
    mongo_uri: str
    db_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProductCreate(BaseModel):
    name: str
    mongo_uri: str
    db_name: str


class ProductUpdate(BaseModel):
    name: str | None = None
    mongo_uri: str | None = None
    db_name: str | None = None


def now_utc() -> datetime:
    return datetime.now(UTC)
