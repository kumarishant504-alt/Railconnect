from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RailConnect"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    reset_token_expire_minutes: int = 15
    database_url: str = "sqlite:///./railconnect.db"
    admin_email: str = "admin@railconnect.com"
    admin_password: str = "Admin@1234"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
