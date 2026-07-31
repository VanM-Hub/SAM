"""OpenClaw Provider — adapter OpenClaw (preview-only).

Sprint 149 — OpenClaw Provider.
Membangun request tool dan preview. Tidak invoke tool apa pun.
Catatan: ini ADAPTER provider; subsystem src/sam/openclaw/ tidak disentuh.
"""
from __future__ import annotations
from typing import Dict, List

from ..base.base_provider import BaseProvider, ProviderError
from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability, ProviderOperation
from ..base.provider_contract import ProviderContract


class OpenClawProvider(BaseProvider):
    """Provider OpenClaw — hanya build & preview request tool, tidak pernah invoke."""

    descriptor = ProviderDescriptor(
        provider_id="openclaw",
        name="OpenClaw Provider",
        provider_type="openclaw",
        version="1.0.0",
        description="Adapter preview untuk tool OpenClaw",
        implements=["connector.contract.openclaw.v1"],
    )
    capabilities = [
        ProviderCapability(
            capability_id="openclaw.tools",
            provider_id="openclaw",
            name="tool_build",
            category="openclaw",
            description="Membangun dan preview request tool tanpa invoke",
            operations=[
                ProviderOperation("tool_build"),
                ProviderOperation("tool_preview"),
                ProviderOperation("tool_validate"),
            ],
        ),
    ]
    contract = ProviderContract(
        contract_id="connector.contract.openclaw.v1",
        provider_id="openclaw",
        name="openclaw-contract",
        guarantees=["build-only", "no-invoke", "deterministic"],
        constraints=["no-tool-execution"],
    )

    def build_tool(self, tool: str, arguments: Dict[str, object] = None) -> Dict[str, object]:
        """Bangun representasi request tool (preview). Tidak memanggil tool."""
        if not tool:
            raise ProviderError("openclaw build requires a tool name")
        args = arguments or {}
        return {
            "provider": "openclaw",
            "tool": tool,
            "arguments": dict(args),
            "preview": True,
            "external_calls": 0,
            "invoked": False,
        }
