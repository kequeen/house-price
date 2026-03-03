from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "房价分析系统"
    APP_VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "sqlite:///./house_price.db"
    
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    LIANJIA_BASE_URL: str = "https://bj.lianjia.com"
    
    class Config:
        env_file = ".env"


settings = Settings()
