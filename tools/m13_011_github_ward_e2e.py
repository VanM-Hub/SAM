# M13-011/012 Real First Ward + External Investigation E2E
# Ward #1 = GitHub Repository VanM-Hub/SAM
#
# Flow REAL (tanpa mutation):
#   REGISTER -> OBSERVE (GitHub public API read) -> INVESTIGATE -> REPORT -> AUDIT
#
# Menggunakan WardGovernor (Universal Governance Engine) + HttpObservationAdapter
# (canonical read) + WardGovernanceBoundary (authorization). TIDAK membuat
# executor kedua; TIDAK menyimpan authority sendiri; mutation TIDAK dilakukan.
#
# Jalankan:
#   python -B tools/m13_011_github_ward_e2e.py [--target VanM-Hub/SAM]
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="VanM-Hub/SAM")
    ap.add_argument("--out", default="docs/engineering/state/M13-011/evidence.json")
    ap.add_argument("--owner", default="owner-van")
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

    target = args.target
    evidence = {"started_at": _now(), "target": target, "steps": [], "audit": [],
                "mutation": "NONE"}

    # ---- REGISTER ----
    repo = WardRepository()
    ident = WardIdentity.new("repository", target, seed="github:{}".format(target))
    repo.register(ident, owner=WardOwner(owner_id=args.owner, owner_name="Van"),
                  access_scope=WardAccessScope(
                      scope="github:{}".format(target), resource=target,
                      endpoints=("read",)))
    # Konsen (entrustment) - observation + investigate (read only) + protect (mutation, tidak dipakai)
    repo.set_entrustment(Entrustment(
        ward_id=ident.ward_id, owner_id=args.owner,
        allowed_capabilities=("observe", "investigate", "protect"),
        access_scope="github:{}".format(target),
        approval_policy=ApprovalPolicy(required=True, approver_role="operator"),
        created_at=_now(), revoked_at=""))
    evidence["steps"].append({"step": "REGISTER", "ward": ident.as_dict()})
    evidence["audit"].append({"step": "register", "verdict": "OK",
                              "subject": ident.as_dict()})
    print("[OK] REGISTER ward_id={}".format(ident.ward_id))

    # ---- GOVERNOR + BOUNDARY ----
    boundary = WardGovernanceBoundary(repo)
    gov = WardGovernor(repo, boundary=boundary)
    subject = SubjectRef(subject_id=ident.ward_id, subject_type="ward",
                         kind=ident.ward_type, name=ident.name)

    # ---- OBSERVE (real GitHub public API read) ----
    helper = HttpObservationAdapter(
        subject,
        base_url="https://api.github.com",
        path="repos/{}".format(target),
        timeout_seconds=25.0)
    obs = gov.observe(subject, helper)
    evidence["steps"].append({"step": "OBSERVE", "outcome": obs.as_dict()})
    obs_err = ""
    if not obs.authorized or not obs.observation or not obs.observation.ok:
        obs_err = "observation not ok"
    else:
        evidence["audit"].append({"step": "observe", "verdict": "REAL_OK",
                                  "subject": subject.as_dict(),
                                  "evidence": obs.observation.evidence})
        print("[OK] OBSERVE real gitHub -> full_name={} private={} open_issues={}".format(
            obs.observation.payload.get("data", {}).get("full_name"),
            obs.observation.payload.get("data", {}).get("private"),
            obs.observation.payload.get("data", {}).get("open_issues_count")))

    # ---- INVESTIGATE (reuse contract; konsumsi evidence dari OBSERVE) ----
    obs_evidence = obs.observation.evidence if (obs.observation and obs.observation.ok) else {}
    inv = gov.investigate(subject, InvestigateFromObservation(subject),
                          evidence=obs_evidence)
    evidence["steps"].append({"step": "INVESTIGATE", "outcome": inv.as_dict()})
    if inv.authorized and inv.investigation:
        evidence["audit"].append({"step": "investigate", "verdict": "OK",
                                  "findings": inv.investigation.findings})
        print("[OK] INVESTIGATE -> {}".format(inv.investigation.summary))

    # ---- REPORT ----
    report = {
        "subject": subject.as_dict(),
        "observed": obs.observation.as_dict() if obs.observation else None,
        "investigation": inv.investigation.as_dict() if inv.investigation else None,
        "mutation": "NONE",
        "timestamp": _now(),
    }
    evidence["steps"].append({"step": "REPORT", "report": report})
    evidence["report"] = report
    evidence["finished_at"] = _now()

    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)
    print("[OK] REPORT -> {}".format(args.out))

    # ---- Verdict ----
    ok = (obs.authorized and obs.observation and obs.observation.ok
          and inv.authorized and inv.investigation and inv.investigation.successful
          and not obs_err)
    print("[VERDICT] M13-011/012 {}".format("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
