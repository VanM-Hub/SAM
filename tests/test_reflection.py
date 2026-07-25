import asyncio
import pytest

from sam.healing.reflection import ReflectionManager, ReflectionRecord


class InMemoryDB:
    def __init__(self):
        self.rows = []

    async def execute(self, sql, params=None):
        # Simulate insert by storing a dict representation
        if params:
            # Map params to columns according to insertion order used in code
            row = {
                "id": params[0],
                "cycle_id": params[1],
                "symptom": params[2],
                "hypothesis": params[3],
                "action_taken": params[4],
                "expected_outcome": params[5],
                "actual_outcome": params[6],
                "gap_analysis": params[7],
                "lessons": params[8],
                "confidence": params[9],
                "success": params[10],
                "timestamp": params[11],
                "metadata": params[12],
            }
            self.rows.append(row)
        return None

    async def fetch_all(self, sql, params=None):
        # Support simple select all or by cycle_id
        if params and len(params) >= 1 and params[0] in [r["cycle_id"] for r in self.rows]:
            cycle_id = params[0]
            limit = params[1] if len(params) > 1 else 50
            offset = params[2] if len(params) > 2 else 0
            filtered = [r for r in self.rows if r["cycle_id"] == cycle_id]
            return filtered[offset: offset + limit]
        # generic
        limit = params[0] if params and len(params) >= 1 else 50
        offset = params[1] if params and len(params) >= 2 else 0
        return self.rows[offset: offset + limit]

    async def fetch_one(self, sql, params=None):
        # Support fetch by id or count
        if params and len(params) == 1:
            key = params[0]
            for r in self.rows:
                if r["id"] == key:
                    return r
        # count or latest
        if "COUNT" in sql.upper():
            return {"cnt": len(self.rows)}
        if "ORDER BY timestamp DESC LIMIT 1" in sql:
            if not self.rows:
                return None
            return self.rows[-1]
        return None


@pytest.mark.asyncio
async def test_record_and_get_reflection():
    db = InMemoryDB()
    rm = ReflectionManager(db=db)

    rec = await rm.record_reflection(
        cycle_id="cycle_1",
        symptom="test symptom",
        hypothesis="root cause",
        action_taken="did something",
        expected_outcome="ok",
        actual_outcome="ok",
        gap_analysis="none",
        lessons=["lesson a"],
        confidence=0.9,
        success=True,
        metadata={"k": "v"},
    )

    assert isinstance(rec, ReflectionRecord)
    fetched = await rm.get_reflection(rec.id)
    assert fetched is not None
    assert fetched.id == rec.id
    assert fetched.cycle_id == "cycle_1"
    assert fetched.lessons == ["lesson a"]


@pytest.mark.asyncio
async def test_get_lessons_summary():
    db = InMemoryDB()
    rm = ReflectionManager(db=db)

    await rm.record_reflection("c1", "s1", lessons=["l1"], success=True, confidence=0.8)
    await rm.record_reflection("c2", "s2", lessons=["l1"], success=False, confidence=0.4)
    await rm.record_reflection("c3", "s3", lessons=["l2"], success=True, confidence=0.7)

    summary = await rm.get_lessons_summary()
    # Expect l1 and l2 present
    lessons = [s["lesson"] for s in summary]
    assert "l1" in lessons
    assert "l2" in lessons
