# Scenario sweep — results

Ten scenarios from [../lanista-scenarios.md](../lanista-scenarios.md). Each was
passed through `lanista pick '<task>' --top 3`, and the resulting self-contained
prompt was answered by a fresh general-purpose Claude subagent **with no lanista
access, no web tools, no other files** — only the prompt itself.

## Top-3 per scenario

| # | Task dimension | Pick 1 | Pick 2 | Pick 3 |
|---|---|---|---|---|
| 01 | cost | deepseek-v4-flash | gemini-3-flash | qwen3-vl-235b-a22b-instruct |
| 02 | latency | gemini-3-flash | deepseek-v4-flash | gemini-3-1-flash-lite-preview |
| 03 | long context (1M) | claude-opus-4-7 | gemini-3-1-pro | claude-opus-4-6 |
| 04 | vision | claude-opus-4-7 | gemini-3-1-pro | claude-sonnet-4-6 |
| 05 | Chinese | qwen3-5-max-preview | glm-5 | deepseek-v4-flash |
| 06 | long-horizon agent | claude-opus-4-7 | gemini-3-1-pro | claude-sonnet-4-6 |
| 07 | local/on-device | gemma-4-31b | qwen3-5-397b-a17b | gemma-4-26b-a4b |
| 08 | hard reasoning | claude-opus-4-6-thinking | gemini-3-1-pro | claude-opus-4-7-thinking |
| 09 | creative writing | claude-opus-4-6 | gemini-3-1-pro | claude-opus-4-7-thinking |
| 10 | document QA | claude-opus-4-6 | gemini-3-1-pro | claude-sonnet-4-6 |

## Does `pick` actually differentiate?

**Yes, in four of ten scenarios the top-3 contains zero frontier-Claude models:**

- **#1 cost**: DeepSeek / Gemini Flash / Qwen-VL — all sub-$1/Mtok
- **#2 latency**: two DeepSeek/Gemini Flash-tier picks + Flash-Lite preview
- **#5 Chinese**: three Chinese-lab models (Qwen, GLM, DeepSeek), no Western frontier
- **#7 local**: three open-weight models (Gemma, Qwen MoE) — no hosted models at all

**In the other six scenarios**, frontier Claude Opus + Gemini 3.1 Pro dominate.
That's not a bug — those are all "frontier quality" tasks (long-context review,
vision, long-horizon agent, hard math, creative writing, document QA) where the
frontier models legitimately lead on the relevant Elo columns. A picker that
*didn't* converge here would be the broken one.

## The single most interesting result: scenario 07

The catalog has no "runs locally" column. No price=$0, no size-in-GB column, no
open-weights flag in the CATALOG slice served to the LLM. The subagent still
correctly picked three open-weight laptop-friendly models — by reaching into
the opinion corpus (Willison's MLX recipe + Qwen-on-MacBook post) for a
capability signal the table lacks.

That is the load-bearing claim of lanista's prompt design: **the opinion block
is not decoration**. It carries signals the structured catalog cannot express,
and a reasonable LLM will use them.

## Status update — gaps addressed

All three gaps below have been closed in a subsequent batch. See
[../workflows.md](../workflows.md) for the new three-lens story and
[06-long-horizon-agent.md](06-long-horizon-agent.md) for the
GLM-5.1 before/after comparison.

- Gap 1 (scenarios 04, 10) — `pick` now emits `modalities`, `caps`, and
  `tier` columns in the CATALOG table.
- Gap 2 (scenario 06) — `pick` now emits a `TIER 1/2 USE-CASE NOTES` block
  below the table; GLM-5.1 surfaces at #2 on a re-run.
- Gap 3 (scenario 09) — still open; numeric-claim verification is a
  separate piece of work.

For trade-off questions (cheapest/balanced/fastest), use the new
`lanista pareto` and `lanista profiles` commands — they short-circuit
the LLM entirely when the question is pure arithmetic.

## Original picker gaps surfaced by this sweep

Three scenarios exposed real weaknesses in the current `pick` prompt body:

1. **Scenario 04 (vision)** and **Scenario 10 (PDFs)**: the `modalities` column
   and `pdf_input` capability flag exist in litellm/pimono observations but are
   not surfaced in the CATALOG table inside the `pick` prompt. Answers ended
   up correct by correlation with `lm_coding` / `lm_document`, but the
   citation contract silently lost its strongest signal.

2. **Scenario 06 (8-hour agent)**: the curated `gkisokay` Tier-1 use-case
   notes (which literally say "8-hour autonomous execution" for GLM-5.1) are
   available via `lanista tier 1` but are NOT injected into the `pick` prompt.
   GLM-5.1 was passed over despite being the single most on-point model.

3. **Scenario 09 (creative writing)**: the subagent claimed `claude-opus-4-6`
   had top `lm_writing` when `claude-opus-4-6-thinking` actually tops it
   (1498 vs 1477). Not a prompt bug — an LLM arithmetic slip — but the
   citation contract did not catch it. A verifier pass that cross-checks
   numeric claims against the table would help.

## Reproducing

```
for i in 01 02 03 04 05 06 07 08 09 10; do
  lanista pick "$(grep -A1 'TASK:' docs/scenarios/$i-*.md | head -2 | tail -1)" --top 3 > /tmp/$i.txt
done
```

Then pipe each `/tmp/$i.txt` into any LLM with no other context and compare
against the per-scenario answers in this directory.
