"""Test IP-4.6-001 - Unified Operational Workspace (MISSION-4.6).

Coverage: WP-01..WP-10 - workspace, session, citizen/runtime/provider
explorers, operational context, workspace API, explainability, compliance,
end-to-end.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_workspace.workspace import (
    UnifiedWorkspace,
)
from sam.operational_workspace.operational_session import SessionManager
from sam.operational_workspace.explorers import (
    CitizenExplorer,
    CitizenInfo,
    ProviderExplorer,
    ProviderView,
    RuntimeExplorer,
    RuntimeView,
)
from sam.operational_workspace.operational_context import (
    ContextManager,
)
from sam.operational_workspace.workspace_api import WorkspaceAPI
from sam.operational_workspace.workspace_explainability import WorkspaceExplainer
from sam.operational_workspace.workspace_compliance import (
    WorkspaceComplianceChecker,
)


# ---------------------------------------------------------------------------
# WP-01 Unified Workspace
# ---------------------------------------------------------------------------

class TestUnifiedWorkspace:
    def test_workspace_metadata(self):
        ws = UnifiedWorkspace("Test WS")
        assert ws.metadata.workspace_id
        assert ws.layout.panels

    def test_workspace_state_session(self):
        ws = UnifiedWorkspace()
        ws.show("citizens", "cit-1")
        assert ws.state.active_panel == "citizens"
        assert ws.state.active_entity_id == "cit-1"

    def test_navigation_back(self):
        ws = UnifiedWorkspace()
        ws.show("runtimes")
        ws.show("providers")
        ws.back()
        assert ws.state.active_panel == "runtimes"

    def test_no_domain_logic(self):
        ws = UnifiedWorkspace()
        # workspace hanya punya state/navigation, bukan logic capability
        assert not hasattr(ws, "execute")
        assert not hasattr(ws, "approve")


# ---------------------------------------------------------------------------
# WP-02 Operational Session
# ---------------------------------------------------------------------------

class TestOperationalSession:
    def test_create_session(self):
        manager = SessionManager()
        session = manager.create(user="op", workspace_id="ws-1")
        assert session.session_id

    def test_session_records_history(self):
        manager = SessionManager()
        session = manager.create(user="op")
        session = manager.record(session.session_id, "navigate", "to citizens")
        assert len(session.history) == 2

    def test_session_complete(self):
        manager = SessionManager()
        session = manager.create(user="op")
        completed = manager.complete(session.session_id)
        assert completed.state == "completed"

    def test_session_recover(self):
        manager = SessionManager()
        recovered = manager.recover("lost-session", {"user": "op", "workspace_id": "ws"})
        assert recovered.session_id == "lost-session"


# ---------------------------------------------------------------------------
# WP-03/04/05 Explorers
# ---------------------------------------------------------------------------

class TestExplorers:
    def test_citizen_explorer(self):
        explorer = CitizenExplorer()
        explorer.register(CitizenInfo("cit-1", "Execution", capabilities=("execute",), health="healthy"))
        explorer.register(CitizenInfo("cit-2", "Knowledge", capabilities=("learn",), health="healthy"))
        assert len(explorer.discover()) == 2
        assert explorer.detail("cit-1")["name"] == "Execution"

    def test_runtime_explorer_no_mutation(self):
        explorer = RuntimeExplorer()
        explorer.register(
            "rt-1",
            lambda: RuntimeView("rt-1", "Main", status="ok", health="healthy", dependencies=("db",)),
        )
        view = explorer.observe("rt-1")
        assert view["health"] == "healthy"
        assert explorer.dependency_map()["rt-1"] == ("db",)

    def test_provider_explorer(self):
        explorer = ProviderExplorer()
        explorer.register(
            "prov-1",
            lambda: ProviderView("prov-1", "LLM", health="healthy", capabilities=("completion",)),
        )
        assert explorer.observe("prov-1")["capabilities"] == ["completion"]


# ---------------------------------------------------------------------------
# WP-06 Operational Context
# ---------------------------------------------------------------------------

class TestOperationalContext:
    def test_context_manager(self):
        manager = ContextManager()
        ctx = manager.update(mission_id="m1", investigation_id="inv-1")
        assert ctx.mission_id == "m1"
        assert ctx.investigation_id == "inv-1"

    def test_context_consistent(self):
        manager = ContextManager()
        manager.update(mission_id="m1")
        ctx = manager.update(investigation_id="inv-2")
        # mission tetap dipertahankan
        assert ctx.mission_id == "m1"
        assert ctx.investigation_id == "inv-2"


# ---------------------------------------------------------------------------
# WP-07 Workspace API
# ---------------------------------------------------------------------------

class TestWorkspaceAPI:
    def _build(self):
        ws = UnifiedWorkspace()
        sessions = SessionManager()
        citizens = CitizenExplorer()
        runtimes = RuntimeExplorer()
        providers = ProviderExplorer()
        context = ContextManager()
        citizens.register(CitizenInfo("cit-1", "Execution", capabilities=("execute",)))
        api = WorkspaceAPI(
            workspace=ws, sessions=sessions, citizens=citizens,
            runtimes=runtimes, providers=providers, context=context,
        )
        return api

    def test_overview(self):
        api = self._build()
        assert api.overview()["metadata"]["name"] == "SAM Operational Workspace"

    def test_create_session_flow(self):
        api = self._build()
        session = api.create_session(user="op")
        assert session["session_id"]
        updated = api.record_activity(session["session_id"], "investigate")
        assert updated["history"]

    def test_citizens_readonly(self):
        api = self._build()
        assert len(api.citizens()) == 1

    def test_context_via_api(self):
        api = self._build()
        ctx = api.set_context(mission_id="m1")
        assert ctx["mission_id"] == "m1"


# ---------------------------------------------------------------------------
# WP-08 Workspace Explainability
# ---------------------------------------------------------------------------

class TestWorkspaceExplainability:
    def test_explain_view(self):
        explainer = WorkspaceExplainer()
        expl = explainer.explain_view("citizens", capabilities=("execution", "learning"))
        traces = {t.capability_id: t.provided_by for t in expl.capability_traces}
        assert traces["execution"] == "execution_runtime"
        assert traces["learning"] == "operational_learning"


# ---------------------------------------------------------------------------
# WP-09 Workspace Compliance
# ---------------------------------------------------------------------------

class TestWorkspaceCompliance:
    def test_certify_clean(self):
        checker = WorkspaceComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_detects_governance_action(self):
        assert not WorkspaceComplianceChecker().certify(governance=True)["certified"]

    def test_detects_execution(self):
        assert not WorkspaceComplianceChecker().certify(execution=True)["certified"]

    def test_detects_forbidden(self):
        assert not WorkspaceComplianceChecker().certify(source="gate.approve(")["certified"]


# ---------------------------------------------------------------------------
# WP-10 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestWorkspaceEndToEnd:
    def test_end_to_end_workspace(self):
        ws = UnifiedWorkspace()
        sessions = SessionManager()
        citizens = CitizenExplorer()
        runtimes = RuntimeExplorer()
        providers = ProviderExplorer()
        context = ContextManager()

        # Data
        citizens.register(CitizenInfo("exec", "Execution", capabilities=("execute",), health="healthy"))
        citizens.register(CitizenInfo("learn", "Learning", capabilities=("learn",), health="healthy"))
        runtimes.register("rt-1", lambda: RuntimeView("rt-1", "Core", health="healthy"))
        providers.register("prov-1", lambda: ProviderView("prov-1", "LLM", health="healthy"))

        api = WorkspaceAPI(
            workspace=ws, sessions=sessions, citizens=citizens,
            runtimes=runtimes, providers=providers, context=context,
        )

        # Alur: session -> eksplorasi -> context
        session = api.create_session(user="operator")
        assert session["session_id"]
        api.navigate("citizens")
        assert api.citizens()
        assert api.runtimes()
        assert api.providers()
        api.set_context(investigation_id="inv-1")

        # Explainability
        explainer = WorkspaceExplainer()
        expl = explainer.explain_view(
            "overview", capabilities=("execution", "learning", "reasoning", "autonomous", "investigation")
        )
        assert len(expl.capability_traces) == 5

        # Compliance: workspace murni presentation/integration
        checker = WorkspaceComplianceChecker()
        assert checker.certify()["certified"] is True
        assert checker.certify(api_only=True)["certified"] is True
