from pydantic import AliasChoices, Field, PostgresDsn, RedisDsn

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_dsn: PostgresDsn = Field(
        default=...,  # required at runtime; satisfies pyright's __init__ check (pydantic/pydantic/#3753)
        validation_alias=AliasChoices("database_url", "database_dsn"),
    )
    redis_dsn: RedisDsn = Field(
        default=...,
        validation_alias=AliasChoices("redis_url", "redis_dsn"),
    )


settings = Settings()
