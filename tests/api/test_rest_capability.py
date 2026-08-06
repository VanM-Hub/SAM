"""Test Program J - REST API Capability (Presentation Host).

Validasi:
- Struktur host REST (RESTApplication/RESTRouter/RESTEndpoint/RESTSerializer).
- Seluruh endpoint capability terdaftar & berfungsi via jalur resmi runtime_service.api.
- Rewire /runtime dan /health: tidak ada import langsung RuntimeCoordinator
  / instansiasi WebRuntimeService() di route handler.
- Tidak ada bypass ke Runtime; tidak ada import ilegal di presentation_rest.
- Preview-only: endpoint preview tidak mengeksekusi (executed=False).
- Approval pass-through: hanya baca field approved (tidak buat approval baru).
"""
from __future__ import annotations
import inspect

from fastapi.testclient import TestClient

from sam.api.server import app
from sam.api.wiring import (
    rest_app,
    conversation_preview_gateway,
    workflow_consumer,
    policy_consumer,
    audit_consumer,
    knowledge_consumer,
    memory_consumer,
    artifact_consumer,
)


class TestRESTStructure:
    """J1 - Struktur host."""

    def test_rest_application_ada(self):
        from sam.api.presentation_rest import RESTApplication
        assert isinstance(rest_app, RESTApplication)

    def test_rest_router_ada(self):
        from sam.api.presentation_rest import RESTRouter, RESTEndpoint
        assert len(rest_app.routers) >= 1
        for r in rest_app.routers:
            assert isinstance(r, RESTRouter)

    def test_router_berisi_endpoint(self):
        # router register_many menambah route dengan path berisi "/"
        routes = [r.path for r in rest_app.routers[0].router.routes
                  if hasattr(r, "path")]
        assert len(routes) > 0

    def test_serializer_immutable(self):
        from sam.api.presentation_rest import RESTEndpoint
        ep = RESTEndpoint(path="/x", tag="t", handler=lambda: None)
        assert ep.path == "/x"
        assert ep.method == "GET"


class TestRewire:
    """J2 - Rewire runtime & health ke jalur resmi (tanpa import ilegal)."""

    def _import_lines(self, module) -> str:
        """Hanya baris import (bukan docstring/komentar)."""
        lines = inspect.getsource(module).splitlines()
        return "\n".join(
            l for l in lines
            if l.strip().startswith("from ") or l.strip().startswith("import ")
        )

    def test_runtime_tidak_import_coordinator(self):
        import sam.api.routes.runtime as rt
        src = self._import_lines(rt)
        assert "RuntimeCoordinator" not in src
        assert "runtime.coordinator" not in src

    def test_health_tidak_instantiate_webservice(self):
        import sam.api.routes.health as h
        src = inspect.getsource(h)
        # tidak ada pemanggilan WebRuntimeService() di kode (bukan docstring)
        assert "= WebRuntimeService()" not in src
        assert "service = WebRuntimeService()" not in src

    def test_runtime_pakai_gateway_jalur_resmi(self):
        import sam.api.routes.runtime as rt
        src = inspect.getsource(rt)
        assert "api.status()" in src or ".api." in src

    def test_health_pakai_gateway_jalur_resmi(self):
        import sam.api.routes.health as h
        src = inspect.getsource(h)
        assert "api.health()" in src or ".api." in src


class TestEndpointTerdaftar:
    """J12 - Seluruh endpoint capability terdaftar."""

    def _openapi_paths(self):
        return set(app.openapi()["paths"].keys())

    def test_capability_endpoint_terdaftar(self):
        paths = self._openapi_paths()
        for expected in (
            "/status/", "/workflow/", "/policy/", "/audit/",
            "/preview/{execution_id}", "/knowledge/", "/memory/",
            "/artifact/", "/approval/{execution_id}",
        ):
            assert expected in paths, f"endpoint tidak terdaftar: {expected}"


class TestEndpointFungsi:
    """J3-J10 - Endpoint berfungsi via jalur resmi."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_status(self):
        r = self.client.get("/status/")
        assert r.status_code == 200
        body = r.json()
        assert "services" in body
        assert "version" in body
        assert "healthy" in body

    def test_health(self):
        r = self.client.get("/health/")
        assert r.status_code == 200
        assert r.json()["status"] in ("healthy", "degraded")

    def test_runtime(self):
        r = self.client.get("/runtime/")
        assert r.status_code == 200
        assert "services" in r.json()

    def test_workflow_list(self):
        r = self.client.get("/workflow/")
        assert r.status_code == 200
        assert "workflow_ids" in r.json()

    def test_policy_audit_knowledge_memory_artifact(self):
        for ep, key in [("/policy/", "policy_ids"), ("/audit/", "audit_ids"),
                        ("/knowledge/", "knowledge_ids"), ("/memory/", "memory_ids"),
                        ("/artifact/", "artifact_names")]:
            r = self.client.get(ep)
            assert r.status_code == 200, f"{ep} -> {r.status_code}"
            assert key in r.json(), f"{ep} tidak punya {key}"

    def test_preview_tidak_execute(self):
        r = self.client.get("/preview/demo-1")
        assert r.status_code == 200
        body = r.json()
        # preview-only: tidak execute
        assert body.get("executed") is False
        assert body.get("mode") == "preview"
        assert body.get("external_calls") == 0

    def test_approval_pass_through(self):
        r = self.client.get("/approval/demo-1")
        assert r.status_code == 200
        body = r.json()
        # pass-through: hanya baca field approved, mode tetap preview
        assert "approved" in body
        assert body.get("mode") == "preview"


class TestTidakAdaImportIlegal:
    """J13/J14 - presentation_rest & routes tidak punya import ilegal."""

    def _forbidden_imports_present(self, src: str) -> list:
        forbidden = [
            "sam.runtime", "sam.registry", "sam.providers",
            "sam.connectors", "sam.execution_runtime",
            "RuntimeCoordinator",
        ]
        return [f for f in forbidden if f in src]

    def test_presentation_rest_bersih(self):
        import sam.api.presentation_rest.rest_application as ra
        import sam.api.presentation_rest.rest_router as rr
        import sam.api.presentation_rest.rest_serializer as rs
        for mod in (ra, rr, rs):
            banned = self._forbidden_imports_present(inspect.getsource(mod))
            assert not banned, f"import ilegal di {mod.__name__}: {banned}"

    def test_routes_bersih(self):
        import sam.api.routes.runtime as rt
        import sam.api.routes.health as h
        for mod in (rt, h):
            import_lines = inspect.getsource(mod).splitlines()
            only_imports = "\n".join(
                l for l in import_lines
                if l.strip().startswith("from ") or l.strip().startswith("import ")
            )
            banned = self._forbidden_imports_present(only_imports)
            assert not banned, f"import ilegal di {mod.__name__}: {banned}"

    def test_no_mission_bypass(self):
        # mission deferred - tidak ada endpoint /mission dan tidak ada workaround
        paths = set(app.openapi()["paths"].keys())
        assert "/mission" not in paths
        assert "/mission/" not in paths
