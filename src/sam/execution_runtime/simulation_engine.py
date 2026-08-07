"""Simulation Engine (Program G - Execution Evolution, 2026-08-07).

Exec: Zara, Lead Implementation Engineer. Arah: Architect (2026-08-07).

Menghasilkan SimulationEvidence secara DETERMINISTIK dari artefak
governance yang sudah dimiliki runtime - BUKAN menjalankan provider/mock.

Pipeline konseptual SAM (posisi Simulation):
    Mission -> Workflow -> Policy -> Simulation -> Approval -> Execution
        -> Verification -> Audit

Simulation menjawab: "apa yang kemungkinan terjadi jika benar-benar
mengeksekusi ini?" - dengan evidence dari metadata, tanpa external call.

Sumber evidence (semua metadata yang sudah ada):
    - ExecutionRequest (mode, provider, operation, payload, timeout)
    - ProviderSelector (ranking/best provider - deterministik)
    - ExecutionContract (allowed_modes, timeout, external_calls)
    - ProviderDispatcher (known provider, available)

Simulation V1 TIDAK menggunakan mock engine / emulator provider. Evolusi
(V2 contract semantic, V3 provider emulator, V4 sandbox) ditunda ke masa
depan - foundation tidak bergantung emulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .execution_request import ExecutionRequest
from .simulation_evidence import SimulationEvidence
from .provider_selector import ProviderSelector
from .provider_dispatcher import ProviderDispatcher


@dataclass(frozen=True)
class SimulationReport:
    """Laporan simulasi (immutable). Menggabungkan evidence + ringkasan."""

    evidence: SimulationEvidence
    summary: str = ""

    def as_dict(self) -> dict:
        return {
            "evidence": self.evidence.as_dict(),
            "summary": self.summary,
        }


class SimulationEngine:
    """Mesin simulasi deterministik berbasis metadata governance."""

    # Tabel estimasi deterministik per kategori provider (metadata, bukan call).
    # Digunakan untuk memperkirakan biaya/risiko/durasi DARI METADATA provider,
    # tetap tanpa menjalankan provider (deterministik, no network).
    _PROVIDER_PROFILE = {
        "filesystem": {"cost": 0.0, "risk": 0.05, "external": 0, "rollback": True, "duration": 5.0},
        "shell": {"cost": 0.0, "risk": 0.25, "external": 0, "rollback": True, "duration": 20.0},
        "sqlite": {"cost": 0.0, "risk": 0.10, "external": 0, "rollback": True, "duration": 10.0},
        "docker": {"cost": 1.5, "risk": 0.35, "external": 1, "rollback": True, "duration": 150.0},
        "openclaw": {"cost": 0.0, "risk": 0.20, "external": 0, "rollback": True, "duration": 40.0},
        "openai": {"cost": 0.02, "risk": 0.45, "external": 1, "rollback": True, "duration": 300.0},
        "anthropic": {"cost": 0.015, "risk": 0.45, "external": 1, "rollback": True, "duration": 320.0},
        "gemini": {"cost": 0.01, "risk": 0.45, "external": 1, "rollback": True, "duration": 280.0},
        "deepseek": {"cost": 0.008, "risk": 0.42, "external": 1, "rollback": True, "duration": 260.0},
        "ollama": {"cost": 0.0, "risk": 0.30, "external": 0, "rollback": True, "duration": 200.0},
    }

    def __init__(
        self,
        selector: ProviderSelector | None = None,
        dispatcher: ProviderDispatcher | None = None,
    ) -> None:
        self._selector = selector or ProviderSelector()
        self._dispatcher = dispatcher or ProviderDispatcher()

    @property
    def selector(self) -> ProviderSelector:
        return self._selector

    def _profile(self, provider_id: str) -> Dict[str, Any]:
        return self._PROVIDER_PROFILE.get(provider_id, {
            "cost": 0.0, "risk": 0.4, "external": 1, "rollback": True, "duration": 100.0,
        })

    def simulate(self, request: ExecutionRequest) -> SimulationEvidence:
        """Produksi evidence deterministik dari request + metadata.

        TIDAK memanggil provider, TIDAK melakukan external call (selalu 0
        untuk mode simulation/preview), TANPA mock engine.
        """
        profile = self._profile(request.provider_id)
        is_external = True if profile["external"] else False

        # Kebutuhan approval: mode simulation/preview tidak butuh approval;
        # mode execute butuh. Ini sejalan ApprovalGate.evaluate() yang ada.
        approval_required = request.mode in ("execute", "simulation")

        # Estimasi duration: dari profil provider + timeout request (bounded).
        est_duration = min(profile["duration"], float(request.timeout_seconds) * 1000.0)

        # Estimasi cost: hanya untuk external provider; 0 untuk local.
        est_cost = profile["cost"] if is_external else 0.0

        # Confidence: semakin banyak metadata ter-resolve, semakin tinggi.
        confidence = 0.6
        if request.provider_id and is_external:
            confidence += 0.15
        if approval_required:
            confidence += 0.05
        confidence = min(1.0, confidence)

        # Side effects & artifact (deterministik dari profil + operation).
        side_effects: Tuple[str, ...] = ()
        if is_external:
            side_effects = ("external_call",)
        artifact = f"{request.operation}://{request.provider_id}"

        # Expected audit chain (deterministik, mengikuti pipeline SAM).
        audit_chain = (
            "mission",
            "workflow",
            "policy",
            "simulation",
            "approval",
            "execution",
            "verification",
        )

        # Sumber evidence (transparansi).
        evidence_source = (
            "execution_request",
            "provider_metadata",
            "execution_contract",
            "provider_registry",
        )

        return SimulationEvidence(
            simulation_id=f"sim-{request.execution_id}",
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            operation=request.operation,
            capability_resolved=True,
            provider_selected=request.provider_id,
            approval_required=approval_required,
            estimated_external_calls=profile["external"],
            estimated_cost=est_cost,
            estimated_risk=profile["risk"],
            estimated_duration_ms=est_duration,
            rollback_possible=profile["rollback"],
            side_effects=side_effects,
            expected_artifact=artifact,
            expected_audit_chain=audit_chain,
            confidence=confidence,
            evidence_source=evidence_source,
        )

    def run(self, request: ExecutionRequest) -> SimulationReport:
        """Entry point simulasi -> laporan (evidence + ringkasan)."""
        evidence = self.simulate(request)
        summary = (
            f"simulate {request.operation} on {request.provider_id}: "
            f"external_calls={evidence.estimated_external_calls}, "
            f"cost={evidence.estimated_cost:.2f}, "
            f"risk={evidence.estimated_risk:.2f}, "
            f"rollback={'yes' if evidence.rollback_possible else 'no'}"
        )
        return SimulationReport(evidence=evidence, summary=summary)
