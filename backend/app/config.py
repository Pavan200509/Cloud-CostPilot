from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Live-ready defaults. Secrets come from env only — never commit keys."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cloud CostPilot"
    discovery_mode: Literal["live"] = "live"
    storage_backend: Literal["local", "bigquery"] = "local"
    data_dir: str = "data"
    ai_provider: Literal["gemini"] = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gcp_project_id: str = ""
    bigquery_dataset: str = "cloudops"
    bigquery_table: str = "resource_metrics"
    cpu_underutilized_pct: float = Field(default=20.0, ge=0, le=100)
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"
    refresh_interval_seconds: int = Field(default=300, ge=60, le=3600)
    session_ttl_hours: int = 24

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def empty_key(cls, v):
        return v or ""


@lru_cache
def get_settings() -> Settings:
    return Settings()