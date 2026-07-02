from pydantic import AliasChoices, Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_dsn: PostgresDsn = Field(
        # required at runtime; satisfies pyright's __init__
        # check (pydantic/pydantic/#3753)
        default=...,
        validation_alias=AliasChoices("database_url", "database_dsn"),
    )
    redis_dsn: RedisDsn = Field(
        default=...,
        validation_alias=AliasChoices("redis_url", "redis_dsn"),
    )

    lease: int = Field(default=60, le=100, ge=30)
    body_cap: int = Field(default=4096, le=8192, ge=1024)
    redispatch_limit: int = Field(default=100, le=150, ge=50)
    backoff_base: int = Field(default=2, le=10, ge=1)
    backoff_factor: float = Field(default=2.0, le=5.0, ge=1.5)
    backoff_ceiling: int = Field(default=60, le=100, ge=30)
    max_attempts: int = Field(default=6, le=20, ge=1)
    inactive_hold_seconds: int = Field(default=900, le=5000, ge=500)


settings = Settings()
