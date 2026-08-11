"""
P5 — Real Tool / GitHub activation via harness.

Menyediakan jalur eksekusi NYATA ke GitHub API (HTTP) melalui pola
RealExecutionHarness (P2-B). READ-ONLY (get repo / list) — tidak menulis.

Prinsip jujur:
  - Tanpa token (env GITHUB_TOKEN kosong / offline)
        -> gate credential GAGAL -> NO EXTERNAL SIDE EFFECT (aman).
  - Dengan token tersedia
        -> panggilan HTTP nyata `httpx` ke api.github.com.

Tidak ada token di-hardcode (baca dari environment). Non-invasif.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN_ENV = "GITHUB_TOKEN"


# ---------------------------------------------------------------------------
# Adapter GitHub nyata (READ-ONLY)
# ---------------------------------------------------------------------------

class RealGitHubAdapter:
    """Akses nyata ke GitHub API via httpx. Hanya operasi baca."""

    OPERATIONS = ("get_repo", "list_repos")

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx  # lazy — dibutuhkan saat runtime call

        token = os.environ.get(GITHUB_TOKEN_ENV, "")
        if not token:
            raise RuntimeError("GITHUB_TOKEN tidak tersedia")

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

        self._audit.record("harness.tool.github.call", action)

        if action == "get_repo":
            owner = params.get("owner")
            repo = params.get("repo")
            if not owner or not repo:
                raise ValueError("get_repo butuh owner & repo")
            url = f"{GITHUB_API}/repos/{owner}/{repo}"
        elif action == "list_repos":
            username = params.get("username")
            if not username:
                raise ValueError("list_repos butuh username")
            url = f"{GITHUB_API}/users/{username}/repos?per_page=5"
        else:
            raise RuntimeError(f"operasi github tidak dikenal: {action}")

        self._audit.record("harness.tool.github.http", url)
        resp = httpx.get(url, headers=headers, timeout=httpx.Timeout(20))
        self._audit.record("harness.tool.github.response", str(resp.status_code))

        if resp.status_code == 401 or resp.status_code == 403:
            return {"ok": False, "action": action, "http_status": resp.status_code,
                    "error": "token tidak valid / tanpa izin", "http_error": True}
        if resp.status_code == 404:
            return {"ok": False, "action": action, "http_status": resp.status_code,
                    "error": "resource tidak ditemukan"}
        resp.raise_for_status()
        data = resp.json()

        if action == "get_repo":
            self._audit.record("harness.tool.github.result", f"{owner}/{repo}",
                               full_name=data.get("full_name"), stars=data.get("stargazers_count"))
            return {"ok": True, "action": action, "full_name": data.get("full_name"),
                    "stars": data.get("stargazers_count"), "language": data.get("language"),
                    "private": data.get("private"), "html_url": data.get("html_url")}

        # list_repos
        repos = [{"full_name": r.get("full_name"), "stars": r.get("stargazers_count")} for r in data]
        self._audit.record("harness.tool.github.result", username, repo_count=len(repos))
        return {"ok": True, "action": action, "repos": repos, "count": len(repos)}


# ---------------------------------------------------------------------------
# Harness Tool — gate P2-B + gate credential GitHub
# ---------------------------------------------------------------------------

class RealToolHarness:
    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        self._harness = RealExecutionHarness(self._audit)
        self._harness.register_capability(
            "tool",
            registry={"id": "tool", "adapter": "RealGitHubAdapter",
                      "external": "GitHub API (read-only)", "operations": RealGitHubAdapter.OPERATIONS},
            contract={"get_repo": {"input": "owner/repo", "output": "repo info", "side_effect": "HTTP GET"},
                      "list_repos": {"input": "username", "output": "repo list", "side_effect": "HTTP GET"}},
            policy="ALLOW",
        )

    def gate_tool(self, request: ExecutionRequest) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists("tool"):
            return [{"id": "capability", "label": "Capability 'tool' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        full_gates = self._harness._evaluate_gates(request)
        # boundary hardcoded file -> timpa utk tool: target = operasi dikenal
        action = request.operation.split("/")[-1]
        ok_op = action in RealGitHubAdapter.OPERATIONS
        full_gates = [
            GateResult("boundary", GATES[6]["label"], ok_op, f"operasi '{action}' dikenal")
            if g.id == "boundary" else g
            for g in full_gates
        ]
        # gate credential tool
        token_ok = bool(os.environ.get(GITHUB_TOKEN_ENV, ""))
        self._audit.record("harness.gate.credential_tool", "github", present=token_ok)
        cred_gate = {"id": "credential_tool",
                     "label": "Kredensial GitHub (GITHUB_TOKEN) tersedia lewat approved boundary",
                     "passed": token_ok, "detail": f"env={GITHUB_TOKEN_ENV}"}
        return [g.to_dict() for g in full_gates] + [cred_gate]

    def execute(self, action: str, params: Dict[str, Any],
                mode: ExecutionMode = ExecutionMode.EXECUTE,
                approval_reason: str = "",
                timeout_seconds: int = 20) -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"tool/{action}",
            target="github-api",
            params={"action": action, **params},
            mode=mode,
            correlation_id=str(uuid.uuid4()),
            timeout_seconds=timeout_seconds,
            approval_reason=approval_reason,
        )
        gates = self.gate_tool(req)
        failed = [g for g in gates if not g["passed"]]
        for g in gates:
            self._audit.record("harness.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("harness.mode.preview", f"tool/{action}")
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.", "gates": gates}

        if failed:
            self._audit.record("harness.execute.blocked", f"tool/{action}",
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gates}

        self._audit.record("harness.execute.allowed", f"tool/{action}")
        try:
            adapter = RealGitHubAdapter(self._audit)
            result = adapter.execute(action, params)
            return {"ok": result.get("ok"), "mode": "EXECUTE", "gates": gates, **result}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("harness.tool.github.fail", action,
                               error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": f"{type(exc).__name__}: {exc}", "gates": gates}


# ---------------------------------------------------------------------------
# CLI pembuktian
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P5 Real Tool / GitHub activation")
    parser.add_argument("action", choices=RealGitHubAdapter.OPERATIONS, default="get_repo",
                        nargs="?", help="Operasi github (read-only)")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--owner", default="VanM-Hub")
    parser.add_argument("--repo", default="SAM")
    parser.add_argument("--username", default="VanM-Hub")
    parser.add_argument("--reason", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit = AuditTrail()
    harness = RealToolHarness(audit)
    mode = ExecutionMode(args.mode)

    params = {"owner": args.owner, "repo": args.repo, "username": args.username}
    reason = args.reason or (f"P5 eksekusi nyata {args.action}" if mode == ExecutionMode.EXECUTE else "")

    result = harness.execute(args.action, params, mode=mode, approval_reason=reason)

    token_present = bool(os.environ.get(GITHUB_TOKEN_ENV, ""))
    print("=" * 70)
    print("  P5 — Real Tool / GitHub activation (via harness)")
    print("=" * 70)
    print(f"  action     : {args.action}")
    print(f"  mode       : {mode.value}")
    print(f"  token      : {'PRESENT' if token_present else 'ABSENT'}")
    print("  gates:")
    for g in result.get("gates", []):
        print(f"    [{'PASS' if g['passed'] else 'FAIL'}] {g['label']}")
    print("  outcome:")
    for k, v in result.items():
        if k == "gates":
            continue
        print(f"    {k} : {str(v)[:120]}")
    print("  audit:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 70)

    if mode == ExecutionMode.EXECUTE and not token_present:
        print("\n  VERDICT: PLATFORM AMAN — tanpa token, EXECUTE diblokir (NO SIDE EFFECT).")
        print("           Untuk E2E penuh: set GITHUB_TOKEN di env saat online.")
        exit_code = 1
    elif mode == ExecutionMode.EXECUTE and token_present:
        ok = result.get("ok")
        print(f"\n  VERDICT: {'REAL E2E OK (HTTP nyata ke GitHub)' if ok else 'GAGAL di HTTP'}")
        exit_code = 0 if ok else 1
    else:
        print("\n  VERDICT: PREVIEW OK (no side effect)")
        exit_code = 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"action": args.action, "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
