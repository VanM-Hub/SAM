"""SQLite Provider — adapter SQLite (preview-only).

Sprint 147 — SQLite Provider.
Membangun query dan preview. Belum connect database nyata.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from ..base.base_provider import BaseProvider, ProviderError
from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability, ProviderOperation
from ..base.provider_contract import ProviderContract


class SQLiteProvider(BaseProvider):
    """Provider SQLite — hanya build & preview query, tidak pernah konek DB."""

    descriptor = ProviderDescriptor(
        provider_id="sqlite",
        name="SQLite Provider",
        provider_type="sqlite",
        version="1.0.0",
        description="Adapter preview untuk query SQLite",
        implements=["connector.contract.sqlite.v1"],
    )
    capabilities = [
        ProviderCapability(
            capability_id="sqlite.queries",
            provider_id="sqlite",
            name="query_build",
            category="sqlite",
            description="Membangun dan preview query tanpa koneksi database",
            operations=[
                ProviderOperation("prepare"),
                ProviderOperation("preview"),
                ProviderOperation("validate"),
            ],
        ),
    ]
    contract = ProviderContract(
        contract_id="connector.contract.sqlite.v1",
        provider_id="sqlite",
        name="sqlite-contract",
        guarantees=["build-only", "no-connection", "deterministic"],
        constraints=["no-database-access"],
    )

    def prepare_query(self, query: str, table: str = "") -> Dict[str, object]:
        """Bangun representasi query (preview). Tidak menjalankan query."""
        if not query:
            raise ProviderError("sqlite prepare requires a query")
        return {
            "provider": "sqlite",
            "query": query,
            "table": table,
            "preview": True,
            "external_calls": 0,
            "connected": False,
        }
