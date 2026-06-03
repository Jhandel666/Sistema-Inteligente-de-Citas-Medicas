from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sistema Inteligente de Citas Medicas"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"
    use_ml: bool = False

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/citas_medicas"

    jwt_secret_key: str = ""
    jwt_refresh_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_username: str = "user@example.com"
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    smtp_use_tls: bool = True
    email_notifications_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()