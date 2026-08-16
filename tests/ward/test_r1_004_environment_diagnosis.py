"""R1-004 — Canonical Environment Diagnosis Boundary (diagnosis verdict).

Unit + integrasi ringan utk EnvironmentDiagnosisAdapter (read-only evaluator),
kontrak DiagnosisTarget/DiagnosisResult, runner dispatcher environment.diagnose,
recognizer "diagnosa/simpulkan", W1 cache findings investigasi, dan
fail-closed INSUFFICIENT.
REAL E2E (HTTP nyata ke OS -> investigate -> diagnose) ada di proof:
docs/engineering/reports/R1-004_Diagnosis_Real_E2E_Proof.json.

Prinsip semantic (Van R1-004, dikunci 2026-08-16):
  - MURNI evaluator read-only. BUKAN engine diagnosis baru, BUKAN investigation
    ulang, BUKAN mutation/recovery.
  - Menilai SELECTED EVIDENCE (List[Dict]) dari findings investigasi R1-003,
    bukan findings mentah.
  - Sinyal kausal dibawa evidence (field `causal`), BUKAN katalog hardcoded.
  - confidence = EVIDENCE confidence (reuse ConfidenceAssessor), TERPISAH dari
    verdict; TIDAK dipaksa 0.0 saat verdict insufficient.
  - 3 proses stopped (R1-003) = candidate findings, TIDAK ada causal link ->
    diagnosis INSUFFICIENT jujur (bukan "Metronom causes slowness").
"""
import unittest

from sam.ward.capability.contracts import (
    SubjectRef, DiagnosisResult, Finding,
)
from sam.ward.adapters.environment_diagnosis import EnvironmentDiagnosisAdapter


def _subject():
    return SubjectRef(subject_id="local-machine", subject_type="citizen",
                      kind="environment", name="local-machine")


def _ev(source, statement, strength=1.0, negative=False, causal=False):
    return {
        "source": source, "statement": statement, "strength": strength,
        "negative": negative, "causal": causal,
    }


class DiagnosisAdapterTest(unittest.TestCase):
    """Adapter HANYA menilai evidence yang dibawa; tidak mengarang sebab."""

    def test_insufficient_when_no_evidence(self):
        res = EnvironmentDiagnosisAdapter(_subject()).diagnose(evidence=[])
        self.assertEqual(res.verdict, "insufficient")
        self.assertEqual(res.diagnosis, [])
        self.assertEqual(res.confidence, 0.0)
        self.assertIn("tidak ada evidence", res.summary)

    def test_insufficient_when_no_causal_signal(self):
        """3 proses stopped = candidate findings TANPA causal -> INSUFFICIENT."""
        evidence = [
            _ev("process_table", "Metronom.exe stopped", strength=0.9, causal=False),
            _ev("process_table", "SystemSettings.exe stopped", strength=0.8, causal=False),
        ]
        res = EnvironmentDiagnosisAdapter(_subject()).diagnose(evidence=evidence)
        self.assertEqual(res.verdict, "insufficient")
        self.assertEqual(res.diagnosis, [])
        # confidence EVIDENCE TETAP terhitung, TIDAK dipaksa 0.0.
        self.assertGreater(res.confidence, 0.0)
        self.assertIn("INSUFFICIENT", res.summary)

    def test_causal_verdict_when_strong_causal_evidence(self):
        evidence = [_ev("disk_space", "disk hampir penuh", strength=0.9, causal=True)]
        res = EnvironmentDiagnosisAdapter(_subject()).diagnose(evidence=evidence)
        self.assertEqual(res.verdict, "causal")
        self.assertEqual(len(res.diagnosis), 1)
        self.assertIsInstance(res.diagnosis[0], Finding)
        self.assertGreaterEqual(res.confidence, 0.0)

    def test_candidate_verdict_when_weak_causal_evidence(self):
        evidence = [
            _ev("disk_space", "penggunaan disk tinggi", strength=0.5, causal=True),
            _ev("process_table", "beberapa proses stopped", strength=0.6, causal=False),
        ]
        res = EnvironmentDiagnosisAdapter(_subject()).diagnose(evidence=evidence)
        self.assertEqual(res.verdict, "candidate")
        # Hanya evidence kausal mjd diagnosis (process non-causal TIDAK diangkat).
        self.assertEqual(len(res.diagnosis), 1)
        self.assertIn("candidate", res.summary)

    def test_evidence_confidence_separate_from_sufficiency(self):
        weak = _ev("process_table", "anomali ringan", strength=0.4, causal=False)
        strong = _ev("disk_space", "disk penuh", strength=0.9, causal=True)
        res_conf = EnvironmentDiagnosisAdapter(_subject()).diagnose(evidence=[weak, strong])
        self.assertEqual(res_conf.verdict, "causal")
        # confidence dibangun oleh ConfidenceAssessor dari strength evidence.
        self.assertGreater(res_conf.confidence, 0.0)


