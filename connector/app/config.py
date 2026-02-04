import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".cloaksheets"
        self.config_path = self.config_dir / "config.json"

        self.max_rows_return = 5000
        self.query_timeout_sec = 10
        self.xlsx_max_size_mb = 200
        self.rate_limit_requests_per_minute = 60

        self._supabase_client: Client | None = None
        self._init_supabase()
        self._load_config()

    def _init_supabase(self):
        supabase_url = os.getenv("VITE_SUPABASE_URL")
        supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            try:
                self._supabase_client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")
        else:
            logger.warning("Supabase credentials not found in environment")

    @property
    def supabase(self) -> Client | None:
        return self._supabase_client

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
            "configPath": str(self.config_path)
        }

    def reload(self):
        self._load_config()
        logger.info("Configuration reloaded")


config = Config()
