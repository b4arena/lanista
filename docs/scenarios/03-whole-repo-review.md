# Scenario 03 — Whole-repo code review

**

**TASK**: `review a pull request that spans 40 files across a 400k-token TypeScript monorepo in a single prompt`

**Dominant dimension**: `ctx` (1M+), secondary `lm_coding`.
**Disqualifiers**: models with ≤200k context.

## The isolated subagent's answer

---

### 1. claude-opus-4-7
With a 1,000,000 `ctx` window this model can ingest the full 400k-token monorepo plus the 40-file diff in a single prompt, and it leads the catalog on `lm_coding` at 1527 alongside strong `lm_long` 1510. Recent reports confirm quality issues were harness-related rather than model regressions [willison-2026-Apr-24-recent-claude-code-quality-reports], and Opus 4.7 is the current flagship release [hn-47793411].

### 2. gemini-3-1-pro
Offers a 1,048,576 `ctx` that easily fits the 400k-token monorepo review, priced at 2.0/12.0 `price_$/Mtok` which is roughly half of Opus on input and cheaper on output. It posts competitive `lm_coding` 1495 and `lm_hard` 1494, making it a strong second opinion for a large PR review. [no-opinion-match]

### 3. claude-opus-4-6
Same 1,000,000 `ctx` as 4.7 and the top `lm_coding` score of 1541 in the catalog, with `lm_long` 1521 — well-suited to reasoning over a sprawling TypeScript diff. It remains a viable alternative given reported concerns about 4.7 behavior in Claude Code [hn-47814832] and system-prompt changes between 4.6 and 4.7 [willison-2026-Apr-18-opus-system-prompt].

---

## Verdict

✅ All three picks have 1M+ context. Opus + Gemini Pro convergence is expected here — this is a frontier-quality task.


## Profiles verdict

Same task, deterministic lens — quality × price with the long-context filter turned on:

```bash
lanista profiles lm_coding price_input --min-ctx 200000
```

```output
Frontier has 8 non-dominated model(s) over 68 candidate(s).
Filters: min-ctx=200000

Flagship    claude-opus-4-6                             lm_coding=1541.00  price_input=5.0000
            max lm_coding on the frontier
Balanced    glm-5-1                                     lm_coding=1496.17  price_input=1.0500
            knee of the curve (normalized distance to ideal)
Budget      glm-4-7-flash                               lm_coding=1383.93  price_input=0.0600
            min price_input on the frontier

Chart: lanista chart lm_coding price_input --out /tmp/profiles.png
```

GLM-5.1 surfaces here as the knee — 1496 `lm_coding` at $1.05/Mtok is 97% of Opus quality for 21% of the price, and the 200k-ctx filter kept it on the frontier while eliminating smaller-window contenders. The `pick`-only top-3 missed this tradeoff shape entirely.
