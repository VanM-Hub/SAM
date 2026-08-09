# -*- coding: utf-8 -*-
"""IP-3.5-005 Platform Integration - Certification (WP-29..33).

Menguji: E2E Integration (WP-29), Regression Gate (WP-30), Compliance Gate
(WP-31), Certification Gate (WP-32), Production Readiness (WP-33).

Guardrail (IP-3.5): Integrasi menyatukan keempat experience menjadi satu
PlatformPresentation (read/assemble only). Tidak menambah governance/authority.
"""

import pytest

from sam.platform import (
    CitizenExperienceAPI,
    ExplainabilityAPI,
    GateResult,
    IntegrationCertification,
    MissionAPI,
    MissionInput,
    MissionTimelineInput,
    PlatformEngine,
    PlatformPresentation,
    ReadinessAttributes,
    certification_gate,
    compliance_gate,
    default_workspace,
    production_readiness_check,
    regression_gate,
)


def _full_engine():
    from sam.platform import CitizenInput, EvidenceInput
    ws = default_workspace()
    mission = MissionAPI()
    mission.register_mission(MissionInput("m1", "Alpha", state="active", progress=0.5))
    mission.register_timeline(MissionTimelineInput("m1", ("plan", "build")))
    citizen = CitizenExperienceAPI()
    citizen.register_citizen(CitizenInput("c1", "agent", "A", "1.0",
                                          capabilities=("observe",)))
    expl = ExplainabilityAPI()
    expl.register_evidence(EvidenceInput("e1", "governance", "DECISION_OUTCOME",
                                         "VERIFIED", "x"))
    return PlatformEngine(ws, mission=mission, citizen=citizen, explainability=expl)
    from sam.platform import CitizenInput, EvidenceInput
    ws = default_workspace()
    mission = MissionAPI()
    mission.register_mission(MissionInput("m1", "Alpha", state="active", progress=0.5))
    mission.register_timeline(MissionTimelineInput("m1", ("plan", "build")))
    citizen = CitizenExperienceAPI()
    citizen.register_citizen(CitizenInput("c1", "agent", "A", "1.0",
                                          capabilities=("observe",)))
    expl = ExplainabilityAPI()
    expl.register_evidence(EvidenceInput("e1", "governance", "DECISION_OUTCOME",
                                         "VERIFIED", "x"))
    return PlatformEngine(ws, mission=mission, citizen=citizen, explainability=expl)


# --- WP-29 E2E integration ---------------------------------------------------

def test_engine_present_full():
    engine = _full_engine()
    pres = engine.present()
    assert isinstance(pres, PlatformPresentation)
    assert pres.summary_keys() == ("workspace", "mission", "citizen", "explainability")
    assert pres.has_mission and pres.has_citizen and pres.has_explainability
    assert pres.workspace.model_name  # workspace terpasang
    assert pres.mission.title == "Alpha"


def test_engine_coverage_order_deterministic():
    engine = _full_engine()
    assert engine.coverage() == ("platform", "mission", "citizen", "explainability")


def test_engine_without_optional_experiences():
    from sam.platform import PlatformEngine as PE
    ws = default_workspace()
    engine = PE(ws)  # hanya workspace
    pres = engine.present()
    assert not pres.has_mission
    assert pres.summary_keys() == ("workspace",)
    assert pres.workspace.model_name


# --- WP-30 Regression gate ---------------------------------------------------

def test_regression_gate_all_pass():
    g = regression_gate([("platform", True), ("citizen", True)])
    assert g.ok
    assert g.verdict == "PASS"
    assert g.name == "regression"


def test_regression_gate_fails_on_any_fail():
    g = regression_gate([("platform", True), ("citizen", False)])
    assert not g.ok
    assert g.verdict == "FAIL"


# --- WP-31 Compliance gate ---------------------------------------------------

def test_compliance_gate_passes():
    g = compliance_gate()
    assert g.ok
    assert g.name == "compliance"
    assert "PEX/MEX/CX/EX all pass" in g.details


# --- WP-32 Certification gate ------------------------------------------------

def test_certification_all_gates():
    c = certification_gate(regression=True, compliance=True, readiness=True)
    assert c.certified
    assert c.summary == ("regression=PASS", "compliance=PASS", "readiness=PASS")


def test_certification_not_when_any_fails():
    c = certification_gate(regression=False, compliance=True, readiness=True)
    assert not c.certified


# --- WP-33 Production readiness ---------------------------------------------

def test_readiness_pass_with_structure():
    r = production_readiness_check(
        ReadinessAttributes(api_count=4, domain_count=7, perspective_count=5))
    assert r.ok
    assert "presentation-passive" in r.details[0]


def test_readiness_fails_without_apis():
    r = production_readiness_check(ReadinessAttributes(api_count=0))
    assert not r.ok
    assert "tidak ada API" in r.details


def test_readiness_fails_if_not_passive():
    r = production_readiness_check(
        ReadinessAttributes(api_count=2, domain_count=3, perspective_count=2,
                            presentation_passive=False))
    assert not r.ok
    assert "presentation bukan passive" in r.details


# --- Exit criteria: integration presentation-passive -------------------------

def test_engine_has_no_execution_verbs():
    names = [n for n in dir(PlatformEngine) if not n.startswith("_")]
    forbidden = {"execute", "orchestrate", "schedule", "run", "approve"}
    assert not (forbidden & set(names))
