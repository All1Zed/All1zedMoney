import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./payment_gateway.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Konik SOAP Configuration
    WSDL_URL: Optional[str] = None
    SERVICE_URL: Optional[str] = None
    KONIK_USERNAME: Optional[str] = None
    KONIK_PASSWORD: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_PAYMENTS: str = "50/minute"
    RATE_LIMIT_ANALYTICS: str = "30/minute"
    RATE_LIMIT_WEBHOOKS: str = "1000/minute"
    
    # Webhook Configuration
    WEBHOOK_TIMEOUT: int = 30
    WEBHOOK_MAX_RETRIES: int = 3
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAYS: list = [60, 300, 900]  # 1min, 5min, 15min
    
    # Monitoring
    ENABLE_METRICS: bool = True
    ENABLE_HEALTH_CHECKS: bool = True
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings() 