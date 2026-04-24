# Scenario 07 — Local/on-device privacy

**TASK**: `process patient medical notes entirely on a MacBook Pro; no data can leave the device`

**Dominant dimension**: open weights + laptop-runnable — signal lives in the opinion corpus, not the catalog.
**Disqualifiers**: any hosted-only model (Claude, GPT, Gemini, Muse Spark).

## The isolated subagent's answer

---

### 1. gemma-4-31b
Runs locally on a MacBook (MLX-compatible Gemma family is documented running on macOS per [willison-2026-Apr-12-mlx-audio]), keeping patient notes fully on-device. Dense 31B size is feasible on a MacBook Pro while still offering solid `lm_overall` 1442 and `lm_document` 1431 for clinical note processing.

### 2. qwen3-5-397b-a17b
MoE with only 17B active parameters makes it tractable on higher-end MacBook Pros, and practitioners have successfully run Qwen MoE variants on a MacBook Pro M5 locally [willison-2026-Apr-16-qwen-beats-opus]. Strong `lm_coding` 1461 and `lm_overall` 1443 give it good general reasoning quality for medical-note extraction tasks.

### 3. gemma-4-26b-a4b
Smaller MoE (4B active) Gemma variant is the most laptop-friendly pick for strict on-device use, consistent with the Gemma-on-MLX MacBook recipe in [willison-2026-Apr-12-mlx-audio]. Despite the compact footprint it still posts respectable `lm_overall` 1435 and `lm_document` is `-` so document-specific quality is unverified, but its small `a4b` active size minimizes risk of OOM on a MacBook Pro.

---

## Verdict

✅ **The strongest result in this suite.** Zero hosted models. The subagent correctly reached into the opinion corpus (Willison's MLX and Qwen-on-MacBook posts) for a capability signal that does not exist in any catalog column. This is proof the opinion block is doing real work — it's not decoration.
