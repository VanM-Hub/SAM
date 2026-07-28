"""
Repository Layer — OP-132, OP-133.

AbstractRepository: base interface untuk semua repository.
ConnectionManager: SQLite connection manager, auto-migration.

Pattern:
  - Repository adalah satu-satunya yang menyentuh SQLite
  - Repository mengembalikan dict atau dataclass
  - Repository tidak berisi business logic
  - Cache opsional di domain logic
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import sqlite3
import os
import json
import threading


SAM_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))),
    "data", "sam.db"
)

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))),
    "data", "migrations"
)


class ConnectionManager:
    """SQLite connection manager.

    - Single connection per thread (thread-local)
    - WAL mode for concurrent read/write safety
    - Auto-creates data/ directory and runs migrations
    - `BEGIN IMMEDIATE` for write transactions
    """

    _local = threading.local()
    _initialized = False

    @classmethod
    def ensure_data_dir(cls):
        db_dir = os.path.dirname(SAM_DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        mig_dir = MIGRATIONS_DIR
        if not os.path.exists(mig_dir):
            os.makedirs(mig_dir, exist_ok=True)

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(cls._local, 'conn') or cls._local.conn is None:
            cls.ensure_data_dir()
            conn = sqlite3.connect(SAM_DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            cls._local.conn = conn
            if not cls._initialized:
                cls._run_migrations(conn)
                cls._initialized = True
        return cls._local.conn

    @classmethod
    def close(cls):
        if hasattr(cls._local, 'conn') and cls._local.conn:
            cls._local.conn.close()
            cls._local.conn = None

    @classmethod
    def _run_migrations(cls, conn: sqlite3.Connection):
        """Run all pending migrations."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                version INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        applied = set()
        for row in conn.execute("SELECT filename FROM _schema_migrations"):
            applied.add(row['filename'])

        if not os.path.exists(MIGRATIONS_DIR):
            return

        migrations = sorted([
            f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')
        ])
        for mf in migrations:
            if mf in applied:
                continue
            path = os.path.join(MIGRATIONS_DIR, mf)
            with open(path, 'r') as fh:
                sql = fh.read()
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _schema_migrations (filename) VALUES (?)",
                (mf,)
            )
            conn.commit()

    @classmethod
    def begin_write(cls):
        conn = cls.get_connection()
        conn.execute("BEGIN IMMEDIATE;")

    @classmethod
    def commit(cls):
        conn = cls.get_connection()
        conn.commit()

    @classmethod
    def rollback(cls):
        conn = cls.get_connection()
        conn.rollback()

    @classmethod
    def reset(cls):
        """Hapus database dan buat ulang (untuk testing)."""
        cls.close()
        if os.path.exists(SAM_DB_PATH):
            os.remove(SAM_DB_PATH)
        for wal in [SAM_DB_PATH + '-wal', SAM_DB_PATH + '-shm']:
            if os.path.exists(wal):
                os.remove(wal)
        cls._initialized = False
        cls._local = threading.local()


class AbstractRepository(ABC):
    """Base repository interface.

    Setiap repository domain harus extend ini.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._conn = conn

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn:
            return self._conn
        return ConnectionManager.get_connection()

    @abstractmethod
    def ensure_schema(self):
        """Buat tabel jika belum ada."""
        ...

    @abstractmethod
    def to_row(self, obj: Any) -> dict:
        """Convert domain object ke dict untuk insert."""
        ...

    def dict_to_row(self, d: dict, columns: List[str]) -> Dict[str, Any]:
        """Filter dict hanya untuk kolom yang ada."""
        return {k: d[k] for k in columns if k in d}

    def row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert sqlite3.Row ke dict."""
        return dict(row)

    def to_obj(self, row_dict: dict) -> Any:
        """Convert dict ke domain object. Override di subclass."""
        return row_dict

    def serialize_json(self, val: Any) -> str:
        return json.dumps(val, default=str)

    def deserialize_json(self, val: Optional[str]) -> Any:
        if val is None:
            return None
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
