# AD-S05 — Knowledge & Memory Activation (kombinasi A + B)

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision (Session 05)

## Keputusan
- **Kombinasi A + B** untuk Knowledge (dan Memory bila didukung).
- **A**: Wire Knowledge consumer di entry (jalur resmi), pakai KnowledgeRegistry +
  ConversationKnowledgeBridge / ConversationIntegrationBridge yang **sudah ada**.
  Tanpa mengubah ExecutionRuntime/RuntimeService/internal knowledge_runtime.
- **B**: Pakai AD-S02-001 namespace — `ExecutionRequest.payload["knowledge"]` diisi saat
  Conversation minta knowledge; namespace `memory` diisi bila Memory didukung.

## Activation Path
```
Conversation → RuntimeService → ExecutionRuntime (preview)
            → Knowledge (via bridge/registry yang sudah ada) → STOP
```

## Aturan
- JANGAN bangun retriever / embedding / index / search / RAG / reasoning baru.
- JANGAN ubah ExecutionRuntime / RuntimeService / internal knowledge_runtime.
- Knowledge = capability pertama yang dormant → aktif via jalur resmi.
- Memory Context mengalir bila memang didukung repo (conditional).
