import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey_change_me_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15   # 15 minutos (OWASP recomienda corto)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7      # Refresh token más duradero
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/iam_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

settings = Settings()
