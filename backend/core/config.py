"""
Centralized Configuration Management

Loads and validates all configuration from environment variables.
"""

import os
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load .env from parent directory (project root) BEFORE anything else
root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(root_env)

# Configure logging
logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongo_uri: Optional[str] = Field(None, description="MongoDB connection URI")
    db_name: str = Field("iec_code_generator", description="Database name")
    collection_name: str = Field("variables", description="Collection name")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    
    # API Configuration
    max_upload_size: int = Field(5 * 1024 * 1024, description="Max upload size in bytes")
    request_timeout: int = Field(30, description="Request timeout in seconds")
    
    # AI Configuration
    groq_api_key: Optional[str] = Field(None, description="Groq API key")
    groq_model_name: str = Field("llama-3.1-70b-versatile", description="Groq model name")
    rag_k: int = Field(3, description="RAG retriever k value")
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator("allowed_origins", pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            logger.warning(f"Invalid log level '{v}', defaulting to INFO")
            return "INFO"
        return upper_v
    
    @property
    def has_database(self) -> bool:
        """Check if database is configured."""
        return bool(self.mongo_uri)
    
    @property
    def has_ai(self) -> bool:
        """Check if AI is configured."""
        return bool(self.groq_api_key)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    # Load from environment variables
    settings = Settings(
        mongo_uri=os.getenv("MONGO_URI"),
        db_name=os.getenv("DB_NAME", "iec_code_generator"),
        collection_name=os.getenv("COLLECTION_NAME", "variables"),
        allowed_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
        max_upload_size=int(os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024)),
        groq_api_key=os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY2"),
        groq_model_name=os.getenv("GROQ_MODEL_NAME", "llama-3.1-70b-versatile"),
        rag_k=int(os.getenv("RAG_K", 3)),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
    
    # Log configuration status
    if not settings.has_database:
        logger.warning("MONGO_URI not configured - database features disabled")
    if not settings.has_ai:
        logger.warning("GROQ_API_KEY not configured - AI features disabled")
    
    return settings


# Convenience function
settings = get_settings()
