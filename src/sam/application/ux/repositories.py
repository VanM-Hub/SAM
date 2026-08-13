"""repositories.py — Repository ports + PostgreSQL implementation (M12-001).

Durable State Foundation.

Clean Architecture:
    Domain (entity / port interface)
        ↓
    Repository Port (interface — domain-owned, di file ini)
        ↓
    Application Service (menggunakan port, tidak tahu backend)
        ↓
    Repository Implementation (PostgreSQL, class Postgres*Repository di file ini)
        ↓
    PostgreSQL

Tujuan M12-001:
  - State operasional (mission / execution / approval / audit / evidence /
    idempotency) dipersist PER-ENTITY (keyed by id), bukan satu blob global.
  - Mission A, B, C dapat hidup bersamaan tanpa saling overwrite.
  - Domain (service) bergantung pada PROTOCOL/interface repository, bukan pada
    PostgreSQL secara langsung. Backend (PG / JSON / in-memory) dapat di-swap.

Konten yang disimpan TIDAK pernah memuat secret (state bukan token; nilai
tersimpan sudah di-sanitize oleh boundary sebelum sampai di sini — sama seperti
store.py / pgstore.py).
"""
from __future__ import annotations

import json
import os
import psycopg2
from typing import Any, Dict, List, Optional, Protocol


# ---------------------------------------------------------------------------
# Repository Ports (domain-owned interfaces). Service bergantung pada ini.
# ---------------------------------------------------------------------------
class MissionRepository(Protocol):
    """State mission per mission_id (understanding, plan, approval, execution)."""

    def save_mission(self, mission_id: str, data: Dict[str, Any]) -> None: ...
    def load_mission(self, mission_id: str) -> Optional[Dict[str, Any]]: ...
    def list_missions(self) -> List[str]: ...
    def remove_mission(self, mission_id: str) -> None: ...


class ExecutionRepository(Protocol):
    """Lifecycle execution per execution_id."""

    def save_execution(self, execution_id: str, data: Dict[str, Any]) -> None: ...
    def load_execution(self, execution_id: str) -> Optional[Dict[str, Any]]: ...
    def list_executions(self, mission_id: str) -> List[str]: ...
    def remove_execution(self, execution_id: str) -> None: ...


class ApprovalRepository(Protocol):
    """Approval decision per approval_id."""

    def save_approval(self, approval_id: str, data: Dict[str, Any]) -> None: ...
    def load_approval(self, approval_id: str) -> Optional[Dict[str, Any]]: ...
    def list_approvals(self, mission_id: str) -> List[str]: ...
    def remove_approval(self, approval_id: str) -> None: ...


class AuditRepository(Protocol):
    """Audit trail per entry id (sanitized)."""

    def append_audit(self, audit_id: str, data: Dict[str, Any]) -> None: ...
    def load_audit(self, mission_id: Optional[str] = None) -> List[Dict[str, Any]]: ...
    def clear_audit(self) -> None: ...


class EvidenceRepository(Protocol):
    """Evidence per execution_id."""

    def save_evidence(self, execution_id: str, data: Dict[str, Any]) -> None: ...
    def load_evidence(self, execution_id: str) -> List[Dict[str, Any]]: ...
    def remove_evidence(self, execution_id: str) -> None: ...


class IdempotencyRepository(Protocol):
    """Durable idempotency: key -> recorded execution identity (M12-002)."""

    def save_idempotency(
        self, key: str, data: Dict[str, Any], mission_id: Optional[str] = None
    ) -> None: ...
    def load_idempotency(self, key: str) -> Optional[Dict[str, Any]]: ...
    def list_keys(self) -> List[str]: ...
    def clear(self) -> None: ...


# Generic interface dipakai service untuk mengelola 6 repo sebagai satu unit.
class PersistenceUnit(Protocol):
    missions: MissionRepository
    executions: ExecutionRepository
    approvals: ApprovalRepository
    audit: AuditRepository
    evidence: EvidenceRepository
    idempotency: IdempotencyRepository

    def ping(self) -> bool: ...
    def close(self) -> None: ...


