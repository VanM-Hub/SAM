# OP-440: Guardian Live Runtime Foundation — Dokumentasi Sprint 43

## Ringkasan

Sprint 43 membangun **Guardian Live Runtime Foundation** — sebuah event-driven runtime synchronous yang memungkinkan seluruh runtime SAM berkomunikasi melalui event internal.

**Versi target:** v5.0.0  
**Branch:** sprint-43  
**Tag:** v5.0.0

---

## Arsitektur

```
                      Event Sources
    ┌──────┬──────┬──────┬──────┬──────┬──────┐
    │ FS   │ Git  │Mission│Conv.│Approv.│Conn.│
    └──────┴──────┴──────┴──────┴──────┴──────┘
           │
           ▼
    ┌──────────────┐
    │ Guardian Live │
    │   Runtime     │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │   Dispatcher  │  ← priority sort → dispatch
    └──────┬───────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │           Pipeline Cascade                  │
    │                                              │
    │  ┌──────────┐  ┌────────┐  ┌────────────┐   │
    │  │ Guardian  │→ │Reasoning│→ │  Learning   │   │
    │  └──────────┘  └────────┘  └────────────┘   │
    │        │                                      │
    │        ▼                                      │
    │  ┌────────────┐  ┌──────────┐  ┌──────────┐  │
    │  │Execution   │→ │Dashboard │→ │Conversat. │  │
    │  │ Preview    │  │          │  │           │  │
    │  └────────────┘  └──────────┘  └──────────┘  │
    └───────────────────────────────────────────────┘
```

---

## Pipeline

Pipeline synchronous, 7 tahap:

| Tahap | Nama | File | Fungsi |
|---|---|---|---|
| 0 | Observasi | `runtime.py` | Menerima observation payload dan membuat event |
| 1 | Dispatch | `dispatcher.py` | Mengirim event ke subscriber terdaftar (priority order) |
| 2 | Guardian | `subscriber.py` | Subscriber yang menangani event Guardian |
| 3 | Reasoning | `reasoning_bridge.py` | Trigger reasoning cycle |
| 4 | Learning | `learning_bridge.py` | Feed event ke learning pipeline |
| 5 | Execution Preview | `execution_bridge.py` | Generate execution preview (NO auto execution) |
| 6 | Dashboard | `dashboard.py` | Refresh 6 dashboard cards |
| 7 | Conversation | `conversation.py` | Update 10 conversation query state |

---

## DTO

Semua DTO bersifat **immutable** (frozen dataclass):

| DTO | File | Field Utama |
|---|---|---|
| `GuardianEvent` | `event.py` | event_id, metadata, payload, correlation_id, parent_event_id |
| `GuardianEventMetadata` | `event.py` | event_type, priority, source, timestamp, version |
| `GuardianEventSnapshot` | `event.py` | cycle_id, timestamp, events, priority_counts, source_counts, completed, errors |
| `EventRecord` | `history.py` | event, dispatched_at, processing_ms, subscriber_count, error_count |
| `LiveRuntimeCard` | `dashboard.py` | is_running, subscriber_count, total_dispatched |
| `RecentEventsCard` | `dashboard.py` | total_events, event counts by type/source/priority |
| `DispatchStatusCard` | `dashboard.py` | subscriber_count, average_processing_ms, errors |
| `SubscribersCard` | `dashboard.py` | count, names |
| `RuntimeHealthCard` | `dashboard.py` | is_running, total_events, processing stats |
| `GuardianActivityCard` | `dashboard.py` | total_dispatched, event type/source counts |

---

## Constraints

| Area | Aturan |
|---|---|
| **Concurrency** | ❌ No async, no threading, no multiprocessing |
| **Network** | ❌ No socket, no websocket, no polling |
| **Queue** | ❌ No eksternal queue |
| **Domain** | ❌ No import `sam.domain`, `sam.repository`, `sam.storage` |
| **Conversation API** | ❌ Tidak mengubah yang sudah ada |
| **Guardian Runtime lama** | ❌ Tidak mengubah yang sudah ada |
| **DTO** | ✅ Semua frozen (immutable) |
| **Pipeline** | ✅ Synchronous |
| **Host** | ✅ Host agnostic |
| **Execution** | ✅ Preview only — no auto execution |

---

## Struktur Folder

```
src/sam/guardian/live/
├── __init__.py              — Ekspor publik
├── event.py                 — DTO event (OP-431)
├── publisher.py             — Publisher (OP-432)
├── subscriber.py            — Subscriber protocol (OP-433)
├── dispatcher.py            — Synchronous dispatcher (OP-434)
├── history.py               — Ring buffer history (OP-435)
├── runtime.py               — Guardian Live Runtime (OP-436)
├── conversation.py          — Conversation bridge (OP-437)
├── dashboard.py             — Dashboard bridge (OP-438)
├── reasoning_bridge.py      — Reasoning bridge (internal)
├── learning_bridge.py       — Learning bridge (internal)
└── execution_bridge.py      — Execution bridge (internal)
```

