from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database & Auth
    DATABASE_URL: str = "sqlite:///./dev.db"
    JWT_SECRET: str = "change_me"
    FRONTEND_URL: str = "http://localhost:5173"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_IDS: Optional[str] = None

    # Email
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "no-reply@example.com"

    # 🔁 AI Settings (OpenAI → Groq/Ollama migration)
    OPENAI_API_KEY: Optional[str] = None          # kept for backward compat (optional)
    GROQ_API_KEY: Optional[str] = None            # ← NEW: for production AI
    ENVIRONMENT: str = "development"              # ← NEW: "development" or "production"
    ADMIN_EMAIL: str = "admin@example.com"        # ← NEW: for alerts/logging

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()