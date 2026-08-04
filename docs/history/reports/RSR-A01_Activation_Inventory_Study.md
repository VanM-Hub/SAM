RSR-A01 â€” Activation Inventory Study

Tipe: Repository Research Report (READ-ONLY)
HEAD: f7e9f01 (hasil Session 06)
Tanggal: 2026-08-04
Penulis: Zara (Repository Research Engineer)
Status: TIDAK ada coding/patch/commit. Seluruh temuan dari source code.

=====================================================================
1. METODOLOGI & SUMBER
=====================================================================
- Inventarisasi seluruh folder src/sam/* sebagai candidate capability.
- Untuk tiap candidate: cek consumer lintas (git grep import dari luar folder),
  existence registry/bridge/engine/integration, test dir, dan jalur activation.
- Fokus: capability yang DORMANT di jalur resmi (belum di-DI ke web/server/runtime_service),
  dibandingkan dengan pola yg SUDAH aktif (Knowledge S05, Workflow S06).

Pola "aktif" (setara S05/S06) = Registry + ConversationBridge(query) +
ConversationIntegrationBridge(pipeline preview) + di-DI ke entry. Ini yang terbukti
bisa diaktifkan TANPA komponen baru.

=====================================================================
2. CAPABILITY INVENTORY & TABEL
=====================================================================
Legend: Y=Ya(dari source) / N=Tidak. Activation Cost: jumlah perubahan yg benar2 dibutuhkan
(berdasar source, bukan opini).

| Capability | Sudah Ada? | Consumer | Activation Path | Registry | Bridge | DI Ready | Dormant Reason | Activation Cost |
|---|---|---|---|---|---|---|---|---|
| Knowledge (S05) | Y | Conversation | Y (jalur resmi) | Y | Y(5q) | Y | - (aktif) | - |
| Workflow (S06) | Y | Conversation | Y (jalur resmi) | Y | Y(5q) | Y | - (aktif) | - |
| Artifact Runtime | Y | 0 (external) | Belum di-wire | Y | Y(5q)+Integ(5q) | Y | belum ada consumer di jalur resmi | LOW |
| Memory (mem) | Y | 0 (external) | Belum di-wire (hook di knowledge_preview) | Y | Y(5q) | Y | belum ada consumer di jalur resmi | LOW |
| Policy Runtime | Y | 0 (external) | Belum di-wire | Y | Y(summary/status)+Integ(5q) | Y | belum ada consumer | LOW |
| Audit Runtime | Y | 0 (external) | Belum di-wire | Y | Y(5q)+Integ(5q) | Y | belum consumer | LOW |
| Cognitive Runtime | Y | 0 (external) | Belum di-wire | Y | Y(5q)+Integ(5q) | Y | belum consumer | LOW |
| Skills | Y | 0 (external) | Belum di-wire | Y | Y+Integ(5q) | Y | belum consumer | LOW |
| Model Runtime | Y | 0 (external) | Belum di-wire | Y | Y(11q) | Y | belum consumer; LLM belum aktif | MEDIUM |
| Mission Runtime | Y | 0 (external) | Belum di-wire | Y(4) | Y(10q) | Y | belum consumer; tanpa integ pipeline? | MEDIUM |
| Intelligence Runtime | Y | 0 (external) | Belum ADA setara | Y(2) | Y(snapshot/scope) | N | bridge minimal; meta-rep; tanpa query capability | HIGH |
| Agent Runtime | Y | 0 (jalur resmi) | Belum setara | Y(3) | Y(8q internal) | N | preview Mission lifecycle; bukan AI agent; tanpa integ pipeline | HIGH |
| Plugin | Y | Y(web/server) | YA (via launcher/plugin_registry) | Y | Y | Y | terpakai (legacy) | N/A (bukan dormant) |
| Guardian | Y | cli/launcher + reasoning | PARTIAL (bukan jalur resmi) | Y | Y | Y | terpakai di CLI/launcher, bukan jalur resmi | MEDIUM |
| Autonomous | Y | web/server (ActionExecutor) | YA (part-simulasi) | Y | Y | Y | terpakai (legacy, part) | N/A |
| Cognition/Cognitive | Y | cluster/cognitive_state | PARTIAL | Y | Y | Y | sebagian terpakai | MEDIUM |
| Dashboard (runtime) | Y | NONE (external) | preview | Y | Y | Y | komposisi dashboard; belum jadi capability | MEDIUM |
| Reasoning | Y | banyak modul (world lama) | PARTIAL (ke execution/) | Y | Y | Y | terikat world lama | HIGH |
| Execution (legacy) | Y | reasoning/healing/runtime_kernel | PARTIAL (world lama) | Y | Y | Y | dunia lama | N/A |
| Provider | Y | ExecutionRuntime (S03) | YA | Y | Y | Y | aktif (resolution) | N/A |
| Launcher | Y | entry | YA | Y | Y | Y | aktif | N/A |
| Hosting | Y | launcher | YA | Y | Y | Y | aktif | N/A |
| Registry (runtime_kernel) | Y | internal kernel | PARTIAL | Y | Y | Y | kernel internal | MEDIUM |
| Service (runtime_service) | Y | Web/Conv/Pres/Know/WF | YA | Y | Y | Y | aktif (gateway) | N/A |

Catatan: "DI Ready" = struktur registry+bridge memungkinkan di-DI ke entry (setara pola S05/S06).

=====================================================================
3. CLASSIFIKASI TIER
=====================================================================
Tier 1 (aktif hanya dgn wiring/consumer, pola sdh lengkap setara S05/S06):
- Artifact Runtime (registry+Bridge 5q+Integ 5q)
- Memory (registry+Bridge 5q; sudah ada hook di knowledge_preview)
- Policy Runtime (registry+Bridge+Integ 5q)
- Audit Runtime (registry+Bridge+Integ 5q)
- Cognitive Runtime (registry+Bridge+Integ 5q)
- Skills (registry+Bridge+Integ 5q)

Tier 2 (butuh sedikit activation tambahan):
- Model Runtime (bridge 11q tapi LLM/embedding belum aktif; perlu wiring + maybe namespace)
- Mission Runtime (bridge 10q tapi tanpa integration/conversation_integration; perlu sedikit)
- Dashboard (komposisi; perlu jadi capability consumer)
- Guardian (terpakai CLI/launcher, perlu pindah ke jalur resmi utk nilai penuh)

Tier 3 (butuh Architecture Decision):
- Intelligence Runtime (bridge minimal snapshot/scope; TIDAK punya query capability setara
  knowledge/workflow; berisiko jadi duplicate coordinator)
- Agent Runtime (preview Mission lifecycle; BUKAN AI agent; membingungkan sbg "intelligence")
- Reasoning (terikat execution/ world lama; menghubungkannya ke jalur resmi = scope besar)

Tier 4 (belum layak disentuh sekarang):
- Execution (world lama; dihindari â€” sudah ada ExecutionRuntime Program C)
- Autonomous (part-simulasi; not fully activated; butuh AD approval utk production)
- Cognition (partially used; overlap cognitive_runtime)
- Plugin (sudah terpakai; bukan dormant)

=====================================================================
4. DEPENDENCY GRAPH (capability -> dependency -> activation)
=====================================================================
Pola yang SUDAH terbukti (S05/S06):
  Conversation (entry)
    -> RuntimeService (gateway)
    -> ExecutionRuntime (preview)
    -> [Capability] Consumer (Knowledge/Workflow)
       -> Registry (yg sudah ada)
       -> Bridge (Conversation/Integration, query read-only)
    -> STOP (preview, external_calls=0)

Candidate Tier-1 bisa masuk POLA YANG SAMA persis:
  Conversation -> RuntimeService -> ExecutionRuntime -> {Artifact|Memory|Policy|Audit|Cognitive|Skills}
  -> registry -> bridge (5q) -> STOP

Intelligence (berbeda):
  Conversation -> RuntimeService -> ExecutionRuntime -> ... Intelligence (meta-representation)
  Intelligence TIDAK punya registry+query-capability setara; ia membaca seluruh runtime
  sbg string route; memberinya consumer = wiring meta-report (berisiko duplicate coordinator).

Agent (berbeda):
  Conversation -> RuntimeService -> ExecutionRuntime -> ... Agent (Mission lifecycle preview)
  Agent = state machine Mission, bukan AI reasoning; memberinya consumer = wiring lifecycle.

=====================================================================
5. DEAD END (capability yg jika diaktifkan skrg jadi pulau baru tdk memberi nilai)
=====================================================================
- Intelligence Runtime: TIDAK punya consumer yg jelas & TIDAK memberi nilai capability
  nyata dlm mode preview (meta-report). Menuai tanpa mengubah = pulau baru (VERIFIED).
- Agent Runtime: sbg "AI Agent" TIDAK memberi nilai (bkn reasoning); sbg Mission lifecycle
  preview = sudah ada MissionRuntime & Operations; duplikatif (HIGH CONFIDENCE).
- Reasoning (langsung diaktifkan): terikat execution/ world lama; wiring = scope besar
  tanpa jaminan nilai (karena sudah dipakai banyak modul internal). (HIGH CONFIDENCE)

=====================================================================
6. QUICK WIN (lengkap, kurang consumer, mengikuti pola S05-S06)
=====================================================================
- Artifact Runtime: pola IDENTIK (registry + ConversationArtifactBridge 5q +
  ConversationIntegrationBridge 5q). Tinggal DI consumer + test. (VERIFIED)
- Memory: pola IDENTIK Knowledge (5q); sdh ada hook ConversationMemoryBridge di
  knowledge_preview.py. Tinggal DI consumer. (VERIFIED)
- Policy Runtime / Audit Runtime / Cognitive Runtime / Skills: semuanya punya
  registry + ConversationBridge + ConversationIntegrationBridge (5q), pola sama.

NILAI ENGINEERING (Readiness 0-100)
Kriteria: Registry, Bridge(query), Consumer(ada?), DI, Preview, Test, TD.
Bobot: Registry 15, Bridge 20, Consumer 15, DI 15, Preview 10, Test 15, TD 10.
- Artifact: 15+20+0(consumer belum)+15+10+15(test8)+10 = 85
- Memory:   15+20+0+15+10+0(test0)+10  = 70  (test kurang)
- Policy:   15+20+0+15+10+15+10        = 85
- Audit:    15+20+0+15+10+15+10        = 85
- Cognitive:15+20+0+15+10+0+10         = 70
- Skills:   15+20+0+15+10+0+10         = 70
- Model:    15+18+0+15+8+15(test11)+6  = 77  (LLM belum aktif, -td)
- Mission:  15+16+0+15+8+0+6           = 60  (tanpa integ pipeline)
- Intelligence: 15+6+0+5(bridge minimal)+10+0+4 = 40 (bridge snapshot/scope)
- Agent:    15+10+0+5+8+0+4            = 42
- Reasoning: 10(terikat lama)+12+0+5+5+0+3 = 35

=====================================================================
7. JAWABAN TIGA PERTANYAAN KESIMPULAN
=====================================================================
1. Capability PALING layak jadi Session 07?
   => ARTIFACT RUNTIME (Readiness 85, Tier 1, Cost LOW, Recommendation: aktivasi sekarang).
   Alasan (VERIFIED): pola IDENTIK knowledge/workflow (registry + ConversationArtifactBridge 5q
   + ConversationIntegrationBridge 5q + test 8), tinggal wiring consumer. Nilai nyata:
   artifact/capability yang dihasilkan runtime bisa dikonsumsi Conversation via jalur resmi.
   (Alternatif setara: Policy/Audit Runtime â€” tapi Artifact paling "lengkap+test".)

2. Capability yg sebaiknya ditunda sampai setelah Session 10?
   => Intelligence Runtime & Agent Runtime (dan Reasoning sbg AI-fundamental).
   Alasan (VERIFIED/HIGH): Intelligence = meta-representation tanpa query-capability &
   berisiko duplicate coordinator; Agent = Mission lifecycle preview bukan AI agent; Reasoning
   terikat execution/ world lama. Ketiganya bukan "quick win", butuh Architecture Decision.

3. Roadmap S07-S10 FINAL (berdasarkan dependency repository, bukan opini):
   S07 = Artifact Runtime (Tier1, quick win, pola S05/S06)          [round out :]
   S08 = Memory (Tier1; settlement hook sdh ada; menambah Memory sbg capability consumer;
         menutup "Memory conditional" yg dibiarkan S05)             [MEMORY]
   S09 = Policy + Audit (Tier1; governance setara knowledge/workflow)
   S10 = Model Runtime (Tier2; LLM/embedding KALAU ADR-024/nilai prod diizinkan) 
         ATAU Technical Debt Reduction (menyatukan dunia lama reasoning/execution).
   Catatan: Intelligence & Agent DITUNDA (butuh AD), TIDAK dimasukkan S07-S10 dgn asumsi
   jadi "AI Agent". Kalau S10 = Operational Product, maka Intelligence/Agent tetap backlog.

   PENTING: urutan ini didasarkan pada (a) pola activation yg TERBUKTI setara S05/S06,
   (b) readiness/cost, (c) nilai capability. Buka yang butuh repo berubah nyata.

=====================================================================
8. TINGKAT KEYAKINAN
=====================================================================
- Semua fakta consumer/existence/struktur/registry/bridge = VERIFIED (git grep + inspect).
- Klasifikasi Tier 1 utk 6 runtime (artifact/memory/policy/audit/cognitive/skills) = HIGH
  CONFIDENCE (pola source identik knowledge/workflow; tinggal wiring).
- Model/Mission Tier 2 = MEDIUM CONFIDENCE (bridge ada tapi LLM/planning belum siap).
- Intelligence/Agent/Reasoning Tier 3 (butuh AD) = HIGH CONFIDENCE (analisis struktur).
- Rekomendasi "Artifact sbg S07" = HIGH CONFIDENCE (quick win paling lengkap+test).
- Roadmap S07-S10 = MEDIUM-HIGH CONFIDENCE (bergantung AD kalau ada capability yg
  menuntut produksi nyata; tanpa AD, urutan berbasis activation-pattern valid).

=====================================================================
9. EXIT CRITERIA CHECKLIST
=====================================================================
- [x] Tidak ada coding/patch/commit (working tree bersih, HEAD f7e9f01).
- [x] Seluruh capability dormant dipetakan (table lengkap).
- [x] Activation Cost tersedia (VERY LOW..VERY HIGH â€” mayoritas LOW/MEDIUM/HIGH).
- [x] Activation Readiness tersedia (0-100 + perhitungan).
- [x] Dependency Graph selesai (pola S05/S06 + candidate setara + pengecualian intelligence/agent).
- [x] Dapat digunakan untuk mengunci roadmap Session 07-10.
