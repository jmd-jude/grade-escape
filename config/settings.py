import os
from pydantic.v1 import BaseSettings
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables for local development
load_dotenv()

def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets'):
            return st.secrets.get(key, "")
    except:
        pass
    
    # Fall back to environment variables
    return os.getenv(key, default)

class Settings(BaseSettings):
    # API Keys and URLs
    openai_api_key: str = get_secret("OPENAI_API_KEY", "")
    supabase_url: str = get_secret("SUPABASE_URL", "")
    supabase_key: str = get_secret("SUPABASE_KEY", "")
    supabase_service_key: str = get_secret("SUPABASE_SERVICE_KEY", "")
    
    # App Settings
    debug: bool = get_secret("DEBUG", "False").lower() == "true"
    environment: str = get_secret("ENVIRONMENT", "development")
    
    # Processing Settings
    max_retries: int = int(get_secret("MAX_RETRIES", "3"))
    batch_size: int = int(get_secret("BATCH_SIZE", "10"))
    ocr_confidence_threshold: float = float(get_secret("OCR_CONFIDENCE_THRESHOLD", "0.8"))
    
    # Storage Settings
    storage_bucket: str = get_secret("STORAGE_BUCKET", "ap-grader-images")
    
    class Config:
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate required settings
        self._validate_settings()
        # Log configuration status
        self._log_status()
    
    def _validate_settings(self):
        """Validate required settings are present"""
        required_settings = {
            "OpenAI API Key": self.openai_api_key,
            "Supabase URL": self.supabase_url,
            "Supabase Key": self.supabase_key,
            "Supabase Service Key": self.supabase_service_key
        }
        
        missing_settings = [k for k, v in required_settings.items() if not v]
        if missing_settings:
            error_msg = f"Missing required settings: {', '.join(missing_settings)}"
            if not hasattr(st, 'secrets'):
                error_msg += "\nNo Streamlit secrets found. Are you running locally? Check your .env file."
            raise ValueError(error_msg)
    
    def _log_status(self):
        """Log configuration status"""
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Supabase URL: {self.supabase_url}")
        if self.supabase_key:
            logger.info("Supabase key is set")
        if self.supabase_service_key:
            logger.info("Supabase service key is set")
        if self.openai_api_key:
            logger.info("OpenAI API key is set")

@lru_cache()
def get_settings() -> Settings:
    """Create cached settings instance"""
    return Settings()
