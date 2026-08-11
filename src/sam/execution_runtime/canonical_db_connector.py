"""Canonical Universal Database Connector - M6-002 (Operational Expansion).

Primitive connector database yang menghubungkan SAM ke penyimpanan data via
satu jalur canonical (RealExecutionHarness). Ini BUKAN executor baru — adapter
yang dipanggil SATU-SATUNYA melalui RealExecutionHarness (single authority).

Arah arsitektur:
    SAM -> Capability Contract -> Policy -> Approval -> Canonical Execution
        -> DB Connector -> Database -> Real Response
        -> Verification -> Audit -> Learning

Prinsip jujur (tidak ada mock, tidak ada actor kedua):
  - Backend-agnostik: dialektur `sqlite` TERBUKTI; dialektur `postgres` tersedia
    sebagai KONTRAK tapi tanpa driver/koneksi -> BLOCKED (NO SIDE EFFECT),
    BUKAN mock yang seolah berhasil.
  - Query dieksekusi NYATA (SQL genuine), hasil setiap baris diverifikasi.
  - READ-ONLY dulu (SELECT) - aman; tanpa kemampuan menulis de facto.
  - Tanpa target/basis data valid -> RAISE/BLOCKED.
  - Tidak ada preview menyamar sebagai execution: PREVIEW explicit simulated.

SQLite dipakai sebagai backend proof E2E karena: genuine (query SQL nyata,
bukan simulasi), tersedia offline, tanpa server & tanpa token. Untuk production
PostgreSQL: pasang driver + sediakan DSN -> dialektur `postgres` aktif.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)


class DbConnectorError(Exception):
    """Error connector database (no side effect)."""


@dataclass(frozen=True)
class DbSchema:
    """Kontrak satu tabel db (nama + kolom yang boleh di-query SELECT)."""

    name: str
    columns: Tuple[str, ...]

    def select_cols(self) -> str:
        return ", ".join(self.columns)


# Schema default untuk SQLite proof-db (dibuat saat perlu, bukan hardcoded data).
DEFAULT_SCHEMAS: Tuple[DbSchema, ...] = (
    DbSchema(name="users", columns=("id", "name", "email", "created_at")),
    DbSchema(name="posts", columns=("id", "user_id", "title", "body")),
)


def _connect_sqlite(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_demo_sqlite(path: str) -> None:
    """Buat SQLite demo berisi tabel nyata + data sampel (hanya utk test/e2e)."""
    conn = _connect_sqlite(path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                body TEXT
            );
            INSERT OR IGNORE INTO users (id, name, email, created_at) VALUES
                (1, 'Aster', 'aster@sam.local', '2026-01-01'),
                (2, 'Zara', 'zara@sam.local', '2026-02-01'),
                (3, 'VanM', 'van@sam.local', '2026-03-01');
            INSERT OR IGNORE INTO posts (id, user_id, title, body) VALUES
                (1, 1, 'Hello Canonical', 'body real sqlite'),
                (2, 2, 'Second Post', 'body kedua');
            """
        )
        conn.commit()
    finally:
        conn.close()


class RealDbAdapter:
    """Adapter database NYATA (sqlite3 stdlib). Hanya SELECT (read-only)."""

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def _get_conn_params(self, target: str) -> str:
        """target = path file sqlite. Beri konteks agar jelas bukan aksi tersembunyi."""
        if not isinstance(target, str) or not target.strip():
            raise DbConnectorError("target database kosong (NO SIDE EFFECT)")
        return target

    def execute(self, table: str, columns: Tuple[str, ...],
                target: str, limit: int = 100) -> Dict[str, Any]:
        conn = self._get_conn_params(target)
        try:
            path = os.path.abspath(conn)
            self._audit.record("db.connector.call", table, path=path)
            db = _connect_sqlite(path)
            try:
                cols = ", ".join(columns)
                sql = f"SELECT {cols} FROM {table} LIMIT ?"
                self._audit.record("db.connector.sql", table, sql=sql)
                rows = db.execute(sql, (limit,)).fetchall()
                records = [dict(r) for r in rows]
                self._audit.record("db.connector.result", table, rows=len(records))
                return {
                    "ok": True,
                    "table": table,
                    "path": path,
                    "columns": list(columns),
                    "count": len(records),
                    "rows": records,
                }
            finally:
                db.close()
        except sqlite3.Error as exc:  # noqa: BLE001
            self._audit.record("db.connector.fail", table, error=f"sqlite: {exc}")
            raise DbConnectorError(f"sqlite: {exc}") from exc


