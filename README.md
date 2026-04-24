# lanista

*A lanista owned a gladiator troupe: he knew each fighter's strengths, weaknesses, and price, and chose which to field for a given match.* This tool does the same for LLMs.

lanista is a local model catalog and picker. It aggregates:

- **Structured per-model data** from eight sources: OpenRouter, LiteLLM, pi-mono, LMArena (per-category Elo ratings), Aider's polyglot coding leaderboard, Factory AI Weather, gkisokay tiers, and Artificial Analysis.
- **Prose practitioner opinions** from three feeds: [Simon Willison's Weblog](https://simonwillison.net/tags/llms/), [Eugene Yan's Blog](https://eugeneyan.com/), and model-release stories on [Hacker News](https://news.ycombinator.com/).

Given a natural-language task, `lanista pick` builds a self-contained, LLM-agnostic prompt. Every recommendation the receiving LLM makes must cite a specific catalog column or a specific opinion entry by ID — verifiable, not vibes.

## Quickstart

```bash
# Install as a uv tool (editable, so source edits apply without reinstall):
uv tool install --editable .

# Pull every structured source + prose feed:
lanista fetch
lanista refresh-opinions

# Pick models for a task — prints a prompt to stdout, paste into any LLM:
lanista pick "write architecture documents for a microservices migration"
```

Optional: set `HF_TOKEN` (free at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)) to double your HuggingFace rate-limit budget.

## See it in action

A full walkthrough — every command executed live, every output real — lives in [`docs/lanista-demo.md`](docs/lanista-demo.md). It was built with [`showboat`](https://github.com/simonw/showboat) so you can verify the outputs still match current reality:

```bash
showboat verify docs/lanista-demo.md
```

## License

[GPL-3.0](LICENSE) © 2026 Marcel Hild
