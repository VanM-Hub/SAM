"""Dashboard Provider Activation (Sprint 260).

Program C - Real Execution Runtime.
Read-only bridge: ringkasan aktivasi provider untuk dashboard.
"""
from __future__ import annotations
from typing import Dict, List

from ..providers.execution.provider_executor import ProviderExecutor, PROVIDER_ENV


class DashboardProviderActivation:
    """Bridge provider activation <-> dashboard. Read-only, no network."""

    def __init__(self, executor: ProviderExecutor | None = None) -> None:
        self._executor = executor or ProviderExecutor()

    def rows(self) -> List[dict]:
        out = []
        for pid in PROVIDER_ENV:
            cfg = self._executor.config(pid)
            out.append({"provider_id": pid,
                        "credentials": cfg.has_credentials(),
                        "requires_key": bool(cfg.api_key_env),
                        "external_calls": 0})
        return out

    def summary(self) -> Dict[str, object]:
        rows = self.rows()
        return {
            "total": len(rows),
            "credentials_ready": sum(1 for r in rows if r["credentials"]),
            "external_calls": 0,
        }
