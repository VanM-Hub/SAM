"""
Plugin Manifest Models for SAM Framework.

Defines the contract between SAM runtime and external plugins.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
import uuid


class PluginStatus(str, Enum):
    """Plugin lifecycle status."""
    INSTALLED = "installed"
    VALIDATED = "validated"
    REGISTERED = "registered"
    ENABLED = "enabled"
    INITIALIZED = "initialized"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    UNINSTALLED = "uninstalled"


class PluginPermission(str, Enum):
    """Plugin permissions."""
    # Filesystem permissions
    READ_WORKSPACE = "read:workspace"
    WRITE_WORKSPACE = "write:workspace"
    READ_PLUGIN_DATA = "read:plugin_data"
    WRITE_PLUGIN_DATA = "write:plugin_data"
    READ_TEMP = "read:temp"
    WRITE_TEMP = "write:temp"

    # Network permissions
    NETWORK_OUTBOUND = "network:outbound"
    NETWORK_INBOUND = "network:inbound"

    # Runtime permissions
    READ_CONFIGURATION = "read:configuration"
    READ_EVIDENCE = "read:evidence"
    WRITE_EVIDENCE = "write:evidence"
    READ_KNOWLEDGE = "read:knowledge"
    WRITE_KNOWLEDGE = "write:knowledge"
    PUBLISH_EVENT = "publish:event"
    READ_AUDIT = "read:audit"


class PluginManifest(BaseModel):
    """
    Plugin Manifest – the contract between plugin and SAM Runtime.

    This defines what the plugin is, what it can do, and what it needs.
    """

    # Identity
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique plugin identifier"
    )
    name: str = Field(..., description="Plugin name", min_length=1)
    version: str = Field(..., description="Semantic version (e.g., 1.0.0)")
    author: str = Field(..., description="Plugin author or organization")
    license: Optional[str] = Field(None, description="License identifier (e.g., MIT, Apache-2.0)")
    description: Optional[str] = Field(None, description="Plugin description")
    status: str = Field(default="installed", description="Plugin lifecycle status")

    # Entrypoint
    entrypoint: str = Field(
        ...,
        description="Python module path (e.g., sam.plugins.nvidia.main)"
    )

    # Capabilities
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of capability IDs provided by this plugin"
    )

    # Dependencies
    dependencies: List[Union[str, Dict[str, str]]] = Field(
        default_factory=list,
        description="List of plugin IDs or capability IDs this plugin depends on. Each item may be a string 'id' or 'id@constraint' or a dict {id:..., version:...}"
    )

    # Permissions
    permissions: List[PluginPermission] = Field(
        default_factory=list,
        description="Permissions required by this plugin"
    )

    # Network allowlist (if network permission is granted)
    network_allowlist: List[str] = Field(
        default_factory=list,
        description="Allowed domains/IPs for outbound connections (e.g., api.openai.com)"
    )

    # Filesystem paths (relative to plugin workspace)
    filesystem_paths: Dict[str, str] = Field(
        default_factory=dict,
        description="Filesystem paths the plugin needs (e.g., {'data': './data', 'cache': './cache'})"
    )

    # Configuration schema (optional)
    config_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema for plugin configuration"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional plugin metadata"
    )

    # Lifecycle hooks (optional)
    lifecycle_hooks: Dict[str, str] = Field(
        default_factory=dict,
        description="Lifecycle hook entrypoints (e.g., {'initialize': 'initialize', 'shutdown': 'shutdown'})"
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError(f"Version must follow SemVer format (e.g., 1.0.0), got: {v}")
        return v

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """Ensure capabilities are unique."""
        if len(set(v)) != len(v):
            raise ValueError("Capabilities must be unique")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: List[Union[str, Dict[str, str]]]) -> List[Union[str, Dict[str, str]]]:
        """Ensure dependencies are unique by id/string."""
        seen = set()
        for item in v:
            if isinstance(item, dict):
                dep_id = item.get("id")
                if not dep_id:
                    raise ValueError("Dependency dict must contain 'id'")
                key = dep_id
            else:
                # string form
                key = str(item)
            if key in seen:
                raise ValueError("Dependencies must be unique")
            seen.add(key)
        return v

