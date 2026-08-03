# Upgrade Path — v1.0

**Date:** 2026-07-25

---

## Overview

SAM v1.0 is the first stable release. There are no prior production versions to upgrade from. This document covers:
- First-time installation
- Data migration for beta/pre-release users (if applicable)
- Breaking changes from earlier development snapshots

## First-Time Installation

See [README.md](/README.md) for installation instructions. TL;DR:

```bash
git clone https://github.com/your-org/sam.git
cd sam
pip install -e .
```

Create a fresh database:

```bash
sam daemon init-db  # or let SAM auto-create on first start
```

## Upgrading from Beta / Development Snapshots

If you ran SAM from the `feature/sprint13-plugin-runtime` branch:

### Step 1: Backup
```bash
cp sam.db sam.db.backup.$(date +%Y%m%d)
```

### Step 2: Pull latest
```bash
git checkout main
git pull origin main
```

### Step 3: Run migrations
```bash
sam daemon migrate  # applies any pending migrations
```

### Step 4: Verify
```bash
sam health
```

## Migration History

| Version | Migration | Changes |
|---|---|---|
| v0.1–0.28 (dev) | 001–036 | Workflow engine, governance, healing, optimization |
| v0.29 (dev) | 037–042 | Cognitive runtime, attention, arbitration, context, sessions |
| v0.30 (dev) | 043–045 | Cross-cluster intelligence |
| v0.31 (dev) | 046 | Knowledge federation |
| v0.32 (dev) | 047 | Autonomous runtime & safety |
| **v1.0.0** | **001–047** | **Cumulative: 47 migrations, all idempotent** |

## Breaking Changes

- **v0.x → v1.0**: No breaking changes from Sprint 28+ development. Backward compatible within the 047 migration range.
- **Pre-Sprint 28**: Not supported for direct upgrade. Fresh install recommended.

## Rollback

```bash
# 1. Restore database backup
cp sam.db.backup.* sam.db

# 2. Revert code
git checkout <previous-tag>

# 3. Verify
sam health
```

---

*Document prepared for SAM v1.0.0 release.*
