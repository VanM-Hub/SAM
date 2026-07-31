"""Artifact — representasi canonical keluaran pipeline (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class Artifact:
    """Bentuk canonical hasil pipeline. Immutable, no storage, no publish."""
    name: str
    kind: str
    content: str = ""
    immutable: bool = True
    no_storage: bool = True
    no_publish: bool = True
    tags: Tuple[str, ...] = ()
