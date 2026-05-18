from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "production"
    LOG_LEVEL: str = "info"

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str  # 64 random hex chars
    ENCRYPTION_KEY: str  # 32-char key for pgcrypto column-level encryption
    SUPABASE_JWT_SECRET: str  # shared with GoTrue — validates Bearer tokens

    # ── Database ───────────────────────────────────────────────────────────
    POSTGRES_DB: str = "mphondo"
    POSTGRES_USER: str = "mphondo"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_PASSWORD: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ── Supabase ───────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:8081", "exp://localhost:8081"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── External APIs ──────────────────────────────────────────────────────
    FX_API_KEY: str = ""  # exchangerate.host — empty = use free endpoint
    ENABLE_BANKING_CLIENT_ID: str = ""
    ENABLE_BANKING_CLIENT_SECRET: str = ""

    # ── Push notifications ─────────────────────────────────────────────────
    NTFY_URL: str = "https://ntfy.sh"
    NTFY_TOPIC: str = ""

    # ── Feature flags ──────────────────────────────────────────────────────
    MPESA_PDF_OCR_FALLBACK: bool = True  # try pytesseract when pdfplumber fails


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings: Settings = get_settings()
