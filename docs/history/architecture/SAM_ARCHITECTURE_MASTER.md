# SAM Architecture Master

**Version:** 1.0
**Status:** Historical Design Reference
**Date:** 2026-07-27

> **Document Status: Historical Design Reference (AD-028).**
> Canonical Architecture of Project SAM adalah `docs/architecture/SAM_ARCHITECTURE.md`.
> Dokumen ini memiliki nilai pada garis evolusi konsep arsitektur; dipertahankan sebagai referensi sejarah, bukan sebagai otoritas aktif.

---

## Overview

SAM adalah **Mission-Aware Guardian Runtime** yang memisahkan eksekusi dari tata kelola (governance), sehingga sistem AI dapat beroperasi secara stabil, dapat diamati, dapat dipulihkan, dan tetap berorientasi pada tujuan.

Arsitektur SAM terdiri dari 7 lapisan yang saling terpisah dan hanya berkomunikasi melalui kontrak.

---

## Layer 1 — Mission Layer

Mission Layer menjawab pertanyaan: **"Mengapa Runtime ini ada?"**

### Komponen
- Mission
- Mission Policy
- Objectives

### Prinsip
Mission adalah sumber kebenaran tertinggi. Tidak ada keputusan Guardian yang boleh bertentangan dengan Mission.

---

## Layer 2 — Desired Operational State (DOS)

DOS menerjemahkan Mission menjadi kondisi operasional yang diharapkan.

### Komponen
- Runtime State (RUNNING, READY, dll.)
- Plugin Expectations
- Health Minimum
- Recovery Policy
- Resource Limits

### Prinsip
DOS bersifat deklaratif. Tidak mengandung logika.

---

## Layer 3 — Guardian Kernel

Guardian adalah pusat pengambilan keputusan.

### Komponen
- Observer Engine
- Analyzer Engine
- Decision Engine
- Policy Engine
- Action Engine
- Verification Engine

### Prinsip
Guardian tidak menjalankan Runtime. Guardian menjaga Runtime melalui Guardian Decision Pipeline (GDP).

---

## Layer 4 — Runtime Kernel

Runtime Kernel menjalankan seluruh kemampuan SAM.

### Komponen
- Lifecycle (Bootstrap, Session, Shutdown, Recovery)
- Scheduler
- Workflow Runtime
- Plugin Runtime
- Knowledge Runtime
- Memory Runtime

### Prinsip
Runtime hanya menyediakan kemampuan. Ia tidak mengambil keputusan strategis.

---

## Layer 5 — Protected Objects

Guardian tidak menjaga Runtime secara langsung. Guardian menjaga Protected Objects.

### Objek
- Runtime
- Plugin
- Workflow
- Session
- Memory
- Knowledge
- Workspace
- Configuration
- Infrastructure

### Prinsip
Setiap Protected Object memiliki kontrak yang sama.

---

## Layer 6 — Operations Layer

Operations Layer menerjemahkan kondisi Guardian menjadi informasi yang dapat dipahami manusia.

### Komponen
- CLI (sam status, sam health, dll.)
- Operations Console
- Runtime API
- Health API
- Telemetry
- Audit Log
- Event Stream

### Prinsip
Layer ini tidak boleh mengubah Runtime secara langsung. Semua perubahan harus melalui Guardian.

---

## Layer 7 — Platform Layer

Platform menyediakan lingkungan eksekusi.

### Platform
- Windows (Desktop, Service)
- Linux (systemd)
- Docker Container
- Kubernetes
- Embedded Runtime

### Prinsip
Platform tidak mengetahui Mission. Platform hanya menjalankan Runtime melalui Hosting Adapter.

---

## Operational Flow

```
Mission
│
▼
Desired Operational State
│
▼
Guardian Kernel (GDP)
│
▼
Runtime Kernel
│
▼
Protected Objects
│
▼
Platform
```

---

## Golden Rule

Setiap perubahan operasional SHALL mengikuti urutan:
Mission → DOS → Policy Evaluation → Decision → Action Plan → Execution → Verification → Audit

---

## Responsibility Matrix

| Layer | Responsibility |
| :--- | :--- |
| Mission | Menentukan tujuan |
| DOS | Menentukan kondisi ideal |
| Guardian | Mengambil keputusan |
| Runtime | Menjalankan kemampuan |
| Protected Objects | Menyediakan kondisi aktual |
| Operations | Menyajikan informasi |
| Platform | Menyediakan lingkungan eksekusi |

---

## Definition of SAM

**SAM** adalah **Contract-Driven, Mission-Aware Guardian Platform** yang mengelola, melindungi, dan memulihkan sistem AI melalui kontrak operasional yang dapat diaudit, dapat diverifikasi, dan independen terhadap platform.
