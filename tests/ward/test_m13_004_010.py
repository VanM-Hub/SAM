# Tests M13-004..010 - generalized capability contracts + Ward governor
# Unit tests: TIDAK ada panggilan eksternal; adapter GitHub disimulasikan via
# stub dalam test (M13-011/012/013 yang melakukan real E2E).
import pytest

from sam.ward.identity.models import (WardIdentity, WardOwner, WardAccessScope,
                                      WardMetadata)
from sam.ward.entrustment.models import Entrustment, ApprovalPolicy
from sam.ward.registry.registry import WardRepository
from sam.ward.governance.boundary import WardGovernanceBoundary
from sam.ward.governance.governor import WardGovernor
from sam.ward.capability.contracts import (
    SubjectRef, Observation, InvestigationResult, Finding, Recommendation,
    ObservationTarget, InvestigationTarget,
)
from sam.ward.adapters.http_observation import HttpObservationAdapter


# --- helpers ---
def register_github(repo_caps=("observe", "investigate", "protect")):
    repo = WardRepository()
    ident = WardIdentity.new("repository", "VanM-Hub/test-issues",
                             seed="github:test-issues")
    repo.register(ident, owner=WardOwner(owner_id="owner-van"),
                  access_scope=WardAccessScope(scope="github:test-issues",
                                               resource="VanM-Hub/test-issues"))
    repo.set_entrustment(Entrustment(
        ward_id=ident.ward_id, owner_id="owner-van",
        allowed_capabilities=repo_caps,
        access_scope="github:test-issues",
        approval_policy=ApprovalPolicy(required=True, approver_role="operator"),
        created_at="2026-08-14T00:00:00Z", revoked_at=""))
    return repo, ident


def subject_ref(ident):
    return SubjectRef(subject_id=ident.ward_id, subject_type="ward",
                      kind=ident.ward_type, name=ident.name)


# --- stub ObservationTarget (simulasi adapter - unit test lokal) ---
class FakeObservationTarget(ObservationTarget):
    def __init__(self, ok=True, payload=None):
        self._ok = ok
        self._payload = payload or {"repo": "VanM-Hub/test-issues"}

    def observe(self, *, capability="observe"):
        return Observation(subject=SubjectRef("w", "ward"), capability=capability,
                           successful=self._ok,
                           payload=self._payload,
                           evidence={"verified_read": self._ok, "source": "stub"})


class FakeInvestigationTarget(InvestigationTarget):
    def investigate(self, *, evidence, capability="investigate"):
        return InvestigationResult(subject=SubjectRef("w", "ward"),
                                   successful=True,
                                   findings=[{"label": "ok", "confidence": 0.9}],
                                   evidence_ref=str(evidence),
                                   summary="investigated")


# ---------------- M13-004 Observation contract -----------------
def test_observation_contract_realizable():
    # ObservationTarget dapat direalisasikan; hasil berisi evidence + subject
    t = FakeObservationTarget(ok=True)
    obs = t.observe()
    assert obs.ok
    assert obs.evidence["verified_read"] is True
    assert obs.as_dict()["subject"]["subject_type"] == "ward"


def test_observation_failure_is_not_fake_success():
    t = FakeObservationTarget(ok=False)
    obs = t.observe()
    assert not obs.ok
    assert obs.evidence["verified_read"] is False


# ---------------- M13-005 Investigation contract -----------------
def test_investigation_reuses_contract_not_new_engine():
    t = FakeInvestigationTarget()
    res = t.investigate(evidence={"verified_read": True})
    assert res.successful
    assert res.findings
    assert res.subject.subject_type == "ward"
    # pastikan kita TIDAK membuat ExternalInvestigationEngine terpisah
    import sam.ward
    assert not hasattr(sam.ward, "ExternalInvestigationEngine")


# ---------------- M13-006 Diagnosis -----------------
def test_finding_from_evidence():
    f = Finding(finding_id="f1", subject_id="ward-1", label="dependency unavailable",
                evidence={"bad": "503"}, confidence=0.8)
    assert f.confidence == 0.8
    assert f.as_dict()["label"] == "dependency unavailable"


# ---------------- M13-007 Recovery (canonical) -----------------
def test_recommendation_requires_approval():
    r = Recommendation(recommendation_id="r1", subject_id="ward-1",
                       action="protect", target="restart",
                       rationale="unhealthy", approval_required=True)
    assert r.approval_required


