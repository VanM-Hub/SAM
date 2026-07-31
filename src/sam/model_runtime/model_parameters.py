"""Model Parameters — parameter generik model (Sprint 240).

Program B — Model Runtime Integration.
Generik, tidak mengenal provider. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ModelParameters:
    """Parameter generik model (immutable). Tidak mengenal provider."""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: tuple = ()
    seed: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": list(self.stop),
            "seed": self.seed,
            "extra": dict(self.extra),
        }

    def merged(self, **overrides: Any) -> "ModelParameters":
        """Return parameter baru dengan override. Immutable (tidak mutasi)."""
        extra = dict(self.extra)
        for k, v in overrides.items():
            if k in ("temperature", "max_tokens", "top_p", "seed"):
                pass  # handled below
            else:
                extra[k] = v
        return ModelParameters(
            temperature=overrides.get("temperature", self.temperature),
            max_tokens=overrides.get("max_tokens", self.max_tokens),
            top_p=overrides.get("top_p", self.top_p),
            stop=self.stop,
            seed=overrides.get("seed", self.seed),
            extra=extra,
        )
