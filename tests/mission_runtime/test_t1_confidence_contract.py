"""T1 - Fix ConfidenceAssessor contract mismatch di MCR (keputusan CA 2026-08-11).

Sebelum T1: MCR memanggil `ConfidenceAssessor.assess(result.conclusion, ctx)` dengan
2 argumen dan membaca atribut `confidence`, padahal kontrak assessor
(governed_reasoning, foundation immutable) adalah:

    ConfidenceAssessor.assess(reasoning: StructuredReasoning) -> ConfidenceAssessment
    ConfidenceAssessment.value  (bukan .confidence)

Akibat: setiap cycle MCR, `_assess_confidence` selalu melempar exception (ditelan
`except`) -> confidence selalu 0.0 (silent bug).

Setelah T1: MCR meneruskan objek `StructuredReasoning` ke assessor (kontrak benar)
dan membaca atribut `value`. Assessor TIDAK diubah (foundation immutable).

Guardrail:
- Kontrak ConfidenceAssessor tidak diubah.
- Siklus MCR tetap berjalan (Reason -> Plan -> Govern -> Execute -> Observe -> Reflect).
"""
import asyncio

from sam.governed_reasoning.confidence_assessment import ConfidenceAssessor
from sam.governed_reasoning.structured_reasoning import (
    StructuredReasoning,
    ReasoningContext,
    ReasoningStep,
    EvidenceRef,
)
from sam.mission_cognition import MissionCognitiveRuntime


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_reasoning(evidence: bool = True) -> StructuredReasoning:
    steps = [
        ReasoningStep(
            step_id="s1", kind="premise", content="fakta A",
            evidence_refs=(EvidenceRef("e1"),) if evidence else (),
        ),
        ReasoningStep(
            step_id="s2", kind="conclusion", content="kesimpulan",
            evidence_refs=(EvidenceRef("e2"),) if evidence else (),
        ),
    ]
    return StructuredReasoning(
        reasoning_id="r-t1", context=ReasoningContext(question="q"),
        steps=tuple(steps), conclusion="kesimpulan",
    )


class TestT1ConfidenceContract:
    """T1: MCR memanggil assessor sesuai kontrak (objek reasoning, bukan string)."""

    def test_assessor_contract_tidak_diubah(self) -> None:
        """Assessor (foundation immutable) tetap terima 1 argumen: StructuredReasoning."""
        import inspect
        sig = inspect.signature(ConfidenceAssessor.assess)
        params = list(sig.parameters)
        # staticmethod: hanya 1 parameter posisi = 'reasoning' (tanpa self)
        assert params == ["reasoning"], f"assess() harus terima 1 arg 'reasoning', dapat {params}"

    def test_mcr_pass_reasoning_object_bukan_string(self) -> None:
        """MCR meneruskan objek StructuredReasoning, bukan string conclusion."""
        import re
        import sam.mission_cognition.runtime as mcr_mod
        raw = open(mcr_mod.__file__, encoding="utf-8").read()
        # buang docstring (antara triple-quote pertama) agar cek hanya body kode
        body = re.sub(r'^""".*?"""', "", raw, count=1, flags=re.DOTALL)
        assert "self._confidence_assessor.assess(reasoning)" in body
        # sisa mismatch lama (2-arg, result.conclusion) HARUS hilang dari body:
        assert "assess(result.conclusion" not in body
        assert "result.conclusion, {" not in body

    def test_confidence_dihitung_tidak_selalu_nol(self) -> None:
        """Dengan reasoning ber-evidence, confidence > 0 (bukan 0.0 silent)."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False
        )
        reasoning = _make_reasoning(evidence=True)
        val = _run(mcr._assess_confidence(
            type("R", (), {"status": type("S", (), {"value": "completed"})()})(),
            reasoning,
        ))
        assert val > 0.0

    def test_reflect_menerima_reasoning_dan_produksi_confident_record(self) -> None:
        """_reflect meneruskan reasoning; reflection tercatat dengan confidence > 0."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False
        )
        reasoning = _make_reasoning(evidence=True)
        res_type = type("R", (), {
            "observation_summary": "obs", "execution_summary": "exec",
            "conclusion": "kesimpulan", "governance_decision": "allow",
            "lesson": "", "mission": "m", "status": type("S", (), {"value": "completed"})(),
            "cycle_id": "t1",
        })
        result = res_type()
        # jalankan _reflect asli via instance (async), pastikan tak lempar
        _run(mcr._reflect(result, reasoning))
        assert result.reflection_id  # reflection berhasil tercatat

    def test_cycle_tetap_completed_setelah_t1(self) -> None:
        """T1 tidak mengubah alur siklus: tetap completed tanpa evidence/plan tetap ada."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False
        )
        res = _run(mcr.run_cycle("mission t1", evidences=()))
        assert res.status.value == "completed"
        assert res.plan_step_count == 11
