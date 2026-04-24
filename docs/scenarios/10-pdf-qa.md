# Scenario 10 — PDF-heavy document QA

**

**TASK**: `answer questions over a corpus of 500 scanned legal PDFs with tables, footnotes, and citations`

**Dominant dimension**: `lm_document` + `pdf_input` capability.

## The isolated subagent's answer

---

### 1. claude-opus-4-6
Top `lm_document` rating of 1528 and strong `lm_long` 1521 make it ideal for analyzing 500 scanned legal PDFs with dense tables/footnotes/citations, and its 1000000 `ctx` lets entire documents fit in context. Highest `lm_hard` at 1528 supports precise citation reasoning. [no-opinion-match]

### 2. gemini-3-1-pro
Massive 1048576 `ctx` supports long legal documents, with strong `lm_long` 1489 and `lm_hard` 1494 at a reasonable 2.0/12.0 `price_$/Mtok`. While its `lm_document` of 1451 is lower than Claude Opus, the context window and price make it a strong practical choice for corpus-scale Q&A. [no-opinion-match]

### 3. claude-sonnet-4-6
Best-in-class `lm_document` 1503 among mid-priced options at 3.0/15.0 `price_$/Mtok`, with 1000000 `ctx` for long PDFs and `lm_long` 1485. Cheaper than Opus while still scoring `lm_hard` 1480, making it a cost-effective choice for answering questions across 500 PDFs. [no-opinion-match]

---

## Verdict

⚠️ Same issue as scenario 04: the `pdf_input` capability flag exists in litellm observations (`caps=pdf_input` for Claude and Gemini models) but is not surfaced in the pick CATALOG table. The answer ended up correct by correlation with `lm_document`, but the citation contract silently lost the strongest signal.


## Profiles verdict

Same task, deterministic lens — document-QA Elo × price with a hard `pdf_input` capability filter:

```bash
lanista profiles lm_document price_input --require-cap pdf_input
```

```output
Frontier has 6 non-dominated model(s) over 11 candidate(s).
Filters: require-cap=pdf_input

Flagship    claude-opus-4-7                             lm_document=1523.50  price_input=5.0000
            max lm_document on the frontier
Balanced    claude-sonnet-4-6                           lm_document=1503.25  price_input=3.0000
            knee of the curve (normalized distance to ideal)
Budget      claude-haiku-4-5-20251001                   lm_document=1429.59  price_input=1.0000
            min price_input on the frontier

Chart: lanista chart lm_document price_input --out /tmp/profiles.png
```

The hard `pdf_input` filter eliminates 35 of the 46 vision-capable models — only Anthropic-family models carry the capability flag in litellm. All three anchors are Claude variants, which ratifies the `pick`-only answer but now the citation contract is a deterministic filter, not an LLM guess.
