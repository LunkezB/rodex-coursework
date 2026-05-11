from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Rodex"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    POSTGRES_DB: str = "rodex"
    POSTGRES_USER: str = "rodex"
    POSTGRES_PASSWORD: str = "rodex"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432

    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated frontend origins",
    )

    @cached_property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
