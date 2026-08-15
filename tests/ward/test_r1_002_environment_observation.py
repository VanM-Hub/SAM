"""R1-002 — Canonical Environment Observation Boundary.

Unit + integrasi ringan utk EnvironmentObservationAdapter, dispatcher
environment.observe, recognizer "Periksa komputer saya", dan fail-closed.
REAL E2E (HTTP nyata ke OS) ada di proof: docs/engineering/reports/
R1-002_Real_E2E_Environment_Observation_Proof.json (dijalankan manual).

Prinsip semantic (Van R1-002): ObservationTarget = port capability, BUKAN
menjadikan environment jadi Ward/Citizen. Adapter hanya menyesuaikan
implementation environment ke kontrak observation. Tidak ada executor kedua,
tidak import harness, tidak katalog Word/PDF/OpenClaw.
"""
import unittest

from sam.ward.capability.contracts import SubjectRef
from sam.ward.adapters.environment_observation import EnvironmentObservationAdapter
from sam.environment.entity import (
    Entity, EntityKind, EntitySource, DiscoveryScan,
)
from sam.environment.discovery import EnvironmentDiscovery


def _subject():
    return SubjectRef(subject_id="local-machine", subject_type="citizen",
                      kind="environment", name="local-machine")


class _FakeScanEntity:
    class _Kind:
        value = "process"

    class _Source:
        value = "process_table"

    def __init__(self):
        self.id = "e1"
        self.kind = self._Kind()
        self.source = self._Source()
        self.label = "bash.exe"
        self.attributes = {"pid": "1", "status": "running", "health": "ok"}
        self.confidence = 1.0


class _FakeDiscovery:
    def __init__(self, entities, failures=None):
        self._entities = entities
        self._failures = failures or []

    def discover(self):
        return DiscoveryScan(entities=self._entities,
                             attributes={"failures": self._failures})


class EnvironmentObservationAdapterTest(unittest.TestCase):
    def test_adapter_is_observation_target_contract_not_new_subject(self):
        # Adapter harus memenuhi kontrak ObservationTarget (port), bukan
        # mendefinisikan entitas/konsep baru.
        self.assertTrue(hasattr(EnvironmentObservationAdapter, "observe"))
        obs = EnvironmentObservationAdapter(subject=_subject(),
                                            discovery=_FakeDiscovery([_FakeScanEntity()]))
        self.assertTrue(callable(obs.observe))

    def test_observe_returns_observation_with_real_entity_evidence(self):
        adapter = EnvironmentObservationAdapter(
            subject=_subject(), discovery=_FakeDiscovery([_FakeScanEntity()]))
        obs = adapter.observe(capability="observe")
        self.assertTrue(obs.successful)
        self.assertEqual(obs.evidence.get("entity_count"), 1)
        self.assertIn("process_table", obs.evidence.get("sources"))
        self.assertEqual(obs.evidence["entities"][0]["kind"], "process")
        self.assertEqual(obs.evidence["entities"][0]["label"], "bash.exe")
        self.assertEqual(obs.evidence["entities"][0]["source"], "process_table")
        self.assertEqual(obs.evidence["entities"][0]["confidence"], 1.0)

    def test_probe_failure_recorded_not_hidden(self):
        adapter = EnvironmentObservationAdapter(
            subject=_subject(),
            discovery=_FakeDiscovery(
                [_FakeScanEntity()],
                failures=[{"source": "env_table", "error": "permission denied"}]))
        obs = adapter.observe()
        self.assertTrue(obs.successful, "sebagian sukses tetap successful")
        self.assertEqual(len(obs.evidence.get("failures")), 1)
        self.assertEqual(obs.evidence["failures"][0]["source"], "env_table")

    def test_empty_discovery_is_fail_honest_not_invented(self):
        adapter = EnvironmentObservationAdapter(
            subject=_subject(),
            discovery=_FakeDiscovery([], failures=[{"source": "process_table",
                                                    "error": "psutil"} ]))
        obs = adapter.observe()
        self.assertFalse(obs.successful, "kosong -> jujur gagal, bukan entitas palsu")
        self.assertEqual(obs.evidence.get("entity_count"), 0)
        self.assertTrue(obs.evidence.get("failures"))

    def test_discovery_exception_is_blocked(self):
        class Boom:
            def discover(self):
                raise RuntimeError("total failure")
        obs = EnvironmentObservationAdapter(subject=_subject(),
                                            discovery=Boom()).observe()
        self.assertFalse(obs.successful)
        self.assertTrue(obs.evidence.get("total_failure"))

    def test_real_discovery_produces_real_os_entities(self):
        # Discovery NYATA (psutil / env) -> evidence dari OS, source process/env.
        adapter = EnvironmentObservationAdapter(subject=_subject())
        obs = adapter.observe()
        self.assertTrue(obs.successful)
        self.assertGreater(obs.evidence.get("entity_count", 0), 0)
        sources = obs.evidence.get("sources") or []
        self.assertTrue(any(s in sources for s in
                            ("process_table", "file_table", "env_table")))

    def test_no_environment_import_in_application_service_layers(self):
        # Anti God Service: application service tidak boleh import environment.
        import sam.application.ux.service as svc_mod
        src = open(svc_mod.__file__, encoding="utf-8").read()
        self.assertNotIn("from sam.environment", src)
        self.assertNotIn("import sam.environment", src)
        import sam.application.ux.conversation as conv_mod
        csrc = open(conv_mod.__file__, encoding="utf-8").read()
        self.assertNotIn("from sam.environment", csrc)
        self.assertNotIn("import sam.environment", csrc)


class EnvironmentRecognizerTest(unittest.TestCase):
    def test_recognizes_periksa_komputer(self):
        from sam.application.ux.service import MissionUXService
        op, tgt, und, planned, _, _ = MissionUXService._interpret("Periksa komputer saya")
        self.assertEqual(op, "environment.observe")
        self.assertEqual(tgt, "local-machine")
        self.assertTrue(planned)

    def test_recognizes_cek_kesehatan_komputer(self):
        from sam.application.ux.service import MissionUXService
        op, *_ = MissionUXService._interpret("Cek kesehatan komputer ini")
        self.assertEqual(op, "environment.observe")

    def test_does_not_recognize_unrelated(self):
        from sam.application.ux.service import MissionUXService
        op, *_ = MissionUXService._interpret("Halo saja")
        self.assertNotEqual(op, "environment.observe")


class EnvironmentDispatcherTest(unittest.TestCase):
    def test_run_mission_environment_observe_real(self):
        from sam.application.ux.runner import run_mission, classify_mission_outcome
        res = run_mission(operation="environment.observe")
        self.assertEqual(res["operation"], "environment.observe")
        self.assertTrue(res["ok"])
        self.assertEqual(res["timeline"][0]["stage"], "environment.observe")
        v = classify_mission_outcome(res)
        self.assertEqual(v["status"], "completed")

    def test_unsupported_not_yet_opened_blocked(self):
        # process.run / email.send dll BELUM dibuka -> UnsupportedOperationError
        # (jujur BLOCKED, 0 side effect), bukan dieksekusi.
        from sam.application.ux.runner import run_mission, UnsupportedOperationError
        with self.assertRaises(UnsupportedOperationError):
            run_mission(operation="process.run")


if __name__ == "__main__":
    unittest.main()
