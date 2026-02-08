import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from connector directory (parent of app directory)
connector_dir = Path(__file__).parent.parent
env_path = connector_dir / ".env"
load_dotenv(dotenv_path=env_path)
logger.info(f"Loading environment from: {env_path}")
if env_path.exists():
    logger.info(f"✓ Found .env file at {env_path}")
else:
    logger.warning(f"✗ No .env file found at {env_path} - using system environment variables")


class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".cloaksheets"
        self.config_path = self.config_dir / "config.json"

        self.max_rows_return = 5000
        self.query_timeout_sec = 10
        self.xlsx_max_size_mb = 200
        self.rate_limit_requests_per_minute = 60

        # AI Configuration
        self.ai_mode = os.getenv("AI_MODE", "off").lower() in ["on", "true", "1", "yes"]
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        self._load_config()
        self._validate_ai_config()

    @property
    def supabase(self):
        """Returns None - Supabase dependency removed for local-only mode"""
        return None

    def _validate_ai_config(self):
        """Validate AI configuration and log status"""
        ai_mode_env = os.getenv("AI_MODE", "off")
        openai_key_env = os.getenv("OPENAI_API_KEY", "")

        logger.info("=" * 60)
        logger.info("AI Configuration Status:")
        logger.info(f"  AI_MODE environment variable: {ai_mode_env}")
        logger.info(f"  OPENAI_API_KEY present: {'Yes' if openai_key_env else 'No'}")
        logger.info(f"  self.ai_mode (parsed): {self.ai_mode}")
        logger.info(f"  self.openai_api_key length: {len(self.openai_api_key) if self.openai_api_key else 0}")

        if self.ai_mode:
            if self.openai_api_key:
                logger.info("✓ AI_MODE: ON (OpenAI API key configured)")
                logger.info(f"  API Key starts with: {self.openai_api_key[:7]}...")
            else:
                logger.warning("✗ AI_MODE: ON but OPENAI_API_KEY not configured")
                logger.warning("  AI features will return errors until OPENAI_API_KEY is set")
                logger.warning("  Please set OPENAI_API_KEY in connector/.env file")
        else:
            logger.info("○ AI_MODE: OFF")
            logger.info("  To enable AI features, set AI_MODE=on in connector/.env")
        logger.info("=" * 60)

    def validate_ai_mode_for_request(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that AI mode is properly configured for processing requests.

        Returns:
            tuple: (is_valid, error_message)
                - (True, None) if AI is ready
                - (False, error_msg) if AI is not available
        """
        if not self.ai_mode:
            return False, "AI mode is disabled. Set AI_MODE=on to enable AI features."

        if not self.openai_api_key:
            return False, "AI mode enabled but OPENAI_API_KEY not configured. Please set OPENAI_API_KEY environment variable."

        return True, None

    def _load_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                self.max_rows_return = data.get('maxRowsReturn', self.max_rows_return)
                self.query_timeout_sec = data.get('queryTimeoutSec', self.query_timeout_sec)
                self.xlsx_max_size_mb = data.get('xlsxMaxSizeMb', self.xlsx_max_size_mb)
                self.rate_limit_requests_per_minute = data.get('rateLimitRequestsPerMinute', self.rate_limit_requests_per_minute)

                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config, using defaults: {e}")
        else:
            self._save_defaults()

    def _save_defaults(self):
        try:
            config_data = {
                "maxRowsReturn": self.max_rows_return,
                "queryTimeoutSec": self.query_timeout_sec,
                "xlsxMaxSizeMb": self.xlsx_max_size_mb,
                "rateLimitRequestsPerMinute": self.rate_limit_requests_per_minute
            }

            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            logger.warning(f"Failed to save default config: {e}")

    def get_safe_summary(self) -> Dict[str, Any]:
        return {
            "maxRowsReturn": self.max_rows_return,
            "queryTimeoutSec": self.query_timeout_sec,
            "xlsxMaxSizeMb": self.xlsx_max_size_mb,
            "rateLimitRequestsPerMinute": self.rate_limit_requests_per_minute,
            "configPath": str(self.config_path),
            "aiMode": "on" if self.ai_mode else "off",
            "openaiApiKeyConfigured": bool(self.openai_api_key)
        }

    def reload(self):
        self._load_config()
        logger.info("Configuration reloaded")


config = Config()
