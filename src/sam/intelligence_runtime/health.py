"""Sprint 266 - Monitoring: health (status kesehatan runtime)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RuntimeHealth:
    """Status kesehatan aplikasi (deterministik, tanpa IO)."""

    healthy: bool = True
    message: str = "ok"

    def as_dict(self) -> Dict[str, object]:
        return {"healthy": self.healthy, "message": self.message}
