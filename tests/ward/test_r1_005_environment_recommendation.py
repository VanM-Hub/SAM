"""R1-005 — Canonical Environment Recommendation Boundary (recommendation).

Unit + integrasi ringan utk EnvironmentRecommendationAdapter (read-only),
kontrak RecommendationTarget/RecommendationResult, runner dispatcher
environment.recommend, recognizer "rekomendasi/sarankan", cache canonical
DiagnosisResult, dan fail-closed (insufficient/candidate/causal-no-mapping).
REAL E2E ada di proof R1-005.

Prinsip semantic (Van R1-005 rev.2, dikunci 2026-08-16):
  - MURNI read-only. BUKAN recovery engine/approval/execution. STOP di Recommendation.
  - Menerima DiagnosisResult (R1-004) - BUKAN findings mentah, BUKAN Dict.
  - Action mutation HANYA bila canonical action mapping TERBUKTI (injected/
    declared di sumber canonical auditable). TIDAK ada _derive_action/
    keyword heuristic (disk->cleanup, process->restore).
  - insufficient/candidate/causal-no-mapping -> recommendations=[] fail-closed.
  - diagnosis_ref = reference hasil diagnosis, BUKAN salinan evidence.
"""
import unittest

from sam.ward.capability.contracts import (
    SubjectRef, DiagnosisResult, RecommendationResult, Finding,
)
from sam.ward.adapters.environment_recommendation import (
    EnvironmentRecommendationAdapter,
)


def _subject():
    return SubjectRef(subject_id="local-machine", subject_type="citizen",
                      kind="environment", name="local-machine")


def _diag(verdict, findings):
    return DiagnosisResult(
        subject=_subject(),
        verdict=verdict,
        diagnosis=findings,
        confidence=0.9,
        evidence_ref="diagnosis evidence sources=disk_space; n=1",
        summary=f"verdict {verdict}",
        error="",
    )


def _finding(label, confidence=0.9):
    return Finding(
        finding_id=f"diag-{label}",
        subject_id="local-machine",
        label=label,
        evidence={"source": "disk_space", "causal": True},
        confidence=confidence,
    )


class RecommendationAdapterTest(unittest.TestCase):
    """Adapter read-only; verdict fail-closed; action hanya via canonical mapping."""

    def test_insufficient_yields_empty(self):
        res = EnvironmentRecommendationAdapter(_subject()).recommend(
            diagnosis=_diag("insufficient", []))
        self.assertEqual(res.recommendations, [])
        self.assertIsInstance(res, RecommendationResult)
        self.assertIn("insufficient", res.summary.lower())

    def test_candidate_yields_no_mutation(self):
        # candidate -> TIDAK mutation, walaupun ada canonical mapping diject.
        adapter = EnvironmentRecommendationAdapter(
            _subject(), canonical_action_map={"disk hampir penuh": "cleanup"})
        res = adapter.recommend(diagnosis=_diag("candidate", [
            _finding("disk hampir penuh")]))
        self.assertEqual(res.recommendations, [])
        self.assertIn("candidate", res.summary.lower())

    def test_causal_without_mapping_yields_empty(self):
        # verdict causal, TETAPI tidak ada canonical action mapping -> [] jujur.
        adapter = EnvironmentRecommendationAdapter(_subject())  # mapping ABSENT
        res = adapter.recommend(diagnosis=_diag("causal", [
            _finding("disk hampir penuh")]))
        self.assertEqual(res.recommendations, [])
        # summary jujur: TIDAK mengarang restore/cleanup.
        self.assertIn("belum ada", res.summary.lower())
        self.assertIn("R1-006", res.summary)

    def test_causal_with_mapping_yields_recommendation(self):
        # mapping canonical TERBUKTI (dideklarasikan) -> action abstract dari mapping.
        adapter = EnvironmentRecommendationAdapter(
            _subject(), canonical_action_map={"disk hampir penuh": "cleanup"})
        res = adapter.recommend(diagnosis=_diag("causal", [
            _finding("disk hampir penuh")]))
        self.assertEqual(len(res.recommendations), 1)
        r = res.recommendations[0]
        self.assertEqual(r.action, "cleanup")          # abstract dari mapping
        self.assertEqual(r.target, "disk hampir penuh")
        self.assertTrue(r.approval_required)
        # rationale berbasis lineage (finding + diagnosis_ref), bukan asumsi AI.
        self.assertIn("diagnosis_ref", r.rationale)

    def test_causal_unmapped_finding_ignored_not_derived(self):
        # finding causal yang TIDAK termapping TIDAK dikonversi heuristic.
        adapter = EnvironmentRecommendationAdapter(
            _subject(), canonical_action_map={})  # kosong
        res = adapter.recommend(diagnosis=_diag("causal", [
            _finding("proses X mati"),
            _finding("disk hampir penuh")]))
        self.assertEqual(res.recommendations, [])

    def test_no_derive_action_helper(self):
        """Adapter TIDAK mendefinisikan helper `_derive_action` / heuristic."""
        import inspect
        from sam.ward.adapters import environment_recommendation as mod
        src = inspect.getsource(mod)
        # Tidak ada FUNGSI helper `def _derive_action` (penyebutan di komentar
        # utk menjelaslarang boleh ada; yang dilarang = implementasi mapping).
        self.assertNotIn("def _derive_action", src)


