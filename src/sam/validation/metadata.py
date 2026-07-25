"""Metadata validation for capability descriptors."""

import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import structlog

from sam.models import CapabilityDescriptor

logger = structlog.get_logger(__name__)


# Valid risk levels
VALID_RISK_LEVELS = frozenset(["Low", "Medium", "High", "Critical"])

# Valid capability types
VALID_CAPABILITY_TYPES = frozenset([
    "observation.health-checks",
    "observation.diagnostics",
    "observation.monitoring",
    "action.configuration",
    "action.remediation",
    "action.provisioning",
    "analysis.correlation",
    "analysis.pattern-detection",
    "analysis.recommendation",
    "decision.approval",
    "decision.routing",
    "decision.escalation",
])

# SemVer regex (basic validation: x.y.z or x.y.z-suffix)
SEMVER_REGEX = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+)?$")


@dataclass
class ValidationResult:
    """Result of metadata validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ValidationError(Exception):
    """Exception raised when metadata validation fails."""
    def __init__(self, capability_id: str, errors: List[str]):
        self.capability_id = capability_id
        self.errors = errors
        super().__init__(f"Validation failed for '{capability_id}': {'; '.join(errors)}")


def validate_semver(version: str) -> bool:
    """Validate a version string follows SemVer format (basic check)."""
    return bool(SEMVER_REGEX.match(version))


def validate_implementation_import(implementation: str) -> List[str]:
    """Attempt to import the implementation class to verify it exists.
    
    Returns list of errors (empty if successful).
    """
    errors = []
    try:
        module_path, class_name = implementation.rsplit(".", 1)
        importlib.import_module(module_path)
    except ValueError:
        errors.append(f"Invalid implementation format (expected 'module.Class'): {implementation}")
    except ImportError as e:
        errors.append(f"Cannot import module for implementation '{implementation}': {e}")
    except Exception as e:
        errors.append(f"Error validating implementation '{implementation}': {e}")
    return errors


def validate_capability_metadata(
    metadata: Dict[str, Any],
    source_document: str,
    existing_ids: Optional[Set[str]] = None,
) -> ValidationResult:
    """Validate capability metadata from a knowledge document.
    
    Args:
        metadata: Dictionary of metadata from the document
        source_document: Path to the source document
        existing_ids: Set of already-registered capability IDs (for uniqueness check)
        
    Returns:
        ValidationResult with validation outcome and any errors/warnings
    """
    errors = []
    warnings = []
    
    # Get capability_id (required)
    capability_id = metadata.get("capability_id", "")
    if not capability_id:
        errors.append("Missing required field: capability_id")
    elif existing_ids and capability_id in existing_ids:
        errors.append(f"Duplicate capability_id: '{capability_id}' already registered")
    
    # Get capability_type (required)
    capability_type = metadata.get("capability_type", "")
    if not capability_type:
        errors.append("Missing required field: capability_type")
    elif capability_type not in VALID_CAPABILITY_TYPES:
        warnings.append(
            f"capability_type '{capability_type}' not in known types; "
            f"valid types: {sorted(VALID_CAPABILITY_TYPES)}"
        )
    
    # Get version (required, must be SemVer)
    version = metadata.get("version", "")
    if not version:
        errors.append("Missing required field: version")
    elif not validate_semver(str(version)):
        errors.append(f"Invalid version format (must be SemVer x.y.z): '{version}'")
    
    # Get implementation (required)
    implementation = metadata.get("implementation", "")
    if not implementation:
        errors.append("Missing required field: implementation")
    else:
        # Validate the implementation can be imported
        import_errors = validate_implementation_import(implementation)
        errors.extend(import_errors)
    
    # Get risk_level (required, must be valid)
    risk_level = metadata.get("risk_level", "")
    if not risk_level:
        errors.append("Missing required field: risk_level")
    elif risk_level not in VALID_RISK_LEVELS:
        errors.append(
            f"Invalid risk_level '{risk_level}'; must be one of: {sorted(VALID_RISK_LEVELS)}"
        )
    
    # Get permissions (optional, must be list or comma-separated string)
    permissions = metadata.get("permissions", [])
    if isinstance(permissions, str):
        if permissions.strip():
            permissions = [p.strip() for p in permissions.split(",") if p.strip()]
        else:
            permissions = []
    elif not isinstance(permissions, list):
        errors.append("permissions must be a list or comma-separated string")
    
    # Get dependencies (optional, must be list or comma-separated string)
    dependencies = metadata.get("dependencies", [])
    if isinstance(dependencies, str):
        if dependencies.strip():
            dependencies = [d.strip() for d in dependencies.split(",") if d.strip()]
        else:
            dependencies = []
    elif not isinstance(dependencies, list):
        errors.append("dependencies must be a list or comma-separated string")
    
    # Get tags (optional, must be list or comma-separated string)
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        if tags.strip():
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        else:
            tags = []
    elif not isinstance(tags, list):
        errors.append("tags must be a list or comma-separated string")
    
    # Get description (required, non-empty)
    description = metadata.get("description", "")
    if not description:
        errors.append("Missing required field: description")
    
    # Validate source_document exists (optional but recommended)
    if source_document:
        if not Path(source_document).exists():
            warnings.append(f"Source document does not exist: {source_document}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


async def validate_and_build_descriptor(
    metadata: Dict[str, Any],
    source_document: str,
    existing_ids: Optional[Set[str]] = None,
) -> CapabilityDescriptor:
    """Validate metadata and build a CapabilityDescriptor.
    
    Raises ValidationError if validation fails.
    """
    result = validate_capability_metadata(metadata, source_document, existing_ids)
    
    if not result.is_valid:
        capability_id = metadata.get("capability_id", "unknown")
        raise ValidationError(capability_id, result.errors)
    
    # Log warnings if any
    for warning in result.warnings:
        logger.warning("Metadata validation warning", capability_id=metadata.get("capability_id", ""), warning=warning)
    
    # Build descriptor from validated metadata
    capability_id = metadata["capability_id"]
    version = str(metadata["version"])
    implementation = metadata["implementation"]
    capability_type = metadata["capability_type"]
    risk_level = metadata["risk_level"]
    
    # Permissions
    permissions_raw = metadata.get("permissions", [])
    if isinstance(permissions_raw, str):
        permissions = [p.strip() for p in permissions_raw.split(",") if p.strip()]
    else:
        permissions = list(permissions_raw)
    
    # Dependencies
    dependencies_raw = metadata.get("dependencies", [])
    if isinstance(dependencies_raw, str):
        dependencies = [d.strip() for d in dependencies_raw.split(",") if d.strip()]
    else:
        dependencies = list(dependencies_raw)
    
    # Tags
    tags_raw = metadata.get("tags", [])
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    else:
        tags = list(tags_raw)
    
    description = metadata["description"]
    
    return CapabilityDescriptor(
        id=capability_id,
        version=version,
        implementation=implementation,
        capability_type=capability_type,
        risk_level=risk_level,
        permissions=permissions,
        dependencies=dependencies,
        tags=tags,
        description=description,
        source_document=source_document,
        enabled=True,
    )