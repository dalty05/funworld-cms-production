import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# Debug — remove once things work
print(f"[config] loading .env from: {ENV_PATH}")
print(f"[config] .env exists: {ENV_PATH.exists()}")
print(f"[config] JWT_SECRET_KEY present: {'JWT_SECRET_KEY' in os.environ}")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # SQLALCHEMY_DATABASE_URI = os.environ.get(
    #     "DATABASE_URL",
    #     "postgresql+psycopg://postgres:Funworld123@localhost:5432/funworld-cms",
    # )
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL_POOLED")
        or os.getenv("DATABASE_URL")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES", 2592000))

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() == "true"
    TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "2500000"))

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() == "true"
    TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))

    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    IDEMPOTENCY_TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_TTL_SECONDS", 86400))

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

  

    # Email (SMTP)
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Funworld Events")
    MAIL_FROM = os.getenv("MAIL_FROM", "hello@funworld.example")
    MAIL_REPLY_TO = os.getenv("MAIL_REPLY_TO", MAIL_FROM)

    # SMS
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "africastalking")
    SMS_USERNAME = os.getenv("SMS_USERNAME", "")
    SMS_API_KEY = os.getenv("SMS_API_KEY", "")
    SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "FUNWORLD")

    

    # Run APScheduler inside this app process only when explicitly enabled.
    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"




    DOCUMENT_STORAGE_BACKEND = os.getenv("DOCUMENT_STORAGE_BACKEND", "local")
    DOCUMENT_LOCAL_ROOT = os.getenv("DOCUMENT_LOCAL_ROOT", "./storage/documents")

    COMPANY_NAME = os.getenv("COMPANY_NAME", "Funworld Events")
    COMPANY_TAGLINE = os.getenv("COMPANY_TAGLINE", "")
    COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE", "")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "")
    COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "")
    COMPANY_KRA_PIN = os.getenv("COMPANY_KRA_PIN", "")
    COMPANY_LOGO_PATH = os.getenv("COMPANY_LOGO_PATH")

    DOCUMENT_CURRENCY_DEFAULT = os.getenv("DOCUMENT_CURRENCY_DEFAULT", "KES")

    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")








class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map[env]