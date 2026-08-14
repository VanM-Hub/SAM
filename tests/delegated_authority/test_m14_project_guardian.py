"""M14-013 tests — Project Guardian (detect + repair when authorized).

Local project probe diuji deterministik (file sistem). GitHub probe diuji dgn
httpx mock (MockTransport) agar tidak bergantung network nyata di test unit.
Real E2E (repo GitHub sungguhan + mutation) terpisah & jujur.
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.real_project_guardian import (
    ProjectGuardian, GitHubProbe, LocalProjectProbe, ProjectKind,
)


def _grant_auto():
    return DelegationGrant(
        ward_id="project", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",), requires_human_approval=False,
    )


class TestLocalProjectProbe:
    def test_missing_path(self):
        p = LocalProjectProbe().probe("D:/does/not/exist_xyz")
        assert p.reachable is False
        assert "not found" in p.detail.lower()

    def test_git_repo_without_readme_flagged(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, ".git"), exist_ok=True)  # mock .git
        p = LocalProjectProbe().probe(d)
        assert p.reachable is True
        assert any("no README" in i for i in p.issues)

    def test_git_repo_with_readme_clean(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, ".git"), exist_ok=True)
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
            f.write("# x\n")
        p = LocalProjectProbe().probe(d)
        assert p.reachable is True
        assert not p.issues


class TestGitHubProbe:
    def test_reachable(self, monkeypatch):
        import httpx

        class FakeClient:
            def get(self, url, timeout=None, headers=None):
                class R:
                    status_code = 200
                r = R()
                r.json = lambda: {"default_branch": "main", "archived": False, "size": 100}
                return r

        monkeypatch.setattr(httpx, "get", FakeClient().get)
        p = GitHubProbe().probe("owner", "repo")
        assert p.reachable is True
        assert "main" in p.detail

    def test_unreachable(self, monkeypatch):
        import httpx

        def fake_get(*a, **k):
            class R:
                status_code = 404
            r = R()
            r.json = lambda: {}
            return r

        monkeypatch.setattr(httpx, "get", fake_get)
        p = GitHubProbe().probe("owner", "nonexistent")
        assert p.reachable is False


class TestProjectGuardian:
    async def test_local_healthy_no_repair(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, ".git"), exist_ok=True)
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
            f.write("# ok\n")
        g = ProjectGuardian()
        res = await g.protect(kind=ProjectKind.LOCAL, target=d, grant=_grant_auto(),
                              execute_fn=lambda r: {"ok": True},
                              verify_fn=lambda r: {"ok": True})
        assert res.repaired is False

    async def test_local_issue_repair_when_authorized(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, ".git"), exist_ok=True)  # tanpa README
        g = ProjectGuardian()
        res = await g.protect(kind=ProjectKind.LOCAL, target=d, grant=_grant_auto(),
                              execute_fn=lambda r: {"ok": True, "created": "README.md"},
                              verify_fn=lambda r: {"ok": True, "verified": "README present"})
        assert res.repaired is True
        assert res.outcome.ok is True

    async def test_local_issue_human_required_escalates(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, ".git"), exist_ok=True)
        g = ProjectGuardian()
        g2 = DelegationGrant(
            ward_id="p", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
            allowed_mutations=("protect",), requires_human_approval=True,
        )
        res = await g.protect(kind=ProjectKind.LOCAL, target=d, grant=g2)
        assert res.repaired is False
        assert res.outcome.ok is False
