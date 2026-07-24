import pytest
import traceback

from sam.persistence.database import Database


@pytest.mark.asyncio
async def test_migrations_apply_and_correlation_columns_present(tmp_path):
    """Integration test: fresh DB -> initialize() -> migrations applied -> correlation_id columns exist.

    Uses a temporary database path (tmp_path fixture) so this is hermetic.
    """
    db_path = str(tmp_path / "sam.db")
    db = None
    try:
        db = Database(db_path)
        # initialize will run the migrations
        await db.initialize()

        # Verify schema_version table has the latest version
        row = await db.fetch_one("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        assert row is not None, "schema_version table is missing or empty after migrations"
        version = int(row["version"])
        # Expect migration version 2 (the correlation migration)
        assert version >= 2, f"Expected schema version >= 2, got {version}"

        # Tables that should include correlation_id
        tables = ["evidence", "knowledge", "patterns", "recommendations", "approvals"]

        for t in tables:
            try:
                cols = await db.fetch_all(f"PRAGMA table_info({t})")
            except Exception as e:
                pytest.fail(f"Error while inspecting table '{t}': {e}\n{traceback.format_exc()}")

            assert cols, f"Table '{t}' does not exist after migrations"
            col_names = [c["name"] for c in cols]
            assert (
                "correlation_id" in col_names
            ), f"Table '{t}' is missing 'correlation_id' column. Columns found: {col_names}"

    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"Migration integration test failed with exception: {exc}\n{traceback.format_exc()}")
    finally:
        if db is not None:
            try:
                await db.close()
            except Exception:
                pass
