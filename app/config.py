from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    GEMINI_API_KEY: str
    MONGODB_URI: str
    BASE_URL: str
    WEBHOOK_SECRET: str          # BẮT BUỘC set trong Render, không để trống
    MAX_HISTORY: int = 20
    BOT_NAME: str = "AI Assistant"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
