from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import now_utc


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    password_hash: str
    email_verified: bool = False
    google_sub: str | None = None
    auth_provider: str = "email"
    verification_token: str | None = None
    reset_token: str | None = None
    reset_token_expires: datetime | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class UserCreate(BaseModel):
    email: str
    password_hash: str


class UserUpdate(BaseModel):
    email_verified: bool | None = None
    verification_token: str | None = None
    reset_token: str | None = None
    reset_token_expires: datetime | None = None
    password_hash: str | None = None
    google_sub: str | None = None
    auth_provider: str | None = None
