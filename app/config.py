from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    GEMINI_API_KEY: str
    MONGODB_URI: str
    BASE_URL: str
    WEBHOOK_SECRET: str = secrets.token_hex(16)
    MAX_HISTORY: int = 20
    BOT_NAME: str = "AI Assistant"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
