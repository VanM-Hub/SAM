# Backup & Restore

**Version:** v1.0.0

---

## Overview

SAM uses **sqlite3** as its embedded database (`sam.db`). Backup and restore are straightforward file operations with integrity verification.

## Automated Backup

Use the validation script:

```bash
python scripts/validate_backup.py /path/to/sam.db [/path/to/backup.db]
```

This script:
1. Validates source database integrity (PRAGMA integrity_check)
2. Creates a file-level backup  
3. Validates backup integrity
4. Restores to a temporary database and compares row counts

### Example

```bash
# Default backup location (sam.db.backup)
python scripts/validate_backup.py ./sam.db

# Custom backup path
python scripts/validate_backup.py ./sam.db /backups/sam-20260725.db
```

## Manual Backup

```bash
# Simple file copy (SAM should not be writing during copy)
cp sam.db sam.db.$(date +%Y%m%d_%H%M%S).backup

# Safe backup using SQLite backup API
sqlite3 sam.db ".backup sam.db.safe_backup"
```

## Restore

```bash
# 1. Stop SAM (if running)

# 2. Restore from backup
cp sam.db.20260725.backup sam.db

# 3. Verify integrity
sqlite3 sam.db "PRAGMA integrity_check;"

# 4. Run migrations (if restoring from older version)
sam daemon migrate

# 5. Start SAM
sam daemon start
```

## Best Practices

| Practice | Recommendation |
|---|---|
| **Frequency** | Daily automated backup via cron/Task Scheduler |
| **Retention** | Keep last 7 daily + 4 weekly backups |
| **Verification** | Always run `validate_backup.py` after backup |
| **Storage** | Store backups on separate physical media |
| **Encryption** | For sensitive data, encrypt backup files |
| **Testing** | Monthly restore drill to verify backups |

## Database Tables (for backup verification)

| Table | Purpose | Backed Up |
|---|---|---|
| `workflow_executions` | Workflow execution records | ✅ |
| `cognitive_state_history` | Cognitive state snapshots | ✅ |
| `working_memory` | Working memory entries | ✅ |
| `attention_profiles` | Attention focus history | ✅ |
| `arbitration_history` | Goal arbitration records | ✅ |
| `context_window` | Context items | ✅ |
| `cognitive_sessions` | Reasoning session tracking | ✅ |
| `optimizable_params` | Tunable parameters | ✅ |
| `optimization_history` | Optimization changes | ✅ |
| `reflection_records` | Healing reflections | ✅ |
| `performance_metrics` | System metrics | ✅ |
| `tuning_history` | Autotuner history | ✅ |
| `cluster_insights` | Cluster insights | ✅ |
| `strategy_proposals` | Strategy proposals | ✅ |
| `cluster_cognitive_states` | Cluster cognitive states | ✅ |
| `federated_insights` | Federated knowledge | ✅ |
| `cluster_trust` | Trust scores | ✅ |
| `federation_config` | Federation config | ✅ |
| `autonomy_history` | Autonomy changes | ✅ |
| `guardrails` | Guardrail rules | ✅ |
| `escalations` | Escalation requests | ✅ |
| `degradation_history` | Degradation events | ✅ |
| *Plus ~25 earlier tables* | Various domains | ✅ |

---

*Document prepared for SAM v1.0.0 release.*
