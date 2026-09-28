from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ComicCraft"
    gemini_api_key: str = ""
    hf_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    hf_image_model: str = "black-forest-labs/FLUX.1-schnell"
    max_prompt_length: int = 1200
    image_timeout_seconds: int = 90
    gemini_timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
