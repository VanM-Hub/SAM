# SAM — Self-evolving AI Operations Framework

SAM is an AI-driven operations framework that can observe, diagnose, heal, optimize, and evolve itself autonomously.

## Features Overview

### Self-Healing
- **Detect → Diagnose → Decide → Execute → Verify → Learn** — 9-phase healing pipeline
- Pattern-based diagnosis with confidence scoring
- Automatic reflection and lesson extraction

### Self-Optimization
- **ParamManager**: 9 default tunable parameters across 5 categories
- **SelfOptimizer**: analyze → suggest → apply → rollback with full history
- **EvolutionPolicy**: Proposal lifecycle with PolicyRule constraints

### Performance Autotuning
- **MetricsCollector**: System metric collection (CPU, memory, queue, latency)
- **Autotuner**: analyze → apply → monitor → rollback with 12 binding rules
- **TuningSuggestion**: confidence-scored parameter adjustments

### Cognitive Runtime
- **CognitiveState** — health, confidence, focus, risk, autonomy tracking
- **WorkingMemory** — session-scoped key-value store with TTL expiry
- **AttentionManager** — 6 priority rules for focus determination
- **GoalArbitrator** — weighted scoring for competing goals
- **ContextWindow** — TTL-based context with importance filtering
- **CognitiveSession** — full reasoning cycle tracking with reflections & decisions

### Governance
- 7 evaluators (Risk, Approval, Maintenance, Cluster, Resource, Capability, Policy)
- Policy-based rules with condition matching
- Wait/approval/reject/escalate decisions

### Cluster & Collaboration
- Node discovery and heartbeat service
- Delegation workflow with full lifecycle
- Workflow distribution across cluster

### Institutional Memory
- Long-term storage of lessons, patterns, and knowledge
- Evidence-based learning and retrieval

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLI (sam.cli)                       │
├─────────────────────────────────────────────────────────┤
│                     Capabilities                        │
├─────────────────────────────────────────────────────────┤
│  Healing    Evolution    Cognition    Governance        │
│  Autotuning  Reasoning   Strategy     Collaboration     │
├─────────────────────────────────────────────────────────┤
│  Runtime (execution, scheduling, job queue)             │
├─────────────────────────────────────────────────────────┤
│  Persistence (Database, Migrations)                    │
├─────────────────────────────────────────────────────────┤
│  Infrastructure (Plugin, Events, Messaging)            │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Requirements
- Python 3.8+ (3.12+ recommended)
- pip

### Installation

```bash
git clone https://github.com/your-org/sam.git
cd sam
pip install -e .
```

### Basic Usage

```bash
# Run health checks
sam health

# List evolution proposals
sam evolution list

# Approve a proposal
sam evolution approve <proposal_id>
```

### Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
cd src
PYTHONPATH=. pytest

# Run specific test file
PYTHONPATH=. pytest tests/test_healing_loop.py -v
```

## Test Statistics

| Metric | Value |
|---|---|
| Total tests | 1694 |
| Passing | 1693 |
| Failing | 0 |
| Skipped | 1 |
| Duration | ~7.5 min |

## Project Status

- [x] Sprint 0–10: Workflow Engine, DSL, Scheduler, Validation
- [x] Sprint 11–15: Runtime, Plugin System, Governance, Reasoning
- [x] Sprint 16–20: Cluster, Collaboration, Goals, Strategy
- [x] Sprint 21–27: Institutional Memory, Cognitive, Healing
- [x] **Sprint 28**: Self-Evolution Engine (Optimization, Healing, Autotuning)
- [x] **Sprint 29**: Cognitive Runtime (State, Memory, Attention, Arbitration, Context, Sessions)

## License

MIT
