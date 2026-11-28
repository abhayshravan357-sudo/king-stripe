from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "sqlite:///./kingstripe.db"
    api_cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080"
    payment_provider: Literal["disabled", "razorpay"] = "disabled"
    payment_mode: Literal["test", "live"] = "test"
    allow_live_payments: bool = False
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    inventory_mode: Literal["disabled", "limited", "preorder", "made_to_order", "unlimited"] = "disabled"
    reservation_minutes: int = Field(default=15, ge=1, le=60)
    admin_username: str = ""
    admin_password_hash: str = ""
    admin_session_hours: int = Field(default=8, ge=1, le=24)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


settings = Settings()
