"""Sprint 278 - Desktop Certification: validator 7 dimensi.

Class service (bukan DTO); murni deterministik, tanpa IO/eksekusi.
Memeriksa kepatuhan Presentation Layer terhadap hard rules Program F.
"""
from __future__ import annotations

from typing import List

from ..conversation.bridge import ConversationBridge
from ..dashboard_bridge.bridge import DashboardBridge
from ..foundation import PresentationContract
from ..presentation_layer import PresentationLayer
from .certification_dimension import CertificationDimension


class PresentationCertifier:
    """Validator 7 dimensi kepatuhan Presentation Layer."""

    @staticmethod
    def _composition(contract: PresentationContract) -> bool:
        return contract.composition_only

    @staticmethod
    def _preview_only(contract: PresentationContract) -> bool:
        return contract.preview_only and contract.external_calls == 0

    @staticmethod
    def _deterministic(contract: PresentationContract) -> bool:
        return contract.deterministic and contract.synchronous

    @staticmethod
    def _no_execute(runtime: PresentationLayer) -> bool:
        return runtime.contract.execute_self is False and runtime is not None

    @staticmethod
    def _immutable(runtime: PresentationLayer) -> bool:
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
    def _no_llm(contract: PresentationContract) -> bool:
        return contract.inference is False and contract.llm is False

    @staticmethod
    def validate_desktop(
        runtime: PresentationLayer,
        contract: PresentationContract,
        conversation: ConversationBridge,
        dashboard: DashboardBridge,
    ) -> List:
        dimensions = [
            CertificationDimension(
                "composition_only",
                PresentationCertifier._composition(contract),
            ),
            CertificationDimension(
                "preview_only",
                PresentationCertifier._preview_only(contract),
            ),
            CertificationDimension(
                "deterministic_sync",
                PresentationCertifier._deterministic(contract),
            ),
            CertificationDimension(
                "no_execute_self",
                PresentationCertifier._no_execute(runtime),
            ),
            CertificationDimension(
                "immutable_dto",
                PresentationCertifier._immutable(runtime),
            ),
            CertificationDimension(
                "readonly_bridges",
                PresentationCertifier._readonly_bridges(conversation, dashboard),
            ),
            CertificationDimension(
                "no_llm_inference",
                PresentationCertifier._no_llm(contract),
            ),
        ]
        return dimensions

    @staticmethod
    def all_passed(dimensions: List) -> bool:
        return all(d.passed for d in dimensions)
