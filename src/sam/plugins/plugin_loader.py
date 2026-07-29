# OP-413 — Plugin Loader
# Python 3.8, frozen DTO, synchronous, no eval/exec/import string

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .plugin_protocol import PluginProtocol, PluginDescriptor, PluginCapability


@dataclass(frozen=True)
class PluginManifest:
    name: str = ""; version: str = ""
    description: str = ""
    author: str = ""
    required_version: str = ""
    capabilities: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True


@dataclass(frozen=True)
class PluginPackage:
    package_id: str = ""
    manifest: Optional[PluginManifest] = None
    validated: bool = False
    errors: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PluginValidation:
    valid: bool = True
    errors: Tuple[str, ...] = field(default_factory=tuple)
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    requires_approval: bool = False


class PluginLoader:
    """Plugin loader — parses manifest, validates compatibility.

    Does NOT load external code. No eval/exec/import string.
    """

    def parse_manifest(self, manifest_data: Dict[str, Any]) -> PluginManifest:
        caps = tuple(
            PluginCapability(name=c.get("name",""), description=c.get("description",""),
                actions=tuple(c.get("actions",[])), requires_approval=c.get("requires_approval",True),
                risk_level=c.get("risk_level","low"), read_only=c.get("read_only",True))
            for c in manifest_data.get("capabilities", [])
        )
        return PluginManifest(
            name=manifest_data.get("name",""), version=manifest_data.get("version",""),
            description=manifest_data.get("description",""),
            author=manifest_data.get("author",""),
            required_version=manifest_data.get("required_version",""),
            capabilities=caps,
            dependencies=tuple(manifest_data.get("dependencies", [])),
            read_only=manifest_data.get("read_only", True),
        )

    def validate_manifest(self, manifest: PluginManifest,
                          sam_version: str = "4.5.0") -> PluginValidation:
        errors: List[str] = []; warnings: List[str] = []

        if not manifest.name: errors.append("Plugin name is required")
        if not manifest.version: errors.append("Plugin version is required")

        if manifest.required_version and manifest.required_version > sam_version:
            warnings.append(f"Plugin requires SAM {manifest.required_version}, current is {sam_version}")

        if manifest.capabilities:
            for cap in manifest.capabilities:
                if not cap.actions:
                    warnings.append(f"Capability '{cap.name}' has no actions")
                if cap.risk_level not in ("low","medium","high","critical"):
                    warnings.append(f"Capability '{cap.name}' has invalid risk level")

        if not manifest.read_only:
            for cap in manifest.capabilities:
                if not cap.read_only and not cap.requires_approval:
                    warnings.append(f"Non-readonly capability '{cap.name}' should require approval")

        requires_approval = not manifest.read_only or any(
            not c.read_only for c in manifest.capabilities
        )

        return PluginValidation(valid=len(errors)==0, errors=tuple(errors),
            warnings=tuple(warnings), requires_approval=requires_approval)

    def load(self, manifest_data: Dict[str, Any],
             sam_version: str = "4.5.0") -> PluginPackage:
        manifest = self.parse_manifest(manifest_data)
        validation = self.validate_manifest(manifest, sam_version)
        if not validation.valid:
            return PluginPackage(manifest=manifest, validated=False, errors=validation.errors)
        return PluginPackage(
            package_id=manifest.name.lower().replace(" ","_"),
            manifest=manifest, validated=True,
        )