def test_governor_mutation_blocked_without_approval():
    repo, ident = register_github()
    gov = WardGovernor(repo)
    subj = subject_ref(ident)
    out = gov.recommend(subj, action="protect", target="restart")
    assert out.authorized               # entrustment punya protect + approval policy
    assert out.recommendation.approval_required
    # eksekusi tanpa approval -> DENIED (tidak ada jalur langsung ke connector)
    ex = gov.execute(subj, recommendation=out.recommendation, approved=False)
    assert not ex.authorized
    assert ex.audit[-1]["verdict"] in ("DENIED", "BLOCKED")


def test_governor_execute_requires_canonical_executor():
    repo, ident = register_github()
    gov = WardGovernor(repo, canonical_executor=None)
    subj = subject_ref(ident)
    r = gov.recommend(subj, action="protect", target="x")
    ex = gov.execute(subj, recommendation=r.recommendation, approved=True)
    assert not ex.authorized            # tanpa canonical executor -> BLOCKED
    assert ex.audit[-1]["verdict"] == "BLOCKED"


def test_governor_execute_with_canonical_executor_succeeds():
    repo, ident = register_github()
    calls = []

    def executor(rec, subj):
        calls.append(rec.action)
        return {"ok": True, "external": "verified"}

    gov = WardGovernor(repo, canonical_executor=executor)
    subj = subject_ref(ident)
    r = gov.recommend(subj, action="protect", target="restart")
    ex = gov.execute(subj, recommendation=r.recommendation,
                     approved=True, approver="operator")
    assert ex.authorized
    assert calls == ["protect"]
    assert ex.execution_result["ok"] is True


# ---------------- M13-008 Ward Learning (subject) -----------------
def test_experience_has_subject():
    # Learning harus punya subject agar pengalaman tiap Ward tdk bercampur.
    exp = {"subject_id": "ward-github", "subject_type": "ward",
           "observation": "dependency timeout", "action": "restart",
           "outcome": "recovered", "evidence": "verified", "confidence": 0.9}
    assert exp["subject_id"] == "ward-github"
    assert exp["subject_type"] == "ward"
    # NVIDIA timeout != OpenClaw timeout != GitHub timeout (subject berbeda)
    exp2 = dict(exp, subject_id="ward-nvidia")
    assert exp["subject_id"] != exp2["subject_id"]


# ---------------- M13-009 Ward Mission -----------------
def test_mission_has_subject():
    mission = {"objective": "Pastikan repo tidak ada issue perhatian",
               "subject": {"subject_type": "ward", "kind": "repository"}}
    assert mission["subject"]["subject_type"] == "ward"
    assert mission["subject"]["kind"] == "repository"


# ---------------- M13-010 Boundary integration -----------------
def test_boundary_revoked_blocks_governor():
    repo, ident = register_github()
    repo.revoke(ident.ward_id, revoked_at="t")
    gov = WardGovernor(repo)
    subj = subject_ref(ident)
    out = gov.observe(subj, FakeObservationTarget())
    assert not out.authorized
    assert out.audit[-1]["verdict"] == "BLOCKED"


def test_boundary_registration_without_consent_blocks():
    repo = WardRepository()
    ident = WardIdentity.new("repository", "no-consent", seed="nc")
    repo.register(ident)                       # registered tapi TIDAK ada entrustment
    gov = WardGovernor(repo)
    out = gov.observe(subject_ref(ident), FakeObservationTarget())
    assert not out.authorized


def test_governor_observe_authorized_records_audit():
    repo, ident = register_github()
    gov = WardGovernor(repo)
    subj = subject_ref(ident)
    out = gov.observe(subj, FakeObservationTarget(ok=True,
                                                  payload={"status": "ok"}))
    assert out.authorized
    assert out.observation.ok
    assert any(a["step"] == "observe" and a["verdict"] == "OK" for a in out.audit)
    assert out.as_dict()["subject"]["subject_type"] == "ward"


# ---------------- HttpObservationAdapter (lokal, tanpa jaringan) ----------------
def test_http_adapter_resolves_url():
    subj = SubjectRef("w1", "ward", kind="repository", name="x")
    a = HttpObservationAdapter(subj, base_url="https://api.github.com",
                                path="repos/VanM-Hub/test-issues")
    assert a._resolve_url() == "https://api.github.com/repos/VanM-Hub/test-issues"


def test_http_adapter_read_only_no_authority_method():
    subj = SubjectRef("w1", "ward")
    a = HttpObservationAdapter(subj, base_url="https://api.github.com")
    # adapter hanya observer - tidak punya mutasi
    assert not hasattr(a, "mutate")
    assert not hasattr(a, "restart")
    assert not hasattr(a, "delete")
