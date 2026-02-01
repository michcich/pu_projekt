from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./financial_chatbot.db"
    
    # File Upload
    upload_folder: str = "./data/reports"
    max_upload_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = ["pdf"]
    
    # CORS
    cors_origins: List[str] = ["http://localhost:4200", "http://localhost:3000"]
    
    # Application
    app_name: str = "Financial Chatbot API"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure upload folder exists
os.makedirs(settings.upload_folder, exist_ok=True)