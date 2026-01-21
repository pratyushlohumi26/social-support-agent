"""
UAE Social Support AI System - Configuration Settings (Fixed)
"""

from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

if PYDANTIC_AVAILABLE:
    class Settings(BaseSettings):
        """Application settings with all required fields"""
        
        # Application
        APP_NAME: str = "UAE Social Support AI System"
        APP_VERSION: str = "3.0.0"
        ENVIRONMENT: str = "development"
        
        # Database
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./social_support.db"
        )
        DATABASE_ECHO: bool = False
        
        # API
        API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        API_PORT: int = os.getenv("API_PORT", 8005)
        API_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]
        
        # Ollama Configuration
        OLLAMA_MODE: str = os.getenv("OLLAMA_MODE", "cloud")
        OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
        OLLAMA_BASE_URL: str = "https://ollama.com"
        OLLAMA_MODEL: str = "gpt-oss:120b-cloud"
        OLLAMA_ENABLED: bool = True
        
        # LangGraph Configuration - ADD THESE MISSING FIELDS
        LANGGRAPH_CHECKPOINTING: bool = True
        WORKFLOW_TIMEOUT: int = 300
        
        # UAE Settings
        DEFAULT_EMIRATE: str = "dubai"
        SUPPORTED_LANGUAGES: List[str] = ["en", "ar"]
        CURRENCY: str = "AED"
        
        # UAE Income Thresholds (AED per month)
        UAE_INCOME_THRESHOLDS: Dict[str, Dict[str, int]] = {
            "dubai": {"low": 5000, "medium": 15000, "high": 25000},
            "abu_dhabi": {"low": 4500, "medium": 14000, "high": 23000},
            "sharjah": {"low": 4000, "medium": 12000, "high": 20000},
            "ajman": {"low": 3500, "medium": 10000, "high": 18000},
            "fujairah": {"low": 3500, "medium": 10000, "high": 18000},
            "ras_al_khaimah": {"low": 3500, "medium": 10000, "high": 18000},
            "umm_al_quwain": {"low": 3500, "medium": 10000, "high": 18000}
        }
        
        # File handling
        UPLOAD_DIR: str = "uploads"
        MAX_FILE_SIZE: int = 52428800  # 50MB
        SUPPORTED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "pdf"]
        SUPPORTED_DOC_FORMATS: List[str] = ["pdf", "xlsx", "csv", "docx"]

        # Required document types for a complete application (mandatory set)
        REQUIRED_DOCUMENT_TYPES: List[str] = [
            "emirates_id",
            "bank_statement",
            "utility_bill",
        ]
        
        # Security
        SECRET_KEY: str = "uae-social-support-secret-key"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        
        # Redis
        REDIS_URL: str = "redis://localhost:6379"
        
        @property
        def database_url(self) -> str:
            return self.DATABASE_URL

        @property
        def database_echo(self) -> bool:
            return self.DATABASE_ECHO

        @classmethod
        def get_uae_threshold(cls, emirate: str) -> Dict[str, int]:
            """Get income thresholds for emirate"""
            settings_instance = cls()
            return settings_instance.UAE_INCOME_THRESHOLDS.get(emirate, settings_instance.UAE_INCOME_THRESHOLDS["dubai"])
        
        class Config:
            env_file = ".env"
            case_sensitive = False
            # Allow extra fields if needed
            extra = "ignore"  # This prevents the validation error

else:
    # Fallback when Pydantic is not available
    class Settings:
        """Fallback settings class"""
        APP_NAME = "UAE Social Support AI System"
        OLLAMA_MODE = os.getenv("OLLAMA_MODE", "cloud")
        OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
        OLLAMA_MODEL = "gpt-oss:120b-cloud"
        LANGGRAPH_CHECKPOINTING = True
        WORKFLOW_TIMEOUT = 300
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./social_support.db")
        DATABASE_ECHO = False

        # Required document types for a complete application (mandatory set)
        REQUIRED_DOCUMENT_TYPES = [
            "emirates_id",
            "bank_statement",
            "utility_bill",
        ]

        @property
        def database_url(self) -> str:
            return self.DATABASE_URL

        @property
        def database_echo(self) -> bool:
            return self.DATABASE_ECHO

def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()

# Global settings instance
settings = get_settings()
