from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
import logging

class Settings(BaseSettings):
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    
    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./commercetwin.db")
    
    # LLM Provider Configuration
    llm_provider: str = Field(default="dummy")
    llm_api_key: SecretStr | None = Field(default=None)
    
    # Razorpay Test Mode Configuration
    razorpay_key_id: str
    razorpay_key_secret: SecretStr
    
    # Chaos Engine Configuration
    chaos_seed: int = Field(default=42)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Validate config immediately on import but catch ValidationError to avoid printing secrets in stack traces if possible.
try:
    settings = Settings()
except Exception as e:
    logging.error("Configuration validation failed. Ensure required environment variables (e.g., RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET) are set.")
    # We do NOT log the exception directly if it contains secret values in the trace.
    raise RuntimeError("Configuration error: missing required environment variables.") from None
