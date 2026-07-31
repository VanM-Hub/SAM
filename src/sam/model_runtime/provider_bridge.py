"""Provider Bridge — bridge model <-> provider (read-only) (Sprint 249).

Program B — Model Runtime Integration.
Read-only bridge ke Provider (Program A); tidak ada panggilan provider nyata.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderBridgeView:
    """View read-only provider (immutable)."""
    provider: str
    selected_model: str = ""
    mode: str = "preview"
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "selected_model": self.selected_model,
            "mode": self.mode,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ProviderBridge:
    """Bridge model <-> provider. Read-only, tidak memanggil provider."""

    KNOWN = ("openai", "anthropic", "gemini", "deepseek", "ollama")

    def view(self, provider: str, selected_model: str = "") -> ProviderBridgeView:
        safe = provider if provider in self.KNOWN else "openai"
        return ProviderBridgeView(
            provider=safe,
            selected_model=selected_model,
            mode="preview",
            preview_only=True,
            external_calls=0,
        )
