from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    cors_origins: str = "*"

    config_db_uri: str = (
        "mongodb+srv://souptik:1234@cluster0.dbtuf4t.mongodb.net/"
        "?appName=Cluster0"
    )
    config_db_name: str = "identity_config"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
