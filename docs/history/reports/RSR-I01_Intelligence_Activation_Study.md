RSR-I01 â€” Intelligence Activation Study

Tipe: Repository Research Report (bukan implementasi)
Status: READ-ONLY (tidak ada coding/patch/commit)
HEAD: f7e9f01 (hasil Session 06)
Tanggal: 2026-08-04
Penulis: Zara (Repository Research Engineer)

Wajib dibaca bersama: MISSION, CONSTITUTION, ADR terbaru, D0-001, D1-001, EC terbaru, 01_AKTUAL_STATE, Session Report S01â€“S06.

=====================================================================
1. EXECUTIVE SUMMARY
=====================================================================
Pertanyaan: Apakah Session 07 memang harus mengaktifkan Intelligence & Agent?
Jawaban: TIDAK otomatis ya. Berdasarkan repository, Intelligence & Agent adalah
Dua dunia yang berbeda dan KEDUANYA belum siap diaktifkan sebagai satu sesi.

Fakta kunci (VERIFIED):
- intelligence_runtime = META-REPRESENTATION (preview-only, tanpa inference/LLM,
  tidak mengeksekusi runtime apa pun). Ia "melihat" seluruh runtime SAM sebagai
  pipeline konseptual (string), bukan dependency nyata.
- agent/ = Agent Runtime (preview-only lifecycle Mission), tidak mengeksekusi,
  tidak reasoning, tidak learning, tidak approval.
- KEDUANYA: 0 consumer produksi; 0 import dari jalur resmi (web/server/runtime_service).
- intelligence_runtime TIDAK mengimpor knowledge/workflow/agent secara nyata
  (hanya string di FINAL_PIPELINE / required_sections).
- Knowledge (S05) & Workflow (S06) sudah aktif karena punya jalur activation
  (registry + bridge query spesifik) yang bisa di-DI ke entry.
- Intelligence TIDAK punya jalur activation yang setara: ConversationBridge-nya
  hanya snapshot/scope; IntelligenceRuntime tidak menghasilkan output capability
  yang bisa dikonsumsi Conversation secara langsung dalam mode preview.

Kesimpulan level tinggi (VERIFIED): Repository TIDAK kekurangan Intelligence
implementation; repository SUDAH cukup kaya. Yang kurang: Intelligence BELUM
memiliki jalur activation yang "memberi nilai operasional nyata" lewat preview
tanpa membangun komponen baru â€” dan S07 TIDAK boleh membangun komponen baru.

=====================================================================
2. CAPABILITY INVENTORY
=====================================================================
Intelligence (legacy, Phase 1) â€” src/sam/intelligence/
- IncidentDetector, RootCauseAnalyzer, Recommender, KnowledgeLookup, models.
- Consumer: Web dashboard (/incidents, /knowledge pakai intelligence legacy).
- Status: PARTIAL (terpakai di web, tapi bukan jalur resmi RuntimeService).

Intelligence Runtime (Program E, v28.0.0) â€” src/sam/intelligence_runtime/
- IntelligenceRuntime (orchestrator meta), IntelligencePipeline, IntelligenceIntegration,
  RuntimeRegistry, PipelineBuilder, ContextBuilder, ContextValidator, certifier, monitor, dll.
- ConversationBridge, DashboardBridge (snapshot/scope read-only).
- Consumer: 0 (VERIFIED â€” tidak ada import dari luar intelligence_runtime).
- Status: DORMANT.

Agent Runtime (Phase XV) â€” src/sam/agent/
- AgentRuntime, RuntimeEngine, RuntimeCoordinator, AgentRegistry, Planner (MissionBuilder),
  StateMachine, Session, dsb. Mengendalikan lifecycle Mission (Created->Completed) preview.
- Consumer: berupa collaboration/ (internal). 0 consumer di jalur resmi.
- Status: DORMANT (di jalur resmi).

