from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Nangarhar University Digital Library API"
    environment: str = "development"
    secret_key: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
    database_url: str = "sqlite:///./nangarhar_library.db"
    upload_dir: str = "./storage"
    max_upload_mb: int = 25
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000"
    admin_name: str = "System Administrator"
    admin_email: str = "admin@nangu.edu.af"
    admin_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
