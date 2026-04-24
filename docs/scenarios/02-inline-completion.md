# Scenario 02 — Real-time inline code completion

**TASK**: `drive real-time inline code completion in an editor; first-token latency under 150ms matters more than raw quality`

**Dominant dimension**: latency proxy — flash/lite tier.
**Expected shape**: Flash-class models.
**Disqualifiers**: thinking variants, Opus-class.

## The isolated subagent's answer

---

### 1. gemini-3-flash
Low-latency flash-tier model with strong `lm_coding` of 1463 relative to its class and very cheap `price_$/Mtok` at 0.5/3, which matters for high-frequency inline completions where first-token latency dominates. Massive `ctx` of 1048576 lets the editor stuff large surrounding files without truncation. [no-opinion-match]

### 2. deepseek-v4-flash
Cheapest viable option at `price_$/Mtok` 0.14/0.28 with `lm_coding` 1441 and huge `ctx` 1048576, making it well-suited to always-on inline completion where throughput and cost per keystroke matter. Recent DeepSeek v4 release drew strong practitioner attention [hn-47884971].

### 3. gemini-3-1-flash-lite-preview
Flash-lite tier targeting latency-sensitive use; `price_$/Mtok` 0.25/1.5 and `ctx` 1048576 favor rapid, cheap completions, and `lm_overall` 1423 is acceptable since the task explicitly deprioritizes raw quality. [no-opinion-match]

---

## Verdict

✅ Three flash/flash-lite models. No thinking variants, no Opus. Task-appropriate.
