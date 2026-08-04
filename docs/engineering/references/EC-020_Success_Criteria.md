# EC-020 — Success Criteria

## Repository dianggap berkembang apabila:

? RuntimeService memiliki consumer. -- [S01/S02] consumer 2 (Web + Conversation preview) SELESAI
? ExecutionRuntime memiliki producer. -- [S01/S02] producer 2 (Web + Conversation preview) SELESAI
▪ Provider aktif.
? Entry point bermigrasi. -- [S02] Web + Conversation pakai jalur resmi; Desktop = S03.
? Provider Resolution aktif di jalur resmi. -- [S03] Provider di-resolve/di-select; execute() TIDAK dipanggil (ADR-024).
? Presentation Layer memakai jalur resmi. -- [S04] Presentation -> RuntimeService via DI; Desktop jadi Presentation pertama.
? Knowledge jadi capability aktif. -- [S05] KnowledgePreviewConsumer pakai KnowledgeRegistry via jalur resmi; Conversation bisa minta knowledge.
? Workflow jadi capability aktif. -- [S06] WorkflowPreviewConsumer via jalur resmi; Conversation bisa aktivasi workflow, knowledge sbg input.
? Artifact jadi capability aktif. -- [S07] ArtifactPreviewConsumer via Activation Pattern Standard.
? Memory jadi capability mandiri. -- [S08] MemoryPreviewConsumer via Activation Pattern Standard (bukan lagi namespace payload).
? Policy & Audit jadi capability governance. -- [S09] PolicyPreviewConsumer + AuditPreviewConsumer via Activation Pattern Standard.
▪ Technical Debt berkurang.
▪ Regression tetap hijau.
▪ Tidak ada Runtime baru.
▪ Tidak ada Architecture Drift.
▪ Tidak ada Business Logic di Presentation.
▪ RuntimeCoordinator mulai kehilangan consumer.
▪ Tidak ada klaim "Operational" untuk host yang masih Not Fully Operational.

---

## Repository belum dianggap berkembang apabila:

- hanya menambah dokumen.
- hanya merapikan struktur.
- hanya memindahkan file.
- hanya menambah framework.
- hanya menambah runtime.

---

## Definisi "SAM hidup"

User dapat menggunakan capability repository melalui jalur resmi:

Presentation
→
RuntimeService
→
ExecutionRuntime
→
Provider

dengan Approval, Monitoring, dan Audit tetap berjalan.

Sampai jalur resmi tersebut dipakai, host desktop tetap menjadi jalur hidup yang ada saat ini.

---

## Referensi

MISSION
CONSTITUTION
E0-001
O0-001
D0-001
D1-001
