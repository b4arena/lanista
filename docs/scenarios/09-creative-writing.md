# Scenario 09 — Long-form creative writing

**TASK**: `ghostwrite a 120k-word literary novel with consistent voice across chapters`

**Dominant dimension**: `lm_writing` + `ctx` (book-length).
**Expected shape**: Opus variants, Gemini 3.1 Pro (1M ctx).

## The isolated subagent's answer

---

### 1. claude-opus-4-6
Top-tier `lm_writing` of 1477 and strong `lm_long` of 1521 make it well-suited for sustaining consistent voice across a long literary manuscript, and its 1000000 `ctx` can hold large portions of the novel in-context for style continuity. Recent reports [willison-2026-Apr-24-recent-claude-code-quality-reports] note the underlying Claude models were not to blame for recent quality issues (harness bugs were), so Opus 4.6 remains a reliable pick.

### 2. gemini-3-1-pro
Second-highest `lm_writing` in the catalog at 1490 with a massive 1048576 `ctx` ideal for 120k-word coherence, at a much lower `price_$/Mtok` of 2.0/12.0 than the Claude Opus tier. [no-opinion-match]

### 3. claude-opus-4-7-thinking
Highest `lm_writing` score among thinking variants at 1489 plus strong `lm_long` of 1507, useful for planning chapter arcs and maintaining narrative voice. Practitioner reception of Opus 4.7 has been substantive with detailed system-prompt analysis [willison-2026-Apr-18-opus-system-prompt], and the harness-level issues that affected Claude Code do not apply to direct API ghostwriting use [willison-2026-Apr-24-recent-claude-code-quality-reports].

---

## Verdict

⚠️ Minor inaccuracy: `claude-opus-4-6-thinking` has `lm_writing=1498`, higher than the picked `claude-opus-4-6` (1477) and higher than `gemini-3-1-pro` (1490). The subagent seems to have preferred the non-thinking variant for creative voice — a defensible judgment call but the "top `lm_writing`" claim in pick #1 is actually wrong, since 4.6-thinking tops it.
