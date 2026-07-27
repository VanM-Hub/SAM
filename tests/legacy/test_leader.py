"""
Tests for Leader Election (LeaderElection + LeaderRecord).
Uses inline replica classes + _TestDB shim.
"""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pytest

# ═══════════════════════════════════════════════════════════════════════
# Leader Record model (inline)
# ═══════════════════════════════════════════════════════════════════════

class _LeaderRecord:
    def __init__(
        self, leader_id: str, cluster_id: str, term: int,
        lease_expires_at: datetime, elected_at: Optional[datetime] = None,
    ):
        self.leader_id = leader_id
        self.cluster_id = cluster_id
        self.term = term
        self.lease_expires_at = lease_expires_at
        self.elected_at = elected_at or datetime.utcnow()

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.lease_expires_at

    @property
    def remaining_seconds(self) -> float:
        diff = (self.lease_expires_at - datetime.utcnow()).total_seconds()
        return max(0.0, diff)


# ═══════════════════════════════════════════════════════════════════════
# Leader Election (inline — cluster_id sebagai PRIMARY KEY)
# ═══════════════════════════════════════════════════════════════════════

class _LeaderElection:
    _TABLE = "cluster_leader"

    def __init__(self, db, cluster_id: str):
        self._db = db
        self._cluster_id = cluster_id

    async def elect(self, node_id: str, lease_seconds: int = 30) -> bool:
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)

        # Step 1: INSERT (hanya berhasil jika belum ada leader)
        try:
            await self._db.execute(
                f"INSERT INTO {self._TABLE} (leader_id, cluster_id, term, lease_expires_at, elected_at) VALUES (?, ?, 1, ?, ?)",
                [node_id, self._cluster_id, lease_at.isoformat(), now.isoformat()],
            )
            return True
        except Exception:
            pass

        # Step 2: Takeover attempt
        return await self._attempt_takeover(node_id, lease_seconds)

    async def _attempt_takeover(self, node_id: str, lease_seconds: int) -> bool:
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)

        row = await self._get_row()
        if not row:
            # Race condition — retry INSERT
            try:
                await self._db.execute(
                    f"INSERT INTO {self._TABLE} (leader_id, cluster_id, term, lease_expires_at, elected_at) VALUES (?, ?, 1, ?, ?)",
                    [node_id, self._cluster_id, lease_at.isoformat(), now.isoformat()],
                )
                return True
            except Exception:
                return False

        r = dict(row) if not isinstance(row, dict) else row
        current_leader = r["leader_id"]
        expired = self._lease_expired(r)

        if not expired:
            return False

        if current_leader == node_id:
            # Renew with same term
            await self._db.execute(
                f"UPDATE {self._TABLE} SET lease_expires_at=?, elected_at=? WHERE leader_id=? AND cluster_id=?",
                [lease_at.isoformat(), now.isoformat(), node_id, self._cluster_id],
            )
            return True

        # Takeover with term+1
        new_term = r["term"] + 1
        result = await self._db.execute(
            f"UPDATE {self._TABLE} SET leader_id=?, term=?, lease_expires_at=?, elected_at=? WHERE leader_id=? AND cluster_id=? AND term=?",
            [node_id, new_term, lease_at.isoformat(), now.isoformat(), current_leader, self._cluster_id, r["term"]],
        )
        return self._rows_affected(result) > 0

    async def renew_lease(self, node_id: str, lease_seconds: int = 30) -> bool:
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)
        result = await self._db.execute(
            f"UPDATE {self._TABLE} SET lease_expires_at=?, elected_at=? WHERE leader_id=? AND cluster_id=?",
            [lease_at.isoformat(), now.isoformat(), node_id, self._cluster_id],
        )
        return self._rows_affected(result) > 0

    async def get_leader(self) -> Optional[_LeaderRecord]:
        row = await self._get_row()
        if not row:
            return None
        r = dict(row) if not isinstance(row, dict) else row
        return _LeaderRecord(
            leader_id=r["leader_id"], cluster_id=r["cluster_id"], term=r["term"],
            lease_expires_at=datetime.fromisoformat(r["lease_expires_at"]),
            elected_at=datetime.fromisoformat(r["elected_at"]),
        )

    async def resign(self, node_id: str) -> None:
        row = await self._get_row()
        if not row:
            return
        r = dict(row) if not isinstance(row, dict) else row
        if r["leader_id"] != node_id:
            return
        await self._db.execute(
            f"DELETE FROM {self._TABLE} WHERE cluster_id=?", [self._cluster_id],
        )

    async def is_leader(self, node_id: str) -> bool:
        row = await self._get_row()
        if not row:
            return False
        r = dict(row) if not isinstance(row, dict) else row
        if r["leader_id"] != node_id:
            return False
        if self._lease_expired(r):
            return False
        return True

    async def _get_row(self):
        return await self._db.fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE cluster_id=?", [self._cluster_id],
        )

    @staticmethod
    def _lease_expired(row: dict) -> bool:
        try:
            dt = datetime.fromisoformat(row["lease_expires_at"])
        except (ValueError, TypeError):
            return True
        return datetime.utcnow() > dt

    @staticmethod
    def _rows_affected(result) -> int:
        if result is None or not hasattr(result, "rowcount"):
            return 0
        return result.rowcount


