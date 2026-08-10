# SAM Manifest

```
Repository:   github.com/VanM-Hub/SAM
License:      Apache-2.0
Python:       >=3.8 (tested on 3.10, 3.11, 3.12)
Status:       Active Development
Current:      SAM 5.x - Universal Governance Platform (versi teknis 4.1.0)
Release:      5 - Universal Governance Platform (SAM 5.x Engineering Implementation Complete,
              MISSION-5.1..5.6 selesai, 158 test, 4817 regression passed)
Baseline:     SAM 1.0 Foundation (rilis pertama, 2026-08-07) -> SAM 2.0
              Operational Governance Platform (rilis kedua, 2026-08-08, Program A-F COMPLETE,
              M1-M6 ACHIEVED) -> SAM 3.6.0 Baseline Release (rilis ketiga, 2026-08-09,
              SAM 3.x COMPLETE 6/6, AO-3.0-001 Close Order) -> SAM 4.0.0 Baseline Release
              (rilis keempat, 2026-08-10, Federated Governance Platform, Architecture Accepted)
              -> SAM 4.1.0 (rilis kelima, 2026-08-10, Universal Governance Platform,
              MISSION-5.1..5.6 implementation complete); seluruh 6 mission SAM 5.x selesai,
              no architecture drift, Foundation immutable.
Framework:    Python
Build:        setuptools
Test:         pytest (unit + 5 BC 4.x + 6 BC 5.x: 4817 passed, 1 skipped; regression 571, 2 xfailed; compliance 559; lint ruff bersih di 5.x)
Lint:         ruff
CI:           GitHub Actions (core + server + desktop)
```

## Subsystem Map

| Subsystem | Path | Files | Status |
|-----------|------|-------|--------|
| Foundation | `src/sam/` | Various | Stable |
| Operational Brain | `src/sam/operational_brain/` | ~15 | Stable |
| Guardian Live | `src/sam/guardian/live/` | ~60 | Stable |
| Decision Runtime | `src/sam/operations/brain/decision/` | ~80 | Stable |
| Activation | `src/sam/activation/` | ~48 | Stable |
| Execution | `src/sam/execution/runtime/` | ~40 | Stable |
| Approval | `src/sam/approval/` | ~50 | Stable |
| Runtime Kernel | `src/sam/runtime_kernel/` | 69 | Preview-only |
| Connector Runtime | `src/sam/connectors/` | 77 | Preview-only |
| Orchestration Runtime | `src/sam/orchestrator/` | 78 | Plan-only |
| Mission Runtime | `src/sam/mission_runtime/` | 70 | Lifecycle-only |
| Provider Runtime | `src/sam/providers/` | 71 | Preview-only |
| Provider Interfaces | `src/sam/providers/interfaces/` (Program A) | 8 | Preview-only |
| LLM Common Adapter | `src/sam/providers/llm/` (Program A) | 9 | Preview-only |
| OpenAI Provider | `src/sam/providers/openai/` (Program A) | 4 | Preview-only |
| Anthropic Provider | `src/sam/providers/anthropic/` (Program A) | 4 | Preview-only |
| Gemini Provider | `src/sam/providers/gemini/` (Program A) | 4 | Preview-only |
| DeepSeek Provider | `src/sam/providers/deepseek/` (Program A) | 4 | Preview-only |
| Ollama Provider | `src/sam/providers/ollama/` (Program A) | 4 | Preview-only |
| Provider Integration | `src/sam/providers/integration/` (Program A) | 2 | Preview-only |
| Connector Bridge | `src/sam/providers/connector_bridge/` (Program A) | 1 | Preview-only |
| Execution Preview | `src/sam/providers/execution/` (Program A) | 1 | Preview-only |
| Provider Certification | `src/sam/providers/certification_program/` (Program A) | 1 | Preview-only |
| Agent Runtime | `src/sam/agent/` | 67 | Lifecycle-only |
| Skill Runtime | `src/sam/skills/` | 67 | Preview-only |
| Memory Runtime | `src/sam/memory/` | 67 | Preview-only |
| Knowledge Runtime | `src/sam/knowledge_runtime/` | 67 | Preview-only |
| Cognitive Runtime | `src/sam/cognitive_runtime/` | 8 folders | Preview-only |
| Workflow Runtime | `src/sam/workflow_runtime/` | 66 | Preview-only |
| Policy Runtime | `src/sam/policy_runtime/` | 66 | Preview-only |
| Audit Runtime | `src/sam/audit_runtime/` | 66 | Preview-only |
| Artifact Runtime | `src/sam/artifact_runtime/` | 66 | Preview-only |
| Model Runtime | `src/sam/model_runtime/` (Program B) | 106 | Preview-only |
| Execution Runtime | `src/sam/execution_runtime/` (Program C) | 59 | Real Execution |
| Runtime Service | `src/sam/runtime_service/` (Program D) | 53 | Runtime Service |
| Unified Intelligence Runtime | `src/sam/intelligence_runtime/` (Program E) | 40 | Graph + Context + Certification |
| Presentation Layer | `src/sam/presentation/` (Program F) | 13 folders | Composition-only UI, no business logic, 189 tests |
| Conversation Host | `src/sam/presentation/conversation/` (Program G) | 4 | Activity presentation host via runtime_service |
| Dashboard Host | `src/sam/presentation/dashboard/` (Program H) | 4 | Activity presentation host via runtime_service |
| CLI Host | `src/sam/presentation/cli/` (Program I) | 5 | Activity presentation host via runtime_service |
| REST Presentation | `src/sam/api/presentation_rest/` (Program J) | 4 | REST host; /runtime & /health rewire ke runtime_service.api |
| LLM Wiring | `src/sam/api/llm_wiring.py` (Program K) | 1 | Composition root aktivasi jalur LLM Connector->Provider->Agent |

## Dependencies

| Group | Packages | Use |
|-------|----------|-----|
| core | structlog, pydantic | Logging, validation |
| console | rich, typer, pyyaml | CLI |
| desktop | PySide6 | GUI |
| server | fastapi, uvicorn, httpx, jinja2, aiosqlite | Web |
| dev | pytest, ruff, build, wheel | Dev tooling |
