# Scenario 01 — Cheap bulk classification

**

**TASK**: `classify 10 million short support tickets into 8 intent buckets; budget is the hard constraint`

**Dominant dimension**: `price_$/Mtok` (input-heavy, output tiny).
**Expected shape**: sub-$0.50/Mtok input models.
**Disqualifiers**: anything at $5+/Mtok input.

## The prompt

```bash
lanista pick 'classify 10 million short support tickets into 8 intent buckets; budget is the hard constraint' --top 3 > /tmp/lanista-prompts/01.txt
```

## The isolated subagent's answer

The prompt at `/tmp/lanista-prompts/01.txt` was piped to a general-purpose subagent with no web access, no lanista access — only the prompt file. Verbatim answer:

---

### 1. deepseek-v4-flash
Cheapest viable option at `price_$/Mtok` of 0.14/0.28, which dominates the budget constraint for 10M classifications, while still carrying a respectable `lm_overall` of 1427 and `lm_english` of 1494 — more than enough for 8-way intent classification on short tickets. Long `ctx` of 1048576 is irrelevant here but shows headroom. [no-opinion-match]

### 2. gemini-3-flash
Very low `price_$/Mtok` of 0.5/3 with the highest `lm_overall` (1467) in the sub-$1 input tier, and `lm_english` of 1513 suggests strong short-text understanding suitable for intent classification. Massive `ctx` of 1048576 allows batching many tickets per call to further cut cost. [no-opinion-match]

### 3. qwen3-vl-235b-a22b-instruct
Budget-tier `price_$/Mtok` of 0.2/0.88 — output nearly 4x cheaper than gemini-3-flash — with `lm_overall` 1421 and `lm_english` 1460, competitive for a simple 8-class intent task. Large `ctx` of 262144 supports aggressive batching to amortize per-call overhead. [no-opinion-match]

---

## Verdict

✅ All three picks are sub-$1/Mtok input. Zero Opus/Pro-tier models. The expected-shape filter held.


## Profiles verdict

Same task, run through the deterministic `profiles` lens (capped at $0.50/Mtok input to match the budget constraint):

```bash
lanista profiles lm_overall price_input --max-cost 0.5
```

```output
Frontier has 8 non-dominated model(s) over 81 candidate(s).
Filters: max-cost=0.5

Flagship    gemini-3-flash                              lm_overall=1466.79  price_input=0.5000
            max lm_overall on the frontier
Balanced    qwen3-next-80b-a3b-instruct                 lm_overall=1418.12  price_input=0.0900
            knee of the curve (normalized distance to ideal)
Budget      llama-3-1-8b-instruct                       lm_overall=1186.51  price_input=0.0200
            min price_input on the frontier

Chart: lanista chart lm_overall price_input --out /tmp/profiles.png
```

Budget floor is a commodity 8B model; the knee pick (Qwen3-Next-80B-A3B at $0.09/Mtok) beats it by 232 Elo points for 4.5x the price — a defensible pick for a 10M-row classification run where gemini-3-flash would 5x the spend for 48 more Elo.
