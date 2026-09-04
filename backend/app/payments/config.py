from pydantic_settings import BaseSettings, SettingsConfigDict

class PaymentSettings(BaseSettings):
    razorpay_key_id: str = "rzp_test_dummy"
    razorpay_key_secret: str = "dummy_secret"
    razorpay_webhook_secret: str = "dummy_webhook_secret"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = PaymentSettings()
