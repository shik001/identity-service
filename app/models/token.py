from datetime import datetime

from pydantic import BaseModel


class AccessTokenPayload(BaseModel):
    sub: str
    product_id: str
    exp: datetime
    iat: datetime
    type: str = "access"


class RefreshTokenPayload(BaseModel):
    sub: str
    product_id: str
    exp: datetime
    iat: datetime
    jti: str
    type: str = "refresh"


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
