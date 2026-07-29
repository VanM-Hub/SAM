# OP-425 — Extension Validator
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .sdk_protocol import SDKVersion, SDKCompatibility
from .plugin_sdk import PluginManifestS, PluginSDK
from .connector_sdk import ConnectorManifest, ConnectorSDK
from .provider_sdk import ProviderManifest, ProviderSDK


@dataclass(frozen=True)
class ValidationIssue:
    category: str = ""; severity: str = "warning"
    message: str = ""; field: str = ""


@dataclass(frozen=True)
class ValidationSummary:
    total: int = 0; errors: int = 0; warnings: int = 0
    infos: int = 0; passed: bool = True


@dataclass(frozen=True)
class CompatibilityReport:
    compatible: bool = True
    sdk_version: Optional[SDKVersion] = None
    python_version_ok: bool = True
    sam_version_ok: bool = True
    issues: Tuple[ValidationIssue, ...] = field(default_factory=tuple)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ExtensionValidator:
    """Validates extensions for SDK compatibility, manifests, capabilities,
    policy, dependencies, permissions, and backward compatibility."""

    def __init__(self):
        self._plugin_sdk = PluginSDK()
        self._connector_sdk = ConnectorSDK()
        self._provider_sdk = ProviderSDK()

    def validate_plugin_manifest(self, manifest: PluginManifestS,
                                 sdk_version: Optional[SDKVersion] = None) -> CompatibilityReport:
        issues: List[ValidationIssue] = []
        sv = sdk_version or SDKVersion.current()

        # SDK version check
        if sv > SDKVersion(1,0,0):
            issues.append(ValidationIssue("sdk_version","warning",
                f"SDK version {sv} may not be fully compatible"))

        # Validate via plugin SDK
        result = self._plugin_sdk.validate_manifest(manifest)
        for err in result.errors:
            issues.append(ValidationIssue("manifest","error", err))
        for warn in result.warnings:
            issues.append(ValidationIssue("manifest","warning", warn))

        # Backward compatibility
        if not manifest.read_only and manifest.requires_approval:
            pass  # OK
        elif not manifest.read_only and not manifest.requires_approval:
            issues.append(ValidationIssue("permissions","error",
                "Non-readonly plugin must require approval"))

        return CompatibilityReport(
            compatible=not any(i.severity=="error" for i in issues),
            sdk_version=sv, issues=tuple(issues))

    def validate_connector_manifest(self, manifest: ConnectorManifest,
                                     sdk_version: Optional[SDKVersion] = None) -> CompatibilityReport:
        issues: List[ValidationIssue] = []
        result = self._connector_sdk.validate_manifest(manifest)
        for err in result.errors: issues.append(ValidationIssue("manifest","error", err))
        for warn in result.warnings: issues.append(ValidationIssue("manifest","warning", warn))
        return CompatibilityReport(compatible=not any(i.severity=="error" for i in issues),
            sdk_version=sdk_version or SDKVersion.current(), issues=tuple(issues))

    def validate_provider_manifest(self, manifest: ProviderManifest,
                                    sdk_version: Optional[SDKVersion] = None) -> CompatibilityReport:
        issues: List[ValidationIssue] = []
        result = self._provider_sdk.validate_manifest(manifest)
        for err in result.errors: issues.append(ValidationIssue("manifest","error", err))
        for warn in result.warnings: issues.append(ValidationIssue("manifest","warning", warn))
        return CompatibilityReport(compatible=not any(i.severity=="error" for i in issues),
            sdk_version=sdk_version or SDKVersion.current(), issues=tuple(issues))

    def check_sdk_compatibility(self, sdk_version: Optional[SDKVersion] = None,
                                python_version: str = "3.8",
                                sam_version: str = "4.45.0") -> SDKCompatibility:
        sv = sdk_version or SDKVersion.current()
        sdk_ok = sv <= SDKVersion(1,0,0)
        py_ok = python_version >= "3.8" if python_version else True
        sam_ok = sam_version >= "4.0.0" if sam_version else True
        issues = []
        if not sdk_ok: issues.append(f"SDK version {sv} may be too new")
        if not py_ok: issues.append(f"Python {python_version} is below minimum 3.8")
        if not sam_ok: issues.append(f"SAM {sam_version} is below minimum 4.0.0")
        return SDKCompatibility(compatible=sdk_ok and py_ok and sam_ok,
            sdk_version_ok=sdk_ok, python_version_ok=py_ok,
            sam_version_ok=sam_ok, issues=tuple(issues))
