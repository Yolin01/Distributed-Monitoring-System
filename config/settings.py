from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_QUEUE: str = "metrics"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AGENT_TOKEN_EXPIRE_DAYS: int = 365

    # Environnement
    ENV: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()