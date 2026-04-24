# docs/

Supporting documentation for lanista. Each file was generated with [`showboat`](https://github.com/simonw/showboat) — commands are executed live, outputs are real.

## Files

| File | What it covers |
|---|---|
| [lanista-demo.md](lanista-demo.md) | Full walkthrough: `fetch`, `show`, `tier`, `agents`, `pick` — all commands with live output. The primary proof-of-work document. |
| [workflows.md](workflows.md) | The three-lens story: when to use `pareto` vs `profiles` vs `pick`, what each misses, and how to combine them for the sharpest answers. |
| [sweetspot-coding.md](sweetspot-coding.md) | Deterministic Pareto frontier for coding quality per dollar — `pareto` + `profiles` + chart, no LLM involved. |
| [lanista-scenarios.md](lanista-scenarios.md) | Ten diverse task scenarios designed to exercise different catalog dimensions (cost, latency, Chinese Elo, vision, on-device, …). |
| [scenarios/README.md](scenarios/README.md) | Results table: top-3 per scenario, differentiation analysis, gaps surfaced and closed. |
| [scenarios/](scenarios/) | Per-scenario showboat documents — each runs `lanista pick`, pipes to an isolated subagent, captures the answer. |

## Reproducing

```bash
showboat verify docs/lanista-demo.md
showboat verify docs/workflows.md
showboat verify docs/sweetspot-coding.md
```

LMArena ratings, HN stories, and blog feeds change daily. `verify` will flag drift in exactly the sections where upstream data has moved — that's a feature, not a bug.
