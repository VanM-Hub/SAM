"""
Plugin Manifest Validator – validates manifest integrity and completeness.
"""

from typing import List, Optional
import structlog
import importlib

from .models import PluginManifest, PluginPermission
from pydantic import ValidationError


class PluginManifestValidator:
    """Validate plugin manifests for correctness and completeness."""

    def __init__(self):
        self.logger = structlog.get_logger()

    def validate(self, manifest: PluginManifest) -> List[str]:
        """
        Validate manifest and return list of errors (empty if valid).

        Checks:
        - Required fields present
        - Version format
        - Entrypoint can be imported
        - Permissions valid
        """
        errors = []

        # If manifest is a raw dict, try to construct PluginManifest to reuse pydantic validation
        if isinstance(manifest, dict):
            try:
                manifest = PluginManifest(**manifest)
            except ValidationError as ve:
                for e in ve.errors():
                    loc = ".".join(str(x) for x in e.get("loc", []))
                    errors.append(f"{loc}: {e.get('msg')}")
                return errors

        # Check entrypoint can be imported (optional, but recommended)
        try:
            module_path = manifest.entrypoint.rsplit(".", 1)[0]
            importlib.import_module(module_path)
        except ImportError:
            errors.append(f"Entrypoint module cannot be imported: {manifest.entrypoint}")
        except Exception as e:
            errors.append(f"Entrypoint import error: {e}")

        # Validate network allowlist
        if PluginPermission.NETWORK_OUTBOUND in manifest.permissions:
            if not manifest.network_allowlist:
                errors.append(
                    "Network permission requires network_allowlist to be specified"
                )
            elif not all(isinstance(domain, str) for domain in manifest.network_allowlist):
                errors.append("network_allowlist must be a list of strings")

        # Validate permissions are valid enums
        for p in manifest.permissions:
            if not isinstance(p, PluginPermission):
                # allow string values too
                try:
                    PluginPermission(p)
                except Exception:
                    errors.append(f"Invalid permission: {p}")

        return errors

    def validate_and_log(self, manifest: PluginManifest) -> bool:
        """Validate and log results. Returns True if valid."""
        errors = self.validate(manifest)
        if errors:
            self.logger.error(
                "manifest_validation_failed",
                name=(manifest.name if hasattr(manifest, "name") else None),
                errors=errors,
            )
            return False
        self.logger.info(
            "manifest_validation_passed",
            name=manifest.name,
            version=manifest.version,
        )
        return True