class RecommendationContractTest(unittest.TestCase):
    def test_contracts_exist(self):
        import dataclasses
        fields = {f.name for f in dataclasses.fields(RecommendationResult)}
        self.assertTrue({"subject", "diagnosis_ref", "recommendations",
                         "summary", "error"} <= fields)
        # RecommendationTarget adalah Protocol; adapter punya recommend.
        self.assertTrue(callable(getattr(EnvironmentRecommendationAdapter, "recommend", None)))

    def test_input_is_diagnosisresult_not_findings(self):
        # Adapter TIDAK menerima findings mentah/Dict sbg input utama:
        # hanya `diagnosis` (DiagnosisResult) + `capability` + self.
        import inspect
        sig = inspect.signature(EnvironmentRecommendationAdapter.recommend)
        params = list(sig.parameters.keys())
        self.assertIn("diagnosis", params)
        self.assertNotIn("findings", params)
        self.assertNotIn("evidence", params)

    def test_diagnosis_ref_is_reference_not_copy(self):
        # diagnosis_ref = reference hasil diagnosis (source-ref), bukan salinan
        # evidence. Objek asli diagnosis TIDAK duplikasi penuh ke recommendations.
        res = EnvironmentRecommendationAdapter(_subject()).recommend(
            diagnosis=_diag("insufficient", []))
        self.assertEqual(res.diagnosis_ref, "diagnosis evidence sources=disk_space; n=1")
        self.assertEqual(len(res.recommendations), 0)


class AntiGodServiceRecommendationTest(unittest.TestCase):
    """Adapter recommendation TIDAK import environment/connector/AI/WardGovernor/executor."""

    def test_adapter_never_imports_forbidden_modules(self):
        import inspect
        from sam.ward.adapters import environment_recommendation as mod
        src = inspect.getsource(mod)
        # Anti-God guard: TIDAK ada IMPORT environment/connector/AI/
        # WardGovernor/executor/harness. (Periksa pernyataan import, bukan
        # penyebutan kata di komentar agar tes tidak salah sasaran.)
        import_lines = [ln.strip() for ln in src.splitlines()
                        if ln.strip().startswith(("import ", "from "))]
        joined = "\n".join(import_lines)
        self.assertNotIn("sam.environment", joined)
        self.assertNotIn("connector", joined)
        self.assertNotIn("WardGovernor", joined)
        self.assertNotIn("ProviderExecutor", joined)
        self.assertNotIn("real_harness", joined)
        self.assertNotIn("m8_mission_framework", joined)
        # Hanya import yang diizinkan: contracts.
        self.assertIn("from sam.ward.capability.contracts", joined)


