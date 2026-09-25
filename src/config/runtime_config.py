import os
import logging
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.database.db import get_db_context
from src.database.repository import Repository
from src.models.domain import CreditSafetyMode

logger = logging.getLogger(__name__)

class RuntimeConfigService:
    """
    Dynamically resolves configuration settings by layering:
    1. Base environment / settings defaults (.env)
    2. Live database overrides from the 'settings' table (updated via UI without server restart)
    """

    def get_all(self) -> Dict[str, Any]:
        overrides = {}
        try:
            with get_db_context() as db:
                repo = Repository(db)
                overrides = repo.get_settings()
        except Exception as e:
            logger.debug(f"Unable to load DB settings overrides: {e}")

        return {
            "FLOW_URL": overrides.get("FLOW_URL", settings.FLOW_URL),
            "FLOW_GENERATION_MODE": overrides.get("FLOW_GENERATION_MODE", settings.FLOW_GENERATION_MODE),
            "FLOW_PROJECT_MODE": overrides.get("FLOW_PROJECT_MODE", settings.FLOW_PROJECT_MODE),
            "AUTO_CONFIRM_GENERATION": overrides.get(
                "AUTO_CONFIRM_GENERATION", str(settings.AUTO_CONFIRM_GENERATION)
            ).lower() == "true",
            "DEFAULT_MODEL": overrides.get("DEFAULT_MODEL", settings.DEFAULT_MODEL),
            "DEFAULT_ORIENTATION": overrides.get("DEFAULT_ORIENTATION", settings.DEFAULT_ORIENTATION),
            "DEFAULT_DURATION": overrides.get("DEFAULT_DURATION", settings.DEFAULT_DURATION),
            "DEFAULT_OUTPUTS": int(overrides.get("DEFAULT_OUTPUTS", str(settings.DEFAULT_OUTPUTS))),
            "MAX_GENERATIONS_PER_JOB": int(
                overrides.get("MAX_GENERATIONS_PER_JOB", str(settings.MAX_GENERATIONS_PER_JOB))
            ),
            "MAX_GENERATIONS_PER_SESSION": int(
                overrides.get("MAX_GENERATIONS_PER_SESSION", str(settings.MAX_GENERATIONS_PER_SESSION))
            ),
            "MAX_DAILY_GENERATIONS": int(
                overrides.get("MAX_DAILY_GENERATIONS", str(settings.MAX_DAILY_GENERATIONS))
            ),
            "CONCURRENCY": int(overrides.get("CONCURRENCY", str(settings.CONCURRENCY))),
            "CREDIT_SAFETY_MODE": overrides.get("CREDIT_SAFETY_MODE", "STRICT"),
            "MAX_DAILY_CREDITS": int(overrides["MAX_DAILY_CREDITS"]) if overrides.get("MAX_DAILY_CREDITS") else None,
            "MAX_SESSION_CREDITS": int(overrides["MAX_SESSION_CREDITS"]) if overrides.get("MAX_SESSION_CREDITS") else None,
            "MAX_JOB_COST": int(overrides["MAX_JOB_COST"]) if overrides.get("MAX_JOB_COST") else None,
            "BLOCK_ON_UNVERIFIED_BALANCE": overrides.get("BLOCK_ON_UNVERIFIED_BALANCE", "true").lower() == "true",
            "BLOCK_ON_UNVERIFIED_COST": overrides.get("BLOCK_ON_UNVERIFIED_COST", "true").lower() == "true",
            "HEADLESS": overrides.get("HEADLESS", str(settings.HEADLESS)).lower() == "true",
            "GENERATION_TIMEOUT": int(
                overrides.get("GENERATION_TIMEOUT", str(settings.GENERATION_TIMEOUT))
            ),
            "BROWSER_TIMEOUT": int(overrides.get("BROWSER_TIMEOUT", str(settings.BROWSER_TIMEOUT))),
            "DOWNLOAD_TIMEOUT": int(overrides.get("DOWNLOAD_TIMEOUT", str(settings.DOWNLOAD_TIMEOUT))),
            "RETRY_COUNT": int(overrides.get("RETRY_COUNT", str(settings.RETRY_COUNT))),
            "RETRY_BACKOFF": int(overrides.get("RETRY_BACKOFF", str(settings.RETRY_BACKOFF))),
            "SCREENSHOT_ON_FAILURE": overrides.get(
                "SCREENSHOT_ON_FAILURE", str(settings.SCREENSHOT_ON_FAILURE)
            ).lower() == "true",
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.get_all().get(key, default)

    def set_many(self, updates: Dict[str, Any]) -> int:
        with get_db_context() as db:
            repo = Repository(db)
            for k, v in updates.items():
                repo.set_setting(k, str(v) if v is not None else "")
        return len(updates)

    @property
    def credit_safety_mode(self) -> CreditSafetyMode:
        val = str(self.get("CREDIT_SAFETY_MODE", "STRICT")).upper()
        try:
            return CreditSafetyMode(val)
        except ValueError:
            return CreditSafetyMode.STRICT

runtime_config = RuntimeConfigService()