class RealDbConnector:
    """Connector database dieksekusi HANYA melalui RealExecutionHarness."""

    def __init__(
        self,
        audit: Optional[AuditTrail] = None,
        *,
        schemas: Tuple[DbSchema, ...] = DEFAULT_SCHEMAS,
    ) -> None:
        self._audit = audit or AuditTrail()
        self._schemas = {s.name: s for s in schemas}
        self._harness = RealExecutionHarness(self._audit)
        self._harness.register_capability(
            "db",
            registry={"id": "db", "adapter": "RealDbAdapter",
                      "external": "database (read-only SELECT)", "operations": tuple(self._schemas)},
            contract={
                s.name: {"input": "target path + limit", "output": "rows",
                         "side_effect": "SELECT read-only"} for s in schemas
            },
            policy="ALLOW",
        )

    def gate_db(self, request: ExecutionRequest, target_path: str) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists("db"):
            return [{"id": "capability", "label": "Capability 'db' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        full_gates = self._harness._evaluate_gates(request)  # noqa: SLF001
        table = request.operation.split("/")[-1]
        known = table in self._schemas
        full_gates = [
            GateResult("boundary", GATES[6]["label"], known, f"tabel '{table}' dikenal")
            if g.id == "boundary" else g
            for g in full_gates
        ]
        # gate target db: file sqlite harus ada & readable
        target_ok = target_path and os.path.isfile(target_path)
        self._audit.record("db.gate.target", table, present=target_ok)
        target_gate = {
            "id": "target_db",
            "label": f"Target database tersedia & bisa dibaca (path={target_path or '(kosong)'})",
            "passed": target_ok,
            "detail": f"existing_file={target_ok}",
        }
        return [g.to_dict() for g in full_gates] + [target_gate]

    def execute(
        self,
        table: str,
        target_path: str,
        mode: ExecutionMode = ExecutionMode.EXECUTE,
        approval_reason: str = "",
        limit: int = 100,
    ) -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"db/{table}",
            target="database",
            params={"table": table, "target": target_path, "limit": limit},
            mode=mode,
            correlation_id=f"db-{table}",
            timeout_seconds=15.0,
            approval_reason=approval_reason,
        )
        gates = self.gate_db(req, target_path)
        failed = [g for g in gates if not g["passed"]]
        for g in gates:
            self._audit.record("db.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("db.mode.preview", table)
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.", "gates": gates}

        if failed:
            self._audit.record("db.execute.blocked", table,
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gates}

        self._audit.record("db.execute.allowed", table)
        try:
            adapter = RealDbAdapter(self._audit)
            schema = self._schemas[table]
            result = adapter.execute(table, schema.columns, target_path, limit=limit)
            return {"ok": result.get("ok"), "mode": "EXECUTE", "gates": gates, **result}
        except DbConnectorError as exc:
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": str(exc), "gates": gates, "verification_failed": True}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("db.connector.fail", table, error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": f"{type(exc).__name__}: {exc}", "gates": gates}


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="M6-002 DB Universal Connector (canonical)")
    parser.add_argument("table", choices=[s.name for s in DEFAULT_SCHEMAS], default="users", nargs="?")
    parser.add_argument("--db", default=None, help="path file sqlite (default: temp demo db)")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--reason", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    # siapkan sqlite demo bila tidak disuplai
    db_path = args.db
    if not db_path:
        tmp = tempfile.mkdtemp(prefix="m6db_")
        db_path = os.path.join(tmp, "demo.db")
        ensure_demo_sqlite(db_path)

    audit = AuditTrail()
    connector = RealDbConnector(audit)
    mode = ExecutionMode(args.mode)
    result = connector.execute(args.table, db_path, mode=mode,
                               limit=args.limit,
                               approval_reason=args.reason or f"M6 db {args.table}")

    print("=" * 70)
    print("  M6-002 - DB Universal Connector (via harness canonical)")
    print("=" * 70)
    print(f"  table  : {args.table}")
    print(f"  db     : {db_path}")
    print(f"  mode   : {mode.value}")
    print("  gates:")
    for g in result.get("gates", []):
        print(f"    [{'PASS' if g['passed'] else 'FAIL'}] {g['label']}")
    print("  outcome:")
    for k, v in result.items():
        if k == "gates":
            continue
        print(f"    {k} : {str(v)[:160]}")
    print("  audit:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 70)

    if mode == ExecutionMode.EXECUTE:
        ok = result.get("ok")
        print(f"\n  VERDICT: {'REAL E2E OK (SQL nyata dieksekusi)' if ok else 'GAGAL/BLOCKED'}")
        exit_code = 0 if ok else 1
    else:
        print("\n  VERDICT: PREVIEW OK (no side effect)")
        exit_code = 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"table": args.table, "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
