import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies import (
    get_password_service,
    get_token_repository,
    get_token_service,
    get_user_repository,
)
from app.models.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RefreshResponse,
    SignupRequest,
    SignupResponse,
    UserResponse,
    VerifyEmailRequest,
    VerifyEmailResendRequest,
)
from app.models.token import RefreshTokenPayload
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.services.password_service import PasswordService
from app.services.token_service import TokenService

router = APIRouter(prefix="/{product_id}/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    product_id: str = Path(...),
    user_repo: UserRepository = Depends(get_user_repository),
    pwd_service: PasswordService = Depends(get_password_service),
    token_service: TokenService = Depends(get_token_service),
) -> SignupResponse:
    existing = await user_repo.get_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    password_hash = pwd_service.hash(body.password)
    verification_token = secrets.token_urlsafe(32)

    user = User(
        email=body.email,
        password_hash=password_hash,
        verification_token=verification_token,
    )
    await user_repo.create(user)

    token_pair = token_service.create_token_pair(
        email=body.email, product_id=product_id
    )

    return SignupResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        user=UserResponse(email=body.email, email_verified=False),
    )


@router.post("/login")
async def login(
    body: LoginRequest,
    product_id: str = Path(...),
    user_repo: UserRepository = Depends(get_user_repository),
    pwd_service: PasswordService = Depends(get_password_service),
    token_service: TokenService = Depends(get_token_service),
) -> LoginResponse:
    user = await user_repo.get_by_email(body.email)
    if user is None or not pwd_service.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token_pair = token_service.create_token_pair(
        email=body.email, product_id=product_id
    )

    return LoginResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        user=UserResponse(
            email=user.email, email_verified=user.email_verified
        ),
    )


@router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    product_id: str = Path(...),
    token_repo: TokenRepository = Depends(get_token_repository),
    token_service: TokenService = Depends(get_token_service),
) -> RefreshResponse:
    try:
        payload = token_service.decode_token(body.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if not isinstance(payload, RefreshTokenPayload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    if await token_repo.is_blacklisted(payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    await token_repo.blacklist(payload.jti, payload.exp)

    token_pair = token_service.create_token_pair(
        email=payload.sub, product_id=product_id
    )

    return RefreshResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    token_repo: TokenRepository = Depends(get_token_repository),
    token_service: TokenService = Depends(get_token_service),
) -> None:
    try:
        payload = token_service.decode_token(body.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if isinstance(payload, RefreshTokenPayload):
        await token_repo.blacklist(payload.jti, payload.exp)


@router.post(
    "/password-reset/request", status_code=status.HTTP_204_NO_CONTENT
)
async def password_reset_request(
    body: PasswordResetRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> None:
    user = await user_repo.get_by_email(body.email)
    if user is None:
        return

    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)
    await user_repo.update(
        user.email,
        {"reset_token": token, "reset_token_expires": expires},
    )


@router.post("/password-reset/confirm")
async def password_reset_confirm(
    body: PasswordResetConfirm,
    user_repo: UserRepository = Depends(get_user_repository),
    pwd_service: PasswordService = Depends(get_password_service),
) -> dict[str, str]:
    user = await user_repo.get_by_reset_token(body.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    if user.reset_token_expires and user.reset_token_expires.replace(tzinfo=None) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    password_hash = pwd_service.hash(body.new_password)
    await user_repo.update(
        user.email,
        {
            "password_hash": password_hash,
            "reset_token": None,
            "reset_token_expires": None,
        },
    )

    return {"detail": "Password reset successful"}


@router.post("/verify-email")
async def verify_email(
    body: VerifyEmailRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, str]:
    user = await user_repo.get_by_verification_token(body.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if user.email_verified:
        return {"detail": "Email already verified"}

    await user_repo.update(
        user.email,
        {"email_verified": True, "verification_token": None},
    )

    return {"detail": "Email verified successfully"}


@router.post(
    "/verify-email/resend", status_code=status.HTTP_204_NO_CONTENT
)
async def resend_verification(
    body: VerifyEmailResendRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> None:
    user = await user_repo.get_by_email(body.email)
    if user is None or user.email_verified:
        return

    new_token = secrets.token_urlsafe(32)
    await user_repo.update(
        user.email, {"verification_token": new_token}
    )
