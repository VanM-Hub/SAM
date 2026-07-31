"""Docker Provider — adapter Docker (preview-only).

Sprint 148 — Docker Provider.
Membangun request container/image/compose dan preview. Tidak eksekusi docker.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from ..base.base_provider import BaseProvider, ProviderError
from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability, ProviderOperation
from ..base.provider_contract import ProviderContract


class DockerProvider(BaseProvider):
    """Provider Docker — hanya build & preview request, tidak pernah jalankan docker."""

    descriptor = ProviderDescriptor(
        provider_id="docker",
        name="Docker Provider",
        provider_type="docker",
        version="1.0.0",
        description="Adapter preview untuk container, image, dan compose",
        implements=["connector.contract.docker.v1"],
    )
    capabilities = [
        ProviderCapability(
            capability_id="docker.container",
            provider_id="docker",
            name="container_operations",
            category="docker",
            description="Membangun request container (preview)",
            operations=[
                ProviderOperation("container_create"),
                ProviderOperation("container_start"),
                ProviderOperation("container_stop"),
                ProviderOperation("container_remove"),
                ProviderOperation("preview"),
            ],
        ),
        ProviderCapability(
            capability_id="docker.image",
            provider_id="docker",
            name="image_operations",
            category="docker",
            description="Membangun request image (preview)",
            operations=[
                ProviderOperation("image_pull"),
                ProviderOperation("image_build"),
                ProviderOperation("image_remove"),
            ],
        ),
        ProviderCapability(
            capability_id="docker.compose",
            provider_id="docker",
            name="compose_operations",
            category="docker",
            description="Membangun request compose (preview)",
            operations=[
                ProviderOperation("compose_up"),
                ProviderOperation("compose_down"),
            ],
        ),
    ]
    contract = ProviderContract(
        contract_id="connector.contract.docker.v1",
        provider_id="docker",
        name="docker-contract",
        guarantees=["build-only", "no-engine", "deterministic"],
        constraints=["no-docker-execution"],
    )

    def plan(self, kind: str, name: str) -> Dict[str, object]:
        """Bangun rencana operasi docker (preview). Tidak menjalankan apa pun."""
        if kind not in {"container", "image", "compose"}:
            raise ProviderError(f"docker kind {kind} unsupported")
        if not name:
            raise ProviderError("docker plan requires a name")
        return {
            "provider": "docker",
            "kind": kind,
            "name": name,
            "preview": True,
            "external_calls": 0,
            "engine_contacted": False,
        }
