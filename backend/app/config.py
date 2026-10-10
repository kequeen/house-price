from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / '.env', extra='ignore')
    APP_NAME: str = '城市住宅观察'
    APP_VERSION: str = '2.0.0'
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'data' / 'official.db'}"
    DATA_DIR: Path = BACKEND_DIR / 'data'
    CORS_ORIGINS: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']
    REQUEST_INTERVAL: float = 0.35
    DEFAULT_START_PERIOD: str = '2023-01'


settings = Settings()
