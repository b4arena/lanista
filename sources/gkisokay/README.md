# Gkisokay LLM Model Stack — source archive

Gkisokay publishes a quarterly "LLM Model Stack" chart on X as a single
image. This directory archives the raw images alongside the extraction
prompt so the structured data in `lanista/data/gkisokay.seed.json` can be
re-derived from the original pixels at any time (e.g. with a newer vision
model).

**Source:** https://x.com/gkisokay (posted as an image — search for "LLM
Model Stack" in the author's feed for the latest chart).

## Archive layout

```
sources/gkisokay/
  README.md                   ← this file
  2026-04-17.jpeg             ← chart image, named by the date in the chart header
  # future: 2026-07-XX.jpeg, ...
```

Name each file by the `Updated MM.DD.YY` banner printed in the chart
header, **not** the download date. If Gkisokay posts a correction, that is
a new dated chart, not a revision — keep both.

Images are kept in the repo but excluded from the built Python wheel (see
`pyproject.toml`'s `[tool.hatch.build].include` pattern — only `*.json`
under `lanista/data/` ships).

## Adding a new chart

1. Download the latest chart image from https://x.com/gkisokay. Save it as
   `sources/gkisokay/YYYY-MM-DD.jpeg` using the `Updated` date from the
   chart header.
2. Run the extraction prompt below against the image with any capable
   vision model.
3. Overwrite `lanista/data/gkisokay.seed.json` with the model's JSON
   output, updating `_chart_date`, `_chart_image`, and `_extracted_with`.
4. Run `uv run pytest tests/test_sources.py::test_gkisokay_seed_parses_and_has_tiers`
   to validate shape.
5. Rerun `lanista fetch` locally and spot-check a few models with
   `lanista show <id>` to confirm the observation merges correctly.

Keep old images in the repo forever — they're the audit trail for every
revision of `gkisokay.seed.json`.

## Extraction prompt

Use this verbatim as a user message to a vision model, attaching the chart
image. It produces a JSON object shaped exactly like
`lanista/data/gkisokay.seed.json`.

---

> You are extracting structured model data from a *Gkisokay LLM Model
> Stack* chart (image attached).
>
> The chart is organized into four role tiers:
>
> - **ROLE 1: Frontier** — maximum capability, complex reasoning, external
>   dev only, use sparingly → `tier: 1`
> - **ROLE 2: Execution** — tool calls, agent pipelines, multi-step task
>   chains, volume work → `tier: 2`
> - **ROLE 3: Balanced** — content, coding, research, day-to-day tasks,
>   where 80% of work should live → `tier: 3`
> - **ROLE 4: Local + free** — summaries, routing, classification,
>   always-on loops, unlimited volume → `tier: 4`
>
> For each model row, extract:
>
> - **Canonical id**: lowercase, dashes only, all punctuation collapsed.
>   Examples: "Claude Opus 4.7" → `claude-opus-4-7`; "GLM-5.1" → `glm-5-1`;
>   "Qwen3.5-27B" → `qwen3-5-27b`.
> - **`tier`**: integer 1–4 derived from the ROLE section.
> - **`strengths`**: 3–5 short factual bullets taken from the "KEY SPECS"
>   and "TOP BENCHMARKS" columns. Keep each bullet under ~60 characters.
> - **`weaknesses`**: 0–3 bullets derived from explicit caveats in the
>   "WHY THIS MODEL" column or obvious downsides (e.g. high price, API
>   only, rate limits). Do not invent weaknesses that are not in the chart.
> - **`use_for`**: the full text of the "USE IT FOR" column, trimmed.
>
> Also extract from the chart header:
>
> - **`_chart_date`**: the `Updated MM.DD.YY` date at the top, as
>   ISO (`YYYY-MM-DD`).
>
> Return **only** a JSON object in exactly this shape. Do not add any prose,
> do not include models not present in the chart, do not invent fields:
>
> ```json
> {
>   "_schema": "Hand-curated notes. Tier 1=frontier, 4=local/free.",
>   "_source": "Gkisokay LLM Model Stack",
>   "_chart_date": "YYYY-MM-DD",
>   "_chart_image": "sources/gkisokay/YYYY-MM-DD.jpeg",
>   "_extracted_with": "<vision-model-id and date, e.g. 'claude-opus-4-7, 2026-04-23'>",
>   "_updated": "YYYY-MM-DD",
>   "models": {
>     "<canonical-id>": {
>       "tier": <int>,
>       "strengths": ["..."],
>       "weaknesses": ["..."],
>       "use_for": "..."
>     }
>   }
> }
> ```

---

## Schema reference

The `models` block is consumed by `lanista.sources.gkisokay` at runtime.
The entire entry (raw) plus a copy as `extracted` becomes one observation
per model in the merged index. `_`-prefixed provenance fields at the root
are ignored by the projector; keep them for audit.
