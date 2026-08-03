# Sprint 165 — Skill Definition — Completion Report

**Fokus:** Definisi skill (definition, input, output, parameter, constraint, validator)
**OP:** OP-1651..OP-1660
**Fase:** XVI — Skill Runtime (v16.0.0)
**Tgl:** 2026-07-31

## Ringkasan

Membangun `src/sam/skills/definition/`: definisi skill lengkap dengan input/output/parameter/constraint + validator.

## Deliverables

- `skill_definition.py` — SkillDefinition
- `skill_input.py` — SkillInput
- `skill_output.py` — SkillOutput
- `skill_parameter.py` — SkillParameter
- `skill_constraint.py` — SkillConstraint
- `skill_validator.py` — SkillValidator (validate, validate_inputs, validate_outputs, validate_constraints)
- `conversation_definition.py`, `dashboard_definition.py` (5 cards)

## Test

22 unit tests, SEMUA HIJAU.

## Konstrain

Preview-only, immutable, deterministic, read-only bridges.
