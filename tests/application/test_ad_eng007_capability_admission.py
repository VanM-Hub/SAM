"""AD-ENG-007 — Invalid / Unresolved Intent Safety Boundary.

Deterministic capability admission (LLM = candidate, SAM validator = authority).

Verifies the exact canonical operation set admission and the invalid/unresolved
boundary: an operation candidate that is NOT in the exact canonical execution set
must never become a Mission / Plan / Approval / Execution.

These tests are deterministic (no network LLM): they exercise
`_resolve_capability` and `_assemble_interpretation` directly.
"""

import unittest

from sam.application.ux.service import MissionUXService


class CapabilityResolutionTest(unittest.TestCase):
    """Exact canonical capability set (ADR-007, execution authority-derived)."""

    CANONICAL = {
        "github.create_issue",
        "web.open",
        "http.call",
        "environment.observe",
        "environment.investigate",
        "environment.diagnose",
        "environment.recommend",
    }

    def test_resolve_capability_valid_canonical(self):
        """Valid canonical operation -> resolved, no reason."""
        for op in self.CANONICAL:
            resolved, reason = MissionUXService._resolve_capability(op)
            self.assertEqual(resolved, op)
            self.assertIsNone(reason)

    def test_resolve_capability_invalid_unsupported(self):
        """Operation tanpa jalur execution canonical -> invalid (unsupported)."""
        for op in ("process.run", "email.send", "db.query", "foo.bar"):
            resolved, reason = MissionUXService._resolve_capability(op)
            self.assertIsNone(resolved)
            self.assertEqual(reason, "unsupported_operation")

    def test_resolve_capability_valid_prefix_unknown_suffix(self):
        """TE2: valid capability prefix + unknown suffix -> bukan canonical -> invalid."""
        # "http.xxx" bukan "http.call" (exact), walau runner prefix-tolerant.
        for op in ("http.foobar", "web.fetch", "github.create_pr", "process.run"):
            resolved, reason = MissionUXService._resolve_capability(op)
            self.assertIsNone(resolved)
            self.assertEqual(reason, "unsupported_operation")

    def test_process_run_keluarga_tidak_diadvertise(self):
        """process.run/email.send/db.query tidak punya jalur eksekusi canonical ->
        tidak diiklankan di _AI_CAPABILITIES dan tidak admissible."""
        caps = MissionUXService._AI_CAPABILITIES
        self.assertNotIn("[process.run]", caps)
        self.assertNotIn("[email.send]", caps)
        self.assertNotIn("[db.query]", caps)
        self.assertIn("[environment.investigate]", caps)  # regression: read-only tetap ada


class CandidateAssemblyBoundaryTest(unittest.TestCase):
    """LLM = candidate, _assemble_interpretation = deterministic authority."""

    def test_te1_lorem_ipsum_process_run_invalid_no_mission(self):
        """TE1: LLM mengusulkan process.run utk garbage -> invalid, BUKAN Mission.

        operation="", no planned steps, resolve_reason='unsupported_operation'
        (tidak pernah promosi ke plan/approval/execution).
        """
        parsed = {
            "operation": "process.run",
            "target": "",
            "understood": "lorem ipsum random text bukan perintah",
            "planned": ["jalankan perintah lorem"],
        }
        out = MissionUXService._assemble_interpretation(parsed, source="DeepSeek")
        self.assertIsNotNone(out)
        operation, target, _, planned, _, _, resolve_reason = out
        self.assertEqual(operation, "")  # no Mission
        self.assertEqual(planned, [])  # no Plan
        self.assertEqual(resolve_reason, "unsupported_operation")  # trace utk observability
        # approval/execution dihindari karena operation kosong (submit L417).

    def test_te2_valid_prefix_unknown_suffix_invalid(self):
        """TE2: http.foobar (valid namespace, unknown suffix) -> BUKAN canonical -> invalid."""
        parsed = {"operation": "http.foobar", "target": "example.com", "planned": ["x"]}
        out = MissionUXService._assemble_interpretation(parsed, source="DeepSeek")
        operation, *_ , resolve_reason = out
        self.assertEqual(operation, "")
        self.assertEqual(resolve_reason, "unsupported_operation")

    def test_te3_valid_canonical_operation_mission(self):
        """TE3: valid canonical operation -> Mission jalan seperti sebelumnya (no regression)."""
        parsed = {
            "operation": "github.create_issue",
            "target": "repo/x",
            "understood": "buat issue",
            "planned": ["verifikasi", "buat issue"],
        }
        out = MissionUXService._assemble_interpretation(parsed, source="DeepSeek")
        operation, target, _, planned, _, _, resolve_reason = out
        self.assertEqual(operation, "github.create_issue")  # Mission (mutating)
        # S2-4 contract: repo Github dikunci ke default, bukan percaya target dari AI.
        self.assertEqual(target, "VanM-Hub/test-issues")
        self.assertTrue(planned)  # Plan ada
        self.assertIsNone(resolve_reason)

    def test_environment_valid_mission_read_only(self):
        """environment canonical valid -> Mission read-only, no approval-required."""
        parsed = {"operation": "environment.observe", "target": "local-machine",
                  "planned": ["periksa komputer"]}
        out = MissionUXService._assemble_interpretation(parsed, source="DeepSeek")
        operation, _, _, planned, _, _, resolve_reason = out
        self.assertEqual(operation, "environment.observe")
        self.assertTrue(planned)
        self.assertIsNone(resolve_reason)
        self.assertTrue(MissionUXService._operation_is_read_only("environment.observe"))
        # observability resolution utk jalur valid = 'valid'


if __name__ == "__main__":
    unittest.main()