Reasoning (Sprint 22) â€” src/sam/reasoning/
- ReasoningEngine, PlanningEngine, IntentParser, PlanRanker, GraphRevision, dll.
- DI-IMPORT OLEH BANYAK modul (agent, cognition, cognitive_runtime, operations/brain,
  guardian, knowledge_runtime builder, workflow_runtime builder, model_runtime, launcher).
- TAPI reasoning/engine.py mengimpor execution/ (world lama: ExecutionGraph/Engine).
- Status: PARTIAL/ACTIVE-internal (dipakai banyak, tapi ke world lama, bukan jalur resmi baru).

Planning â€” tidak ada folder terpisah; ada PlanningEngine di reasoning/planner.py
dan MissionBuilder di agent/planner/. Status: PARTIAL (di dalam reasoning/agent).

Observation â€” tidak ada komponen terpisah. Conversation.observe() ada di operations
(legacy). Di intelligence_runtime/agent: tidak ada Observer. Status: DORMANT/tersebar.

Verification â€” ada guardian/verification.py, operations/verification.py (jalur lama).
Di intelligence_runtime/agent: tidak ada. Status: PARTIAL (Guardian/Operations).

Workflow (S06 aktif) â€” workflow_runtime + WorkflowPreviewConsumer (jalur resmi).
Knowledge (S05 aktif) â€” knowledge_runtime + KnowledgePreviewConsumer (jalur resmi).

=====================================================================
3. CONSUMER MAP
=====================================================================
| Capability        | Consumer produksi di jalur resmi? | Detail |
|-------------------|----------------------------------|--------|
| RuntimeService    | 3 (Web + Conversation + Presentation) | S01, S02, S04 |
| ExecutionRuntime  | 2 (Web + Conversation preview)   | S01-S03 |
| Knowledge         | 1 (KnowledgePreviewConsumer)     | S05 |
| Workflow          | 1 (WorkflowPreviewConsumer)      | S06 |
| Intelligence Runtime | 0                          | VERIFIED |
| Agent Runtime     | 0 (hanya collaboration internal) | VERIFIED |
| Reasoning (legacy)| banyak internal, tapi ke world lama | PARTIAL |
| Intelligence (legacy) | Web (/incidents, /knowledge)  | PARTIAL |

=====================================================================
4. PRODUCER MAP
=====================================================================
| Capability        | Producer | Detail |
|-------------------|----------|--------|
| RuntimeService    | Web, Conversation, Presentation | S01-S04 |
| ExecutionRuntime  | Web, Conversation (preview) | S01-S06 |
| Knowledge         | Conversation (KnowledgePreviewConsumer) | S05 |
| Workflow          | Conversation (WorkflowPreviewConsumer) | S06 |
| Intelligence Runtime | 0 (tidak ada yg memicunya) | VERIFIED |
| Agent Runtime     | 0 di jalur resmi | VERIFIED |

=====================================================================
5. DEPENDENCY GRAPH (faktual, dari source)
=====================================================================
Dependency NYATA (import & wiring):
  RuntimeService (gateway)
    |-- WebRuntimeService (S01)          <- di-DI ke Presentation (S04)
    |-- ConversationPreviewGateway (S02)  <- RuntimeAPI -> ExecutionRuntime (preview)
    |-- PresentationLayer (S04)           <- RuntimeService via DI
    |-- KnowledgePreviewConsumer (S05)    <- KnowledgeRegistry (knowledge_runtime)
    |-- WorkflowPreviewConsumer (S06)     <- WorkflowRegistry (workflow_runtime)
    |-- ExecutionRuntime (S01-S03)        <- Pipeline -> ProviderActivationExecutor
               |-- Provider Resolution (S03)
  
Dependency KONSEPTUAL (string route, BUKAN import nyata):
  IntelligenceRuntime.required_sections = [Mission, Agent, Workflow, Skill,
     Memory, Knowledge, Policy, Audit, Artifact, Model, Provider, Execution]
  IntelligencePipeline.FINAL_PIPELINE   = [Mission, Agent, Workflow, Knowledge, ...]
  WorkflowRuntimePipeline.INTEGRATION_ROUTE = [..., knowledge, ...]
  KnowledgeRuntimePipeline.INTEGRATION_ROUTE = [...]

