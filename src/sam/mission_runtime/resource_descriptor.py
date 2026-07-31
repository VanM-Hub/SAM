# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: resource_descriptor.

Describes a resource available to a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceDescriptor:
    """Immutable description of a resource."""

    resource_id: str
    name: str = ""
    available: bool = True
    capacity: int = 0
