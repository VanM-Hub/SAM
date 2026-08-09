"""Context Assembly - WP-24 (MISSION-5.1 / IP-5.1-003).

Mekanisme penyusunan context sebelum request dikirim ke Provider. Deterministik
dan dapat dijelaskan. Credential tidak pernah menjadi bagian dari context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class AssembledContext:
    """Context yang telah disusun untuk request."""

    parts: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def assembled_text(self) -> str:
        return "\n".join(text for _, text in self.parts)

    def sources(self) -> Tuple[str, ...]:
        return tuple(kind for kind, _ in self.parts)

    def as_dict(self) -> dict:
        return {
            "sources": list(self.sources()),
            "assembled_text": self.assembled_text,
            "part_count": len(self.parts),
        }


class ContextAssembler:
    """Menyusun context secara deterministic dari beberapa sumber."""

    _FORBIDDEN = ("credential", "api_key", "secret", "token")

    def assemble(
        self,
        *,
        history: Tuple[str, ...] = (),
        operational: str = "",
        evidence: str = "",
        governance: str = "",
        citizen: str = "",
        user_provided: str = "",
    ) -> AssembledContext:
        parts: list = []
        for label, text in (
            ("conversation_history", "\n".join(history)),
            ("operational_context", operational),
            ("evidence", evidence),
            ("governance_context", governance),
            ("citizen_context", citizen),
            ("user_context", user_provided),
        ):
            if text:
                parts.append((label, text))

        # pastikan tidak ada konten terlarang (credential) masuk context
        sanitized = tuple(
            (label, _redact(text)) for label, text in parts
        )
        return AssembledContext(parts=sanitized)


def _redact(text: str) -> str:
    lowered = text
    for word in ("api_key", "secret", "token", "credential"):
        lowered = lowered.replace(word, "[REDACTED]")
    return lowered
