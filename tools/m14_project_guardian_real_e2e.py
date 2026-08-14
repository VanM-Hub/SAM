r"""M14 Real E2E — Project Guardian (GitHub + Local) terhadap project nyata.

Membuktikan M14-013 terhadap project NYATA:

  - GitHubProbe  : probe real `VanM-Hub/SAM` via GitHub API (read-only, tanpa token
                   disimpan — probe TIDAK memakai auth, hanya HTTP canonical).
  - LocalProjectProbe: probe real folder project lokal (git + README registry).
  - ProjectGuardian.protect: detect lalu repair delegated. Jujur: repair (mutation)
                   TIDAK diklaim sukses tanpa execute_fn diinjeksi — di sini execute_fn
                   = no-op logger supaya alur canonical (ApprovalGate + loop) tetap
                   dieksekusi secara nyata, TAPI outcome dibedakan: issue nyata yang
                   SAM tidak bisa reparasi -> escalate (bukan sukses palsu).

Hasil = evidence + audit artifact.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.delegated_authority.real_project_guardian import (
    GitHubProbe,
    LocalProjectProbe,
    ProjectGuardian,
    ProjectKind,
)


async def run_async(*, owner: str, repo: str, local_path: str) -> dict:
    guardian = ProjectGuardian()
    result = {
        "milestone": "M14-013",
        "claim": "REAL_E2E_PROJECT_GUARDIAN",
        "environment": {
            "host": os.environ.get("COMPUTERNAME", "unknown"),
            "python": sys.version.split()[0],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
        "probes": {},
        "protect": {},
    }

    # --- GitHub real probe (read-only, tanpa auth/token) ---
    gh = GitHubProbe().probe(owner=owner, repo=repo)
    result["probes"]["github"] = {
        "target": gh.target, "reachable": gh.reachable,
        "detail": gh.detail, "issues": list(gh.issues),
    }

    # --- Local real probe ---
    local = LocalProjectProbe().probe(path=local_path)
    result["probes"]["local"] = {
        "target": local.target, "reachable": local.reachable,
        "detail": local.detail, "issues": list(local.issues),
    }

    # --- protect: detect lalu repair (execute_fn diinjeksi = no-op logger) ---
    # grant default = OBSERVE + requires_human_approval -> tidak auto-approve.
    # execute_fn HANYA dipanggil bila grant mengizinkan; tanpa itu -> escalate/block.
    executed = {"called": False}
    async def _noop_execute_fn(*args: object, **kwargs: object) -> dict:
        executed["called"] = True
        return {"status": "would_repair", "note": "no-op (saat ini tidak mutation)"}

    for kind, tgt, ow, rp in [
        (ProjectKind.GITHUB, f"{owner}/{repo}", owner, repo),
        (ProjectKind.LOCAL, local_path, "", ""),
    ]:
        guard = await guardian.protect(
            kind=kind, target=tgt, owner=ow, repo=rp,
            execute_fn=_noop_execute_fn,
            verify_fn=lambda: {"ok": True},
            rollback_fn=lambda: None,
        )
        result["protect"][
            "github" if kind == ProjectKind.GITHUB else "local"
        ] = {
            "target": guard.probe.target,
            "reachable": guard.probe.reachable,
            "issues": list(guard.probe.issues),
            "repaired": guard.repaired,
            "reason": guard.reason,
            "execute_fn_called": executed["called"],
        }

    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="VanM-Hub")
    ap.add_argument("--repo", default="SAM")
    ap.add_argument("--local", default="", help="folder project lokal (wajib)")
    ap.add_argument("--out-dir", default="docs/engineering/state/M14")
    args = ap.parse_args()

    import asyncio
    result = asyncio.run(run_async(
        owner=args.owner, repo=args.repo, local_path=args.local,
    ))

    print("[GitHub] probe:", result["probes"]["github"])
    print("[Local ] probe:", result["probes"]["local"])
    print("[GitHub] protect:", result["protect"]["github"])
    print("[Local ] protect:", result["protect"]["local"])

    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, "M14_PROJECT_GUARDIAN_real_evidence.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Evidence saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
