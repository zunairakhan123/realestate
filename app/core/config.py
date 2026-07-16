from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Load configuration from .env.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database connection URL.
    database_url: str

    # Enable customer deletion protection.
    enforce_customer_delete_guard: bool = True

    # Add this line so Pydantic knows to load it from the .env file
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    # Cache the settings instance to avoid repeatedly reading the .env file.
    return Settings()