import os
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    FLOW_URL: str = os.getenv("FLOW_URL", "https://flow.google.com/")
    FLOW_GENERATION_MODE: str = os.getenv("FLOW_GENERATION_MODE", "TEST_MODE")
    FLOW_PROJECT_MODE: str = os.getenv("FLOW_PROJECT_MODE", "REUSE_SINGLE_PROJECT")
    AUTO_CONFIRM_GENERATION: bool = os.getenv("AUTO_CONFIRM_GENERATION", "false").lower() == "true"
    
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "veo")
    DEFAULT_ORIENTATION: str = os.getenv("DEFAULT_ORIENTATION", "16:9")
    DEFAULT_DURATION: str = os.getenv("DEFAULT_DURATION", "5")
    DEFAULT_OUTPUTS: int = int(os.getenv("DEFAULT_OUTPUTS", "1"))
    
    MAX_GENERATIONS_PER_JOB: int = int(os.getenv("MAX_GENERATIONS_PER_JOB", "1"))
    MAX_GENERATIONS_PER_SESSION: int = int(os.getenv("MAX_GENERATIONS_PER_SESSION", "10"))
    MAX_DAILY_GENERATIONS: int = int(os.getenv("MAX_DAILY_GENERATIONS", "20"))
    
    GENERATION_TIMEOUT: int = int(os.getenv("GENERATION_TIMEOUT", "600"))
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "60"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))
    
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "2"))
    RETRY_BACKOFF: int = int(os.getenv("RETRY_BACKOFF", "30"))
    CONCURRENCY: int = int(os.getenv("CONCURRENCY", "1"))
    
    BROWSER_PROFILE_DIR: str = os.getenv("BROWSER_PROFILE_DIR", "runtime/profile")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    DIAGNOSTICS_DIR: str = os.getenv("DIAGNOSTICS_DIR", "diagnostics")
    
    SCREENSHOT_ON_FAILURE: bool = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"

    @property
    def database_path(self) -> str:
        return os.path.abspath("data/bot.db")

settings = Settings()
