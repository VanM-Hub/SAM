"""
OP-368 — Version & Plugin Discovery
=====================================

Version: reads SAM version, git commit, build date, Python, platform.
Plugin discovery: scans plugin folders — read-only, no loading.
"""

import os
import sys
import platform
import subprocess
from typing import Any, Dict, List, Optional


class SamVersion:
    """SAM version information. Immutable."""

    __slots__ = (
        "version",
        "commit",
        "build_date",
        "python_version",
        "platform_name",
    )

    def __init__(
        self,
        version: str = "",
        commit: str = "",
        build_date: str = "",
        python_version: str = "",
        platform_name: str = "",
    ) -> None:
        self.version = version
        self.commit = commit
        self.build_date = build_date
        self.python_version = python_version
        self.platform_name = platform_name

    @classmethod
    def detect(cls) -> "SamVersion":
        """Detect version info from the environment."""
        version = cls._read_version()
        commit = cls._read_commit()
        return cls(
            version=version,
            commit=commit,
            build_date="",
            python_version=sys.version.split()[0],
            platform_name=platform.system(),
        )

    @staticmethod
    def _read_version() -> str:
        try:
            from sam import __version__  # type: ignore[import]
            return str(__version__)
        except (ImportError, AttributeError):
            return "unknown"

    @staticmethod
    def _read_commit() -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def to_dict(self) -> Dict[str, str]:
        return {
            "version": self.version,
            "commit": self.commit,
            "build_date": self.build_date,
            "python": self.python_version,
            "platform": self.platform_name,
        }

    def __repr__(self) -> str:
        return f"<SamVersion v{self.version} commit={self.commit}>"


class PluginInfo:
    """Information about a discovered plugin. Immutable."""

    __slots__ = ("name", "path", "type")

    def __init__(self, name: str, path: str, type_: str = "") -> None:
        self.name = name
        self.path = path
        self.type = type_ or self._infer_type()

    def _infer_type(self) -> str:
        p = self.path.lower()
        if "provider" in p:
            return "provider"
        if "executor" in p:
            return "executor"
        if "connector" in p:
            return "connector"
        if "plugin" in p:
            return "plugin"
        return "unknown"

    def __repr__(self) -> str:
        return f"<Plugin {self.name} ({self.type})>"


class PluginDiscovery:
    """Scans plugin folders without loading anything.

    Read-only — does NOT import or execute any plugin code.
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()

    def discover_all(self) -> List[PluginInfo]:
        """Discover all plugins across known folders."""
        plugins: List[PluginInfo] = []
        for folder_name in ("plugins", "providers", "executors", "connectors"):
            plugins.extend(self._scan_folder(folder_name))
        return plugins

    def _scan_folder(self, folder_name: str) -> List[PluginInfo]:
        folder = os.path.join(self._workspace, folder_name)
        if not os.path.isdir(folder):
            return []

        results: List[PluginInfo] = []
        for entry in os.listdir(folder):
            entry_path = os.path.join(folder, entry)
            # .py files and directories with __init__.py
            if entry.endswith(".py") and entry != "__init__.py":
                name = entry[:-3]
                results.append(PluginInfo(name, entry_path, folder_name))
            elif os.path.isdir(entry_path):
                init_file = os.path.join(entry_path, "__init__.py")
                if os.path.isfile(init_file):
                    results.append(PluginInfo(entry, entry_path, folder_name))
        return results
