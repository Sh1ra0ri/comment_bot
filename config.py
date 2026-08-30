from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str
    super_admin_id: int

    # PostgreSQL
    database_url: str

    # Meta / Instagram Graph API
    meta_app_id: str
    meta_app_secret: str
    meta_api_version: str = "v21.0"
    meta_verify_token: str
    meta_redirect_uri: str

    # Webhook-сервер (FastAPI/uvicorn)
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000

    log_level: str = "INFO"


settings = Settings()