"""Runtime Status — DTO status connector runtime.

Sprint 121 — Connector Runtime.
Status agregat runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class RuntimeStatus:
    """Status connector runtime."""
    ready: bool = False
    phase: str = "boot"
    connectors_registered: int = 0
    message: str = ""
