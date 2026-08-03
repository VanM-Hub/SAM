# ADR-016 — Headless Runtime

**Status:** Accepted
**Date:** 2026-07-27
**Deciders:** Runtime Architecture Decisions

## Context

Runtime harus dapat dijalankan di Desktop, Service, dan Docker tanpa perubahan. GUI hanyalah client.

## Decision

Runtime berjalan tanpa GUI (headless). GUI, CLI, dan Operations Console adalah client yang terpisah, dan semuanya berinteraksi dengan Runtime melalui API atau CLI.

## Consequences

- GUI, CLI, dan Operations Console adalah client yang terpisah.
- Runtime tidak memiliki dependensi GUI.
- Semua interaksi dengan Runtime melalui API atau CLI.

## Rejected Alternatives

- GUI sebagai bagian Runtime.
- Runtime yang bergantung pada display server.