# ═══════════════════════════════════════════════════════════════════════
# _TestDB shim — cluster_id sebagai PRIMARY KEY
# ═══════════════════════════════════════════════════════════════════════

class _TestDB:
    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.execute(
            "CREATE TABLE cluster_leader ("
            "leader_id TEXT NOT NULL,"
            "cluster_id TEXT NOT NULL PRIMARY KEY,"
            "term INTEGER NOT NULL DEFAULT 1,"
            "lease_expires_at TEXT NOT NULL,"
            "elected_at TEXT NOT NULL)"
        )
        self._conn.commit()

    async def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        self._conn.commit()
        return cur

    async def fetch_one(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchone()

    async def fetch_all(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    def close(self):
        self._conn.close()


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def db():
    _db = _TestDB()
    yield _db
    _db.close()


@pytest.fixture
def election(db):
    return _LeaderElection(db, cluster_id="cluster-test")


# ═══════════════════════════════════════════════════════════════════════
# LeaderRecord Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeaderRecord:
    def test_defaults(self):
        r = _LeaderRecord("node-a", "c1", 1, datetime.utcnow() + timedelta(seconds=30))
        assert r.leader_id == "node-a"
        assert r.cluster_id == "c1"
        assert r.term == 1
        assert not r.is_expired
        assert r.remaining_seconds > 0

    def test_expired(self):
        r = _LeaderRecord("node-a", "c1", 1, datetime.utcnow() - timedelta(seconds=1))
        assert r.is_expired
        assert r.remaining_seconds == 0.0

    def test_remaining_zero_when_expired(self):
        r = _LeaderRecord("node-a", "c1", 5, datetime.utcnow() - timedelta(seconds=60))
        assert r.remaining_seconds == 0.0


# ═══════════════════════════════════════════════════════════════════════
# Elect Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeaderElect:
    @pytest.mark.asyncio
    async def test_first_node_elected(self, election):
        assert await election.elect("node-a", 30) is True
        leader = await election.get_leader()
        assert leader is not None
        assert leader.leader_id == "node-a"
        assert leader.term == 1

    @pytest.mark.asyncio
    async def test_second_node_cannot_elect_when_leader_valid(self, election):
        await election.elect("node-a", 60)
        result = await election.elect("node-b", 60)
        assert result is False
        leader = await election.get_leader()
        assert leader.leader_id == "node-a"

    @pytest.mark.asyncio
    async def test_second_node_takes_over_when_lease_expired(self, election):
        await election.elect("node-a", lease_seconds=-1)
        result = await election.elect("node-b", 60)
        assert result is True
        leader = await election.get_leader()
        assert leader.leader_id == "node-b"
        assert leader.term == 2

    @pytest.mark.asyncio
    async def test_same_node_reelects_when_lease_expired(self, election):
        await election.elect("node-a", lease_seconds=-1)
        result = await election.elect("node-a", 60)
        assert result is True
        leader = await election.get_leader()
        assert leader.leader_id == "node-a"
        assert leader.term == 1  # renew, not takeover

    @pytest.mark.asyncio
    async def test_elect_different_cluster_independent(self, db):
        e1 = _LeaderElection(db, "cluster-1")
        e2 = _LeaderElection(db, "cluster-2")
        await e1.elect("node-a", 60)
        await e2.elect("node-b", 60)
        assert (await e1.get_leader()).leader_id == "node-a"
        assert (await e2.get_leader()).leader_id == "node-b"


# ═══════════════════════════════════════════════════════════════════════
# Renew Lease Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeaderRenew:
    @pytest.mark.asyncio
    async def test_renew_success(self, election):
        await election.elect("node-a", 1)
        original = await election.get_leader()
        orig_expires = original.lease_expires_at
        await asyncio.sleep(0.01)
        assert await election.renew_lease("node-a", 60) is True
        renewed = await election.get_leader()
        assert renewed.lease_expires_at > orig_expires

    @pytest.mark.asyncio
    async def test_renew_fails_for_non_leader(self, election):
        await election.elect("node-a", 60)
        assert await election.renew_lease("node-b", 60) is False

    @pytest.mark.asyncio
    async def test_renew_fails_when_no_leader(self, election):
        assert await election.renew_lease("node-a", 60) is False


# ═══════════════════════════════════════════════════════════════════════
# Resign Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeaderResign:
    @pytest.mark.asyncio
    async def test_resign_removes_leader(self, election):
        await election.elect("node-a", 60)
        await election.resign("node-a")
        assert await election.get_leader() is None

    @pytest.mark.asyncio
    async def test_resign_non_leader_does_nothing(self, election):
        await election.elect("node-a", 60)
        await election.resign("node-b")
        leader = await election.get_leader()
        assert leader is not None
        assert leader.leader_id == "node-a"

    @pytest.mark.asyncio
    async def test_resign_when_no_leader_does_not_error(self, election):
        await election.resign("node-a")
        assert True

    @pytest.mark.asyncio
    async def test_after_resign_new_node_can_elect(self, election):
        await election.elect("node-a", 60)
        await election.resign("node-a")
        assert await election.elect("node-b", 60) is True
        leader = await election.get_leader()
        assert leader.leader_id == "node-b"
        assert leader.term == 1  # fresh term


# ═══════════════════════════════════════════════════════════════════════
# IsLeader Tests
# ═══════════════════════════════════════════════════════════════════════

class TestIsLeader:
    @pytest.mark.asyncio
    async def test_true(self, election):
        await election.elect("node-a", 60)
        assert await election.is_leader("node-a") is True

    @pytest.mark.asyncio
    async def test_false_for_follower(self, election):
        await election.elect("node-a", 60)
        assert await election.is_leader("node-b") is False

    @pytest.mark.asyncio
    async def test_false_when_no_leader(self, election):
        assert await election.is_leader("node-a") is False

    @pytest.mark.asyncio
    async def test_false_when_lease_expired(self, election):
        await election.elect("node-a", lease_seconds=-1)
        assert await election.is_leader("node-a") is False


# ═══════════════════════════════════════════════════════════════════════
# Concurrent Election Tests
# ═══════════════════════════════════════════════════════════════════════

class TestConcurrentElection:
    @pytest.mark.asyncio
    async def test_two_nodes_cannot_both_be_leader(self, db):
        e = _LeaderElection(db, "cluster-x")
        assert await e.elect("node-a", 60) is True
        assert await e.elect("node-b", 60) is False
        leader = await e.get_leader()
        assert leader.leader_id == "node-a"

    @pytest.mark.asyncio
    async def test_concurrent_elect_after_expiry(self, db):
        e = _LeaderElection(db, "cluster-y")
        await e.elect("node-old", lease_seconds=-1)
        # Yang pertama menang
        assert await e.elect("node-a", 60) is True
        # Yang kedua kalah
        assert await e.elect("node-b", 60) is False
        leader = await e.get_leader()
        assert leader.leader_id == "node-a"

    @pytest.mark.asyncio
    async def test_race_insert_vs_takeover(self, db):
        e = _LeaderElection(db, "cluster-z")
        assert await e.elect("node-a", 30) is True
        assert await e.elect("node-b", 30) is False
        leader = await e.get_leader()
        assert leader.leader_id == "node-a"
