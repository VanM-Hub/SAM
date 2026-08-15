"""R1-003 — Canonical Environment Investigation Boundary.

Unit + integrasi ringan utk EnvironmentInvestigationAdapter, dispatcher
environment.investigate, recognizer "kenapa komputer lambat?", mapping
Hypothesis -> InvestigationResult.findings (tanpa model Finding baru), dan
fail-closed INSUFFICIENT.
REAL E2E (HTTP nyata ke OS, evidence-cukup & evidence-tak-cukup) ada di
proof: docs/engineering/reports/R1-003_Investigation_Real_E2E_Proof.json.

Prinsip semantic (Van R1-003):
  - Murni boundary/jembatan, reuse DiagnosisEngine.investigate() (canonical).
  - TIDAK membuat model Finding baru; hasil = InvestigationResult.findings
    (List[Dict]). Finding (M13-006) milik R1-004 Diagnosis.
  - TIDAK menambah fakta (CPU%/mem%/disk) yang belum diobservasi.
  - Berhenti di finding kandidat + confidence; TIDAK mengklaim root cause.
  - Read-only, fail-closed INSUFFICIENT (0 fabrikasi).
"""
import unittest

from sam.ward.capability.contracts import SubjectRef
from sam.ward.adapters.environment_investigation import EnvironmentInvestigationAdapter
from sam.environment.entity import (
    Entity, EntityKind, EntitySource, DiscoveryScan,
)


def _subject():
    return SubjectRef(subject_id="local-machine", subject_type="citizen",
                      kind="environment", name="local-machine")


def _proc(pid, label, health, status="running"):
    return Entity(
        id=f"p-{pid}", kind=EntityKind.PROCESS, source=EntitySource.PROCESS_TABLE,
        label=label, attributes={"pid": pid, "status": status, "health": health},
    )


def _port(num, pid):
    return Entity(
        id=f"pt-{num}", kind=EntityKind.PORT, source=EntitySource.PORT_TABLE,
        label=f"tcp:{num}", attributes={"port": str(num), "pid": pid or ""},
    )


class _FakeDiscovery:
    def __init__(self, entities):
        self._entities = entities

    def discover(self):
        return DiscoveryScan(entities=self._entities,
                             attributes={"failures": []})


class _BoomDiscovery:
    def discover(self):
        raise RuntimeError("probe discovery rusak")


