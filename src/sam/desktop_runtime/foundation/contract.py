"""Sprint 272 - Desktop Runtime Foundation: contract (kontrak tanpa IO)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DesktopContract:
    """Kontrak aplikasi: composition-only, deterministik, tanpa eksekusi nyata."""

    preview_only: bool = True
    deterministic: bool = True
    synchronous: bool = True
    composition_only: bool = True
    execute_self: bool = False
    inference: bool = False
    llm: bool = False
    external_calls: int = 0
    forbidden: Tuple[str, ...] = (
        "async",
        "thread",
        "multiprocessing",
        "socket",
        "requests",
        "httpx",
        "subprocess",
    )

    def as_dict(self) -> dict:
        return {
            "preview_only": self.preview_only,
            "deterministic": self.deterministic,
            "synchronous": self.synchronous,
            "composition_only": self.composition_only,
            "execute_self": self.execute_self,
            "inference": self.inference,
            "llm": self.llm,
            "external_calls": self.external_calls,
            "forbidden": list(self.forbidden),
        }
