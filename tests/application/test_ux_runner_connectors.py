"""Tests B (M11) — dispatcher eksekusi multi-connector pada MissionUXService.

Menegakkan keputusan B (buka pintu eksekusi non-GitHub):
  - `run_mission` memilih eksekutor canonical berdasarkan operasi (B1/B2).
  - `web.open` / `web.get` -> browser connector read-only (fetch tanpa driver).
  - `http.<endpoint>` -> http connector read-only (GET).
  - Operasi berisiko yang belum dibuka (email.send, dll) -> BLOCKED jujur,
    0 side effect (UnsupportedOperationError).
  - Service end-to-end: submit web.open -> approve -> completed + evidence
    read-only (tanpa secret, tanpa driver browser).
"""
from __future__ import annotations

import unittest

from sam.application.ux.approval import ApprovalDecisionIntent
from sam.application.ux.runner import UnsupportedOperationError, run_mission
from sam.application.ux.service import MissionUXService

APPROVED = "APPROVED by user (test B)"


class RunnerDispatcherTest(unittest.TestCase):
    """B1/B2 — dispatcher memilih eksekutor canonical sesuai operasi."""

    def test_web_open_routes_to_browser_readonly(self):
        r = run_mission("web.open", target="example.com", approval_reason=APPROVED)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["operation"], "browser/fetch_url")
        self.assertEqual(r["target"], "https://example.com")
        self.assertTrue(r["timeline"])  # ada stage web.fetch

    def test_web_get_routes_to_browser_readonly(self):
        r = run_mission("web.get", target="https://example.com", approval_reason=APPROVED)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["operation"], "browser/fetch_url")

    def test_http_endpoint_routes_to_http_readonly(self):
        r = run_mission("http.httpbin_get", approval_reason=APPROVED)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["operation"], "http/httpbin_get")

    def test_unsafe_operation_blocked_honest(self):
        # email belum dibuka -> BLOCKED jujur, hingga UnsupportedOperationError.
        with self.assertRaises(UnsupportedOperationError):
            run_mission("email.send", target="x@y.com", approval_reason=APPROVED)

    def test_web_without_url_blocked(self):
        with self.assertRaises(UnsupportedOperationError):
            run_mission("web.open", target="", approval_reason=APPROVED)


class ServiceWebOpenE2ETest(unittest.TestCase):
    """B3 — service end-to-end: submit web.open -> approve -> completed + evidence."""

    def test_web_open_full_journey(self):
        svc = MissionUXService()
        st = svc.submit("buka website example.com")
        self.assertEqual(st.operation, "web.open")
        self.assertEqual(st.approval_status, "waiting_approval")

        st2 = svc.decide(ApprovalDecisionIntent.APPROVE, approver="van")
        self.assertEqual(st2.status, "completed", st2.failure_message)
        self.assertTrue(st2.evidence)
        first = st2.evidence[0]
        self.assertEqual(first["kind"], "read_only_result")
        self.assertEqual(first["target"], "https://example.com")

    def test_reject_web_open_no_execution(self):
        svc = MissionUXService()
        st = svc.submit("buka website example.com")
        self.assertEqual(st.operation, "web.open")

        st2 = svc.decide(ApprovalDecisionIntent.REJECT, approver="van")
        self.assertEqual(st2.status, "rejected")
        # reject -> TIDAK ada eksekusi, tidak ada evidence.
        self.assertEqual(st2.evidence, [])
