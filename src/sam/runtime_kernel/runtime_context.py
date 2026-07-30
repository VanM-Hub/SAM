"""Runtime Context — frozen DTOs untuk konteks runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RuntimeContext:
    """Konteks runtime utama."""
    runtime_id: str
    name: str
    version: str
    description: str = ""


@dataclass(frozen=True)
class RuntimeIdentity:
    """Identitas runtime."""
    identity_id: str
    hostname: str
    instance_name: str
    instance_type: str = "development"
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeEnvironment:
    """Lingkungan runtime."""
    environment_id: str
    environment_type: str
    variables: Dict[str, str] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeProfile:
    """Profil runtime."""
    profile_id: str
    name: str
    mode: str = "normal"
    capabilities: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeConfiguration:
    """Konfigurasi runtime."""
    config_id: str
    settings: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    timeout_seconds: float = 30.0
