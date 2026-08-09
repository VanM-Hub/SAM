# -*- coding: utf-8 -*-
"""IP-3.5-003 Citizen Experience - Certification (WP-17..23).

Menguji: Citizen Workspace (WP-17), Federation Workspace (WP-18),
Collaboration Workspace (WP-19), Compatibility Workspace (WP-20),
Certification Workspace (WP-21), Unified Citizen/Federation UX (WP-22),
Citizen Compliance (WP-23).

Guardrail (MISSION-3.5): Citizen Experience PRESENTS citizen/federation,
TIDAK memodifikasi citizens, TIDAK mengeksekusi aksi citizen/federation.
Seluruh data DIBERIKAN dari luar (governed capability API), bukan ditarik.
"""

import pytest

from sam.platform import (
    CertificationStatus,
    CertificationWorkspaceView,
    CitizenExperienceAPI,
    CitizenInput,
    CitizenSnapshot,
    CitizenWorkspaceView,
    CollaborationInput,
    CollaborationWorkspaceView,
    CompatibilityAssessment,
    FederationInput,
    FederationMemberInput,
    FederationWorkspaceView,
    assess_compatibility,
    build_certification_view,
    build_citizen_view,
    build_federation_view,
    citizen_compliance_check,
)


# --- WP-17 Citizen Workspace ------------------------------------------------

def test_citizen_requires_id():
    with pytest.raises(ValueError):
        CitizenInput(identity_id="")


def test_citizen_view_lookup_and_by_kind():
    cits = (CitizenInput("c1", "agent", "A", capabilities=("x",)),
            CitizenInput("c2", "analyst", "B"))
    view = build_citizen_view(cits)
    assert view.citizen("c2").name == "B"
    assert view.citizen("ghost") is None
    assert view.by_kind("agent")[0].identity_id == "c1"
    assert view.count == 2


# --- WP-18 Federation Workspace ---------------------------------------------

def test_federation_trusted_untrusted():
    fed = FederationInput("f1", (
        FederationMemberInput("m1", "A", trusted=True),
        FederationMemberInput("m2", "B", trusted=False),
    ))
    assert len(fed.trusted_members()) == 1
    assert len(fed.untrusted_members()) == 1


def test_federation_view_aggregate():
    v = build_federation_view((
        FederationInput("f1", (FederationMemberInput("m1"), FederationMemberInput("m2"))),
        FederationInput("f2", (FederationMemberInput("m3"),)),
    ))
    assert v.federation_count() == 2
    assert v.total_members() == 3
    assert v.federation("f2") is not None
    assert v.federation("ghost") is None


# --- WP-19 Collaboration Workspace ------------------------------------------

def test_collaboration_view():
    v = CollaborationWorkspaceView(collaborations=(
        CollaborationInput("col1", "X", "active", ("a", "b")),
    ))
    assert v.count() == 1
    assert v.collaboration("col1").status == "active"
    assert v.collaboration("nope") is None


# --- WP-20 Compatibility Workspace ------------------------------------------

def test_compat_assessment_satisfied():
    a = assess_compatibility("src", "tgt", ("x", "y"), ("x", "y", "z"))
    assert a.compatible
    assert a.verdict == "compatible"


def test_compat_assessment_missing_required():
    a = assess_compatibility("src", "tgt", ("x", "y"), ("x",), required=("x", "y"))
    assert not a.compatible
    assert "y" in a.rationale  # sebut capability yang kurang


def test_immutable_compat():
    a = assess_compatibility("s", "t", ("x",), ("x",))
    with pytest.raises(Exception):
        a.compatible = False  # frozen


# --- WP-21 Certification Workspace ------------------------------------------

def test_certification_view():
    c = (CertificationStatus("c1", "t1", True), CertificationStatus("c2", "t2", False))
    v = build_certification_view(c)
    assert v.count() == 2
    assert v.certified_count() == 1
    assert [x.certified for x in v.certifications] == [True, False]  # sort id


# --- WP-22 Unified Citizen/Federation UX ------------------------------------

def _setup_api():
    api = CitizenExperienceAPI()
    api.register_citizen(CitizenInput("c1", "agent", "Alpha", "1.0",
                                      capabilities=("observe", "execute")))
    api.register_citizen(CitizenInput("c2", "analyst", "Beta", "2.0",
                                      capabilities=("observe", "report")))
    api.register_federation(FederationInput("f1", (
        FederationMemberInput("c1", "Alpha", ("observe",), trusted=True),
        FederationMemberInput("c2", "Beta", ("observe",), trusted=False),
    )))
    api.register_collaboration(CollaborationInput("col1", "A-B", "active", ("c1", "c2")))
    api.register_certification(CertificationStatus("cert1", "c1", True))
    return api


def test_api_snapshot_counts():
    api = _setup_api()
    snap = api.snapshot()
    assert isinstance(snap, CitizenSnapshot)
    assert snap.citizen_count == 2
    assert snap.federation_count == 1


def test_api_compat_uses_registered_capabilities():
    api = _setup_api()
    a = api.compat("c1", "c2", required=("observe",))
    assert a.compatible
    a2 = api.compat("c1", "c2", required=("report", "execute"))
    assert not a2.compatible  # c2 tidak punya execute


def test_api_views():
    api = _setup_api()
    assert api.citizen_view().count == 2
    assert api.federation_view().federation_count() == 1
    assert api.collaboration_view().count() == 1
    assert api.certification_view().certified_count() == 1
    assert api.count_citizens() == 2
    assert api.count_federations() == 1


# --- WP-23 Citizen Compliance -----------------------------------------------

def test_citizen_compliance_passes():
    res = citizen_compliance_check()
    assert res.ok, res.messages
    assert res.group == "CX"
    assert res.forbidden_found == ()


# --- Exit criteria: presentation-passive citizen ----------------------------

def test_citizen_api_has_no_action_verbs():
    names = [n for n in dir(CitizenExperienceAPI) if not n.startswith("_")]
    forbidden = {"approve_citizen", "modify_citizen", "start_collaboration",
                 "issue_certification", "certify", "negotiate", "join_federation"}
    assert not (forbidden & set(names))
