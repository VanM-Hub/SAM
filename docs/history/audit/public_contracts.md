# Public Contract Audit

**Date:** 2026-07-25  
**Status:** ✅ Complete

---

## Contract Labels

| Label | Meaning | Can Change? |
|---|---|---|
| **Stable** | Will not break in v1.x | ❌ No breaking changes |
| **Experimental** | May change, needs feedback | ⚠️ Yes, with notice |
| **Internal** | Private implementation detail | ✅ Anytime |
| **Deprecated** | Will be removed in v2.0 | ✅ Use replacement |

---

## CLI Commands

### Stable

| Command | Since | Notes |
|---|---|---|
| `sam health` | v1.0 | Text + JSON output |
| `sam evolution list` | v1.0 | Filter by status/type |
| `sam evolution show <id>` | v1.0 | — |
| `sam evolution approve <id>` | v1.0 | Applies PARAMETER_TUNE |
| `sam evolution reject <id>` | v1.0 | — |
| `sam cluster status` | v1.0 | Aggregated cognitive state |
| `sam cluster insights-list` | v1.0 | Node/type filters |
| `sam cluster strategies-list` | v1.0 | Status filter |
| `sam cluster strategies-vote <id>` | v1.0 | Approve/reject |
| `sam cluster sync` | v1.0 | Force knowledge sync |
| `sam federation status` | v1.0 | — |
| `sam federation clusters` | v1.0 | Peer list |
| `sam autonomy status` | v1.0 | Current level |
| `sam autonomy set <level>` | v1.0 | 5 valid levels |
| `sam autonomy history` | v1.0 | Change log |
| `sam autonomy guardrails` | v1.0 | Active rules |
| `sam autonomy degrade` | v1.0 | — |
| `sam autonomy upgrade` | v1.0 | — |

### Experimental

| Command | Since | Notes |
|---|---|---|
| `sam autonomy escalate <issue>` | v1.0 | API may change with human-in-loop UI |
| `sam cluster knowledge-pull <id>` | v1.0 | Pull semantics may evolve |

---

## Python Package Public API

### Stable (`sam.cognition`)

```python
CognitiveState           # Immutable state snapshot
CognitiveStateManager    # get/update/history
WorkingMemory            # Session-scoped K-V
WorkingMemoryManager     # Multi-session WM
CognitiveManager         # Orchestrator (state + WM + context + session)
ContextWindow            # TTL-based context items
CognitiveSession         # Reasoning session
CognitiveSessionManager  # Session lifecycle
AttentionManager         # Focus determination
FocusArea                # Enum (6 values)
GoalArbitrator           # Goal priority scoring
GoalType                 # Enum (HEAL, OPTIMIZE, etc.)
```

### Stable (`sam.healing`)

```python
SelfHealingLoop          # 9-phase pipeline
ReflectionManager        # Lesson extraction
```

### Stable (`sam.evolution`)

```python
EvolutionPolicy          # Proposal lifecycle
ProposalType              # PARAMETER_TUNE, STRATEGY_SHIFT, etc.
SelfOptimizer             # Analyze → apply → rollback
ParamManager              # Parameter CRUD
```

### Stable (`sam.tuning`)

```python
Autotuner                # analyze/apply/monitor/rollback
MetricsCollector          # CPU, memory, queue, latency
TuningSuggestion          # Param change proposal
```

### Stable (`sam.autonomy`)

```python
AutonomyLevel             # Enum (5 levels)
AutonomyController        # Level management
AutonomyConfig            # Configuration
SafetyEnvelope            # Bounded boundaries
Guardrails                # Operational guardrails
GuardrailRule             # Rule definition
EscalationManager         # Human escalation
GracefulDegradation       # Level transitions
SelfAssessment            # Before/after evaluation
```

### Stable (`sam.cluster`)

```python
ClusterKnowledgeShare     # Publish/subscribe knowledge
SharedKnowledge           # Knowledge item model
ClusterStrategySync       # Proposal/vote/adopt
StrategyProposal          # Proposal model
InsightBroker             # Cross-node insights
ClusterCognitiveState     # Aggregated state
ClusterCognitiveStateManager  # State publishing
LearningAggregator        # Knowledge aggregation
```

### Stable (`sam.federation`)

```python
FederationManager         # Cluster lifecycle
FederatedCluster          # Cluster model
FederationProtocol        # Message exchange
KnowledgeOffer            # Offer model
KnowledgeRequest          # Request model
TrustManager              # Trust scoring
ClusterTrust              # Trust record
ConflictResolver          # 5 resolution strategies
ProvenanceManager         # Origin tracking
Provenance                # Provenance model
ConsensusEngine           # Weighted majority
SovereigntyManager        # Sharing policies
SovereigntyPolicy         # PUBLIC/INTERNAL/RESTRICTED
```

### Experimental

| Module | Reason |
|---|---|
| `sam.cluster.distributor` | Algorithm may change with load patterns |
| `sam.cluster.leader` | Election protocol may be refined |

### Deprecated

| Path | Replaced By | Target Removal |
|---|---|---|
| `sam.cognitive.*` | `sam.cognition.*` | v1.2 |
| `sam.cluster.discovery` | `sam.cluster.ClusterKnowledgeShare` | v1.2 |

### Internal (Not Public)

- All `_`-prefixed classes, methods, and modules
- `sam.cli.cluster_app`, `sam.cli.evolution_app`, etc. (use `sam.cli.main` instead)
- `sam.persistence.*` (use CLI or public API for DB operations)
- `sam.events.*` (internal event bus)
- `sam.plugin.*` (plugin internals)

---

## Database Schema (Stable)

All migration files `001_*.sql` through `047_*.sql` are **stable**. No existing tables or columns will be removed in v1.x. New tables may be added via new migration files.

---

## Configuration (Stable)

| Config | Format | Stable Since |
|---|---|---|
| `AutonomyConfig` | Python object | v1.0 |
| `DaemonConfig` | Python object | v1.0 |
| `SafetyBoundary` | Python object | v1.0 |
| `GuardrailRule` | Python object | v1.0 |
| `SovereigntyPolicy` | Python object | v1.0 |

---

*Audit prepared for SAM v1.0.0 release.*
