"""Model Request — request generik model (Sprint 240).

Program B — Model Runtime Integration.
Generik, tidak mengenal provider. Immutable, preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from .model_context import ModelContext
from .model_parameters import ModelParameters


@dataclass(frozen=True)
class ModelRequest:
    """Request generik model (immutable). Tidak mengenal provider."""
    request_id: str
    task: str = "chat"  # chat | embedding | reasoning | vision | tool
    context: ModelContext = field(default_factory=ModelContext)
    parameters: ModelParameters = field(default_factory=ModelParameters)
    model_type: str = "chat"
    mode: str = "preview"  # preview | approval | execute
    external_calls: int = 0  # selalu 0 di preview

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "task": self.task,
            "context": self.context.as_dict(),
            "parameters": self.parameters.as_dict(),
            "model_type": self.model_type,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
