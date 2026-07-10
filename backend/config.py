from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database
    database_url: str = "postgresql://admin:password@localhost:5432/jha_ml_platform"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    debug: bool = True
    api_title: str = "JHA ML Platform"
    api_version: str = "0.1.0"

    # Storage
    storage_path: str = "/app/storage"

    # CORS
    cors_origins: list = ["*"]

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480


settings = Settings()
