# OP-390 — Learning Foundation Completion (Sprint 33)

Dokumentasi arsitektur Learning Runtime untuk Sprint 33.

---

## 1. Arsitektur

Learning Runtime adalah pipeline deterministic, synchronous, read-only untuk menyimpan, menganalisis, dan merekomendasikan pola operasional.

```
Experience Repository
     ↓
Knowledge Base
     ↓
Pattern Evolution Engine
     ↓
Recommendation Optimizer V2
     ↓
Learning Policy Engine
     ↓
Learning Recommendation (DTO)
     ↓
Dashboard DTO / Conversation DTO
     ↓
Conversation Learning Bridge / Learning Dashboard
```

**Lokasi kode:** `src/sam/operations/brain/learning/`

---

## 2. Pipeline

| Langkah | Modul | Output |
|---|---|---|
| Experience Collection | `experience_repository.py` | ExperienceRecord (frozen) |
| Knowledge Storage | `knowledge_base.py` | KnowledgeRecord, KnowledgeSnapshot |
| Pattern Evolution | `pattern_evolution.py` | EvolutionSummary, EvolutionCandidate |
| Recommendation Optimization | `optimizer_v2.py` | OptimizationSummary, OptimizationCandidate |
| Policy Evaluation | `policy.py` | PolicyDecision (8 policies) |
| Learning Recommendation | `runtime_v2.py` | LearningRecommendation, LearningPipelineResult |
| Dashboard DTO | `dashboard_learning.py` | LearningDashboard, 6 sub-cards |
| Conversation DTO | `conversation_learning.py` | LearningQueryResult (10 query types) |

Pipeline synchronous — semua langkah berjalan dalam satu thread tanpa async.

---

## 3. DTO (Frozen Dataclass)

Semua DTO menggunakan `dataclass(frozen=True)` — immutable.

| DTO | Modul | Fungsi |
|---|---|---|
| KnowledgeRecord | knowledge_base | Single knowledge entry |
| KnowledgeSnapshot | knowledge_base | Snapshot seluruh KB |
| KnowledgeStatistics | knowledge_base | Statistik KB |
| KnowledgeIndex | knowledge_base | Index internal (tidak frozen, mutable) |
| ExperienceRecord | experience_repository | Single experience record |
| ExperienceSummary | experience_repository | Ringkasan experience |
| EvolutionCandidate | pattern_evolution | Candidate pola evolve |
| EvolutionSummary | pattern_evolution | Summary hasil evolve |
| OptimizationCandidate | optimizer_v2 | Candidate optimasi |
| OptimizationSummary | optimizer_v2 | Summary optimasi |
| LearningPolicy | policy | Policy config |
| PolicyDecision | policy | Hasil evaluasi policy |
| LearningRecommendation | runtime_v2 | Rekomendasi final |
| LearningPipelineResult | runtime_v2 | Hasil pipeline lengkap |
| LearningQueryResult | conversation_learning | Hasil query conversation |
| KnowledgeCard | dashboard_learning | Dashboard KB card |
| ExperienceCard | dashboard_learning | Dashboard experience card |
| PatternCard | dashboard_learning | Dashboard pattern card |
| OptimizationCard | dashboard_learning | Dashboard optimasi card |
| TrendCard | dashboard_learning | Dashboard trend card |
| PolicyCard | dashboard_learning | Dashboard policy card |
| LearningDashboard | dashboard_learning | Dashboard lengkap |

---

## 4. Constraints

- **Python 3.8 compatible** — no match-case, no walrus in conditionals
- **frozen dataclass** — semua DTO immutable
- **synchronous only** — tidak ada async/await, threading, atau asyncio
- **deterministic only** — input sama = output sama
- **no ML** — tidak ada model training, inference, atau ML library
- **no AI training** — tidak ada self-training loop
- **no LLM** — tidak memanggil LLM atau provider eksternal
- **no self-modifying code** — tidak mengubah dirinya sendiri di runtime
- **no persistence** — data hanya in-memory (belum ada SQL/file/DB storage)
- **no execution** — tidak mengeksekusi aksi nyata
- **no connector** — tidak ada external connector
- **no plugin** — tidak ada plugin system
- **recommendation only** — semua output berupa rekomendasi
- **evidence mandatory** — semua record wajib punya evidence
- **approval mandatory** — rekomendasi confidence tinggi wajib approval
- **guardian compatible** — Learning Runtime compatible dengan Guardian Runtime
- **conversation first** — akses utama lewat Conversation Learning Bridge
- **dashboard ready** — LearningDashboardBuilder siap di-render
- **backward compatible** — tidak mengubah public API, domain modules, atau contracts yang sudah ada

---

## 5. Integration

| Modul | Cara integrasi |
|---|---|
| Conversation API | via `ConversationLearningBridge.query(type, params)` |
| Dashboard | via `LearningDashboardBuilder.build(runtime, result)` |
| Guardian Runtime | Learning Policy menghasilkan PolicyDecision yang bisa dikonsumsi Guardian |
| Operations Brain | `LearningRuntimeV2` bisa diinstansiasi di orchestrator |

**Tidak ada circular dependency.** Learning Runtime hanya mengimport modul dalam learning/ sendiri.

---

## 7. Files (ringkasan)

| File | Baris | Isi |
|---|---|---|
| `__init__.py` | 2 | Package init |
| `knowledge_base.py` | ~250 | KnowledgeBase, KnowledgeRecord, KnowledgeSnapshot, KnowledgeStatistics, KnowledgeIndex |
| `experience_repository.py` | ~140 | ExperienceRepository, ExperienceRecord, ExperienceSummary |
| `pattern_evolution.py` | ~230 | PatternEvolutionEngine, EvolutionCandidate, EvolutionSummary |
| `optimizer_v2.py` | ~250 | RecommendationOptimizerV2, OptimizationCandidate, OptimizationSummary |
| `policy.py` | ~340 | LearningPolicyEngine, 8 built-in policies |
| `runtime_v2.py` | ~240 | LearningRuntimeV2, pipeline runner |
| `conversation_learning.py` | ~330 | ConversationLearningBridge, 10 query handlers |
| `dashboard_learning.py` | ~200 | LearningDashboardBuilder, 6 dashboard cards |

Signature: ZARA 🦋
