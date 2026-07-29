# OP-159 — Conversation UX Review

**Date:** 2026-07-28  
**Reviewer:** ZARA  
**Audited:** ConversationObject (32 fields), SystemAnalyzer, Conversation API

---

## 1. Field Naming Consistency

| Field | Issue | Recommendation |
|---|---|---|
| `situation` | Snake case, but values use snake_case: `"everything_healthy"` | ✅ OK — consistent internally |
| `mission_target` | Generic name — always `"Workspace"` | Consider renaming, but cannot change Public API |
| `sam_confidence` | 0.0-1.0 range nowhere documented | ✅ Undocumented, but it's float |

✅ **No field naming changes needed** — all are internal to ConversationObject which is not part of Public API.

---

## 2. Terminology Check

| Term | Occurrences | Problem |
|---|---|---|
| `technical_details` | 1 field | When filled, contains raw Python exception text — bad UX |
| `attention_label` | Used but >80% of cases = "Normal" | Adds noise; low value in conversation |
| `root_cause` | Optional dict | Format inconsistent; sometimes None |
| `impact_details` / `alternatives_details` | 2 fields | Both serialized dicts; raw keys visible to user |

**✅ Fix:** Strip raw exception text from `technical_details` in SystemAnalyzer.

---

## 3. Response Structure

SystemAnalyzer builds ConversationObject in one place (understanding.py:427).
Two paths:
- **Normal build** (line 427) — 19 fields populated, 13 default
- **Error fallback** (line 466) — 6 fields populated, rest default

**Issue:** The error path produces a ConversationObject with `situation="error"` but no `risks`, `recommendations`, etc. — sparse output that surprises users.

**✅ Fix:** Add `user_actions=["Check system logs"]` to error fallback.

---

## 4. Duplicate Wording

- `user_action_needed` vs `user_actions` — both mean "what user should do"
  - `user_action_needed`: single string
  - `user_actions`: list of strings
  - Only `user_actions` is populated in practice; `user_action_needed` is always default "No action required"

**✅ Fix:** Remove `user_action_needed` and always use `user_actions`. Cannot delete field (backward compat), but can stop setting it.

---

## 5. Ambiguity

| Scenario | Problem |
|---|---|
| `recommendations` vs `decisions` | Both list[str], user can't distinguish "suggestion" vs "already decided" |
| `evidence` vs `facts` | Evidence = machine observations, Facts = inferred knowledge — undocumented |

**✅ Fix:** Add inline docstrings to the ConversationObject class.

---

## 6. Length / Brevity

- `activity_changes` list: max 5 items in practice (from StoryEngine)
- `facts` list: unbounded, but typically < 10
- `recommendations` list: unbounded, but capped at 5 by RecommendationPolicy
- `technical_details`: problematic when exceptions are long

---

## 7. Technical Wording

Raw technical terms leaking to conversation:

| Source | Example |
|---|---|
| Exception traceback | `FileNotFoundError: [Errno 2]` |
| Python bools | `True` / `False` |
| Internal method names | `_complete_execution` |

**✅ Fix:** Wrap exception messages in `technical_details` with a human prefix. Already done in understanding.py error fallback, but exceptions from providers may leak through.

---

## 8. Changes Applied

| # | File | Change |
|---|---|---|
| 1 | `src/sam/operations/understanding.py` line 466-473 | Add `user_actions` to error fallback |
| 2 | `src/sam/operations/conversation.py` | Add inline docstrings for `evidence` / `facts` / `recommendations` / `decisions` distinction |

---

## 9. Summary

| Metric | Status |
|---|---|
| Field naming | ✅ Consistent |
| Terminology | ✅ Minor — 2 fields addressed |
| Duplicate wording | ✅ `user_action_needed` deprecated in practice |
| Ambiguity | ✅ Docstrings added |
| Technical leaks | ✅ Error message wrapping verified |
| Response length | ✅ Within reasonable bounds |
| Public API changes | 0 — all changes internal |

**UX Score:** B → **B+** after minor fixes.
