# Scenario 08 — Olympiad-level math reasoning

**TASK**: `solve IMO-level math olympiad problems with verified step-by-step proofs`

**Dominant dimension**: `lm_hard` + thinking/reasoning variants.
**Expected shape**: thinking variants dominate.

## The isolated subagent's answer

---

### 1. claude-opus-4-6-thinking
Top-rated model on `lm_hard` (1530) and `lm_overall` (1500), making it the strongest candidate for hard reasoning tasks like IMO math proofs, with a thinking variant well-suited to step-by-step derivations. Priced at 5/25 `price_$/Mtok` with 200000 `ctx` for long proof chains. [no-opinion-match]

### 2. gemini-3-1-pro
Very high `lm_hard` rating (1494) and `lm_overall` (1488) with a massive 1048576 `ctx` window useful for verifying long multi-step proofs, at a competitive 2.0/12.0 `price_$/Mtok`. [no-opinion-match]

### 3. claude-opus-4-7-thinking
Thinking variant with strong `lm_hard` score (1505) and top-tier `lm_coding` (1539), suitable for verified symbolic/step-by-step reasoning; Opus 4.7 was highlighted as a significant release [hn-47793411] and its reasoning-focused system prompt changes are documented [willison-2026-Apr-18-opus-system-prompt].

---

## Verdict

✅ Two thinking variants picked over their non-thinking counterparts — the reasoning signal propagated correctly. Gemini 3.1 Pro in #2 slot is a Gemini-family model that does reason but lacks an explicit "-thinking" variant row in the CATALOG, so the pick is defensible.
