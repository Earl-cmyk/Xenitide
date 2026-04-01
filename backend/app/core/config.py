import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Xendit Configuration
    XENDIT_SECRET_KEY: Optional[str] = None
    XENDIT_PUBLIC_KEY: Optional[str] = None
    XENDIT_WEBHOOK_TOKEN: Optional[str] = None
    XENDIT_DONATION_LINK: Optional[str] = None
    XENDIT_LINK_EXPIRY_DAYS: int = 30
    
    # Subscription Configuration
    FREE_PROJECT_LIMIT: int = 5
    SUBSCRIPTION_REQUIRED_PROJECT_LIMIT: int = 50
    
    # Application Configuration
    APP_NAME: str = "Xenitide API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-production-domain.com",
    ]
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "text/plain", "text/html", "text/css", "text/javascript",
        "application/json", "application/xml"
    ]
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Redis Configuration (for caching)
    REDIS_URL: Optional[str] = None
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
