from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    PLONE_BASE_URL: str
    QDRANT_URL: str
    CORS_ORIGINS: list[str] = ["*"]
    ENVIRONMENT: str = "development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI provider settings
    AI_MODE: str = "demo"                    # "demo" = Ollama | "demo-api" = Claude
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    ANTHROPIC_API_KEY: str = ""             # empty if AI_MODE != "demo-api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
