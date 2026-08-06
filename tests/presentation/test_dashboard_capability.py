"""ENG-H-001 (AP-MISSION-003-001) — Program H Dashboard capability tests.

Menutupi struktur H1, wiring H2, integration H10, dan visualisasi Approval
(H6 limited). Hanya assertion pada read-only composition — tidak ada
eksekusi runtime nyata; semua gateway/consumer palsu (dummy) via injeksi.

Area yang diharapkan:
  - ready   : workflow, execution, audit, runtime, health -> handler terpasang
  - limited : approval -> hanya visualisasi dari outcome execution
  - missing : mission, provider, connector, telemetry -> escalation
"""
import unittest

from sam.presentation.dashboard import (
    DashboardViewModel,
    DashboardPanel,
    DashboardComposition,
    compose_dashboard,
    DashboardRuntimeWiring,
    wire_dashboard_runtime,
    DashboardIntegration,
    DashboardResult,
)
from sam.runtime_service.api.status import APIStatus
from sam.runtime_service.api.health import APIHealth

from sam.presentation.dashboard.card_model import DashboardCard


class _FakeAPI:
    def status(self):
        return APIStatus(services={"rt": "ok"}, healthy=True)

    def health(self):
        return APIHealth(status="healthy")


class _FakeGateway:
    def __init__(self):
        self.api = _FakeAPI()

    def preview(self, context, execution_id):
        class R:
            def as_dict(self):
                return {"executed": False, "approved": True}

        return R()

    def preview_with_workflow(self, context, wc, wid, eid, kc="", kid=""):
        return {"execution": {"approved": True}, "workflow": {"id": wid}}

    def preview_with_audit(self, context, ac, aid, eid):
        return {"execution": {"approved": True}, "audit": {"id": aid}}


def _viewmodel():
    return DashboardViewModel()


class TestDashboardViewModel(unittest.TestCase):
    def test_default_panels(self):
        vm = _viewmodel()
        self.assertEqual(vm.dashboard_id, "main")
        self.assertEqual(len(vm.panels), 10)

    def test_ready_areas_detached_default(self):
        vm = _viewmodel()
        for area in ("workflow", "execution", "audit", "runtime", "health", "approval"):
            self.assertEqual(vm.panel_status(area), "detached")

    def test_missing_areas(self):
        vm = _viewmodel()
        for area in ("mission", "provider", "connector", "telemetry"):
            self.assertEqual(vm.panel_status(area), "missing")

    def test_immutable(self):
        vm = _viewmodel()
        with self.assertRaises(Exception):
            vm.dashboard_id = "x"

    def test_as_dict(self):
        dd = _viewmodel().as_dict()
        self.assertEqual(dd["mode"], "capability")
        self.assertTrue(dd["read_only"])
        self.assertEqual(len(dd["panels"]), 10)


class TestDashboardComposition(unittest.TestCase):
    def test_compose_orders_cards(self):
        comp = compose_dashboard(_viewmodel())
        self.assertIsInstance(comp, DashboardComposition)
        cards = [c.title for c in comp.cards]
        self.assertEqual(cards, sorted(cards))

    def test_missing_areas_not_cards(self):
        for card in compose_dashboard(_viewmodel()).cards:
            self.assertNotIn(card.title.lower(), ("mission", "provider", "connector", "telemetry"))

    def test_cards_are_dashboard_card(self):
        for card in compose_dashboard(_viewmodel()).cards:
            self.assertIsInstance(card, DashboardCard)


class TestDashboardWiring(unittest.TestCase):
    def test_status_map(self):
        w = wire_dashboard_runtime(_FakeGateway(), _viewmodel())
        m = w.status_map()
        for area in ("workflow", "execution", "audit", "runtime", "health"):
            self.assertEqual(m[area], "ready")
        self.assertEqual(m["approval"], "limited")
        for area in ("mission", "provider", "connector", "telemetry"):
            self.assertEqual(m[area], "missing")

    def test_ready_handlers_attached(self):
        w = wire_dashboard_runtime(_FakeGateway(), _viewmodel())
        for area in ("workflow", "execution", "audit", "runtime", "health"):
            self.assertTrue(w.has_handler(area))

    def test_missing_not_handlers(self):
        w = wire_dashboard_runtime(_FakeGateway(), _viewmodel())
        for area in w.MISSING_AREAS:
            self.assertFalse(w.has_handler(area))

    def test_runtime_handler(self):
        w = wire_dashboard_runtime(_FakeGateway(), _viewmodel())
        self.assertEqual(w._handle_runtime()["healthy"], True)

    def test_health_handler(self):
        w = wire_dashboard_runtime(_FakeGateway(), _viewmodel())
        self.assertEqual(w._handle_health()["status"], "healthy")

    def test_wiring_uses_runtime_service_only(self):
        # Dependency tunggal keluar: package runtime_service.api.
        import inspect
        import sam.presentation.dashboard.wiring as wm
        src = inspect.getsource(wm)
        self.assertIn("from sam.runtime_service.api import", src)
        for bad in ("sam.runtime", "sam.operations", "sam.activation", "ExecutionRuntime"):
            self.assertNotIn("import " + bad, src)


class TestDashboardIntegration(unittest.TestCase):
    def test_run_all_ready_ok(self):
        vm = _viewmodel()
        w = wire_dashboard_runtime(_FakeGateway(), vm)
        res = DashboardIntegration(vm, w).run()
        for area in ("workflow", "execution", "audit", "runtime", "health"):
            self.assertEqual(res.panel_status[area], "ok")

    def test_approval_visualize_from_outcome(self):
        vm = _viewmodel()
        w = wire_dashboard_runtime(_FakeGateway(), vm)
        res = DashboardIntegration(vm, w).run()
        self.assertEqual(res.approval, {"approved": True})
        self.assertEqual(res.approval_status(), "approved")

    def test_escalated_missing(self):
        vm = _viewmodel()
        w = wire_dashboard_runtime(_FakeGateway(), vm)
        res = DashboardIntegration(vm, w).run()
        self.assertEqual(
            res.escalated,
            {"mission": "missing", "provider": "missing", "connector": "missing", "telemetry": "missing"},
        )

    def test_result_immutable_dict(self):
        vm = _viewmodel()
        w = wire_dashboard_runtime(_FakeGateway(), vm)
        res = DashboardIntegration(vm, w).run()
        self.assertIsInstance(res, DashboardResult)
        self.assertEqual(res.dashboard_id, "main")


if __name__ == "__main__":
    unittest.main()
