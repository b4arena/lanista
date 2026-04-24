# lanista

*A lanista owned a gladiator troupe: he knew each fighter's strengths, weaknesses, and price, and chose which to field for a given match.* This tool does the same for LLMs.

lanista is a local model catalog and picker. It aggregates:

- **Structured per-model data** from eight sources: OpenRouter, LiteLLM, pi-mono, LMArena (per-category Elo ratings), Aider's polyglot coding leaderboard, Factory AI Weather, gkisokay tiers, and Artificial Analysis.
- **Prose practitioner opinions** from three feeds: [Simon Willison's Weblog](https://simonwillison.net/tags/llms/), [Eugene Yan's Blog](https://eugeneyan.com/), and model-release stories on [Hacker News](https://news.ycombinator.com/).

The result: 2,700+ models, with per-task picks that are citation-grounded and verifiable.

## Three lenses

Most "which model?" questions have a shape. lanista has a tool for each:

| Question | Use | Why |
|---|---|---|
| "Cheapest model that beats X on coding" | `pareto` | Deterministic — no LLM, just math |
| "Give me one model per budget tier" | `profiles` | Collapses the frontier to flagship / balanced / budget |
| "Which model for this nuanced task?" | `pick` | LLM-synthesized, every claim must cite a catalog column or opinion ID |

`pareto` and `profiles` are pure arithmetic — fast, deterministic, reproducible. `pick` reaches into the opinion corpus for signals the table can't express: "GLM-5.1 ran unattended for 8 hours" lives in a blog post, not a benchmark column.

## Quickstart

```bash
# Install as a uv tool (editable, so source edits apply without reinstall):
uv tool install --editable .

# Pull every structured source + prose feed:
lanista fetch
lanista refresh-opinions

# Deterministic picks: Pareto frontier + three anchors
lanista pareto lm_coding price_input --max-cost 1
lanista profiles lm_coding price_input

# LLM-synthesized pick with citations — paste output into any LLM:
lanista pick "write architecture documents for a microservices migration"
```

Optional: set `HF_TOKEN` (free at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)) to double your HuggingFace rate-limit budget.

## What `pick` actually looks like

`lanista pick` builds a self-contained, LLM-agnostic prompt. The answering LLM gets:

- A **catalog table** of the top 60 models by LMArena Elo, with columns for price, context, Aider pass-rate, and per-category ratings (`lm_coding`, `lm_writing`, `lm_chinese`, `lm_document`, …).
- **Curated tier notes** — e.g. "GLM-5.1: Long-horizon agentic coding, sustained optimization loops."
- **40 recent opinion excerpts** from Willison, Eugene Yan, and HN — each with a stable, citeable ID.
- A **citation contract**: every claim must cite a catalog column or a specific opinion ID. Picks without matching opinions must end with `[no-opinion-match]`.

The prompt works with any LLM — Claude, ChatGPT, Gemini, local. Every cited ID is in the prompt with its source URL.

## Does differentiation actually work?

Ten deliberately diverse tasks were each routed through `pick`. In four of ten, the top-3 contains zero frontier-Claude models:

- **Cost-constrained bulk classification** → DeepSeek Flash / Gemini Flash / Qwen-VL, all sub-$1/Mtok
- **Real-time inline completion** → Flash-tier models only
- **Chinese-language support** → Qwen, GLM, DeepSeek — no Western frontier model
- **On-device, privacy-sensitive** → three open-weight models (Gemma, Qwen MoE) — no hosted models at all

The last one is the most striking: the catalog has no "runs locally" column. The subagent picked correctly by reaching into the opinion corpus (Willison's MLX recipe, Qwen-on-MacBook post) for a signal the table lacks. **The opinion block is not decoration.**

## See it in action

A full walkthrough — every command executed live, every output real — lives in [`docs/lanista-demo.md`](docs/lanista-demo.md). It was built with [`showboat`](https://github.com/simonw/showboat) so you can verify the outputs still match current reality:

```bash
showboat verify docs/lanista-demo.md
```

More docs — the three-lens workflow, scenario sweep results, Pareto sweet-spot analysis — are in [`docs/`](docs/).

## License

[GPL-3.0](LICENSE) © 2026 Marcel Hild
