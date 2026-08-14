"""M14-013 Real Project Guardian — detect + repair project (GitHub/local).

Target real Van: "Real GitHub project -> detect + repair when authorized."

Desain:
  - PROJECT KINDS:
      github  : repo GitHub. Probe read-only via HTTP GET ke
                api.github.com/repos/<owner>/<repo> (canonical read - httpx).
      local   : folder project lokal (mis. repo git di disk). Probe via file
                sistem: ada .git? README? isi? (read-only).
  - detect  : probe + baca indikator kesehatan.
  - diagnose: temuan (repo unreachable / README hilang / cache besar / dll).
  - repair  : AutonomousRecoveryLoop; execute_fn DIINJEKSIKAN (action nyata).
              UNTUK github: mutation via jalur canonical (m8_002 / GitHub API)
              dan HANYA bila authorized + credential tersedia; tanpa itu ->
              honest BLOCKED/escalate. TIDAK pernah mutasi di luar scope.

Boundary: probe GitHub read-only TIDAK menyimpan token; repair via canonical
CredentialBoundary; audit tidak pernah memuat raw token.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.recovery import (
    AutonomousRecoveryLoop, RecoveryOutcome,
)


class ProjectKind:
    GITHUB = "github"
    LOCAL = "local"


@dataclass(frozen=True)
class ProjectProbe:
    """Hasil probe satu project (read-only)."""

    kind: str
    target: str                       # repo "owner/repo" atau folder path
    reachable: bool
    detail: str = ""
    issues: tuple = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind, "target": self.target,
            "reachable": self.reachable, "detail": self.detail,
            "issues": list(self.issues),
        }


@dataclass
class ProjectGuardianResult:
    """Hasil siklus guardian (auditable)."""

    probe: Optional[ProjectProbe] = None
    repaired: bool = False
    outcome: Optional[RecoveryOutcome] = None
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "probe": self.probe.as_dict() if self.probe else None,
            "repaired": self.repaired, "reason": self.reason,
            "outcome": self.outcome.as_dict() if self.outcome else None,
        }


class GitHubProbe:
    """Probe repo GitHub via HTTP read-only (canonical; tanpa token disimpan)."""

    def probe(self, owner: str, repo: str, timeout_seconds: int = 15) -> ProjectProbe:
        target = f"{owner}/{repo}"
        try:
            import httpx
            resp = httpx.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                timeout=httpx.Timeout(timeout_seconds),
                headers={"Accept": "application/vnd.github+json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                issues = []
                if data.get("archived"):
                    issues.append("repo archived")
                if data.get("size", 0) > 500 * 1024:   # KB
                    issues.append("large repo (.git size) - may be slow")
                return ProjectProbe(
                    ProjectKind.GITHUB, target, True,
                    f"reachable (default_branch={data.get('default_branch','?')})",
                    tuple(issues),
                )
            return ProjectProbe(
                ProjectKind.GITHUB, target, False,
                f"http {resp.status_code}",
                ("repo unreachable via GitHub API",),
            )
        except Exception as e:  # noqa: BLE001
            return ProjectProbe(
                ProjectKind.GITHUB, target, False, str(e),
                ("probe failed (network/API)",),
            )


class LocalProjectProbe:
    """Probe project lokal (folder) via file sistem (read-only)."""

    def probe(self, path: str) -> ProjectProbe:
        if not os.path.isdir(path):
            return ProjectProbe(ProjectKind.LOCAL, path, False,
                                "folder not found", ("local path missing",))
        issues = []
        has_git = os.path.isdir(os.path.join(path, ".git"))
        has_readme = any(
            os.path.exists(os.path.join(path, r)) for r in ("README.md", "README", "Readme.md")
        )
        if has_git and not has_readme:
            issues.append("no README for a git repo")
        if not has_git:
            issues.append("not a git repository (.git missing)")
        return ProjectProbe(
            ProjectKind.LOCAL, path, True,
            f"git={'yes' if has_git else 'no'}, readme={'yes' if has_readme else 'no'}",
            tuple(issues),
        )


class ProjectGuardian:
    """Guardian project: detect -> diagnose -> repair (delegated authority)."""

    def __init__(
        self,
        loop: Optional[AutonomousRecoveryLoop] = None,
        github_probe: Optional[GitHubProbe] = None,
        local_probe: Optional[LocalProjectProbe] = None,
    ) -> None:
        self._loop = loop or AutonomousRecoveryLoop()
        self._gh = github_probe or GitHubProbe()
        self._local = local_probe or LocalProjectProbe()

    # --- detect / diagnose ---

    def detect(
        self, *, kind: str = ProjectKind.GITHUB, target: str = "", owner: str = "", repo: str = ""
    ) -> ProjectProbe:
        if kind == ProjectKind.LOCAL:
            return self._local.probe(target)
        return self._gh.probe(owner or (target.split("/")[0] if "/" in target else ""),
                              repo or (target.split("/")[1] if "/" in target else target))

    # --- repair ---

    async def protect(
        self,
        *,
        kind: str = ProjectKind.GITHUB,
        target: str = "",
        owner: str = "",
        repo: str = "",
        grant: Optional[DelegationGrant] = None,
        risk: float = 0.4,
        risk_label: str = "medium",
        execute_fn: Optional[Callable] = None,
        verify_fn: Optional[Callable] = None,
        rollback_fn: Optional[Callable] = None,
    ) -> ProjectGuardianResult:
        """Detect lalu repair project bila authorized.

        execute_fn DIINJEKSIKAN (action nyata — utk github mutation via canonical
        m8_002 / GitHub API; utk local: action file sistem). Tanpa injeksi ->
        report issue (detect) tapi TIDAK sukses palsu utk repair.
        """
        probe = self.detect(kind=kind, target=target, owner=owner, repo=repo)
        ward_id = f"project-{probe.target.replace('/', ':')}"

        if probe.reachable and not probe.issues:
            return ProjectGuardianResult(
                probe=probe, repaired=False, reason="project healthy - no repair needed",
            )

        grant = grant or DelegationGrant(
            ward_id=ward_id, owner_id="owner", autonomy_level=AutonomyLevel.OBSERVE,
            requires_human_approval=True,
        )

        from sam.execution_runtime.execution_request import ExecutionRequest
        request = ExecutionRequest(
            execution_id=f"exec-project-{ward_id}", provider_id="project",
            operation="repair", mode="execute", approved=False,
            payload={"ward_id": ward_id, "target": probe.target, "kind": kind},
            timeout_seconds=30,
        )

        outcome = await self._loop.run(
            request=request, grant=grant, capability="protect",
            risk=risk, risk_label=risk_label,
            evidence_refs=(f"probe:{probe.detail}",),
            plan={"probe": probe.as_dict()},
            observe_fn=lambda: {"reachable": probe.reachable,
                                "issues": list(probe.issues)},
            investigate_fn=lambda: {"detail": probe.detail},
            diagnose_fn=lambda: {"issues": list(probe.issues)},
            execute_fn=execute_fn,
            verify_fn=verify_fn,
            rollback_fn=rollback_fn,
        )

        return ProjectGuardianResult(
            probe=probe, repaired=outcome.ok, outcome=outcome, reason=outcome.reason,
        )
