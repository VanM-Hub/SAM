"""Validation utilities for capability metadata."""

import importlib
import os
import re
from typing import Any, Dict, List, Optional, Set

import structlog

from sam.models import CapabilityDescriptor

logger = structlog.get_logger(__name__)

# Valid risk levels
VALID_RISK_LEVELS = {"Low", "Medium", "High", "Critical"}

# SemVer regex (simplified - requires at least major.minor.patch)
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")


class ValidationError(Exception):
    """Raised when capability metadata validation fails."""

    def __init__(self, capability_id: str, errors: List[str]) -> None:
        self.capability_id = capability_id
        self.errors = errors
        super().__init__(f"Validation failed for {capability_id}: {'; '.join(errors)}")


def validate_capability_metadata(
    metadata: Dict[str, Any],
    source_document: str,
    existing_ids: Optional[Set[str]] = None,
) -> List[str]:
    """Validate capability metadata and return list of errors.

    Args:
        metadata: Dictionary of metadata from knowledge document
        source_document: Path to the source document
        existing_ids: Set of already-registered capability IDs (for duplicate check)

    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []
    cap_id = metadata.get("capability_id", "")

    # 1. id tidak boleh kosong
    if not cap_id or not isinstance(cap_id, str) or not cap_id.strip():
        errors.append("capability_id is required and cannot be empty")

    # 2. version harus mengikuti format SemVer (minimal x.y.z)
    version = metadata.get("version", "1.0.0")
    if version and not SEMVER_PATTERN.match(str(version)):
        errors.append(f"version '{version}' must follow SemVer format (e.g., 1.0.0)")

    # 3. implementation boleh kosong; if present we will validate format/import later
    implementation = metadata.get("implementation", "")

    # 4. capability_type tidak boleh kosong
    capability_type = metadata.get("capability_type", "")
    if not capability_type or not isinstance(capability_type, str) or not capability_type.strip():
        errors.append("capability_type is required and cannot be empty")

    # 5. risk_level harus salah satu dari: "Low", "Medium", "High", "Critical"
    risk_level = metadata.get("risk_level", "Low")
    if risk_level not in VALID_RISK_LEVELS:
        errors.append(
            f"risk_level must be one of {sorted(VALID_RISK_LEVELS)}, got '{risk_level}'"
        )

    # 6. permissions harus berupa list (boleh kosong)
    permissions = metadata.get("permissions", [])
    if isinstance(permissions, str):
        # If it's a comma-separated string, it will be parsed later
        pass
    elif isinstance(permissions, list):
        for p in permissions:
            if not isinstance(p, str):
                errors.append(f"permissions must be list of strings, got {type(p).__name__}")
    else:
        errors.append(f"permissions must be a list or comma-separated string, got {type(permissions).__name__}")

    # 7. dependencies harus berupa list (boleh kosong)
    dependencies = metadata.get("dependencies", [])
    if isinstance(dependencies, str):
        pass
    elif isinstance(dependencies, list):
        for d in dependencies:
            if not isinstance(d, str):
                errors.append(f"dependencies must be list of strings, got {type(d).__name__}")
    else:
        errors.append(f"dependencies must be a list or comma-separated string, got {type(dependencies).__name__}")

    # 8. tags harus berupa list (boleh kosong)
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        pass
    elif isinstance(tags, list):
        for t in tags:
            if not isinstance(t, str):
                errors.append(f"tags must be list of strings, got {type(t).__name__}")
    else:
        errors.append(f"tags must be a list or comma-separated string, got {type(tags).__name__}")

    # 9. description tidak boleh kosong
    description = metadata.get("description", "")
    if not description or not isinstance(description, str) or not description.strip():
        errors.append("description is required and cannot be empty")

    # 10. source_document existence is recommended but not required; log as warning if missing
    if source_document and not os.path.exists(source_document):
        logger.warning("source_document does not exist (recommended to include full path)", source_document=source_document)

    # 11. capability_id unik (tidak duplikat)
    if existing_ids and cap_id and cap_id in existing_ids:
        errors.append(f"duplicate capability_id: '{cap_id}' already registered")

    return errors


async def _try_import_implementation(implementation: str) -> Optional[str]:
    """Try to import the implementation class to verify it exists.
    
    Returns error message if import fails, None if successful.
    """
    try:
        module_path, class_name = implementation.rsplit(".", 1)
        module = importlib.import_module(module_path)
        getattr(module, class_name)
        logger.debug("Implementation class imported successfully", implementation=implementation)
        return None
    except ImportError as e:
        return f"Cannot import module for implementation '{implementation}': {e}"
    except AttributeError as e:
        return f"Class not found in module for implementation '{implementation}': {e}"
    except ValueError:
        return f"Invalid implementation format '{implementation}': must be 'module.ClassName'"
    except Exception as e:
        return f"Unexpected error importing '{implementation}': {e}"


def _parse_list_field(value: Any) -> List[str]:
    """Parse a field that can be either a comma-separated string or a list."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    elif isinstance(value, str) and value.strip():
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


async def validate_and_build_descriptor(
    metadata: Dict[str, Any],
    source_document: str,
    existing_ids: Optional[Set[str]] = None,
) -> CapabilityDescriptor:
    """Validate metadata and build a CapabilityDescriptor.

    Args:
        metadata: Dictionary of metadata from knowledge document
        source_document: Path to the source document
        existing_ids: Set of already-registered capability IDs

    Returns:
        Validated CapabilityDescriptor

    Raises:
        ValidationError: If validation fails
    """
    cap_id = metadata.get("capability_id", "")
    
    # First, validate basic metadata
    errors = validate_capability_metadata(metadata, source_document, existing_ids)
    
    # Then, try to import the implementation class
    implementation = metadata.get("implementation", "")
    if implementation:
        import_error = await _try_import_implementation(implementation)
        if import_error:
            errors.append(import_error)

    if errors:
        raise ValidationError(capability_id=cap_id, errors=errors)

    # Build descriptor from validated metadata
    cap_type = metadata.get("capability_type", "")
    version = str(metadata.get("version", "1.0.0"))
    risk_level = metadata.get("risk_level", "Low")
    permissions = _parse_list_field(metadata.get("permissions", []))
    dependencies = _parse_list_field(metadata.get("dependencies", []))
    tags = _parse_list_field(metadata.get("tags", []))
    description = metadata.get("description", "")

    # Build implementation path if not provided
    if not implementation:
        parts = cap_id.split(".")
        if len(parts) >= 2:
            module_name = parts[-1].replace("-", "_")
            class_parts = module_name.split("_")
            if class_parts and class_parts[-1].endswith("s"):
                class_parts[-1] = class_parts[-1][:-1]
            class_name = "".join(word.capitalize() for word in class_parts) + "Capability"
            implementation = f"sam.capabilities.{module_name}.{class_name}"
        else:
            implementation = f"sam.capabilities.{cap_id.replace('-', '_')}.{cap_id.split('.')[-1].replace('-', '_').capitalize()}Capability"

    return CapabilityDescriptor(
        id=cap_id,
        version=version,
        implementation=implementation,
        capability_type=cap_type,
        risk_level=risk_level,
        permissions=permissions,
        dependencies=dependencies,
        tags=tags,
        description=description,
        source_document=source_document,
        enabled=True,
    )