# ---------------------------------------------------------------------------
# PostgreSQL implementation (Infrastructure)
# ---------------------------------------------------------------------------
def _environ_dsn() -> str:
    """DSN dari env produksi; DSN eksplisit dapat menimpa ini."""
    pw = os.environ.get("SAM_PG_PASSWORD", "")
    return (
        f"host={os.environ.get('SAM_PG_HOST', '127.0.0.1')} "
        f"port={os.environ.get('SAM_PG_PORT', '5432')} "
        f"dbname={os.environ.get('SAM_PG_DB', 'sam')} "
        f"user={os.environ.get('SAM_PG_USER', 'sam')} "
        f"password={pw}"
    )


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sam_mission (
    mission_id  TEXT PRIMARY KEY,
    data        JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sam_execution (
    execution_id TEXT PRIMARY KEY,
    mission_id   TEXT NOT NULL,
    data         JSONB NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sam_execution_mission ON sam_execution(mission_id);
CREATE TABLE IF NOT EXISTS sam_approval (
    approval_id TEXT PRIMARY KEY,
    mission_id  TEXT NOT NULL,
    data        JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sam_approval_mission ON sam_approval(mission_id);
CREATE TABLE IF NOT EXISTS sam_audit (
    audit_id    TEXT PRIMARY KEY,
    mission_id  TEXT,
    data        JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sam_audit_mission ON sam_audit(mission_id);
CREATE TABLE IF NOT EXISTS sam_evidence (
    execution_id TEXT NOT NULL,
    seq          SERIAL,
    data         JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (execution_id, seq)
);
CREATE TABLE IF NOT EXISTS sam_idempotency (
    key         TEXT PRIMARY KEY,
    mission_id  TEXT,
    data        JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


class _PgBase:
    """Helper koneksi + init schema."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        self._dsn = dsn or _environ_dsn()

    def _conn(self):
        conn = psycopg2.connect(self._dsn)
        conn.autocommit = True
        return conn

    def init_schema(self) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA)
        finally:
            conn.close()


class PgMissionRepository(MissionRepository):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self._base = _PgBase(dsn)

    def save_mission(self, mission_id: str, data: Dict[str, Any]) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    """INSERT INTO sam_mission (mission_id, data, updated_at)
                       VALUES (%s, %s::jsonb, now())
                       ON CONFLICT (mission_id) DO UPDATE
                         SET data=EXCLUDED.data, updated_at=now()""",
                    (mission_id, _dumps(data)),
                )
        finally:
            c.close()

    def load_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("SELECT data FROM sam_mission WHERE mission_id=%s", (mission_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                p = row[0]
                return dict(p) if isinstance(p, dict) else json.loads(p)
        except Exception:
            return None
        finally:
            c.close()

    def list_missions(self) -> List[str]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("SELECT mission_id FROM sam_mission ORDER BY updated_at")
                return [r[0] for r in cur.fetchall()]
        finally:
            c.close()

    def remove_mission(self, mission_id: str) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("DELETE FROM sam_mission WHERE mission_id=%s", (mission_id,))
        finally:
            c.close()


class PgExecutionRepository(ExecutionRepository):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self._base = _PgBase(dsn)

    def save_execution(self, execution_id: str, data: Dict[str, Any]) -> None:
        mission_id = (data or {}).get("mission_id", "")
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    """INSERT INTO sam_execution (execution_id, mission_id, data, updated_at)
                       VALUES (%s,%s,%s::jsonb, now())
                       ON CONFLICT (execution_id) DO UPDATE
                         SET mission_id=EXCLUDED.mission_id, data=EXCLUDED.data, updated_at=now()""",
                    (execution_id, mission_id, _dumps(data)),
                )
        finally:
            c.close()

    def load_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("SELECT data FROM sam_execution WHERE execution_id=%s", (execution_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                p = row[0]
                return dict(p) if isinstance(p, dict) else json.loads(p)
        finally:
            c.close()

    def list_executions(self, mission_id: str) -> List[str]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT execution_id FROM sam_execution WHERE mission_id=%s ORDER BY updated_at",
                    (mission_id,),
                )
                return [r[0] for r in cur.fetchall()]
        finally:
            c.close()

    def remove_execution(self, execution_id: str) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("DELETE FROM sam_execution WHERE execution_id=%s", (execution_id,))
        finally:
            c.close()


class PgApprovalRepository(ApprovalRepository):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self._base = _PgBase(dsn)

    def save_approval(self, approval_id: str, data: Dict[str, Any]) -> None:
        mission_id = (data or {}).get("mission_id", "")
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    """INSERT INTO sam_approval (approval_id, mission_id, data, updated_at)
                       VALUES (%s,%s,%s::jsonb, now())
                       ON CONFLICT (approval_id) DO UPDATE
                         SET mission_id=EXCLUDED.mission_id, data=EXCLUDED.data, updated_at=now()""",
                    (approval_id, mission_id, _dumps(data)),
                )
        finally:
            c.close()

    def load_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("SELECT data FROM sam_approval WHERE approval_id=%s", (approval_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                p = row[0]
                return dict(p) if isinstance(p, dict) else json.loads(p)
        finally:
            c.close()

    def list_approvals(self, mission_id: str) -> List[str]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT approval_id FROM sam_approval WHERE mission_id=%s ORDER BY updated_at",
                    (mission_id,),
                )
                return [r[0] for r in cur.fetchall()]
        finally:
            c.close()

    def remove_approval(self, approval_id: str) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("DELETE FROM sam_approval WHERE approval_id=%s", (approval_id,))
        finally:
            c.close()


class PgAuditRepository(AuditRepository):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self._base = _PgBase(dsn)

    def append_audit(self, audit_id: str, data: Dict[str, Any]) -> None:
        mission_id = (data or {}).get("mission_id")
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    "INSERT INTO sam_audit (audit_id, mission_id, data) VALUES (%s,%s,%s::jsonb)",
                    (audit_id, mission_id, _dumps(data)),
                )
        finally:
            c.close()

    def load_audit(self, mission_id: Optional[str] = None) -> List[Dict[str, Any]]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                if mission_id:
                    cur.execute(
                        "SELECT data FROM sam_audit WHERE mission_id=%s ORDER BY created_at, audit_id",
                        (mission_id,),
                    )
                else:
                    cur.execute("SELECT data FROM sam_audit ORDER BY created_at, audit_id")
                out = []
                for (p,) in cur.fetchall():
                    out.append(dict(p) if isinstance(p, dict) else json.loads(p))
                return out
        finally:
            c.close()

    def clear_audit(self) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("DELETE FROM sam_audit")
        finally:
            c.close()


class PgEvidenceRepository(EvidenceRepository):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self._base = _PgBase(dsn)

    def save_evidence(self, execution_id: str, data: Dict[str, Any]) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    "INSERT INTO sam_evidence (execution_id, data) VALUES (%s,%s::jsonb)",
                    (execution_id, _dumps(data)),
                )
        finally:
            c.close()

    def load_evidence(self, execution_id: str) -> List[Dict[str, Any]]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT data FROM sam_evidence WHERE execution_id=%s ORDER BY seq",
                    (execution_id,),
                )
                out = []
                for (p,) in cur.fetchall():
                    out.append(dict(p) if isinstance(p, dict) else json.loads(p))
                return out
        finally:
            c.close()

    def remove_evidence(self, execution_id: str) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("DELETE FROM sam_evidence WHERE execution_id=%s", (execution_id,))
        finally:
            c.close()


class PgIdempotencyRepository(IdempotencyRepository):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self._base = _PgBase(dsn)

    def save_idempotency(
        self, key: str, data: Dict[str, Any], mission_id: Optional[str] = None
    ) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute(
                    """INSERT INTO sam_idempotency (key, mission_id, data, updated_at)
                       VALUES (%s,%s,%s::jsonb, now())
                       ON CONFLICT (key) DO UPDATE
                         SET mission_id=EXCLUDED.mission_id, data=EXCLUDED.data, updated_at=now()""",
                    (key, mission_id, _dumps(data)),
                )
        finally:
            c.close()

    def load_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("SELECT data FROM sam_idempotency WHERE key=%s", (key,))
                row = cur.fetchone()
                if row is None:
                    return None
                p = row[0]
                return dict(p) if isinstance(p, dict) else json.loads(p)
        finally:
            c.close()

    def list_keys(self) -> List[str]:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("SELECT key FROM sam_idempotency ORDER BY updated_at")
                return [r[0] for r in cur.fetchall()]
        finally:
            c.close()

    def clear(self) -> None:
        c = self._base._conn()
        try:
            with c.cursor() as cur:
                cur.execute("DELETE FROM sam_idempotency")
        finally:
            c.close()


class PostgresPersistenceUnit(PersistenceUnit):
    """Kumpulan 6 repository PostgreSQL + ping/close. Menyatu agar service
    memperlakukan persistence sebagai satu unit (transaksi logis per save)."""

    def __init__(self, dsn: Optional[str] = None, init_schema: bool = True) -> None:
        self.dsn = dsn or _environ_dsn()
        self.missions = PgMissionRepository(self.dsn)
        self.executions = PgExecutionRepository(self.dsn)
        self.approvals = PgApprovalRepository(self.dsn)
        self.audit = PgAuditRepository(self.dsn)
        self.evidence = PgEvidenceRepository(self.dsn)
        self.idempotency = PgIdempotencyRepository(self.dsn)
        if init_schema:
            self.missions._base.init_schema()

    def ping(self) -> bool:
        try:
            c = self.missions._base._conn()
            try:
                with c.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone()[0] == 1
            finally:
                c.close()
        except Exception:
            return False

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# In-memory implementation (untuk test / dev default — regresi M10 aman)
# ---------------------------------------------------------------------------
class InMemoryMissionRepository(MissionRepository):
    def __init__(self) -> None:
        self._d: Dict[str, Dict[str, Any]] = {}

    def save_mission(self, mission_id: str, data: Dict[str, Any]) -> None:
        self._d[mission_id] = dict(data)

    def load_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        v = self._d.get(mission_id)
        return dict(v) if v is not None else None

    def list_missions(self) -> List[str]:
        return list(self._d.keys())

    def remove_mission(self, mission_id: str) -> None:
        self._d.pop(mission_id, None)


class InMemoryExecutionRepository(ExecutionRepository):
    def __init__(self) -> None:
        self._d: Dict[str, Dict[str, Any]] = {}

    def save_execution(self, execution_id: str, data: Dict[str, Any]) -> None:
        self._d[execution_id] = dict(data)

    def load_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        v = self._d.get(execution_id)
        return dict(v) if v is not None else None

    def list_executions(self, mission_id: str) -> List[str]:
        return [k for k, v in self._d.items() if (v or {}).get("mission_id") == mission_id]

    def remove_execution(self, execution_id: str) -> None:
        self._d.pop(execution_id, None)


class InMemoryApprovalRepository(ApprovalRepository):
    def __init__(self) -> None:
        self._d: Dict[str, Dict[str, Any]] = {}

    def save_approval(self, approval_id: str, data: Dict[str, Any]) -> None:
        self._d[approval_id] = dict(data)

    def load_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        v = self._d.get(approval_id)
        return dict(v) if v is not None else None

    def list_approvals(self, mission_id: str) -> List[str]:
        return [k for k, v in self._d.items() if (v or {}).get("mission_id") == mission_id]

    def remove_approval(self, approval_id: str) -> None:
        self._d.pop(approval_id, None)


class InMemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self._d: Dict[str, Dict[str, Any]] = {}

    def append_audit(self, audit_id: str, data: Dict[str, Any]) -> None:
        self._d[audit_id] = dict(data)

    def load_audit(self, mission_id: Optional[str] = None) -> List[Dict[str, Any]]:
        items = sorted(self._d.items(), key=lambda kv: kv[0])
        return [dict(v) for k, v in items
                if mission_id is None or (v or {}).get("mission_id") == mission_id]

    def clear_audit(self) -> None:
        self._d.clear()


class InMemoryEvidenceRepository(EvidenceRepository):
    def __init__(self) -> None:
        self._d: Dict[str, List[Dict[str, Any]]] = {}

    def save_evidence(self, execution_id: str, data: Dict[str, Any]) -> None:
        self._d.setdefault(execution_id, []).append(dict(data))

    def load_evidence(self, execution_id: str) -> List[Dict[str, Any]]:
        return [dict(v) for v in self._d.get(execution_id, [])]

    def remove_evidence(self, execution_id: str) -> None:
        self._d.pop(execution_id, None)


class InMemoryIdempotencyRepository(IdempotencyRepository):
    def __init__(self) -> None:
        self._d: Dict[str, Dict[str, Any]] = {}

    def save_idempotency(
        self, key: str, data: Dict[str, Any], mission_id: Optional[str] = None
    ) -> None:
        rec = dict(data)
        rec["mission_id"] = mission_id
        self._d[key] = rec

    def load_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        v = self._d.get(key)
        return dict(v) if v is not None else None

    def list_keys(self) -> List[str]:
        return list(self._d.keys())

    def clear(self) -> None:
        self._d.clear()


class InMemoryPersistenceUnit(PersistenceUnit):
    """Default dev/test: state aman di-disk-less, regresi M10 tidak berubah."""

    def __init__(self) -> None:
        self.missions = InMemoryMissionRepository()
        self.executions = InMemoryExecutionRepository()
        self.approvals = InMemoryApprovalRepository()
        self.audit = InMemoryAuditRepository()
        self.evidence = InMemoryEvidenceRepository()
        self.idempotency = InMemoryIdempotencyRepository()

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        pass
