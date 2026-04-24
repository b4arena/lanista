# Scenario 05 — Chinese-language customer support

**TASK**: `power a Mandarin-language customer support chatbot for a Chinese e-commerce company; cultural fluency matters`

**Dominant dimension**: `lm_chinese` Elo.
**Disqualifiers**: models with `lm_english` >> `lm_chinese`.

## The isolated subagent's answer

---

### 1. qwen3-5-max-preview
Strong Chinese-language capability with `lm_chinese` of 1528, built by a Chinese lab which aligns with cultural fluency needs for Mandarin customer support, and solid `lm_overall` of 1472. [no-opinion-match]

### 2. glm-5
Chinese-built model from Z.ai with high `lm_chinese` of 1524 and very attractive pricing at `price_$/Mtok` of 0.6/2.08, making it cost-effective for high-volume customer support traffic [willison-2026-Apr-7-glm-51].

### 3. deepseek-v4-flash
Chinese-developed model with strong `lm_chinese` of 1494 and the cheapest `price_$/Mtok` at 0.14/0.28 in the catalog, ideal for scaling a chatbot economically; DeepSeek v4 was a major recent release [hn-47884971].

---

## Verdict

✅ Zero Claude, zero Gemini, zero OpenAI. Three Chinese-lab models. The `lm_chinese` column did its job.
