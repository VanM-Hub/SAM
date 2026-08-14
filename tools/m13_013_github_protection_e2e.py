# M13-013 First External Protection E2E — real GitHub mutation via Ward governance
#
# Alur (semua lewat canonical, tanpa executor kedua):
#   REGISTER -> OBSERVE (read) -> INVESTIGATE (read) -> RECOMMEND (protect)
#   -> APPROVE (operator) -> CANONICAL EXECUTE (m8_002 real create issue)
#   -> VERIFY eksternal (read-back issue) -> AUDIT -> LEARN (subject=ward)
#
# Mutasi nyata: create issue di repo GitHub. Target = repo test private milik Van
# (VanM-Hub/test-issues) — BUKAN repo produksi. Token diambil dari env GITHUB_TOKEN
# (set di SAME exec, dibaca dari file, tidak pernah ditampilkan/tersimpan).
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="VanM-Hub/test-issues")
    ap.add_argument("--title", default="Operational finding detected by SAM (M13-013)")
    ap.add_argument("--owner", default="owner-van")
    ap.add_argument("--out", default="docs/engineering/state/M13-013/evidence.json")
    args = ap.parse_args(argv)

    from sam.ward.identity.models import (WardIdentity, WardOwner, WardAccessScope)
    from sam.ward.entrustment.models import Entrustment, ApprovalPolicy
    from sam.ward.registry.registry import WardRepository
    from sam.ward.governance.boundary import WardGovernanceBoundary
    from sam.ward.governance.governor import WardGovernor
    from sam.ward.capability.contracts import SubjectRef
    from sam.ward.adapters.http_observation import (
        HttpObservationAdapter, InvestigateFromObservation,
    )
    from sam.execution_runtime.real_harness import AuditTrail
    from sam.application.ux.runner import run_github_real_mission

    repo = args.repo
    evidence = {"started_at": _now(), "repo": repo, "title": args.title,
                "steps": [], "audit": [], "mutation": "github.create_issue"}

    # ---- REGISTER Ward (capability protect termasuk) ----
    wrepo = WardRepository()
    ident = WardIdentity.new("repository", repo, seed="github:{}".format(repo))
    wrepo.register(ident, owner=WardOwner(owner_id=args.owner, owner_name="Van"),
                   access_scope=WardAccessScope(scope="github:{}".format(repo),
                                                resource=repo, endpoints=("read", "write")))
    wrepo.set_entrustment(Entrustment(
        ward_id=ident.ward_id, owner_id=args.owner,
        allowed_capabilities=("observe", "investigate", "protect"),
        access_scope="github:{}".format(repo),
        approval_policy=ApprovalPolicy(required=True, approver_role="operator"),
        created_at=_now(), revoked_at=""))
    evidence["steps"].append({"step": "REGISTER", "ward": ident.as_dict()})
    evidence["audit"].append({"step": "register", "verdict": "OK",
                              "subject": ident.as_dict()})
    print("[OK] REGISTER ward_id={}".format(ident.ward_id))

    # ---- GOVERNOR + canonical executor = m8_002 (PROVEN, bukan executor kedua) ----
    audit = AuditTrail()

    def canonical_executor(recommendation, subject):
        """Terjemahkan rekomendasi proteksi Ward -> jalur canonical GitHub mutation.
        Ini ADAPTER ke canonical connector yang sudah terbukti (m8_002); BUKAN
        executor kedua. Hanya action 'protect/create_issue' yang dibuka."""
        action = (recommendation.action if recommendation else "") or ""
        if action not in ("protect", "create_issue"):
            return {"ok": False, "detail": "action {} belum dibuka jalur canonical".format(action)}
        return run_github_real_mission(repo=repo, audit=audit,
                                       artifact_dir="docs/engineering/state/M13-013")

    boundary = WardGovernanceBoundary(wrepo)
    gov = WardGovernor(wrepo, boundary=boundary, canonical_executor=canonical_executor)
    subject = SubjectRef(subject_id=ident.ward_id, subject_type="ward",
                         kind=ident.ward_type, name=ident.name)

    # ---- OBSERVE (read) ----
    # Header Authorization diisi oleh wiring (composition root) dari env runtime;
    # format 'token <tok>' adalah detail connector GitHub, bukan domain.
    gh_auth = os.environ.get("GITHUB_TOKEN", "").strip()
    auth_header = ("token " + gh_auth) if gh_auth else ""
    if auth_header:
        os.environ["GH_AUTH_HEADER"] = auth_header
    try:
        obs = gov.observe(subject, HttpObservationAdapter(
            subject, base_url="https://api.github.com",
            path="repos/{}".format(repo), timeout_seconds=25.0,
            headers_env={"Authorization": "GH_AUTH_HEADER"}))
    finally:
        os.environ.pop("GH_AUTH_HEADER", None)
    evidence["steps"].append({"step": "OBSERVE", "outcome": obs.as_dict()})
    if not (obs.authorized and obs.observation and obs.observation.ok):
        print("[FAIL] observe"); return 1
    evidence["audit"].append({"step": "observe", "verdict": "REAL_OK",
                              "evidence": obs.observation.evidence})
    print("[OK] OBSERVE -> full_name={}".format(
        obs.observation.payload.get("data", {}).get("full_name")))

    # ---- INVESTIGATE (read, pakai evidence observe) ----
    inv = gov.investigate(subject, InvestigateFromObservation(subject),
                          evidence=obs.observation.evidence)
    evidence["steps"].append({"step": "INVESTIGATE", "outcome": inv.as_dict()})
    if not (inv.authorized and inv.investigation):
        print("[FAIL] investigate"); return 1
    evidence["audit"].append({"step": "investigate", "verdict": "OK",
                              "findings": inv.investigation.findings})
    print("[OK] INVESTIGATE -> {}".format(inv.investigation.summary))

    # ---- RECOMMEND (protect) ----
    rec = gov.recommend(subject, action="protect",
                        target="create_issue",
                        rationale="Operational finding: perlu pencatatan. "
                                  "Mutasi relevan dengan protection Ward.")
    evidence["steps"].append({"step": "RECOMMEND", "outcome": rec.as_dict()})
    if not (rec.authorized and rec.recommendation and rec.recommendation.approval_required):
        print("[FAIL] recommend harus require approval"); return 1
    evidence["audit"].append({"step": "recommend", "verdict": "OK",
                              "approval_required": True})
    print("[OK] RECOMMEND -> approval_required=True")

    # ---- APPROVE + CANONICAL EXECUTE (real mutation) ----
    ex = gov.execute(subject, recommendation=rec.recommendation,
                     approved=True, approver=args.owner)
    evidence["steps"].append({"step": "EXECUTE", "outcome": ex.as_dict()})
    evidence["audit"].extend(ex.audit)
    if not (ex.authorized and ex.execution_result and ex.execution_result.get("ok")):
        print("[FAIL] execute"); return 1
    _detail = ""
    for _t in (ex.execution_result.get("timeline") or []):
        _s = _t.get("scrubbed") if isinstance(_t, dict) else None
        if isinstance(_s, dict) and _s.get("detail"):
            _detail = _s["detail"]
            break
    print("[OK] EXECUTE real gitHub mutation -> {}".format(_detail or "ok"))

    # ---- VERIFY eksternal: baca issue via API (independent read-back) ----
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    # number/url issue dari hasil canonical (issue nyata yang dibuat m8_002)
    issue_number = None
    issue_url = ""
    tl = (ex.execution_result or {}).get("timeline") or []
    for t in tl:
        scr = (t.get("scrubbed") or {}) if isinstance(t, dict) else {}
        if isinstance(scr, dict) and scr.get("number"):
            issue_number = scr["number"]
            issue_url = scr.get("issue_url", "")
            break
    verify = {"verified": False, "issue_url": issue_url or "",
              "number": issue_number, "state": ""}
    if tok and issue_number:
        try:
            import httpx
            headers = {"Authorization": "Bearer " + tok,
                       "Accept": "application/vnd.github+json",
                       "User-Agent": "sam-ward"}
            it = httpx.get(
                "https://api.github.com/repos/{}/issues/{}".format(repo, issue_number),
                headers=headers, timeout=25).json()
            verify = {"verified": bool(it.get("number")),
                      "issue_url": it.get("html_url", ""),
                      "number": it.get("number"),
                      "state": it.get("state"),
                      "title": it.get("title")}
        except Exception as e:
            verify["error"] = str(e)
    evidence["steps"].append({"step": "VERIFY_EXTERNAL", "verify": verify})
    evidence["audit"].append({"step": "verify_external", "verdict": "OK" if verify["verified"] else "FAIL",
                              "issue_url": verify.get("issue_url"),
                              "number": verify.get("number")})
    print("[{}] VERIFY external -> #{}".format(
        "OK" if verify["verified"] else "FAIL", verify))

    # ---- LEARN (experience dengan subject ward) ----
    learn = {"subject_id": ident.ward_id, "subject_type": "ward",
             "observation": "operational finding", "action": "protect/create_issue",
             "outcome": "recorded" if verify["verified"] else "failed",
             "evidence": verify["verified"], "confidence": 0.95}
    evidence["steps"].append({"step": "LEARN", "learn": learn})
    evidence["audit"].append({"step": "learn", "verdict": "OK", "subject_type": "ward"})
    print("[OK] LEARN -> subject_type=ward, action=protect/create_issue")

    evidence["finished_at"] = _now()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)
    print("[OK] EVIDENCE -> {}".format(args.out))

    ok = verify["verified"] and ex.authorized and bool(ex.execution_result.get("ok"))
    print("[VERDICT] M13-013 {}".format("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
