# -*- coding: utf-8 -*-
"""IP-3.5-001 Platform Workspace - Certification (WP-01..08).

Menguji: Unified Platform Model (WP-01), Navigation (WP-02), Perspective
Management (WP-03), Context Preservation (WP-04), Layout Model (WP-05),
Workspace Descriptor (WP-06), Workspace API (WP-07), Compliance (WP-08).

Guardrail yang diverifikasi (PEX-01..10 di compliance.py) diuji lewat
compliance_check + assertion presentasi-passive (tidak ada eksekusi).
"""

import pytest

from sam.platform import (
    compliance_check,
    ContextStore,
    LayoutModel,
    NavigationModel,
    NavigationRoute,
    PanelSlot,
    Perspective,
    PerspectiveBinding,
    PerspectiveRegistry,
    PerspectiveState,
    PlatformDomain,
    WorkspaceAPI,
    WorkspaceContext,
    WorkspaceDescriptor,
    WorkspaceModel,
    build_domain,
    build_navigation,
    build_perspective,
    default_workspace,
    descriptor_from_model,
)


# --- WP-01 Unified Platform Model ------------------------------------------

def test_model_build_and_query():
    m = WorkspaceModel(name="T", version="1.0.0")
    m = build_domain(m, PlatformDomain("a", "Alpha", source_package="sam.x"))
    m = build_domain(m, PlatformDomain("b", "Beta", source_package="sam.y"))
    m = build_perspective(m, Perspective("p1", "P1", bindings=(
        PerspectiveBinding("a", "overview"),
        PerspectiveBinding("b", "detail"),
    )))
    assert m.domain_keys() == ("a", "b")
    assert m.perspective_keys() == ("p1",)
    assert m.perspective("p1").roles_for("b") == ("detail",)
    assert m.domain("a").source_package == "sam.x"


def test_model_domain_required_key():
    with pytest.raises(ValueError):
        PlatformDomain("", "X")


def test_model_rejects_duplicate():
    m = WorkspaceModel(name="T")
    m = build_domain(m, PlatformDomain("a", "A"))
    with pytest.raises(ValueError):
        build_domain(m, PlatformDomain("a", "A2"))


def test_model_rejects_unknown_binding():
    m = WorkspaceModel(name="T")
    with pytest.raises(ValueError):
        build_perspective(m, Perspective("p", "P", bindings=(
            PerspectiveBinding("ghost", "overview"),
        )))


def test_model_immutable():
    m = WorkspaceModel(name="T", domains=(PlatformDomain("a", "A"),))
    with pytest.raises(Exception):
        m.domains = ()  # frozen


# --- WP-02 Navigation -------------------------------------------------------

def test_navigation_routes():
    nav = build_navigation((
        NavigationRoute("root", label="Home"),
        NavigationRoute("m", domain="mission", parent="root", label="Mission"),
        NavigationRoute("m2", domain="mission", parent="m", label="Sub"),
    ))
    assert nav.route("m").domain == "mission"
    assert nav.children_of("root")[0].route_id == "m"
    assert nav.routes_for_domain("mission")[0].route_id == "m"
    # deterministik
    assert nav.route_ids() == tuple(sorted(nav.route_ids()))


# --- WP-03 Perspective Management ------------------------------------------

def test_perspective_registry_order():
    reg = PerspectiveRegistry(perspectives=("b", "a", "c"), display_order=("c", "a"))
    # c, a urut sesuai display_order; b menyusul alfabetis
    assert reg.ordered() == ("c", "a", "b")


def test_perspective_state_select():
    st = PerspectiveState(active="overview", default="overview", available=("overview", "ops"))
    assert st.select("ops").active == "ops"
    # invalid fallback ke default (bukan error)
    assert st.select("nope").active == "overview"
    assert st.reset().active == "overview"


# --- WP-04 Context Preservation --------------------------------------------

def test_context_preservation():
    store = ContextStore()
    store.set("s1", WorkspaceContext(perspective="ops").push_crumb("home").push_crumb("mission"))
    assert store.get("s1").crumb_path() == ("home", "mission")
    assert store.get("s1").pop_crumb().crumb_path() == ("home",)
    assert store.get("missing") == WorkspaceContext()
    store.clear("s1")
    assert "s1" not in store.keys()
    assert len(store) == 0


# --- WP-05 Layout Model -----------------------------------------------------

def test_layout_panels_ordered():
    lay = LayoutModel(
        layout_id="L",
        regions=("header", "main"),
        panels=(
            PanelSlot("b", "main", domain="x", priority=1),
            PanelSlot("a", "main", domain="x", priority=10),
            PanelSlot("h", "header", domain="y", priority=5),
        ),
    )
    assert lay.panels_in("main")[0].slot_id == "a"  # priority desc
    assert lay.region_order() == ("header", "main")


# --- WP-06 Workspace Descriptor --------------------------------------------

def test_descriptor_from_model():
    m = WorkspaceModel(name="W", version="2.0.0")
    m = build_domain(m, PlatformDomain("a", "A"))
    d = descriptor_from_model(m, source_packages=("sam.x",))
    assert isinstance(d, WorkspaceDescriptor)
    assert d.workspace_name == "W"
    assert d.has_domain("a")
    assert d.summary_dict()["domain_count"] == 1


# --- WP-07 Workspace API (read-only facade) --------------------------------

def test_default_workspace():
    ws = default_workspace()
    assert "mission" in ws.domains()
    assert "ecosystem" in ws.perspectives()
    snap = ws.snapshot()
    assert snap.model_name == "SAM Platform"
    assert snap.layout.regions  # punya layout
    assert ws.descriptor.has_domain("federation")


def test_workspace_select_perspective_only_view():
    ws = default_workspace()
    ws.select_perspective("default", "operations")
    snap = ws.snapshot("default")
    assert snap.active_perspective == "operations"


def test_workspace_routes():
    ws = default_workspace()
    assert ws.routes_for_domain("mission")  # ada rute mission


# --- WP-08 Compliance -------------------------------------------------------

def test_compliance_passes():
    res = compliance_check()
    assert res.ok, res.messages
    assert res.group == "PEX"
    assert res.forbidden_found == ()


def test_compliance_catches_execution_token(tmp_path):
    # pastikan scanner mendeteksi token eksekusi yang dilarang
    src_dir = tmp_path / "sam" / "platform"
    src_dir.mkdir(parents=True)
    (src_dir / "bad.py").write_text(
        "def run():\n    return execute('x')\n",
        encoding="utf-8",
    )
    res = compliance_check(source_files=[str(src_dir / "bad.py")])
    assert not res.ok
    assert "execute" in res.forbidden_found


# --- Exit criteria: presentation-passive (tidak ada eksekusi) ---------------

def test_workspace_has_no_autority_verbs():
    # API tidak boleh mengekspos metode eksekusi/orchestration
    names = [n for n in dir(WorkspaceAPI) if not n.startswith("_")]
    forbidden = {"execute", "orchestrate", "schedule", "run_workflow",
                 "start_collaboration", "activate_remote"}
    assert not (forbidden & set(names))