Artinya: antar-runtime saling "melihat" sebagai stage pipeline dalam representasi
string, TAPI TIDAK ada import/delegasi nyata antar runtime. Ini desain "unified
representation" (Program E) â€” setiap runtime menyusun graph/route sendiri.

Agent dependency (import nyata, agent_runtime.py): hanya internal agent
(agent_registry, mission_builder, state_machine, transition_history, runtime_registry,
runtime_queue, transition_monitor). TIDAK ke knowledge/workflow/intelligence/execution/provider
secara langsung.

=====================================================================
6. ACTIVATION STATUS
=====================================================================
ACTIVE (jalur resmi):
- RuntimeService (Web/Conversation/Presentation)
- ExecutionRuntime (preview)
- Provider Resolution
- Knowledge (S05)
- Workflow (S06)

PARTIAL (terpakai internal, bukan jalur resmi):
- Reasoning (dipakai banyak modul, tapi ke execution/ world lama)
- Intelligence (legacy, web /incidents /knowledge)
- Guardian Verification (jalur lama)

DORMANT (0 consumer di jalur resmi):
- Intelligence Runtime
- Agent Runtime
- Model Runtime, Memory (bila tak di-DI), Plugin, dsb.

=====================================================================
7. DORMANT COMPONENTS (yang relevan S07)
=====================================================================
- Intelligence Runtime: lengkap secara struktur (Program E) tapi 0 consumer;
  ConversationBridge-nya minimal (snapshot/scope), tidak ada query capability spesifik
  setara Knowledge/Workflow.
- Agent Runtime: lengkap, tapi mengendalikan lifecycle Mission (preview), tidak
  mengeksekusi; tidak ada consumer di jalur resmi; bergantung internal agent saja.

=====================================================================
8. TECHNICAL DEBT
=====================================================================
- DUA dunia Intelligence (legacy src/sam/intelligence/ yg dipakai web, dan
  intelligence_runtime yg dormant) â€” duplikasi, mirip dua dunia execution (D1-001).
- DUA dunia Reasoning: reasoning/ (world lama, import execution/) vs cognitive_runtime
  (baru) â€” reasoning ke world lama.
- intelligence_runtime memakai string route (required_sections/FINAL_PIPELINE) sbg
  representasi; tidak ada wiring nyata antar runtime => activation debt.
- Agent Runtime & Intelligence Runtime belum punya jalur activation setara
  Knowledge/Workflow (yang butuh registry + bridge query spesifik + di-DI ke entry).

=====================================================================
9. ENGINEERING RISK
=====================================================================
- Jika S07 "mengaktifkan Intelligence & Agent" TANPA jalur activation yg jelas:
  berisiko membuat dua consumer buatan/framework baru utk setara knowledge/workflow,
  MELANGGAR prinsip SAM (abstraction lahir dari kebutuhan, bukan prediksi) & STOP RULE.
- IntelligenceRuntime sbg pintu masuk "semua runtime" berisiko jadi God Object / duplikasi
  RuntimeCoordinator (TD god object sudah ada) bila dipaksa meng-consumeri banyak runtime.
- Agent Runtime (preview Mission lifecycle) TIDAK sama dengan "AI Agent reasoning";
  mengaktifkannya sbg "Intelligence" adalah salah kaprah jika bukan yg diinginkan.
- activation vs implementation: repo SUDAH kaya implementation; masalahnya activation.

=====================================================================
10. KESIMPULAN
=====================================================================
Q: Apakah Session 07 memang harus Intelligence & Agent?
A: TIDAK otomatis. Berdasarkan repository:

10a. Intelligence Runtime BUKAN "engine intelligence" â€” ia meta-representation
     (registry->graph->context->validation->report), preview-only, tanpa inference.
     Ia TIDAK menghasilkan output capability yg bisa dikonsumsi Conversation dalam
     mode preview TANPA membangun jalur/komponen baru. (VERIFIED)

