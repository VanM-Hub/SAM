"""Runtime Registry — frozen DTOs registri subsystem."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RegistryEntry:
    entry_id: str
    subsystem_name: str
    version: str
    status: str = "registered"
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CatalogEntry:
    catalog_id: str
    name: str
    category: str
    description: str = ""
    entry_count: int = 0


@dataclass(frozen=True)
class LocatorResult:
    locator_id: str
    target: str
    found: bool = False
    entries: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeDescriptor:
    descriptor_id: str
    subsystem: str
    runtime_type: str
    capabilities: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeManifest:
    manifest_id: str
    runtime_name: str
    version: str
    dependencies: Dict[str, str] = field(default_factory=dict)
