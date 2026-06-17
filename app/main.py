from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, auth
from app.config import Settings
from app.database import create_mongo_client
from app.middleware import RequestIDMiddleware
from app.repositories.user_repo_factory import UserRepositoryFactory
from app.services.google_auth import GoogleAuthService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = getattr(app.state, "settings", None) or Settings()
    if settings.config_db_uri:
        client, db = await create_mongo_client(settings)
        app.state.db = db
        app.state.mongo_client = client
    app.state.user_repo_factory = UserRepositoryFactory()
    if settings.google_client_id:
        app.state.google_auth_service = GoogleAuthService(
            google_client_id=settings.google_client_id,
            allowed_domain=settings.allowed_email_domain,
        )
    yield
    if hasattr(app.state, "user_repo_factory"):
        await app.state.user_repo_factory.close_all()
    if hasattr(app.state, "mongo_client"):
        app.state.mongo_client.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="Identity Service",
        version="0.1.0",
        description="Reusable Authentication Service",
        lifespan=lifespan,
    )
    app.state.settings = settings

    origins = (
        [o.strip() for o in settings.cors_origins.split(",")]
        if settings.cors_origins
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": "Validation failed",
                "errors": exc.errors(),
            },
        )

    app.include_router(admin.router)
    app.include_router(auth.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": app.version}

    return app


app = create_app()
