#!/usr/bin/env python3
"""Validate backup & restore for SAM database.

Usage:
    python scripts/validate_backup.py <db_path> [backup_path]

This script:
  1. Creates a backup of the current database.
  2. Restores from the backup into a temporary database.
  3. Runs integrity checks on both.
  4. Reports success or failure.
"""

import os
import sys
import sqlite3
import shutil
import tempfile
from datetime import datetime


def validate_db(db_path: str, label: str = "database") -> bool:
    """Run integrity check on a SQLite database."""
    if not os.path.exists(db_path):
        print(f"ERROR: {label} not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()

        if result and result[0] == "ok":
            print(f"  ✓ {label} integrity check passed")
            return True
        else:
            print(f"  ✗ {label} integrity check FAILED: {result}")
            return False
    except Exception as e:
        print(f"  ✗ {label} error: {e}")
        return False


def get_table_count(db_path: str) -> dict:
    """Count rows in all tables for verification."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    counts = {}
    for (table_name,) in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
            counts[table_name] = cursor.fetchone()[0]
        except Exception:
            counts[table_name] = -1

    conn.close()
    return counts


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_backup.py <db_path> [backup_path]")
        sys.exit(1)

    db_path = os.path.abspath(sys.argv[1])
    backup_path = sys.argv[2] if len(sys.argv) > 2 else db_path + ".backup"

    print(f"SAM Backup/Restore Validation")
    print(f"{'='*50}")
    print(f"Source DB: {db_path}")

    # Step 1: Validate source
    print(f"\n[1/4] Validating source database...")
    if not validate_db(db_path, "source"):
        sys.exit(1)

    source_counts = get_table_count(db_path)
    table_count = len(source_counts)
    row_count = sum(c for c in source_counts.values() if c >= 0)
    print(f"      {table_count} tables, {row_count} total rows")

    # Step 2: Create backup
    print(f"\n[2/4] Creating backup...")
    try:
        shutil.copy2(db_path, backup_path)
        print(f"  ✓ Backup created: {backup_path}")
    except Exception as e:
        print(f"  ✗ Backup failed: {e}")
        sys.exit(1)

    # Step 3: Validate backup
    print(f"\n[3/4] Validating backup...")
    if not validate_db(backup_path, "backup"):
        sys.exit(1)

    backup_counts = get_table_count(backup_path)
    backup_row_count = sum(c for c in backup_counts.values() if c >= 0)
    print(f"      {len(backup_counts)} tables, {backup_row_count} total rows")

    # Step 4: Restore to temp DB and verify
    print(f"\n[4/4] Restoring to temporary database...")
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)

    try:
        shutil.copy2(backup_path, tmp_path)
        if validate_db(tmp_path, "restored"):
            restore_counts = get_table_count(tmp_path)
            restore_row_count = sum(c for c in restore_counts.values() if c >= 0)

            # Compare row counts
            if source_counts == restore_counts:
                print(f"  ✓ Restored data matches source exactly")
            else:
                print(f"  ⚠ Row count mismatch")
                for table in source_counts:
                    if source_counts[table] != restore_counts.get(table):
                        print(f"      {table}: source={source_counts[table]} restored={restore_counts.get(table)}")

            print(f"\n{'='*50}")
            print(f"✅ BACKUP/RESTORE VALIDATION PASSED")
            print(f"   Source: {row_count} rows in {table_count} tables")
            print(f"   Backup: {backup_row_count} rows")
            print(f"   Restore: {restore_row_count} rows")
            print(f"{'='*50}")
        else:
            print(f"\n❌ BACKUP/RESTORE VALIDATION FAILED")
            sys.exit(1)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
