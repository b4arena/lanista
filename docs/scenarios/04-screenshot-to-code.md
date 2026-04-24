# Scenario 04 — Screenshot-to-code (vision)

**

**TASK**: `turn a Figma screenshot into production React components with Tailwind`

**Dominant dimension**: vision modality (`modalities=text,image`).
**Disqualifiers**: text-only models.

## The isolated subagent's answer

---

### 1. claude-opus-4-7
Top-tier `lm_coding` rating of 1527 makes it strong for translating Figma UI into React/Tailwind, and it has the highest `lm_overall` among generally-available non-thinking models at 1480 with a 1000000 `ctx` for handling large component files. Recent harness issues affecting Claude Code have reportedly been resolved [willison-2026-Apr-24-recent-claude-code-quality-reports], and Opus 4.7 is the headline coding release [hn-47793411].

### 2. gemini-3-1-pro
Excellent multimodal reasoning with `lm_overall` 1488 and competitive `lm_coding` 1495, at a much lower `price_$/Mtok` of 2.0/12.0 than Opus, plus a 1048576 `ctx` that easily accommodates screenshots plus large design systems. [no-opinion-match]

### 3. claude-sonnet-4-6
Strong `lm_coding` score of 1499 and `lm_hard` of 1480 at half the `price_$/Mtok` (3.0/15.0) of Opus, with a 1000000 `ctx` suitable for large component trees — a practical workhorse for iterating Figma-to-React conversions. [no-opinion-match]

---

## Verdict

⚠️ Weak spot: the subagent justified multimodality implicitly (Opus/Gemini/Sonnet are known vision models) but did not cite a `modalities` column, because the catalog table doesn't expose it. The prompt's catalog slice omits that signal — a potential improvement area for `lanista pick`.


## Profiles verdict

Same task, deterministic lens — quality × price with the vision capability filter:

```bash
lanista profiles lm_coding price_input --require-cap vision
```

```output
Frontier has 9 non-dominated model(s) over 46 candidate(s).
Filters: require-cap=vision

Flagship    claude-opus-4-6                             lm_coding=1541.00  price_input=5.0000
            max lm_coding on the frontier
Balanced    kimi-k2-6                                   lm_coding=1486.03  price_input=0.7448
            knee of the curve (normalized distance to ideal)
Budget      amazon-nova-lite-v1-0                       lm_coding=1239.23  price_input=0.0600
            min price_input on the frontier

Chart: lanista chart lm_coding price_input --out /tmp/profiles.png
```

Kimi K2.6 is the knee pick at 96% of Opus `lm_coding` quality for 15% of the input price — a signal the `pick`-only top-3 (three frontier-Claude/Gemini models) collapsed into a single answer. See [../workflows.md](../workflows.md) for the full vision-axis chart.
