# RC2 Validation Guide for Linux

> Untuk Van — jalankan langkah-langkah ini di environment Linux.

## Prerequisites

```bash
# 1. Python 3.12
python3 --version  # Must be 3.12.x

# 2. Clone repo
git clone https://github.com/VanM-Hub/SAM.git
cd SAM

# 3. Virtual env
python3 -m venv venv
source venv/bin/activate

# 4. Install
pip install -e .
pip install -e ".[dev]"

# 5. Set PYTHONPATH
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

## Step 1 — Fresh Install Validation

```bash
cd SAM
python -m pytest tests/ -v --tb=short
```

Expected: all tests pass (0 failed).

## Step 2 — CLI Smoke Test

```bash
# Help
python -m sam.cli.main --help

# Health check
python -m sam.cli.main health

# Cluster status (standalone mode)
python -m sam.cli.main cluster status

# Autonomy status
python -m sam.cli.main autonomy status
```

Expected:
- `health` → "System status: HEALTHY"
- `cluster status` → "Cluster: standalone mode"
- `autonomy status` → no errors

## Step 3 — Module Import

```bash
python -c "
import sam.cognition
import sam.healing
import sam.evolution
import sam.tuning
import sam.autonomy
import sam.cluster
import sam.federation
import sam.persistence.database
print('All modules import OK')
"
```

## Step 4 — Database Migration

```bash
# Clean test
python -c "
import asyncio, os
os.chdir('/path/to/SAM')
from sam.persistence.database import Database

async def test():
    db = Database('test_rc2.db')
    await db.initialize()
    rows = await db.fetch_all('SELECT COUNT(*) as cnt FROM schema_version')
    print(f'Migrations: {rows[0][0]} of 47')
    await db.close()
    os.unlink('test_rc2.db')

asyncio.run(test())
"
```

Expected: `Migrations: 47 of 47`

## Step 5 — Failure Injection Tests

```bash
python -m pytest tests/test_failure_injection.py -v
```

Expected: 16/16 passed.

## Checklist RC2

| Item | Status |
|---|---|
| All tests pass | |
| CLI health OK | |
| CLI cluster status (standalone) OK | |
| All modules import OK | |
| 47 migrations applied | |
| Failure injection 16/16 | |
| No Python 3.8 specific errors | |
