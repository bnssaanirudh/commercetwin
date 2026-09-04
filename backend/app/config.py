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

    # CORS configuration
    cors_origins: str = Field(default="http://localhost:5173")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

# Validate config immediately on import
try:
    settings = Settings()
    if settings.razorpay_key_id.startswith("rzp_live"):
        raise ValueError("Live Razorpay keys are explicitly forbidden in this environment.")
except Exception as e:
    logging.error("Configuration validation failed.")
    raise RuntimeError(f"Configuration error: {str(e)}") from None
