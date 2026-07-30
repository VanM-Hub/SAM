"""Runtime Adapter — DTOs bridge antar subsystem."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SubsystemAdapter:
    adapter_id: str
    subsystem_name: str
    source_format: str = ""
    target_format: str = ""
    mappings: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BridgeRoute:
    route_id: str
    source: str = ""
    target: str = ""
    active: bool = True


@dataclass(frozen=True)
class TransformRule:
    rule_id: str
    source_field: str = ""
    target_field: str = ""
    transform_type: str = "direct"


@dataclass(frozen=True)
class ProtocolMap:
    map_id: str
    protocol: str = "internal"
    subsystem: str = ""
    version: str = "1.0"


@dataclass(frozen=True)
class InteropResult:
    result_id: str
    compatible: bool = False
    messages: List[str] = field(default_factory=list)
