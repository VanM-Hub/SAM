# ADR-015 — Runtime Hosting Independence

**Status:** Accepted
**Date:** 2026-07-27
**Deciders:** Runtime Architecture Decisions

## Context

Runtime Core tidak boleh mengetahui platform hosting.

## Decision

Runtime dijalankan tanpa bergantung pada satu platform hosting. Portabilitas adalah prioritas: Runtime harus dapat dijalankan di Desktop, Windows Service, systemd, Docker, Kubernetes, dan Embedded tanpa perubahan kode.

## Consequences

- Hosting Adapter wajib ada sebagai abstraksi platform.
- Runtime tidak memiliki logika spesifik Windows/Linux/Docker.
- Semua perbedaan platform ditangani oleh Hosting Adapter.

## Rejected Alternatives

- Platform-specific Runtime.
- Runtime dengan logika `if windows`, `elif linux`, `elif docker`.
