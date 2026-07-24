"""
Plugin Manifest Loader – reads manifests from YAML/JSON.
"""

import json
from pathlib import Path
from typing import List, Optional
import structlog
import yaml

# Note: Loader returns raw dicts; parsing into PluginManifest occurs in validator/installer


class PluginManifestLoader:
    """Load and parse plugin manifests from files."""

    def __init__(self):
        self.logger = structlog.get_logger()

    def load_from_yaml(self, path: Path) -> dict:
        """Load manifest from YAML file and return raw dict."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            data = data or {}
            from .models import PluginManifest

            return PluginManifest(**data)
        except yaml.YAMLError as e:
            self.logger.error("invalid_yaml", path=str(path), error=str(e))
            raise ValueError(f"Invalid YAML in {path}: {e}")
        except Exception as e:
            self.logger.error("load_failed", path=str(path), error=str(e))
            raise

    def load_from_json(self, path: Path) -> dict:
        """Load manifest from JSON file and return raw dict."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = data or {}
            from .models import PluginManifest

            return PluginManifest(**data)
        except json.JSONDecodeError as e:
            self.logger.error("invalid_json", path=str(path), error=str(e))
            raise ValueError(f"Invalid JSON in {path}: {e}")
        except Exception as e:
            self.logger.error("load_failed", path=str(path), error=str(e))
            raise

    def load_from_directory(self, directory: Path) -> List[dict]:
        """Load all manifests from a directory (recursively). Returns list of PluginManifest instances."""
        manifests = []
        for path in directory.rglob("*"):
            if path.suffix in [".yaml", ".yml"]:
                try:
                    manifest = self.load_from_yaml(path)
                    manifests.append(manifest)
                    self.logger.info("manifest_loaded", path=str(path), name=manifest.name)
                except Exception as e:
                    self.logger.warning("manifest_skipped", path=str(path), error=str(e))
            elif path.suffix == ".json":
                try:
                    manifest = self.load_from_json(path)
                    manifests.append(manifest)
                    self.logger.info("manifest_loaded", path=str(path), name=manifest.name)
                except Exception as e:
                    self.logger.warning("manifest_skipped", path=str(path), error=str(e))
        return manifests
