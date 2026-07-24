"""Leader Election — mekanisme sederhana berbasis lease di Node Registry.

Setiap node dalam cluster dapat mencoba menjadi leader. Lease-based:
node yang menjadi leader harus memperpanjang lease secara periodik.
Jika lease expired, node lain dapat mengambil alih.

Integrasi:
- NodeRegistry: leader mengirim heartbeat khusus (flag is_leader=True)
- HeartbeatService: leader memperpanjang lease di setiap heartbeat
- Daemon: otomatis mencoba elect saat startup, resign saat shutdown
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

import structlog

# ── Enums ───────────────────────────────────────────────────────────

class LeaderState(str):
    """Status kepemimpinan sebuah node dalam cluster."""

    UNKNOWN = "UNKNOWN"
    ELECTED = "ELECTED"
    FOLLOWER = "FOLLOWER"


# ── Models ──────────────────────────────────────────────────────────

class LeaderRecord:
    """Record kepemimpinan term dalam cluster.

    Attributes:
        leader_id: Node ID yang memimpin.
        cluster_id: Cluster tempat leader berada.
        term: Nomor term kepemimpinan — meningkat setiap pergantian leader.
        lease_expires_at: Kapan lease leader berakhir (UTC).
        elected_at: Kapan leader terpilih (UTC).
    """

    def __init__(
        self,
        leader_id: str,
        cluster_id: str,
        term: int,
        lease_expires_at: datetime,
        elected_at: Optional[datetime] = None,
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

    def __repr__(self) -> str:
        return (
            f"LeaderRecord(leader={self.leader_id}, term={self.term}, "
            f"lease_expires={self.lease_expires_at.isoformat()})"
        )


# ── Error classes ───────────────────────────────────────────────────

class LeaderElectionError(Exception):
    """Base error untuk Leader Election."""


class LeaderNotFoundError(LeaderElectionError):
    """Tidak ada leader saat ini dalam cluster."""

    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        super().__init__(f"No leader found for cluster: {cluster_id}")


# ── Leader Election ─────────────────────────────────────────────────

class LeaderElection:
    """Leader Election — lease-based, optimistic locking via term.

    cluster_id adalah PRIMARY KEY di tabel cluster_leader — hanya satu
    row per cluster yang diizinkan.

    Cara kerja:
    1. INSERT OR ABORT — jika belum ada leader, jadi leader (term=1).
    2. Jika sudah ada leader, cek lease:
       a. Lease masih valid → return False
       b. Lease expired, node == leader_lama → renew dengan term sama
       c. Lease expired, node != leader_lama → takeover dengan term+1

    Thread safety: SQLite serializes writes; setiap operasi atomik.
    """

    _TABLE = "cluster_leader"

    def __init__(self, db: Any, cluster_id: str):
        self._db = db
        self._cluster_id = cluster_id
        self._logger = structlog.get_logger()

    # ── API ──────────────────────────────────────────────────────────

    async def elect(self, node_id: str, lease_seconds: int = 30) -> bool:
        """Coba menjadi leader untuk cluster ini.

        Returns:
            True jika berhasil menjadi leader, False jika gagal.
        """
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)

        # Step 1: Coba INSERT — valid jika belum ada leader di cluster ini
        try:
            await self._db.execute(
                f"""INSERT INTO {self._TABLE}
                    (leader_id, cluster_id, term, lease_expires_at, elected_at)
                    VALUES (?, ?, 1, ?, ?)""",
                [node_id, self._cluster_id, lease_at.isoformat(), now.isoformat()],
            )
            self._logger.info(
                "leader_elected",
                node_id=node_id,
                cluster_id=self._cluster_id,
                term=1,
            )
            return True
        except Exception:
            pass  # Leader sudah ada — lanjut ke Step 2

        # Step 2: Leader sudah ada — coba ambil alih jika lease expired
        return await self._attempt_takeover(node_id, lease_seconds)

    async def renew_lease(self, node_id: str, lease_seconds: int = 30) -> bool:
        """Perpanjang lease leader saat ini.

        Hanya leader yang valid (sesuai node_id) yang bisa perpanjang lease.

        Args:
            node_id: Node yang mencoba perpanjang lease.
            lease_seconds: Durasi lease baru dalam detik.

        Returns:
            True jika lease berhasil diperpanjang, False jika gagal.
        """
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)

        result = await self._db.execute(
            f"""UPDATE {self._TABLE}
                SET lease_expires_at=?, elected_at=?
                WHERE leader_id=? AND cluster_id=?""",
            [lease_at.isoformat(), now.isoformat(), node_id, self._cluster_id],
        )
        rows = self._rows_affected(result)
        if rows > 0:
            self._logger.debug(
                "leader_lease_renewed",
                node_id=node_id,
                lease_seconds=lease_seconds,
            )
            return True

        self._logger.warning(
            "leader_lease_renewal_failed",
            node_id=node_id,
            reason="not_current_leader",
        )
        return False

    async def get_leader(self) -> Optional[LeaderRecord]:
        """Dapatkan leader saat ini.

        Returns:
            LeaderRecord jika ada leader, None jika tidak ada.
        """
        row = await self._get_row()
        if not row:
            return None
        return self._row_to_record(dict(row) if not isinstance(row, dict) else row)

    async def resign(self, node_id: str) -> None:
        """Resign sebagai leader.

        Menghapus record leader dari database jika node_id cocok
        dengan leader saat ini.

        Args:
            node_id: Node yang mengundurkan diri.
        """
        row = await self._get_row()
        if not row:
            self._logger.debug("resign_no_leader", node_id=node_id)
            return

        current_leader = row["leader_id"] if isinstance(row, dict) else row[0]
        if current_leader != node_id:
            self._logger.warning(
                "resign_not_leader",
                node_id=node_id,
                current_leader=current_leader,
            )
            return

        await self._db.execute(
            f"DELETE FROM {self._TABLE} WHERE cluster_id=?",
            [self._cluster_id],
        )
        self._logger.info("leader_resigned", node_id=node_id)

    async def is_leader(self, node_id: str) -> bool:
        """Check apakah node tertentu adalah leader saat ini.

        Returns:
            True jika node adalah leader dan lease masih valid.
        """
        row = await self._get_row()
        if not row:
            return False

        d = dict(row) if not isinstance(row, dict) else row
        if d["leader_id"] != node_id:
            return False
        if self._is_lease_expired(d):
            return False
        return True

    # ── Internal ─────────────────────────────────────────────────────

    async def _attempt_takeover(self, node_id: str, lease_seconds: int) -> bool:
        """Coba ambil alih kepemimpinan setelah INSERT gagal."""
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)

        current = await self._get_row()
        if not current:
            # Race: INSERT gagal tapi row tidak ada — coba sekali lagi
            return await self._retry_insert(node_id, lease_seconds)

        d = dict(current) if not isinstance(current, dict) else current
        current_leader = d["leader_id"]
        is_expired = self._is_lease_expired(d)

        if not is_expired:
            # Leader valid — tidak bisa ambil alih
            return False

        if current_leader == node_id:
            # Leader lama (saya), lease expired — renew term sama
            await self._db.execute(
                f"""UPDATE {self._TABLE}
                    SET lease_expires_at=?, elected_at=?
                    WHERE leader_id=? AND cluster_id=?""",
                [lease_at.isoformat(), now.isoformat(), node_id, self._cluster_id],
            )
            self._logger.info("leader_reelected", node_id=node_id, term=d["term"])
            return True

        # Takeover dengan term baru
        new_term = d["term"] + 1
        result = await self._db.execute(
            f"""UPDATE {self._TABLE}
                SET leader_id=?, term=?, lease_expires_at=?, elected_at=?
                WHERE leader_id=? AND cluster_id=? AND term=?""",
            [node_id, new_term, lease_at.isoformat(), now.isoformat(),
             current_leader, self._cluster_id, d["term"]],
        )
        rows = self._rows_affected(result)
        if rows > 0:
            self._logger.info(
                "leader_takeover",
                node_id=node_id,
                previous_leader=current_leader,
                new_term=new_term,
            )
            return True

        self._logger.warning(
            "leader_takeover_race_lost",
            node_id=node_id,
            previous_leader=current_leader,
        )
        return False

    async def _retry_insert(self, node_id: str, lease_seconds: int) -> bool:
        """Coba INSERT sekali lagi saat race condition."""
        now = datetime.utcnow()
        lease_at = now + timedelta(seconds=lease_seconds)

        try:
            await self._db.execute(
                f"""INSERT INTO {self._TABLE}
                    (leader_id, cluster_id, term, lease_expires_at, elected_at)
                    VALUES (?, ?, 1, ?, ?)""",
                [node_id, self._cluster_id, lease_at.isoformat(), now.isoformat()],
            )
            self._logger.info("leader_elected_retry", node_id=node_id)
            return True
        except Exception:
            return False

    # ── Helpers ───────────────────────────────────────────────────────

    async def _get_row(self) -> Optional[dict]:
        return await self._db.fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE cluster_id=?",
            [self._cluster_id],
        )

    def _row_to_record(self, row: dict) -> LeaderRecord:
        return LeaderRecord(
            leader_id=row["leader_id"],
            cluster_id=row["cluster_id"],
            term=row["term"],
            lease_expires_at=datetime.fromisoformat(row["lease_expires_at"]),
            elected_at=datetime.fromisoformat(row["elected_at"]),
        )

    @staticmethod
    def _is_lease_expired(row: dict) -> bool:
        try:
            lease = datetime.fromisoformat(row["lease_expires_at"])
        except (ValueError, TypeError):
            return True
        return datetime.utcnow() > lease

    @staticmethod
    def _rows_affected(result: Any) -> int:
        if result is None:
            return 0
        if hasattr(result, "rowcount"):
            return result.rowcount
        return 0
