"""Test IP-4.3-001 - Persistent Experience Repository (MISSION-4.3).

Coverage: WP-01..WP-10 - repository, persistent storage, model, histories,
API, explainability, compliance, persistence-across-restart, e2e.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_learning.experience_model import (
    Experience,
    ExperienceClassification,
    ExperienceEvidenceRef,
    ExperienceStatus,
)
from sam.operational_learning.persistent_storage import (
    PersistenceEngine,
    SerializationLayer,
    StorageConfig,
    StorageHealth,
)
from sam.operational_learning.experience_repository import ExperienceRepository
from sam.operational_learning.history import (
    ExecutionHistory,
    HistoryStore,
    InvestigationHistory,
    VerificationHistory,
)
from sam.operational_learning.repository_api import RepositoryAPI
from sam.operational_learning.repository_explainability import RepositoryExplainer
from sam.operational_learning.repository_compliance import (
    RepositoryComplianceChecker,
)


def _engine(tmp_path, collection="test"):
    return PersistenceEngine(
        StorageConfig(base_dir=str(tmp_path), collection=collection)
    )


def _repo_and_history(tmp_path):
    # Engine terpisah agar record experience & history tidak campur.
    repo = ExperienceRepository(_engine(tmp_path, "test_repo"))
    store = HistoryStore(_engine(tmp_path, "test_hist"))
    return repo, store


def _exp(summary="test experience", classification=ExperienceClassification.EXECUTION, evidence=()):
    return Experience.create(
        summary=summary,
        classification=classification,
        evidence=evidence,
        outcome="success",
        tags=("test",),
    )


# ---------------------------------------------------------------------------
# WP-03 Experience Model
# ---------------------------------------------------------------------------

class TestExperienceModel:
    def test_create_valid(self):
        exp = _exp()
        assert exp.experience_id
        assert exp.status == ExperienceStatus.RECORDED
        assert ExperienceClassification.valid(exp.classification)

    def test_invalid_classification_raises(self):
        with pytest.raises(ValueError):
            Experience.create(summary="x", classification="not_valid")

    def test_immutable(self):
        exp = _exp()
        with pytest.raises(Exception):
            exp.summary = "changed"  # frozen dataclass


# ---------------------------------------------------------------------------
# WP-01 Experience Repository
# ---------------------------------------------------------------------------

class TestExperienceRepository:
    def test_add_and_get(self, tmp_path):
        repo = ExperienceRepository(_engine(tmp_path))
        exp = _exp()
        repo.add(exp)
        assert repo.get(exp.experience_id).summary == "test experience"

    def test_unique_identity(self, tmp_path):
        repo = ExperienceRepository(_engine(tmp_path))
        a = _exp("a")
        b = _exp("b")
        assert a.experience_id != b.experience_id
        repo.add(a)
        repo.add(b)
        assert repo.count() == 2

    def test_catalog_and_statistics(self, tmp_path):
        repo = ExperienceRepository(_engine(tmp_path))
        repo.add(_exp(classification=ExperienceClassification.EXECUTION))
        repo.add(_exp(classification=ExperienceClassification.INVESTIGATION))
        stats = repo.statistics()
        assert stats.total_experiences == 2
        assert stats.by_classification[ExperienceClassification.EXECUTION] == 1

    def test_append_only_rejects_duplicate(self, tmp_path):
        repo = ExperienceRepository(_engine(tmp_path))
        exp = _exp()
        repo.add(exp)
        with pytest.raises(ValueError):
            repo.add(exp)


# ---------------------------------------------------------------------------
# WP-02 Persistent Storage
# ---------------------------------------------------------------------------

class TestPersistentStorage:
    def test_survives_restart(self, tmp_path):
        store_path = tmp_path / "test_store.json"
        engine1 = PersistenceEngine(
            StorageConfig(base_dir=str(tmp_path), collection="test")
        )
        engine1.append("r1", {"summary": "hello"})
        # Simulasi restart: instance baru dari file yang sama
        engine2 = PersistenceEngine(
            StorageConfig(base_dir=str(tmp_path), collection="test")
        )
        assert engine2.get("r1") is not None
        assert engine2.count() == 1

    def test_atomic_write_creates_valid_file(self, tmp_path):
        engine = _engine(tmp_path)
        engine.append("r1", {"a": 1})
        assert StorageHealth.check(engine.store_path)["ok"] is True

    def test_record_integrity_verified(self, tmp_path):
        engine = _engine(tmp_path)
        record = engine.append("r1", {"a": 1})
        assert record.verify() is True

    def test_serialization_deterministic(self):
        payload = {"z": 1, "a": 2}
        assert SerializationLayer.canonical_hash(payload) == SerializationLayer.canonical_hash(payload)


# ---------------------------------------------------------------------------
# WP-04/05/06 Histories
# ---------------------------------------------------------------------------

class TestHistories:
    def test_investigation_history(self, tmp_path):
        store = HistoryStore(_engine(tmp_path))
        hist = InvestigationHistory(store)
        record = hist.record("inv-1", "investigate cpu", timeline=(("start", "t1"), ("end", "t2")))
        assert hist.get("inv-1").summary == "investigate cpu"
        assert len(hist.all()) == 1

    def test_execution_history_with_approval(self, tmp_path):
        store = HistoryStore(_engine(tmp_path))
        hist = ExecutionHistory(store)
        record = hist.record(
            "exec-1", "restart provider", approval_id="appr-1", audit_id="aud-1", outcome="completed"
        )
        assert record.metadata["approval_id"] == "appr-1"
        assert hist.get("exec-1").metadata["audit_id"] == "aud-1"

    def test_verification_history(self, tmp_path):
        store = HistoryStore(_engine(tmp_path))
        hist = VerificationHistory(store)
        hist.record("ver-1", "verify outcome", result={"passed": True}, evidence_ids=("e1",))
        assert hist.get("ver-1").result["passed"] is True

    def test_search(self, tmp_path):
        store = HistoryStore(_engine(tmp_path))
        hist = InvestigationHistory(store)
        hist.record("inv-1", "cpu high latency")
        hist.record("inv-2", "memory leak")
        assert len(hist.search("cpu")) == 1
        assert len(hist.search()) == 2


# ---------------------------------------------------------------------------
# WP-07 Repository API
# ---------------------------------------------------------------------------

class TestRepositoryAPI:
    def test_query_experiences(self, tmp_path):
        repo, store = _repo_and_history(tmp_path)
        repo.add(_exp(classification=ExperienceClassification.EXECUTION))
        api = RepositoryAPI(repository=repo, history=store)
        result = api.experiences.by_classification(ExperienceClassification.EXECUTION)
        assert result.count == 1
        assert api.metadata()["name"] == "experience_repository"

    def test_history_query(self, tmp_path):
        repo, store = _repo_and_history(tmp_path)
        InvestigationHistory(store).record("inv-1", "cpu")
        api = RepositoryAPI(repository=repo, history=store)
        result = api.history.search(kind="investigation", query="cpu")
        assert result.count == 1

    def test_statistics_api(self, tmp_path):
        repo, store = _repo_and_history(tmp_path)
        repo.add(_exp())
        api = RepositoryAPI(repository=repo, history=store)
        assert api.statistics.statistics()["total_experiences"] == 1


# ---------------------------------------------------------------------------
# WP-08 Repository Explainability
# ---------------------------------------------------------------------------

class TestRepositoryExplainability:
    def test_explain_experience(self, tmp_path):
        exp = _exp(
            evidence=(
                ExperienceEvidenceRef("e1", "runtime", "r1"),
                ExperienceEvidenceRef("e2", "provider", "p1"),
            )
        )
        explainer = RepositoryExplainer()
        expl = explainer.explain(exp)
        assert expl.trace.evidence_chain == (("e1", "r1"), ("e2", "p1"))
        assert expl.context.targets == ()


# ---------------------------------------------------------------------------
# WP-09 Repository Compliance
# ---------------------------------------------------------------------------

class TestRepositoryCompliance:
    def test_certify_clean(self, tmp_path):
        engine = _engine(tmp_path)
        rec = engine.append("r1", {"a": 1})
        checker = RepositoryComplianceChecker()
        cert = checker.certify(records=(rec,))
        assert cert["certified"] is True

    def test_detects_execution(self, tmp_path):
        checker = RepositoryComplianceChecker()
        cert = checker.certify(execution=True)
        assert not cert["certified"]

    def test_detects_governance_mutation(self, tmp_path):
        checker = RepositoryComplianceChecker()
        cert = checker.certify(governance_mutation=True)
        assert not cert["certified"]


# ---------------------------------------------------------------------------
# WP-10 Integration & Certification (end-to-end + persistence)
# ---------------------------------------------------------------------------

class TestRepositoryEndToEnd:
    def test_end_to_end_persistent_repository(self, tmp_path):
        path = str(tmp_path)
        # Sesi 1: simpan (repo & history pakai engine berbeda agar tidak campur)
        repo_engine = PersistenceEngine(StorageConfig(base_dir=path, collection="e2e_repo"))
        hist_engine = PersistenceEngine(StorageConfig(base_dir=path, collection="e2e_hist"))
        repo = ExperienceRepository(repo_engine)
        store = HistoryStore(hist_engine)

        exp = _exp(classification=ExperienceClassification.INVESTIGATION)
        repo.add(exp)
        hist = InvestigationHistory(store)
        hist.record("inv-1", "investigate issue", evidence_ids=(exp.experience_id,))

        # Sesi 2: restart -> data tetap ada
        repo_engine2 = PersistenceEngine(StorageConfig(base_dir=path, collection="e2e_repo"))
        hist_engine2 = PersistenceEngine(StorageConfig(base_dir=path, collection="e2e_hist"))
        repo2 = ExperienceRepository(repo_engine2)
        store2 = HistoryStore(hist_engine2)
        assert repo2.get(exp.experience_id) is not None
        assert len(repo2.all()) == 1
        assert len(HistoryStore(hist_engine2).all()) == 1

        # API read-only
        api = RepositoryAPI(repository=repo2, history=store2)
        assert api.experiences.all().count == 1
        assert api.audit()["verified"] is True

        # Compliance penuh
        checker = RepositoryComplianceChecker()
        assert checker.certify(records=repo_engine2.all()).get("certified") is True
