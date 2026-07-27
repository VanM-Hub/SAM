# CLI Reference

> Semua perintah yang tersedia di SAM Framework.

## Penggunaan Dasar

```bash
python -m sam.cli.main [COMMAND] [ARGS]
# atau jika terinstal sebagai package:
sam [COMMAND] [ARGS]
```

## Perintah Utama

### `health`

Menampilkan status kesehatan sistem secara agregat.

```bash
sam health
sam health --json   # Output JSON
```

Output:
```
=== SAM Health ===
  Python      : 3.12.0
  Database    : OK
  cognition   : OK
  healing     : OK
  evolution   : OK
  tuning      : OK
  autonomy    : OK
  cluster     : OK
System status: HEALTHY
```

### `run <capability_id>`

Menjalankan satu capability berdasarkan ID.

```bash
sam run diagnose-runtime
sam run repair-provider
```

### `workflow <steps>`

Menjalankan workflow dengan daftar capability.

```bash
sam workflow "diagnose-runtime,repair-provider,deploy-workspace"
```

---

## Autonomy Commands

### `sam autonomy status`

Menampilkan level autonomy saat ini.

```
Current autonomy level: supervise (level 4/5)
```

### `sam autonomy set <level>`

Mengubah level autonomy.

```bash
sam autonomy set observe    # Level 1 — hanya observasi
sam autonomy set recommend  # Level 2 — rekomendasi
sam autonomy set assist     # Level 3 — asisten
sam autonomy set supervise  # Level 4 — supervisi (default)
sam autonomy set autonomous # Level 5 — otonom penuh
```

### `sam autonomy history`

Riwayat perubahan level autonomy.

### `sam autonomy guardrails`

Menampilkan guardrails aktif.

### `sam autonomy escalate <message>`

Membuat escalation request.

```bash
sam autonomy escalate "CPU usage di atas 90%"
```

### `sam autonomy degrade`

Menurunkan level autonomy satu tingkat.

### `sam autonomy upgrade`

Menaikkan level autonomy satu tingkat.

---

## Evolution Commands

### `sam evolution list`

Menampilkan daftar proposal.

```bash
sam evolution list
sam evolution list --status approved
sam evolution list --status pending
```

### `sam evolution show <proposal_id>`

Detail proposal.

```bash
sam evolution show prop_001
```

### `sam evolution approve <proposal_id>`

Menyetujui proposal.

```bash
sam evolution approve prop_001
```

### `sam evolution reject <proposal_id>`

Menolak proposal.

```bash
sam evolution reject prop_001
```

---

## Cluster Commands

### `sam cluster status`

Status cluster (standalone atau multi-node).

```
Cluster: standalone mode
  Status : running as single node
  ID     : default-cluster
```

### `sam cluster sync`

Sinkronisasi state cluster.

### `sam cluster strategies-list`

Daftar proposal strategi.

### `sam cluster strategies-vote <proposal_id>`

Vote proposal strategi.

```bash
sam cluster strategies-vote strategy_001 --approve
```

---

## Federation Commands

### `sam federation status`

Status federasi knowledge.

### `sam federation clusters`

Daftar cluster peer.

---

## Graph Commands

### `sam graph run <file>`

Menjalankan execution graph dari file.

```bash
sam graph run examples/monitoring_graph.yaml
```
