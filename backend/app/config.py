import json
from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PropertyHub API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(..., min_length=32)
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./propertyhub.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    celery_task_eager_propagates: bool = False
    document_storage_dir: str = "./storage/documents"
    backend_cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: SecretStr | None = None
    bootstrap_admin_organization_id: str = "00000000-0000-0000-0000-000000000001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @computed_field
    @property
    def document_storage_path(self) -> Path:
        return Path(self.document_storage_dir).expanduser().resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
