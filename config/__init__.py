"""Configuration module for Flask application."""
from __future__ import annotations

import os


class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        # For development, generate a persistent key if not set
        import secrets
        SECRET_KEY = secrets.token_hex(32)

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # Session settings
    SESSION_COOKIE_SECURE = False  # Override in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire

    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///db.sqlite3"
    )
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration.

    Note: DATABASE_URL and SECRET_KEY environment variables should be set in production.
    """

    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")

    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    RATELIMIT_ENABLED = False  # Disable rate limiting for tests
    RATELIMIT_STORAGE_URL = None  # Disable storage for tests
    LOG_LEVEL = "WARNING"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(env: str | None = None) -> type[Config]:
    """Get configuration based on environment.

    Args:
        env: Environment name (development, production, testing)

    Returns:
        Configuration class for the specified environment
    """
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")
    return config.get(env, config["default"])
