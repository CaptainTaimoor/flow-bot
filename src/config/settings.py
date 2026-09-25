import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Explicitly load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

@dataclass
class Settings:
    # App
    APP_NAME: str = "Google Flow Automation Bot V2"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Flow Configuration
    FLOW_URL: str = os.getenv("FLOW_URL", "https://flow.google.com/")
    FLOW_GENERATION_MODE: str = os.getenv("FLOW_GENERATION_MODE", "STANDARD") # STANDARD, AGENT
    FLOW_PROJECT_MODE: str = os.getenv("FLOW_PROJECT_MODE", "REUSE_SINGLE_PROJECT") # REUSE_SINGLE_PROJECT, CREATE_PROJECT_PER_JOB
    AUTO_CONFIRM_GENERATION: bool = os.getenv("AUTO_CONFIRM_GENERATION", "true").lower() == "true"

    # Default Generation Settings
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "veo")
    DEFAULT_ORIENTATION: str = os.getenv("DEFAULT_ORIENTATION", "16:9")
    DEFAULT_DURATION: str = os.getenv("DEFAULT_DURATION", "5")
    DEFAULT_OUTPUTS: int = int(os.getenv("DEFAULT_OUTPUTS", "1"))

    # Limits & Safety
    MAX_GENERATIONS_PER_JOB: int = int(os.getenv("MAX_GENERATIONS_PER_JOB", "1"))
    MAX_GENERATIONS_PER_SESSION: int = int(os.getenv("MAX_GENERATIONS_PER_SESSION", "10"))
    MAX_DAILY_GENERATIONS: int = int(os.getenv("MAX_DAILY_GENERATIONS", "20"))
    CONCURRENCY: int = int(os.getenv("CONCURRENCY", "1"))

    # Timeouts (seconds)
    GENERATION_TIMEOUT: int = int(os.getenv("GENERATION_TIMEOUT", "600"))
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "60"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))

    # Retries
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "2"))
    RETRY_BACKOFF: int = int(os.getenv("RETRY_BACKOFF", "30"))

    # Browser
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    BROWSER_PROFILE_DIR: str = os.getenv("BROWSER_PROFILE_DIR", str(BASE_DIR / "runtime" / "profile"))

    # Storage Paths
    DATA_DIR: str = str(BASE_DIR / "data")
    MEDIA_DIR: str = str(BASE_DIR / "data" / "media")
    VIDEOS_DIR: str = str(BASE_DIR / "data" / "media" / "videos")
    THUMBNAILS_DIR: str = str(BASE_DIR / "data" / "media" / "thumbnails")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", str(BASE_DIR / "output"))
    DIAGNOSTICS_DIR: str = os.getenv("DIAGNOSTICS_DIR", str(BASE_DIR / "diagnostics"))

    # Diagnostics & Features
    SCREENSHOT_ON_FAILURE: bool = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"

    @property
    def database_path(self) -> str:
        return str(Path(self.DATA_DIR) / "bot.db")

    @property
    def database_url(self) -> str:
        db_file = Path(self.database_path).as_posix()
        return f"sqlite:///{db_file}"

    def ensure_directories(self):
        for path_str in [
            self.DATA_DIR,
            self.MEDIA_DIR,
            self.VIDEOS_DIR,
            self.THUMBNAILS_DIR,
            self.OUTPUT_DIR,
            self.DIAGNOSTICS_DIR,
            os.path.dirname(self.BROWSER_PROFILE_DIR),
        ]:
            os.makedirs(path_str, exist_ok=True)

settings = Settings()
settings.ensure_directories()
