# Architecture Freeze — v1.0.0

**Effective:** 2026-07-25  
**Status:** ✅ Frozen for v1.0.x lifecycle

---

## What "Freeze" Means

Starting with v1.0.0, the following aspects of SAM's architecture are **frozen** and will not change in a breaking way during the v1.x lifecycle:

1. **Public API contracts** (see `docs/history/audit/public_contracts.md`) will remain backward compatible.
2. **Database schema** (migrations 001–047) — existing tables and columns will not be removed or renamed.
3. **CLI command structure** — registered commands and their flags will not be removed.
4. **Module exports** — public `__all__` exports will remain available.
5. **Architectural layers** — the 4-layer model will remain the same.

## What Can Still Change

- Bug fixes (PATCH releases)
- New features (MINOR releases) via new modules or new CLI commands
- Performance improvements
- Additional database migrations (048+)
- Deprecation of features with proper notice (see `docs/development/api_stability.md`)

## Frozen Contracts

### CLI System (`sam.cli.main`)

```
app = typer.Typer()  # Main entry point
```

The following sub-apps are registered:

| Sub-app | Stable Since | Notes |
|---|---|---|
| `evolution` | v1.0 | Proposal management |
| `cluster` | v1.0 | Cluster operations |
| `federation` | v1.0 | Knowledge federation |
| `autonomy` | v1.0 | Autonomy & safety |

New sub-apps may be added in MINOR releases.

### Database Schema

The migration manager (`sam.persistence.migrations.manager.MigrationManager`) and database wrapper (`sam.persistence.database.Database`) are frozen interfaces.

### Module Structure

```
src/sam/
  cognition/     ── Frozen public API
  healing/       ── Frozen public API
  evolution/     ── Frozen public API
  tuning/        ── Frozen public API
  autonomy/      ── Frozen public API
  cluster/       ── Frozen public API
  federation/    ── Frozen public API
  cli/           ── Frozen command structure
```

## Unfreeze Process

If a breaking change to frozen architecture is absolutely necessary:

1. File an RFC (see `docs/development/RFC_PROCESS.md`)
2. Obtain consensus from architecture team
3. Schedule for next MAJOR version (v2.0)
4. Provide deprecation path for at least 2 MINOR versions

## Verification

Every PR to `main` must verify:
- All existing tests pass
- No public API signatures changed
- No database migrations altered retroactively

---

*Document prepared for SAM v1.0.0 release.*
