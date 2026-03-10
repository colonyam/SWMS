"""Configuration settings for the Smart Waste Management System"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    APP_NAME: str = "Smart Waste Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./waste_management.db"
    
    # API settings
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # WebSocket
    WS_PING_INTERVAL: int = 20
    WS_PING_TIMEOUT: int = 10
    
    # IoT Simulator
    SIMULATOR_ENABLED: bool = True
    SIMULATOR_UPDATE_INTERVAL: int = 30  # seconds
    
    # Analytics
    PREDICTION_HORIZON_DAYS: int = 7
    EFFICIENCY_ANALYSIS_DAYS: int = 30
    
    # Alerts
    ALERT_FILL_THRESHOLD_HIGH: int = 80
    ALERT_FILL_THRESHOLD_CRITICAL: int = 95
    ALERT_BATTERY_THRESHOLD: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
