"""Sprint 278 - Desktop Certification: validator 7 dimensi.

Class service (bukan DTO); murni deterministik, tanpa IO/eksekusi.
Memeriksa kepatuhan Desktop Runtime terhadap hard rules Program F.
"""
from __future__ import annotations

from typing import List

from ..conversation.bridge import ConversationBridge
from ..dashboard_bridge.bridge import DashboardBridge
from ..foundation import DesktopContract
from ..runtime.desktop_runtime import DesktopRuntime
from .certification_dimension import CertificationDimension


class DesktopCertifier:
    """Validator 7 dimensi kepatuhan Desktop Runtime."""

    @staticmethod
    def _composition(contract: DesktopContract) -> bool:
        return contract.composition_only

    @staticmethod
    def _preview_only(contract: DesktopContract) -> bool:
        return contract.preview_only and contract.external_calls == 0

    @staticmethod
    def _deterministic(contract: DesktopContract) -> bool:
        return contract.deterministic and contract.synchronous

    @staticmethod
    def _no_execute(runtime: DesktopRuntime) -> bool:
        return runtime.contract.execute_self is False and runtime is not None

    @staticmethod
    def _immutable(runtime: DesktopRuntime) -> bool:
        try:
            runtime.snapshot_summary()
        except Exception:
            return False
        return True

    @staticmethod
    def _readonly_bridges(
        conversation: ConversationBridge,
        dashboard: DashboardBridge,
    ) -> bool:
        return conversation.read_only() and dashboard.read_only()

    @staticmethod
    def _no_llm(contract: DesktopContract) -> bool:
        return contract.inference is False and contract.llm is False

    @staticmethod
    def validate_desktop(
        runtime: DesktopRuntime,
        contract: DesktopContract,
        conversation: ConversationBridge,
        dashboard: DashboardBridge,
    ) -> List:
        dimensions = [
            CertificationDimension(
                "composition_only",
                DesktopCertifier._composition(contract),
            ),
            CertificationDimension(
                "preview_only",
                DesktopCertifier._preview_only(contract),
            ),
            CertificationDimension(
                "deterministic_sync",
                DesktopCertifier._deterministic(contract),
            ),
            CertificationDimension(
                "no_execute_self",
                DesktopCertifier._no_execute(runtime),
            ),
            CertificationDimension(
                "immutable_dto",
                DesktopCertifier._immutable(runtime),
            ),
            CertificationDimension(
                "readonly_bridges",
                DesktopCertifier._readonly_bridges(conversation, dashboard),
            ),
            CertificationDimension(
                "no_llm_inference",
                DesktopCertifier._no_llm(contract),
            ),
        ]
        return dimensions

    @staticmethod
    def all_passed(dimensions: List) -> bool:
        return all(d.passed for d in dimensions)
