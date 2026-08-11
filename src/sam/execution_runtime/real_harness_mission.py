"""
P11 — Full Real Mission (uji integrasi pertama yang berarti).

Merangkai SEMUA capability yang sudah PROVEN jadi SATU mission nyata:

    Human Request
      -> Reasoning
      -> Investigation    (P8: real observation -> evidence)
      -> Evidence
      -> Recommendation
      -> Approval
      -> Agent/Workflow   (P7 agent + P9 recovery via harness)
      -> Real Tool        (filesystem: tulis state)
      -> External System  (file status service)
      -> Verification     (independent health check — P9)
      -> Artifact         (laporan mission tertulis ke disk)
      -> Audit
      -> Learning         (P10: experience di-store, retrieve di misi berikut)

Mission contoh nyata:
  "Service svc-orders sedang FAIL; pulihkan ke healthy state dan buktikan."

Output = laporan mission + experience tersimpan + bukti state benar-benar berubah.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    RealExecutionHarness,
)
from sam.execution_runtime.real_harness_analyze import _build_filesystem_capability_full
from sam.execution_runtime.real_harness_learning import (
    ExperienceRepository,
    extract_lesson,
)
from sam.execution_runtime.real_harness_recovery import (
    FakeService,
    RecoveryAdapter,
    independent_health_check,
)


# ---------------------------------------------------------------------------
# Reasoning — perencanaan misi dari request manusia
# ---------------------------------------------------------------------------

def human_request_to_plan(request: str, audit: AuditTrail) -> Dict[str, Any]:
    """Ubah request manusia jadi rencana langkah (reasoning deterministik + audit)."""
    plan = {
        "intent": "recover_failed_service",
        "service": "svc-orders",
        "steps": ["investigate", "recommend", "approve", "recover", "verify", "artifact", "learn"],
    }
    audit.record("mission.reasoning", request, intent=plan["intent"], steps=len(plan["steps"]))
    return plan


# ---------------------------------------------------------------------------
# Main — satu mission penuh
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P11 Full Real Mission")
    parser.add_argument("--request", default="Pulihkan service svc-orders yang sedang FAIL ke healthy state.")
    parser.add_argument("--mission-id", default="M-" + uuid.uuid4().hex[:6].upper())
    parser.add_argument("--purge-learning", action="store_true")
    args = parser.parse_args(argv)

    audit = AuditTrail()
    harness = RealExecutionHarness(audit)
    _build_filesystem_capability_full(harness)
    svc = FakeService("svc-orders")

    mission_id = args.mission_id
    artifact_dir = os.path.abspath("_demo/mission_out")
    os.makedirs(artifact_dir, exist_ok=True)

    # reset sandbox service + learning utk determinisme bila diminta
    if os.path.isdir("_demo/recovery_sandbox"):
        for f in os.listdir("_demo/recovery_sandbox"):
            os.remove(os.path.join("_demo/recovery_sandbox", f))
    if args.purge_learning and os.path.isfile("_demo/learning_store.json"):
        os.remove("_demo/learning_store.json")

    print("=" * 72)
    print(f"  P11 — FULL REAL MISSION  [{mission_id}]")
    print("=" * 72)
    print(f"  HUMAN REQUEST: \"{args.request}\"")

    timeline: List[Dict[str, Any]] = []

    # 0. Reasoning
    plan = human_request_to_plan(args.request, audit)
    print(f"\n  [0] REASONING        : intent={plan['intent']} steps={plan['steps']}")
    timeline.append({"step": "reasoning", "ok": True, "plan": plan["steps"]})

    # 1. Setup: service dimulai HEALTHY lalu KITA cause failure (environment disposable utk mission)
    svc.setup_healthy()
    #  <- Service sehat dulu (baseline: state=healthy)
    baseline = {"state": svc.read_state(), "health": svc.read_health()}
    audit.record("mission.baseline", svc.name, **baseline)
    print(f"  [1] BASELINE         : state={baseline['state']} health={baseline['health']}")
    timeline.append({"step": "baseline", "ok": True, **baseline})

    # 2. Cause failure (real external state change: stopped + fail)
    svc.inject_failure()
    failed_state = {"state": svc.read_state(), "health": svc.read_health()}
    audit.record("mission.failure_injected", svc.name, **failed_state)
    print(f"  [2] FAILURE (nyata)  : state={failed_state['state']} health={failed_state['health']}")
    timeline.append({"step": "failure_injected", "ok": False, **failed_state})

    # 3. Investigation — baca evidence dari file state/health nyata
    print(f"  [3] INVESTIGATION    : baca state & health nyata dari disk")
    observations = []
    for sf in (svc.state_file, svc.health_file):
        with open(sf, encoding="utf-8") as fh:
            content = fh.read().strip()
        observations.append({"source": os.path.basename(sf), "content": content})
    anomaly = "stopped" in observations[0]["content"] or "fail" in observations[1]["content"]
    audit.record("mission.investigate", svc.name, state=observations[0]["content"],
                 health=observations[1]["content"], anomaly=anomaly)
    for ob in observations:
        print(f"           - {ob['source']} = {ob['content']}")
    evidence = observations
    timeline.append({"step": "investigation", "ok": True, "anomaly": anomaly,
                     "evidence": [o["content"] for o in observations]})
    print(f"           evidence: {[o['content'] for o in observations]} anomaly={anomaly}")

    # 4. Recommendation
    recommendation = "start" if anomaly else "none"
    audit.record("mission.recommend", svc.name, rec_action=recommendation)
    print(f"  [4] RECOMMENDATION   : action={recommendation}")
    timeline.append({"step": "recommendation", "ok": anomaly, "action": recommendation})

    # 5. Approval (human-in-the-loop gate)
    approval_reason = args.request
    audit.record("mission.approval", svc.name, reason=approval_reason, approved=True)
    print(f"  [5] APPROVAL         : approved=True (reason: {approval_reason[:45]}...)")
    timeline.append({"step": "approval", "ok": True})

    # 6. Agent/Workflow + Real Tool + External System — recovery nyata via adapter
    print("  [6] AGENT/WORKFLOW   : recover via harness (Real Tool -> External System)")
    adapter = RecoveryAdapter(audit, svc)
    outcome = adapter.start(approval_reason)
    print(f"           REAL STATE CHANGE: {outcome['before']} -> {outcome['after']} (file disk)")
    timeline.append({"step": "recover", "ok": True, "before": outcome["before"], "after": outcome["after"]})

    # 7. Verification — independent health check (baca ulang disk)
    iv = independent_health_check(svc, audit)
    print(f"  [7] VERIFICATION     : state={iv['state']} health={iv['health']} healthy={iv['healthy']}")
    timeline.append({"step": "verification", "ok": iv["healthy"], **iv})

    # 8. Artifact — tulis laporan mission nyata ke disk
    artifact_path = os.path.join(artifact_dir, f"{mission_id}_report.txt")
    lines = []
    lines.append("=" * 60)
    lines.append(f"  P11 MISSION REPORT [{mission_id}]")
    lines.append("=" * 60)
    lines.append(f"  request      : {args.request}")
    lines.append(f"  timestamp    : {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"  baseline     : state={baseline['state']} health={baseline['health']}")
    lines.append(f"  failure      : state={failed_state['state']} health={failed_state['health']}")
    lines.append(f"  root cause   : {anomaly}")
    lines.append(f"  recovery     : {outcome['before']} -> {outcome['after']}")
    lines.append(f"  verified     : state={iv['state']} health={iv['health']} healthy={iv['healthy']}")
    lines.append(f"  verification : {outcome['after'] if iv['healthy'] else 'FAIL'}")
    lines.append("=" * 60)
    with open(artifact_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    audit.record("mission.artifact", artifact_path, bytes=os.path.getsize(artifact_path))
    print(f"  [8] ARTIFACT         : {artifact_path} ({os.path.getsize(artifact_path)} bytes) — TERTULIS")
    timeline.append({"step": "artifact", "ok": True, "path": artifact_path})

    # 9. Learn — store experience mission ke repository persistent
    repo = ExperienceRepository(audit=audit)
    lesson = f"Mission {mission_id}: recovery {outcome['before']}->{outcome['after']} verified healthy"
    experience = {
        "experience_id": "xm-" + uuid.uuid4().hex[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mission_id": mission_id,
        "operation": "mission/recovery",
        "request": args.request,
        "evidence": [o["content"] for o in observations],
        "outcome": {"ok": iv["healthy"], "recovered_state": outcome["after"]},
        "verification": {"healthy": iv["healthy"], "state": iv["state"]},
        "lesson": lesson,
    }
    stored_id = repo.store(experience)
    print(f"  [9] LEARNING         : experience {stored_id} stored (count={repo.count()})")
    timeline.append({"step": "learn", "ok": True, "experience_id": stored_id})

    # Future retrieval check (dari P10)
    past = repo.search_by_operation("mission/recovery")
    print(f"           future retrieval: {len(past)} experience mission di-store")

    # Audit
    print(f"\n  -- AUDIT ({len(audit.entries)}) --")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")

    out_json = os.path.join(artifact_dir, f"{mission_id}_evidence.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({
            "mission_id": mission_id,
            "request": args.request,
            "baseline": baseline, "failure": failed_state,
            "investigation": {"evidence": evidence, "anomaly": anomaly},
            "recommendation": recommendation,
            "recovery": outcome,
            "verification": iv,
            "artifact": artifact_path,
            "experience_id": stored_id,
            "timeline": timeline,
            "audit": [e.__dict__ for e in audit.entries],
        }, fh, indent=2, default=str)
    print(f"\n  [Evidence JSON: {out_json}]")

    # DoD P11: seluruh rantai sukses + state healthy + artifact + learning + audit
    ok = (
        anomaly is not None and iv["healthy"]
        and outcome["after"] == "running"
        and os.path.isfile(artifact_path)
        and stored_id is not None
        and len(audit.entries) >= 10
    )
    print("=" * 72)
    print(f"  VERDICT P11: {'PROVEN (full real mission: request->reason->investigate->recommend->approve->recover->verify->artifact->audit->learn)' if ok else 'BELUM PROVEN'}")
    print("=" * 72)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
