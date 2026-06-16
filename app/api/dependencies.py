from fastapi import Depends, HTTPException, Path, Request, status

from app.config import Settings
from app.models.product import ProductConfig
from app.models.token import AccessTokenPayload
from app.repositories.memory_product_repo import MemoryProductRepository
from app.repositories.memory_token_repo import MemoryTokenRepository
from app.repositories.memory_user_repo import MemoryUserRepository
from app.repositories.mongo_product_repo import MongoProductRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repo_factory import UserRepositoryFactory
from app.repositories.user_repository import UserRepository
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


def get_product_repository(request: Request) -> ProductRepository:
    repo: ProductRepository | None = getattr(
        request.app.state, "product_repo", None
    )
    if repo is not None:
        return repo
    db = getattr(request.app.state, "db", None)
    if db is not None:
        return MongoProductRepository(db)
    return MemoryProductRepository()


async def get_product_from_path(
    product_id: str = Path(...),
    repo: ProductRepository = Depends(get_product_repository),
) -> ProductConfig:
    product = await repo.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return product


async def get_user_repository(
    request: Request,
    product: ProductConfig = Depends(get_product_from_path),
) -> UserRepository:
    factory: UserRepositoryFactory | None = getattr(
        request.app.state, "user_repo_factory", None
    )
    if factory is not None:
        return factory.get_user_repository(product)
    return MemoryUserRepository()


async def get_token_repository(
    request: Request,
    product: ProductConfig = Depends(get_product_from_path),
) -> TokenRepository:
    factory: UserRepositoryFactory | None = getattr(
        request.app.state, "user_repo_factory", None
    )
    if factory is not None:
        return factory.get_token_repository(product)
    return MemoryTokenRepository()


def get_password_service() -> PasswordService:
    return PasswordService()


def get_token_service(request: Request) -> TokenService:
    settings: Settings = request.app.state.settings
    return TokenService(settings)


async def get_current_user(
    request: Request,
    token_service: TokenService = Depends(get_token_service),
) -> AccessTokenPayload:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = auth.removeprefix("Bearer ")
    try:
        payload = token_service.decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if not isinstance(payload, AccessTokenPayload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload
