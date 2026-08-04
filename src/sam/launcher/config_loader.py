"""
OP-365 — Configuration Loader
===============================

Loads and validates launcher configuration.
All configuration objects are immutable.
"""

import os
import json
from typing import Any, Dict, List, Tuple


class LauncherConfig:
    """Immutable launcher configuration.

    All fields are read-only by convention (no setters).
    """

    __slots__ = (
        "_theme",
        "_workspace",
        "_language",
        "_log_level",
        "_host",
        "_provider",
        "_refresh_rate",
        "_safe_mode",
        "_readonly",
    )

    def __init__(
        self,
        theme: str = "dark",
        workspace: str = "",
        language: str = "en",
        log_level: str = "INFO",
        host: str = "console",
        provider: str = "",
        refresh_rate: int = 30,
        safe_mode: str = "NORMAL",
        readonly: bool = False,
    ) -> None:
        self._theme = theme
        self._workspace = workspace
        self._language = language
        self._log_level = log_level
        self._host = host
        self._provider = provider
        self._refresh_rate = refresh_rate
        self._safe_mode = safe_mode
        self._readonly = readonly

    # ── properties ─────────────────────────────

    @property
    def theme(self) -> str:
        return self._theme

    @property
    def workspace(self) -> str:
        return self._workspace

    @property
    def language(self) -> str:
        return self._language

    @property
    def log_level(self) -> str:
        return self._log_level

    @property
    def host(self) -> str:
        return self._host

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def refresh_rate(self) -> int:
        return self._refresh_rate

    @property
    def safe_mode(self) -> str:
        return self._safe_mode

    @property
    def readonly(self) -> bool:
        return self._readonly

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self._theme,
            "workspace": self._workspace,
            "language": self._language,
            "log_level": self._log_level,
            "host": self._host,
            "provider": self._provider,
            "refresh_rate": self._refresh_rate,
            "safe_mode": self._safe_mode,
            "readonly": self._readonly,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LauncherConfig":
        return cls(
            theme=data.get("theme", "dark"),
            workspace=data.get("workspace", ""),
            language=data.get("language", "en"),
            log_level=data.get("log_level", "INFO"),
            host=data.get("host", "console"),
            provider=data.get("provider", ""),
            refresh_rate=data.get("refresh_rate", 30),
            safe_mode=data.get("safe_mode", "NORMAL"),
            readonly=data.get("readonly", False),
        )

    def __repr__(self) -> str:
        return f"<LauncherConfig host={self._host} theme={self._theme}>"


class ConfigValidator:
    """Validates configuration values."""

    VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    VALID_THEMES = {"dark", "light", "auto"}
    VALID_LANGUAGES = {"en", "id"}
    VALID_HOSTS = {"console", "desktop", "headless", "api_server", "testing"}

    @classmethod
    def validate(cls, config: LauncherConfig) -> List[str]:
        errors: List[str] = []

        if config.log_level not in cls.VALID_LOG_LEVELS:
            errors.append(
                f"Invalid log_level '{config.log_level}'; "
                f"valid: {', '.join(sorted(cls.VALID_LOG_LEVELS))}"
            )
        if config.theme not in cls.VALID_THEMES:
            errors.append(
                f"Invalid theme '{config.theme}'; "
                f"valid: {', '.join(cls.VALID_THEMES)}"
            )
        if config.language not in cls.VALID_LANGUAGES:
            errors.append(
                f"Invalid language '{config.language}'; "
                f"valid: {', '.join(cls.VALID_LANGUAGES)}"
            )
        if config.host not in cls.VALID_HOSTS:
            errors.append(
                f"Invalid host '{config.host}'; "
                f"valid: {', '.join(cls.VALID_HOSTS)}"
            )
        if config.refresh_rate < 1:
            errors.append(
                f"Invalid refresh_rate {config.refresh_rate}; must be >= 1"
            )

        return errors


class ConfigLoader:
    """Loads and resolves launcher configuration.

    Priority: defaults ← file ← environment variables.
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()

    def load(self) -> Tuple[LauncherConfig, List[str]]:
        """Load configuration and return (config, validation_errors)."""
        config = self._load_defaults()
        config = self._merge_file(config)
        config = self._merge_env(config)

        errors = ConfigValidator.validate(config)
        return config, errors

    def _load_defaults(self) -> LauncherConfig:
        return LauncherConfig(workspace=self._workspace)

    def _merge_file(self, base: LauncherConfig) -> LauncherConfig:
        config_path = os.path.join(self._workspace, "sam_config.json")
        if not os.path.isfile(config_path):
            return base

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = base.to_dict()
            merged.update(data)
            return LauncherConfig.from_dict(merged)
        except (json.JSONDecodeError, OSError):
            return base

    def _merge_env(self, base: LauncherConfig) -> LauncherConfig:
        data = base.to_dict()
        env_map = {
            "SAM_THEME": "theme",
            "SAM_WORKSPACE": "workspace",
            "SAM_LANGUAGE": "language",
            "SAM_LOG_LEVEL": "log_level",
            "SAM_HOST": "host",
            "SAM_PROVIDER": "provider",
            "SAM_REFRESH_RATE": "refresh_rate",
            "SAM_SAFE_MODE": "safe_mode",
        }
        changed = False
        for env_key, config_key in env_map.items():
            value = os.environ.get(env_key)
            if value is not None:
                if config_key == "refresh_rate":
                    try:
                        data[config_key] = int(value)
                    except ValueError:
                        continue
                elif config_key == "readonly":
                    data[config_key] = value.lower() in ("1", "true", "yes")
                else:
                    data[config_key] = value
                changed = True

        if changed:
            return LauncherConfig.from_dict(data)
        return base