class RunnerRecommendationTest(unittest.TestCase):
    """Runner dispatcher + service wiring untuk environment.recommend (R1-005)."""

    def test_run_mission_dispatch_recommend_not_observe(self):
        from sam.application.ux.runner import run_mission
        res = run_mission("environment.recommend", target="local-machine")
        self.assertEqual(res["operation"], "environment.recommend")
        self.assertEqual(res["timeline"][0]["stage"], "environment.recommend")
        # Tanpa diagnosis -> adapter jujur kosong (0 rekomendasi).
        self.assertEqual(res["evidence"]["recommendation_count"], 0)
        self.assertEqual(res["evidence"]["recommendations"], [])

    def test_run_mission_recommend_consumes_canonical_diagnosis(self):
        """Recommendation menerima DiagnosisResult CANONICAL (bukan findings mentah)."""
        from sam.application.ux.runner import run_mission
        # BUILD diagnosis causal tanpa mapping -> recommendations harus [] jujur.
        diag = DiagnosisResult(
            subject=_subject(), verdict="causal",
            diagnosis=[_finding("disk hampir penuh")],
            confidence=0.9,
            evidence_ref="diagnosis evidence sources=disk_space; n=1",
            summary="verdict causal", error="",
        )
        res = run_mission("environment.recommend", target="local-machine",
                          diagnosis=diag)
        self.assertEqual(res["operation"], "environment.recommend")
        # Diagnosis tersedia (causal) tetapi TIDAK ada canonical action mapping
        # -> rekomendasi kosong jujur (fail-closed, tanpa mengarang).
        self.assertEqual(res["evidence"]["recommendation_count"], 0)
        self.assertIn("R1-006", res["evidence"]["summary"])

    def test_classify_recommend_completed(self):
        from sam.application.ux.runner import classify_mission_outcome, run_mission
        res = run_mission("environment.recommend", target="local-machine")
        verdict = classify_mission_outcome(res)
        self.assertEqual(verdict["status"], "completed")
        self.assertIn("rekomendasi", verdict.get("message", ""))


class ServiceRecommendationWiringTest(unittest.TestCase):
    """Service: cache DiagnosisResult CANONICAL + alur decide utk recommend."""

    def test_service_caches_canonical_diagnosis(self):
        """Setelah diagnose, service menyimpan DiagnosisResult canonical (bukan Dict)."""
        from sam.application.ux.service import (
            MissionUXService, ApprovalDecisionIntent,
        )
        svc = MissionUXService()
        # diagnose -> verdict insufficient (tanpa cache findings) -> state completed.
        svc.submit("simplulkan diagnosis komputer ini")
        svc.decide(ApprovalDecisionIntent.APPROVE, approver="user")
        # Diagnosis TIDAK menghasilkan verdict causal dari no-evidence, tapi cache
        # setidaknya tersimpan sebagai objek canonical (bukan None bila ada diagnosis).
        # (insufficient -> Recommended masih akan [] jujur di langkah berikutnya.)
        self.assertIsNotNone(svc._last_diagnosis_result)

    def test_recommend_via_service_fail_closed_zero_side_effect(self):
        """Alur /ux: diagnose -> recommend. Tanpa canonical mapping -> [] jujur."""
        from sam.application.ux.service import (
            MissionUXService, ApprovalDecisionIntent,
        )
        svc = MissionUXService()
        # Langkah 1: diagnose.
        svc.submit("simplulkan diagnosis komputer ini")
        st1 = svc.decide(ApprovalDecisionIntent.APPROVE, approver="user")
        self.assertEqual(st1.status, "completed")
        # Langkah 2: recommend (makan dari cache DiagnosisResult canonical).
        svc.submit("rekomendasikan tindakan yang layak")
        st2 = svc.decide(ApprovalDecisionIntent.APPROVE, approver="user")
        self.assertEqual(st2.status, "completed")
        ev = next((e for e in st2.evidence
                   if e.get("kind") == "environment_recommendation"), None)
        self.assertIsNotNone(ev)
        self.assertEqual(ev.get("recommendation_count", -1), 0)
        self.assertEqual(ev.get("recommendations", [None]), [])


if __name__ == "__main__":
    unittest.main()
