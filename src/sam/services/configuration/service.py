import json
import os
from typing import Any, Dict, Optional
import structlog

from .models import ConfigSchema, ConfigValue

logger = structlog.get_logger()


class ConfigurationService:
    """Minimal Configuration Service backed by a JSON file.

    Provides typed accessors and optional schema validation.
    """

    def __init__(self, config_path: str, schema: Optional[ConfigSchema] = None) -> None:
        self.config_path = config_path
        self.schema = schema
        self._data: Dict[str, Any] = {}
        logger.info("ConfigurationService initializing", path=self.config_path)
        self._load()

    def _load(self) -> None:
        try:
            if not os.path.exists(self.config_path):
                logger.warning("Configuration file not found, using empty config", path=self.config_path)
                self._data = {}
                return
            with open(self.config_path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
            logger.info("Configuration loaded", path=self.config_path)
            if self.schema is not None:
                try:
                    self.validate()
                except Exception as e:
                    logger.error("Configuration validation failed", error=str(e))
                    raise
        except Exception:
            logger.exception("Failed loading configuration")
            raise

    def reload(self) -> None:
        logger.info("Reloading configuration", path=self.config_path)
        self._load()

    def validate(self) -> None:
        if self.schema is None:
            return
        # Use schema.validate to raise on mismatch
        self.schema.validate(self._data)
        logger.info("Configuration validated against schema", path=self.config_path)

    def _resolve(self, key: str) -> Optional[Any]:
        # Support dotted keys for nested lookup
        parts = key.split(".") if key else []
        cur: Any = self._data
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return None
        return cur

    def get(self, key: str, default: Any = None) -> Any:
        val = self._resolve(key)
        if val is None:
            logger.debug("Configuration key not found, returning default", key=key)
            return default
        return val

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        val = self._resolve(key)
        if val is None:
            logger.warning("Configuration string key not found", key=key)
            return default
        if isinstance(val, str):
            return val
        # Coerce to str for basic types
        try:
            return str(val)
        except Exception:
            logger.error("Failed coercing configuration value to str", key=key, value=val)
            return default

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        val = self._resolve(key)
        if val is None:
            logger.warning("Configuration int key not found", key=key)
            return default
        if isinstance(val, int):
            return val
        try:
            return int(val)
        except Exception:
            logger.error("Failed coercing configuration value to int", key=key, value=val)
            return default

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        val = self._resolve(key)
        if val is None:
            logger.warning("Configuration bool key not found", key=key)
            return default
        if isinstance(val, bool):
            return val
        # Accept common string forms
        if isinstance(val, str):
            lowered = val.lower()
            if lowered in ("true", "1", "yes", "y", "on"):
                return True
            if lowered in ("false", "0", "no", "n", "off"):
                return False
        try:
            return bool(val)
        except Exception:
            logger.error("Failed coercing configuration value to bool", key=key, value=val)
            return default

    def get_path(self, key: str, default: Optional[str] = None) -> Optional[str]:
        val = self._resolve(key)
        if val is None:
            logger.warning("Configuration path key not found", key=key)
            return default
        if isinstance(val, str):
            # No normalization here, caller can os.path.abspath if needed
            return val
        try:
            return str(val)
        except Exception:
            logger.error("Failed coercing configuration value to path string", key=key, value=val)
            return default

    def set(self, key: str, value: Any, source: str = "runtime") -> None:
        # Shallow set only; does not persist to disk
        parts = key.split(".") if key else []
        if not parts:
            return
        cur = self._data
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value
        logger.info("Configuration value set (in-memory)", key=key, source=source)

    def items(self) -> Dict[str, Any]:
        return dict(self._data)
