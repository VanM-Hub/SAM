# Disaster Recovery Drill

**Version:** v1.0.0

---

## Overview

This document defines recovery procedures for common failure scenarios. Each drill includes preconditions, steps, and validation criteria.

---

## Scenario 1: Database Corruption

**Symptoms:** `PRAGMA integrity_check` fails; SAM crashes on startup.

### Recovery

```bash
# 1. Identify corruption
sqlite3 sam.db "PRAGMA integrity_check;"

# 2. Restore from latest known-good backup
cp sam.db.20260725.backup sam.db

# 3. Validate restored database
sqlite3 sam.db "PRAGMA integrity_check;"

# 4. Apply any pending migrations
sam daemon migrate

# 5. Start SAM
sam daemon start

# 6. Verify health
sam health
```

**RTO:** < 5 minutes (with valid backup)  
**RPO:** Depends on backup frequency (recommended: daily)

---

## Scenario 2: Node Crash / Process Failure

**Symptoms:** SAM process exits unexpectedly; daemon not running.

### Recovery

```bash
# 1. Check if database is intact
sqlite3 sam.db "PRAGMA integrity_check;"

# 2. Restart daemon
sam daemon start

# 3. Verify cluster rejoin (if applicable)
sam cluster status

# 4. Check for unfinished sessions
sam autonomy status
```

**RTO:** < 1 minute  
**Note:** SAM is stateless between operations; all state is in the database.

---

## Scenario 3: Cluster Split (Multi-Node)

**Symptoms:** Nodes cannot communicate; split-brain condition.

### Recovery

```bash
# 1. Identify surviving partitions
#    - Check which nodes can communicate
#    - Identify the node with the latest data

# 2. Designate authoritative node
sam cluster status  # On each partition

# 3. On losing partition nodes:
#    - Stop SAM services
#    - Backup local database
#    - Copy database from authoritative node

# 4. Restart all nodes and verify gossip
sam daemon start
sam cluster status
```

**RTO:** < 15 minutes  
**Prevention:** Use consensus engine with weighted trust scoring (Sprint 31).

---

## Scenario 4: Federated Cluster Disconnection

**Symptoms:** Federation peers go OFFLINE; knowledge sync stops.

### Recovery

```bash
# 1. Check federation status
sam federation status
sam federation clusters

# 2. Verify network connectivity to peer endpoint

# 3. If peer is temporarily offline:
#    - Knowledge will queue; sync when peer returns
#    - Trust score will decay (0.01/day)

# 4. If peer is permanently gone:
sam federation clusters remove <peer_id>

# 5. Force sync
sam cluster sync
```

**RTO:** Automatic (60s periodic sync)  
**Prevention:** Federation heartbeat monitoring.

---

## Scenario 5: Autonomous Action Goes Wrong

**Symptoms:** Autotuner or Self-Healing Loop applies harmful changes.

### Recovery

```bash
# 1. Check current autonomy level
sam autonomy status

# 2. Reduce autonomy immediately
sam autonomy set observe

# 3. Review autonomous history
sam autonomy history
sam autonomy guardrails

# 4. Rollback parameter changes (if Autotuner applied bad params)
sam evolution list --status approved

# 5. Escalate to human if needed
sam autonomy escalate "Harmful autonomous action"
```

**RTO:** < 30 seconds  
**Safety:** SafetyEnvelope + Guardrails prevent most harmful actions.

---

## Regular Drill Schedule

| Drill | Frequency | Responsible |
|---|---|---|
| Database restore test | Monthly | Operations |
| Node crash simulation | Quarterly | Operations |
| Cluster partition | Yearly | DevOps |
| Parameter rollback | Quarterly | Engineering |

---

*Document prepared for SAM v1.0.0 release.*