---

## Sequence Diagram

```
Observation        Guardian Live Runtime          Subscribers        Reasoning    Learning   Execution   Dashboard   Conversation
    │                      │                          │                 │           │            │          │              │
    │   observation        │                          │                 │           │            │          │              │
    │─────────────────────>│                          │                 │           │            │          │              │
    │                      │   dispatch(event)        │                 │           │            │          │              │
    │                      │─────────────────────────>│                 │           │            │          │              │
    │                      │                          │                 │           │            │          │              │
    │                      │   trigger(event)         │                 │           │            │          │              │
    │                      │───────────────────────────────────────────>│           │            │          │              │
    │                      │                          │                 │           │            │          │              │
    │                      │   feed(event)            │                 │           │            │          │              │
    │                      │──────────────────────────────────────────────────────>│            │          │              │
    │                      │                          │                 │           │            │          │              │
    │                      │   preview(event)         │                 │           │            │          │              │
    │                      │─────────────────────────────────────────────────────────────────>│          │              │
    │                      │                          │                 │           │            │          │              │
    │                      │   refresh()              │                 │           │            │          │              │
    │                      │───────────────────────────────────────────────────────────────────────────>│              │
    │                      │                          │                 │           │            │          │              │
    │                      │   update()               │                 │           │            │          │              │
    │                      │────────────────────────────────────────────────────────────────────────────────────>│
    │                      │                          │                 │           │            │          │              │
    │                      │   snapshot               │                 │           │            │          │              │
    │<─────────────────────│                          │                 │           │            │          │              │
```

---

## Event Types

| Event Type | Penggunaan |
|---|---|
| `OBSERVATION_UPDATE` | Data observasi dari pipeline upstream |
| `GUARDIAN_HEALTH_UPDATE` | Perubahan status kesehatan Guardian |
| `DASHBOARD_REFRESH` | Permintaan refresh dashboard |
| `REASONING_TRIGGER` | Trigger siklus reasoning |
| `LEARNING_UPDATE` | Update dari learning pipeline |
| `EXECUTION_PREVIEW` | Preview execution tanpa eksekusi |
| `CONVERSATION_UPDATE` | Update state conversation |
| `ALERT_RAISED` | Alert baru |
| `ALERT_CLEARED` | Alert selesai |
| `STATE_CHANGE` | Perubahan state runtime |
| `CONFIG_CHANGE` | Perubahan konfigurasi |
| `SYSTEM_STATUS` | Status sistem periodik |

---

## Priority Levels

| Level | Nilai | Deskripsi |
|---|---|---|
| `CRITICAL` | 0 | Harus segera diproses |
| `HIGH` | 1 | Prioritas tinggi |
| `MEDIUM` | 2 | Prioritas normal |
| `LOW` | 3 | Prioritas rendah |
| `BACKGROUND` | 4 | Prioritas latar belakang |

---

## Event Source Mapping

1. **Filesystem Event** → Source: `FILESYSTEM`, Type: `OBSERVATION_UPDATE`
2. **Git Event** → Source: `GIT`, Type: `STATE_CHANGE`
3. **Mission Event** → Source: `MISSION`, Type: `STATE_CHANGE`
4. **Conversation Event** → Source: `CONVERSATION`, Type: `CONVERSATION_UPDATE`
5. **Approval Event** → Source: `APPROVAL`, Type: `ALERT_RAISED`
6. **Connector Event** → Source: `CONNECTOR`, Type: `GUARDIAN_HEALTH_UPDATE`

Semua event source sudah didefinisikan di `GuardianEventSource` enum dan siap digunakan.

---

## Test Coverage

| Area | Tests | Status |
|---|---|---|
| Sprint 43 core | 132 tests (133 assertions) | ✅ All passed |
| DTO immutability | 5 tests | ✅ All passed |
| Dispatcher determinism | 1 test | ✅ All passed |
| Forbidden imports | 1 test (scan pattern) | ✅ Clean |
| Async/thread scan | 1 test (file scan) | ✅ Clean |
| Bridge tests | 6 tests | ✅ All passed |
| Full pipeline | 1 test | ✅ All passed |
| Unit regression (existing) | 1282 tests + 1 skipped | ✅ Unchanged |

---

*Dokumentasi Sprint 43 — Guardian Live Runtime Foundation v5.0.0*
