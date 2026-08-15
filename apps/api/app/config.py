from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    BUILD_SHA: str = "dev-local-c0ff33"
    INDEX_VERSION: str = "pgvector_cosine_v1"
    SCORE_VERSION: str = "sigmoid_calibrated_v1"

    SECRET_KEY: str = "default_development_secret_key_change_me"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "celebrity_lookalike"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/celebrity_lookalike"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/celebrity_lookalike"

    # Redis & Job Queue Settings
    REDIS_URL: str = "redis://redis:6379/0"
    ASYNC_MATCHING_ENABLED: bool = True
    MAX_QUEUE_CAPACITY: int = 100
    JOB_RESULT_TTL_SECONDS: int = 600
    JOB_TIMEOUT_SECONDS: int = 30
    MAX_TRANSIENT_RETRIES: int = 3

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ML / Recognition Settings
    RECOGNITION_PROVIDER: str = "insightface"  # 'insightface', 'siglip2', 'real', or 'fake'
    INSIGHTFACE_MODEL_NAME: str = "buffalo_l"
    EMBEDDING_DIMENSION: int = 512
    MODEL_WEIGHTS_PATH: Optional[str] = None
    MODEL_LICENSE_PATH: Optional[str] = None
    REAL_MODEL_VERSION: str = "real_v1"

    # Security Feature Flags
    ENABLE_URL_UPLOADS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