10b. Agent Runtime TIDAK sama dengan "AI Agent" â€” ia mengendalikan lifecycle Mission
     preview; tanpa reasoning/execution/approval. Bukan capability "intelligent agent"
     yg dimaksud EWO S07 (Planning/Reasoning/Tool Selection/Observation). (VERIFIED)

10c. Knowledge (S05) & Workflow (S06) aktif karena punya jalur activation: registry +
     bridge query spesifik + di-DI ke entry (via Conversation, RuntimeService, ExecutionRuntime
     preview). Intelligence TIDAK punya jalur activation setara yg sdh siap. (VERIFIED)

10d. Planning/Reasoning sdh ada (di reasoning/, agent/planner) TAPI reasoning terikat ke
     execution/ world lama; Observation/Verification hanya di Guardian/Operations (jalur lama).
     Mengaktifkan sbg "Intelligence & Agent" = memindahkan/menghubungkan dunia lama, bukan
     mengaktifkan capability dormant sederhana. (HIGH CONFIDENCE)

10e. Yang PALING penting (Q12): Repository SUDAH KAYA implementation; TIDAK kekurangan
     implementation. Ia kekurangan ACTIVATION utk capability yg sudah siap dijalur resmi.
     Intelligence & Agent BELUM punya jalur activation yg "memberi nilai nyata" ohne
     membangun komponen baru. (VERIFIED)

Oleh karena itu:
- JANGAN jadikan S07 = "Intelligence & Agent" sbg satu sesi wajib, karena akan memaksa
  membangun jalur activation utk dua capability yg nature-nya beda & belum siap, berisiko
  framework baru (melanggar disiplin S01-S06).
- ALTERNATIF yg lebih tepat (berdasarkan fakta repo): S07 FOKUS pada SATU capability yg
  sudah punya jalur activation setara knowledge/workflow, ATAU menunda Intelligence/Agent
  sampai ada jalur activation nyata. Lihat rekomendasi di bawah.

=====================================================================
REKOMENDASI (bukan proposal implementasi, hanya arah berdasarkan repo)
=====================================================================
Berdasarkan dependency yang TERVERIFIKASI, urutan yg "paling natural" untuk sesi
berikutnya (mengikuti pola S05=Knowledge, S06=Workflow):

A. Capability lain yg SUDAH punya jalur activation setara (registry + bridge +
   struktur menyerupai knowledge/workflow) lebih aman utk diaktifkan terlebih dulu.
   (Bagian ini perlu RSR terpisah utk menginventaris mana yg benar2 setara. HYPOTHESIS â€”
   karena memerlukan scan lanjutan.)

B. Intelligence Runtime hanya boleh diaktifkan bila ada "pintu masuk" nyata:
   Intelligence sbg meta-representation bisa jadi diwiring sbg consumer yang membaca
   status seluruh runtime (registry) â€” TAPI ini berisiko jadi duplicate coordinator.
   (HIGH CONFIDENCE utk risiko; perlu AD utk konfirmasi arah.)

C. Agent Runtime BUKAN target "AI Agent reasoning" saat ini. Jika yg dimaksud Session
   07 adalah AI Agent (planning/reasoning/tool), itu memerlukan menghubungkan reasoning
   (yg terikat world lama) ke jalur resmi â€” scope besar & berisiko. (HIGH CONFIDENCE)

Tingkat Keyakinan:
- Semua pernyataan fakta (consumer 0, import, struktur, dependency) = VERIFIED (dari source).
- Arah rekomendasi = HIGH CONFIDENCE / HYPOTHESIS (butuh AD / RSR lanjutan).

=====================================================================
EXIT CRITERIA CHECKLIST
=====================================================================
- [x] Tidak ada coding/patch/commit.
- [x] Seluruh jawaban dari repository (source code).
- [x] Dependency Intelligence dijelaskan lengkap (world lama vs runtime, konseptual vs nyata).
- [x] Dapat jadi dasar S07 tanpa asumsi (mengungkap gap activation & double-world intelligence).
