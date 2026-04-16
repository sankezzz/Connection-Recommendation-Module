from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str

    # Auth
    DEV_MODE: bool = True
    MSG91_AUTH_KEY: Optional[str] = None
    MSG91_TEMPLATE_ID: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
