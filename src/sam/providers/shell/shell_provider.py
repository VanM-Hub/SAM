"""Shell Provider — adapter shell (preview-only).

Sprint 146 — Shell Provider.
Membangun command dan preview. Belum execute. Hanya build command.
"""
from __future__ import annotations
from typing import Dict, List

from ..base.base_provider import BaseProvider, ProviderError
from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability, ProviderOperation
from ..base.provider_contract import ProviderContract


class ShellProvider(BaseProvider):
    """Provider shell — hanya build & preview command, tidak pernah execute."""

    descriptor = ProviderDescriptor(
        provider_id="shell",
        name="Shell Provider",
        provider_type="shell",
        version="1.0.0",
        description="Adapter preview untuk perintah shell",
        implements=["connector.contract.shell.v1"],
    )
    capabilities = [
        ProviderCapability(
            capability_id="shell.commands",
            provider_id="shell",
            name="command_build",
            category="shell",
            description="Membangun dan preview command tanpa eksekusi",
            operations=[ProviderOperation("build"), ProviderOperation("preview")],
        ),
    ]
    contract = ProviderContract(
        contract_id="connector.contract.shell.v1",
        provider_id="shell",
        name="shell-contract",
        guarantees=["build-only", "no-execution", "deterministic"],
        constraints=["no-subprocess"],
    )

    def build_command(self, command: str, args: List[str] = None) -> Dict[str, object]:
        """Bangun representasi command (preview). Tidak menjalankan apa pun."""
        args = args or []
        if not command:
            raise ProviderError("shell build requires a command")
        return {
            "provider": "shell",
            "command": command,
            "args": list(args),
            "preview": True,
            "external_calls": 0,
            "executed": False,
        }
