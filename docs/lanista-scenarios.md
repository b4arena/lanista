# lanista pick — scenario matrix

Ten deliberately diverse tasks for `lanista pick`, designed to exercise different
columns of the catalog and different slices of the opinion corpus. If `pick` is
working, the top-3 should *not* be the same three models every time — each
scenario's constraints should force a different front-runner.

Each scenario lists:

- **task** — the exact string to pass to `lanista pick`.
- **dominant dimension** — what column or constraint should dictate the answer.
- **expected shape** — what a good answer looks like (not a specific model;
  a *shape* the top-3 should roughly satisfy).
- **disqualifiers** — models that would be obviously wrong picks, to help
  spot degenerate "always picks Claude Opus" behavior.

---

## 1. Cheap bulk classification

- **task**: `classify 10 million short support tickets into 8 intent buckets; budget is the hard constraint`
- **dominant dimension**: `price_$/Mtok` (input-heavy, output tiny)
- **expected shape**: sub-$0.50/Mtok input models; DeepSeek V3/V4-flash, Gemini Flash-Lite, Qwen3 small tier, GLM-4/5 budget variants
- **disqualifiers**: anything at $5+/Mtok input (Opus, GPT-5.4-high)

## 2. Real-time inline code completion

- **task**: `drive real-time inline code completion in an editor; first-token latency under 150ms matters more than raw quality`
- **dominant dimension**: latency proxy — small/flash models, `pimono` speed observations
- **expected shape**: Flash-class (Gemini Flash, Haiku-class, DeepSeek-flash); pass rate matters less than tiny parameter counts
- **disqualifiers**: thinking/reasoning variants, Opus-class

## 3. Whole-repo code review

- **task**: `review a pull request that spans 40 files across a 400k-token TypeScript monorepo in a single prompt`
- **dominant dimension**: `ctx` (1M+ context), secondary `lm_coding`
- **expected shape**: Gemini 3.1 Pro / 3 Flash (1M ctx), Claude Opus 4.x (1M ctx), Qwen3.6-plus (1M ctx)
- **disqualifiers**: 200k or smaller context models

## 4. Screenshot-to-code (vision)

- **task**: `turn a Figma screenshot into production React components with Tailwind`
- **dominant dimension**: vision modality (`modalities=text,image` in litellm/pimono observations)
- **expected shape**: Opus 4.x, Gemini 3.1 Pro, GPT-5.x — models with documented multimodal input
- **disqualifiers**: text-only models (DeepSeek text variants, pure-text Qwen checkpoints)

## 5. Chinese-language customer support

- **task**: `power a Mandarin-language customer support chatbot for a Chinese e-commerce company; cultural fluency matters`
- **dominant dimension**: `lm_chinese` Elo
- **expected shape**: Qwen, GLM, Kimi, DeepSeek Chinese-tuned models — watch for big `lm_chinese` leaders relative to `lm_english`
- **disqualifiers**: a model whose `lm_english` beats `lm_chinese` by 50+ points

## 6. Long-horizon autonomous agent

- **task**: `run an autonomous coding agent for 8 hours of continuous refactoring work without human intervention`
- **dominant dimension**: long-horizon reliability — curated `gkisokay` T1 notes, `lm_hard`
- **expected shape**: GLM-5.1 (explicitly called out for 8-hour runs), Opus 4.7, GPT-5.4/5.5 Codex-tier
- **disqualifiers**: non-reasoning/flash models

## 7. Local/on-device, privacy-sensitive

- **task**: `process patient medical notes entirely on a MacBook Pro; no data can leave the device`
- **dominant dimension**: open weights + small enough to run locally — opinion corpus is the only place this signal lives
- **expected shape**: Qwen3.6-27B, Gemma 4 E2B/E4B, Qwen3.6-35B-A3B — all called out in the Willison feed
- **disqualifiers**: any hosted-only model (Claude, GPT, Gemini, Muse Spark)

## 8. Hard math / olympiad-style reasoning

- **task**: `solve IMO-level math olympiad problems with verified step-by-step proofs`
- **dominant dimension**: `lm_hard` Elo + thinking/reasoning variants
- **expected shape**: thinking variants (`claude-opus-4-6-thinking`, `claude-opus-4-7-thinking`, `gpt-5-4-high`, `deepseek-v4-pro-thinking`)
- **disqualifiers**: non-thinking flash models, chat-tuned-only variants

## 9. Long-form creative writing

- **task**: `ghostwrite a 120k-word literary novel with consistent voice across chapters`
- **dominant dimension**: `lm_writing` + `ctx` (book-length context)
- **expected shape**: Opus 4.6-thinking (lm_writing=1498), Gemini 3.1 Pro (lm_writing=1490 and 1M ctx), Claude Opus 4.7
- **disqualifiers**: coding-specialized, short-context models

## 10. PDF-heavy document QA

- **task**: `answer questions over a corpus of 500 scanned legal PDFs with tables, footnotes, and citations`
- **dominant dimension**: `lm_document` + `pdf_input` capability flag (from litellm caps)
- **expected shape**: Opus 4.6/4.7 (lm_document 1520+), Gemini 3.1 Pro (pdf in Gemini API), Sonnet 4.6
- **disqualifiers**: models without `pdf_input` in their litellm caps

---

## Results

See [`scenarios/README.md`](scenarios/README.md) for the comparison table, the
top-3 per scenario, and three picker gaps this sweep surfaced.

## Execution plan

For each scenario we will produce a showboat document at
`docs/scenarios/NN-<slug>.md` that:

1. Runs `lanista pick '<task>' --top 3` and captures the prompt.
2. Pipes that prompt to an isolated subagent with no tools (or minimal tools).
3. Captures the subagent's top-3 answer verbatim.
4. Checks whether the answer satisfies the **expected shape** / avoids
   the **disqualifiers** from this document.

If the same three models appear across all ten scenarios, the picker is not
actually doing its job and we need to either broaden the catalog slice or
rethink the prompt template.