class EnvironmentInvestigationAdapterTest(unittest.TestCase):
    def test_adapter_is_investigation_target_contract(self):
        # Adapter memenuhi kontrak InvestigationTarget (port) - investigate().
        self.assertTrue(hasattr(EnvironmentInvestigationAdapter, "investigate"))
        a = EnvironmentInvestigationAdapter(subject=_subject())
        self.assertTrue(callable(a.investigate))

    def test_healthy_only_no_signal_is_insufficient_not_fabricated(self):
        # Semua sehat & port bound -> tidak ada sinyal -> INSUFFICIENT jujur
        # (0 findings), BUKAN mengarang masalah / root cause.
        ents = [_proc("1", "svchost.exe", "ok", "running"),
                _proc("2", "explorer.exe", "ok", "running"),
                _port(80, "1")]
        adapter = EnvironmentInvestigationAdapter(
            subject=_subject(), discovery=_FakeDiscovery(ents))
        res = adapter.investigate()
        self.assertTrue(res.successful)
        self.assertEqual(res.findings, [])
        self.assertTrue("tidak" in res.summary.lower()
                        or "insufficient" in res.summary.lower())

    def test_unhealthy_process_becomes_candidate_finding(self):
        # Proses dengan health!=ok -> finding kandidat (bukan root cause).
        ents = [_proc("1", "node.exe", "stopped", "stopped")]
        adapter = EnvironmentInvestigationAdapter(
            subject=_subject(), discovery=_FakeDiscovery(ents))
        res = adapter.investigate()
        self.assertTrue(res.successful)
        self.assertGreaterEqual(len(res.findings), 1)
        f = res.findings[0]
        # semantic guardrail: candidate, BUKAN diagnosis/root cause
        self.assertEqual(f["claim"], "candidate")
        self.assertIn("confidence", f)
        self.assertIn("evidence", f)
        self.assertIn("entity", f)
        # label HANYA menyebut fakta observasi (process/process_table), tidak
        # menyimpulkan "penyebab lambat".
        self.assertNotIn("penyebab", f["label"].lower())
        self.assertGreaterEqual(f["confidence"], 0.0)
        self.assertLessEqual(f["confidence"], 1.0)

    def test_unbound_port_becomes_candidate_finding(self):
        ents = [_port(8080, None), _proc("1", "svchost.exe", "ok")]
        adapter = EnvironmentInvestigationAdapter(
            subject=_subject(), discovery=_FakeDiscovery(ents))
        res = adapter.investigate()
        self.assertTrue(res.successful)
        lab = " ".join(f["label"] for f in res.findings)
        self.assertIn("tcp:8080", lab)

    def test_empty_discovery_insufficient(self):
        adapter = EnvironmentInvestigationAdapter(
            subject=_subject(), discovery=_FakeDiscovery([]))
        res = adapter.investigate()
        self.assertTrue(res.successful, "investigasi jalan, temuan kosong jujur")
        self.assertEqual(res.findings, [])

    def test_discovery_exception_is_blocked_zero_side_effect(self):
        adapter = EnvironmentInvestigationAdapter(
            subject=_subject(), discovery=_BoomDiscovery())
        res = adapter.investigate()
        self.assertFalse(res.successful)
        self.assertEqual(res.findings, [])
        self.assertIn("gagal", res.summary.lower())

    def test_does_not_add_unobserved_facts(self):
        # Adapter TIDAK boleh menambahkan fakta yang belum diobservasi
        # (mis. CPU%/mem%/disk). Cuma menerjemahkan EntityGraph -> DiagnosisEngine.
        import sam.ward.adapters.environment_investigation as mod
        src = open(mod.__file__, encoding="utf-8").read()
        for forbidden in ("cpu_percent", "memory_percent", "disk_free_bytes"):
            self.assertNotIn(forbidden, src)

    def test_findings_are_dicts_not_finding_dataclass(self):
        # R1-003 pakai InvestigationResult.findings: List[Dict], BUKAN model
        # Finding (M13-006). Pastikan hasil investigation berupa dict, dan
        # adapter tidak pernah mengembalikan objek Finding.
        ents = [_proc("1", "node.exe", "stopped", "stopped")]
        adapter = EnvironmentInvestigationAdapter(
            subject=_subject(), discovery=_FakeDiscovery(ents))
        res = adapter.investigate()
        for f in res.findings:
            self.assertIsInstance(f, dict)

    def test_real_discovery_produces_real_candidate_findings(self):
        # Discovery NYATA -> findings dari fakta OS (proses status!=ok / port
        # unbound). Boleh kosong (INSUFFICIENT) bila mesin sehat - jujur.
        adapter = EnvironmentInvestigationAdapter(subject=_subject())
        res = adapter.investigate()
        self.assertTrue(res.successful)
        for f in res.findings:
            self.assertEqual(f["claim"], "candidate")
            self.assertEqual(f["subject_id"], "local-machine")


class EnvironmentInvestigationRecognizerTest(unittest.TestCase):
    def test_recognizes_kenapa_komputer_lambat(self):
        from sam.application.ux.service import MissionUXService
        op, tgt, und, planned, _, _ = MissionUXService._interpret(
            "kenapa komputer saya lambat?")
        self.assertEqual(op, "environment.investigate")
        self.assertEqual(tgt, "local-machine")
        self.assertTrue(planned)

    def test_recognizes_apakah_perlu_selidiki(self):
        from sam.application.ux.service import MissionUXService
        op, *_ = MissionUXService._interpret(
            "selidiki apa masalah dengan sistem ini")
        self.assertEqual(op, "environment.investigate")

    def test_does_not_intercept_observe(self):
        # "Periksa komputer" tetap observe, BUKAN investigate.
        from sam.application.ux.service import MissionUXService
        op, *_ = MissionUXService._interpret("Periksa komputer saya")
        self.assertEqual(op, "environment.observe")

    def test_investigate_is_before_ai_capability_list(self):
        # environment.investigate terdaftar di _AI_CAPABILITIES (untuk info AI),
        # TAPI routing deterministik ada di _interpret sebelum AI.
        from sam.application.ux.service import MissionUXService
        self.assertIn("[environment.investigate]", MissionUXService._AI_CAPABILITIES)


