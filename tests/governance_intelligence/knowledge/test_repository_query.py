"""repository + query — WP-02/03 tests (IP-3.1-001)."""

from sam.governance_intelligence.knowledge.query import KnowledgeQueryAPI


class TestRepositoryQueryOnly:
    def test_repo_query_only(self, mission_repo):
        assert mission_repo.size() >= 3
        assert mission_repo.by_key("mission.objective") is not None

    def test_by_kind_filter(self, mission_repo):
        assert len(mission_repo.by_kind("mission")) == mission_repo.size()

    def test_evidence_repo_by_claim(self, evidence_repo):
        # by_claim filters keys prefixed evidence.<claim>
        assert evidence_repo.by_claim("nonexistent") == []


class TestQueryAPI:
    def test_find(self, mission_repo, query_api):
        r = query_api.find(mission_repo, "mission.objective")
        assert r.size() == 1
        assert r.keys() == ["mission.objective"]

    def test_search(self, mission_repo, query_api):
        r = query_api.search(mission_repo, "governance")
        assert isinstance(r.jsonable(), dict)

    def test_lookup_facet(self, mission_repo, query_api):
        r = query_api.lookup(mission_repo, "objective")
        assert r.size() >= 1

    def test_reference_by_source(self, mission_repo, query_api):
        r = query_api.reference(mission_repo, "docs/foundation/MISSION.md")
        assert r.size() == mission_repo.size()
