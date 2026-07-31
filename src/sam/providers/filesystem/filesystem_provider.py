"""Filesystem Provider — adapter filesystem (preview-only).

Sprint 145 — Filesystem Provider.
Membangun request, validasi, dan representasi aksi filesystem
TANPA eksekusi nyata. Support: read, write, copy, move, delete,
exists, list, mkdir, preview.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from ..base.base_provider import BaseProvider, ProviderError
from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability, ProviderOperation
from ..base.provider_contract import ProviderContract

FILESYSTEM_OPERATIONS = [
    "read", "write", "copy", "move", "delete",
    "exists", "list", "mkdir", "preview",
]


class FilesystemProvider(BaseProvider):
    """Provider filesystem — hanya preview, tidak pernah akses disk nyata."""

    descriptor = ProviderDescriptor(
        provider_id="filesystem",
        name="Filesystem Provider",
        provider_type="filesystem",
        version="1.0.0",
        description="Adapter preview untuk operasi filesystem",
        implements=["connector.contract.filesystem.v1"],
    )
    capabilities = [
        ProviderCapability(
            capability_id="fs.files",
            provider_id="filesystem",
            name="file_operations",
            category="filesystem",
            description="Operasi dasar file (preview)",
            operations=[ProviderOperation(op) for op in FILESYSTEM_OPERATIONS],
        ),
        ProviderCapability(
            capability_id="fs.dirs",
            provider_id="filesystem",
            name="directory_operations",
            category="filesystem",
            description="Operasi direktori (preview)",
            operations=[ProviderOperation("list"), ProviderOperation("mkdir")],
        ),
    ]
    contract = ProviderContract(
        contract_id="connector.contract.filesystem.v1",
        provider_id="filesystem",
        name="filesystem-contract",
        guarantees=["preview-only", "no-disk-access", "deterministic"],
        constraints=["no-execution"],
    )

    def preview_operation(self, operation: str, request: Dict[str, str]) -> Dict[str, object]:
        """Preview operasi filesystem. path wajib ada; eksekusi selalu 0."""
        if not self.supports(operation):
            raise ProviderError(
                f"filesystem provider does not support {operation}"
            )
        path = request.get("path", "")
        if not path:
            raise ProviderError("filesystem preview requires 'path'")
        return {
            "provider": "filesystem",
            "operation": operation,
            "path": path,
            "preview": True,
            "external_calls": 0,
            "dry_run": True,
        }
