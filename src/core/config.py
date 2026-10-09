import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Library AI Studio"
    
    # Laravel .env faylidagi JWT_SECRET bilan DTM/Aynan bir xil bo'lishi shart!
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-laravel-fastapi-key-2026")
    JWT_ALGORITHM: str = "HS256"

settings = Settings()