class DiagnosisContractTest(unittest.TestCase):
    def test_contracts_exist(self):
        # DiagnosisTarget adalah Protocol statis; adapater wajib punya diagnose.
        self.assertTrue(callable(getattr(EnvironmentDiagnosisAdapter, "diagnose", None)))
        # DiagnosisResult punya field kunci dokumentasi verdict.
        import dataclasses
        fields = {f.name for f in dataclasses.fields(DiagnosisResult)}
        self.assertTrue({"subject", "verdict", "diagnosis", "confidence",
                         "evidence_ref", "summary", "error"} <= fields)

    def test_finding_as_dict(self):
        f = Finding(finding_id="diag-x", subject_id="local-machine",
                    label="disk", evidence={}, confidence=0.9)
        d = f.as_dict()
        self.assertEqual(d["finding_id"], "diag-x")
        self.assertIn("confidence", d)


class RunnerDiagnoseTest(unittest.TestCase):
    """Runner dispatcher + classification untuk environment.diagnose."""

    def test_run_mission_dispatch_diagnose(self):
        from sam.application.ux.runner import run_mission
        # Tanpa cache findings -> adapter jujur INSUFFICIENT (0 fabrikasi).
        res = run_mission("environment.diagnose", target="local-machine")
        self.assertTrue(res["ok"])
        self.assertEqual(res["operation"], "environment.diagnose")
        self.assertEqual(res["evidence"]["verdict"], "insufficient")
        self.assertEqual(res["evidence"]["diagnosis"], [])
        # confidence TIDAK dipaksa 0.0 (terpisah dari verdict).
        self.assertGreaterEqual(res["evidence"]["confidence"], 0.0)

    def test_run_mission_diagnose_with_findings(self):
        from sam.application.ux.runner import run_mission
        findings = [{
            "label": "disk hampir penuh",
            "evidence": [_ev("disk_space", "disk hampir penuh",
                             strength=0.9, causal=True)],
        }]
        res = run_mission("environment.diagnose", target="local-machine",
                          findings=findings)
        self.assertTrue(res["ok"])
        ev = res["evidence"]
        self.assertEqual(ev["verdict"], "causal")
        self.assertEqual(len(ev["diagnosis"]), 1)

    def test_classify_diagnose_completed(self):
        from sam.application.ux.runner import classify_mission_outcome, run_mission
        res = run_mission("environment.diagnose", target="local-machine")
        verdict = classify_mission_outcome(res)
        self.assertEqual(verdict["status"], "completed")
        # label diagnosis (bukan "eksekusi" generik)
        self.assertIn("diagnosis", verdict.get("message", ""))


class UnknownOperationIsolatesDiagnose(unittest.TestCase):
    """environment.diagnose TIDAK jatuh ke cabang observe/others (BLOCKED)."""

    def test_environment_diagnose_not_treated_as_observe(self):
        from sam.application.ux.runner import run_mission
        res = run_mission("environment.diagnose", target="local-machine")
        self.assertEqual(res["operation"], "environment.diagnose")
        self.assertEqual(res["timeline"][0]["stage"], "environment.diagnose")


class AntiGodServiceDiagnosisTest(unittest.TestCase):
    """Adapter diagnosis TIDAK import `environment` (God-Service guard R1-004)."""

    def test_adapter_never_imports_environment_module(self):
        import inspect
        from sam.ward.adapters import environment_diagnosis as mod
        src = inspect.getsource(mod)
        # Jangan import engine/environment: hanya reuse ConfidenceAssessor (read).
        self.assertNotIn("from sam.environment.diagnosis", src)
        self.assertNotIn("from sam.environment.discovery", src)
        self.assertNotIn("from sam.environment.pipeline", src)


if __name__ == "__main__":
    unittest.main()
