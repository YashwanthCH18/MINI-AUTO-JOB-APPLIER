"""
Job Fetcher Stack - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # Apify
    apify_api_token: str
    apify_actor_id: str = "bebity~linkedin-jobs-scraper"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    
    # Development Mode
    dev_mode: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
