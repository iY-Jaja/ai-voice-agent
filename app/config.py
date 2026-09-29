# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    assemblyai_api_key: str
    assemblyai_sample_rate: int = 24000
    assemblyai_stt_model: str = "universal-3-6-pro"

    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()