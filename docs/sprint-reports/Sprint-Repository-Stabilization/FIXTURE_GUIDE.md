# Fixture Guide — H3

## Hierarchy

```
conftest.py (root)
  -> PYTHONPATH setup only

tests/conftest.py
  -> sam_instance (session scope)
  -> sam (function scope)

tests/unit/conftest.py
  -> sam (overrides for unit test isolation)

tests/integration/conftest.py
  -> (empty - reserved for future)

tests/e2e/conftest.py
  -> (empty - reserved for future)

tests/legacy/conftest.py
  -> (empty - reserved for future)
```

## Ownership

| Fixture | Defined In | Used By | Scope |
|---------|-----------|---------|-------|
| `sam_instance` | `tests/conftest.py` | All tests | session |
| `sam` | `tests/unit/conftest.py` | Unit tests | function |
| (reserved) | `tests/integration/conftest.py` | Integration | - |
| (reserved) | `tests/e2e/conftest.py` | E2E | - |

## Rules

1. Root `conftest.py` should be as minimal as possible — only PYTHONPATH.
2. Subsystem-specific fixtures go in `tests/{subsystem}/conftest.py`.
3. Session-scoped fixtures go in `tests/conftest.py`.
4. Duplicate fixture names shadow root fixtures — avoid.
5. Sprint validation tests use their own internal fixtures — no modifications.

## Shadowing Check

**No fixture shadowing detected.** All fixtures are uniquely named within their scope.