class EnvironmentInvestigationDispatcherTest(unittest.TestCase):
    def test_run_mission_environment_investigate_real(self):
        from sam.application.ux.runner import run_mission, classify_mission_outcome
        res = run_mission(operation="environment.investigate")
        self.assertEqual(res["operation"], "environment.investigate")
        self.assertTrue(res["ok"])
        self.assertEqual(res["timeline"][0]["stage"], "environment.investigate")
        self.assertIn("kind", res["evidence"])
        self.assertEqual(res["evidence"]["kind"], "environment_investigation")
        v = classify_mission_outcome(res)
        self.assertEqual(v["status"], "completed")

    def test_unsupported_not_yet_opened_blocked(self):
        from sam.application.ux.runner import run_mission, UnsupportedOperationError
        with self.assertRaises(UnsupportedOperationError):
            run_mission(operation="process.run")


class EnvironmentInvestigationFlowTest(unittest.TestCase):
    def test_full_service_flow_investigate(self):
        from sam.application.ux.approval import ApprovalDecisionIntent
        from sam.application.ux.service import MissionUXService
        svc = MissionUXService()
        st = svc.submit("kenapa komputer saya lambat?")
        self.assertEqual(st.operation, "environment.investigate")
        self.assertEqual(st.status, "waiting_approval")
        st = svc.decide(ApprovalDecisionIntent.APPROVE)
        self.assertEqual(st.status, "completed")
        ev = svc.get_evidence()
        self.assertTrue(ev)
        self.assertEqual(ev[0]["kind"], "environment_investigation")
        # field-field evidence investigation; insuffICIENT diset sesuai hasil.
        self.assertIn("findings", ev[0])
        self.assertIn("insufficient", ev[0])
        self.assertIn("confidence", ev[0]["findings"][0]
                      if ev[0]["findings"] else {})

    def test_full_service_flow_insufficient_honest(self):
        # INSUFFICIENT path full-stack: bila discovery bersih (semua proses
        # sehat, port bound) -> submit/decide menghasilkan completed + evidence
        # environment_investigation dgn insufficient=True + findings kosong.
        # (patch HANYA pada probe OS; seluruh service/runner/adapter/engine
        # tetap jalan kode asli - membuktikan pemetaan insufficient jujur.)
        from unittest.mock import patch
        from sam.application.ux.approval import ApprovalDecisionIntent
        from sam.application.ux.service import MissionUXService
        from sam.environment.entity import (
            Entity, EntityKind, EntitySource, DiscoveryScan)

        ents = [
            Entity(id="p-1", kind=EntityKind.PROCESS,
                   source=EntitySource.PROCESS_TABLE,
                   label="svchost.exe",
                   attributes={"pid": "1", "status": "running", "health": "ok"}),
            Entity(id="p-2", kind=EntityKind.PROCESS,
                   source=EntitySource.PROCESS_TABLE,
                   label="explorer.exe",
                   attributes={"pid": "2", "status": "running", "health": "ok"}),
        ]

        def _clean_discover(self):
            return DiscoveryScan(entities=ents, attributes={"failures": []})

        with patch(
            "sam.environment.discovery.EnvironmentDiscovery.discover",
            _clean_discover,
        ):
            svc = MissionUXService()
            st = svc.submit("kenapa komputer saya lambat?")
            self.assertEqual(st.operation, "environment.investigate")
            self.assertEqual(st.status, "waiting_approval")
            st = svc.decide(ApprovalDecisionIntent.APPROVE)
            self.assertEqual(st.status, "completed")
            ev = svc.get_evidence()
            self.assertTrue(ev)
            inv = ev[0]
            self.assertEqual(inv["kind"], "environment_investigation")
            self.assertTrue(inv["insufficient"],
                            "evidence tak cukup -> insufficient=True jujur")
            self.assertEqual(inv["findings"], [], "0 temuan, 0 fabrikasi")


if __name__ == "__main__":
    unittest.main()
