from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ==========================================
    # Database
    # ==========================================
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5433/internado_uv"

    # ==========================================
    # Authentication - JWT Legacy
    # ==========================================
    SECRET_KEY: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ==========================================
    # Authentication - Keycloak (FASE 1)
    # ==========================================
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "internado-uv"
    KEYCLOAK_CLIENT_ID: str = "internado-backend"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_REDIRECT_URI: str = "http://localhost:5173/callback"
    
    # Admin credentials for user management operations
    KEYCLOAK_ADMIN_USERNAME: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: str = "admin123"
    KEYCLOAK_ADMIN_CLIENT_ID: str = "admin-cli"

    # ==========================================
    # MinIO - Object Storage (FASE 2)
    # ==========================================
    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False

    # ==========================================
    # Redis - Cache & Queue (FASE 3)
    # ==========================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==========================================
    # Celery - Background Jobs (FASE 3)
    # ==========================================
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ==========================================
    # Email
    # ==========================================
    MAIL_SERVER: str = "localhost"
    MAIL_PORT: int = 1025
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@internado-uv.cl"
    MAIL_USE_TLS: bool = False

    # ==========================================
    # reCAPTCHA v2
    # ==========================================
    RECAPTCHA_SECRET_KEY: str = "6Ldh5pksAAAAAMF8OQwyLQi00Q126kxh50iDN_IN"
    # IMPORTANTE: Cambiar a True en producción para habilitar reCAPTCHA
    # Para desarrollo, está desactivado para facilitar las pruebas
    RECAPTCHA_ENABLED: bool = False  # ⚠️ Cambiar a True en producción

    # ==========================================
    # HashiCorp Vault (FASE 3)
    # ==========================================
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = "root"

    # ==========================================
    # Sentry - Error Tracking (FASE 2)
    # ==========================================
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ==========================================
    # Prometheus - Monitoring (FASE 2)
    # ==========================================
    PROMETHEUS_ENABLED: bool = True
    METRICS_ENDPOINT: str = "/metrics"

    # ==========================================
    # CORS
    # ==========================================
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # ==========================================
    # Environment
    # ==========================================
    ENVIRONMENT: str = "development"


settings = Settings()
