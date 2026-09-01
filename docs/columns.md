# Catalog columns: glossary

*2026-05-18T14:13:53Z by Showboat dev*
<!-- showboat-id: eb183c69-667a-4d14-bab6-182d7a7ac275 -->

Every `lanista pick` prompt, every `lanista pareto` axis, and every entry in the catalog table comes from the same column registry. This page is generated from that registry — `lanista.columns` — so it cannot drift from what the commands actually accept.

## The full glossary

```bash
uv run lanista columns
```

```output
LMArena Elo categories                                                          
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ column      ┃ lmarena_key      ┃ description                                 ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ lm_overall  │ overall          │ Whole-text leaderboard. Default quality     │
│             │                  │ signal lanista uses when sorting the        │
│             │                  │ catalog.                                    │
│ lm_coding   │ coding           │ Head-to-head wins on code-writing prompts.  │
│ lm_writing  │ creative_writing │ Wins on creative / long-form writing        │
│             │                  │ prompts.                                    │
│ lm_hard     │ hard_prompts     │ Wins on the 'hard prompts' subset           │
│             │                  │ (adversarial, multi-step, ambiguous).       │
│ lm_long     │ longer_query     │ Wins when the user prompt itself is long.   │
│ lm_english  │ english          │ Wins on prompts judged to be English.       │
│ lm_chinese  │ chinese          │ Wins on prompts judged to be Chinese.       │
│ lm_document │ document/overall │ Wins on prompts that include an attached    │
│             │                  │ document (PDF, long text). Closest LMArena  │
│             │                  │ signal for 'can it ground answers in        │
│             │                  │ supplied material'.                         │
└─────────────┴──────────────────┴─────────────────────────────────────────────┘

Capability flags                                                                
┏━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ short ┃ capability       ┃ description                                       ┃
┡━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ pdf   │ pdf_input        │ Provider accepts PDF files directly as input (no  │
│       │                  │ client-side parsing).                             │
│ cu    │ computer_use     │ Anthropic-style 'Computer Use' — model can drive  │
│       │                  │ a screen/keyboard/mouse.                          │
│ fn    │ function_calling │ Native tool / function calling.                   │
│ vis   │ vision           │ Image input.                                      │
│ think │ reasoning        │ Exposed extended-thinking / reasoning mode.       │
└───────┴──────────────────┴───────────────────────────────────────────────────┘

Modalities                                                               
┏━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ short ┃ modality ┃ description                                        ┃
┡━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ txt   │ text     │ Text input.                                        │
│ img   │ image    │ Image input.                                       │
│ aud   │ audio    │ Audio input.                                       │
│ vid   │ video    │ Video input.                                       │
│ pdf   │ pdf      │ PDF input. May co-occur with the `pdf` capability. │
└───────┴──────────┴────────────────────────────────────────────────────┘

Notes:
  - lm_* values are Elo ratings (relative, not %). ~1500 is current frontier; 
30-50 pt gaps are meaningful, sub-10 is noise.
  - `tier` is curated: 1=frontier, 2=workhorse, 3=practical, 4=local-only.
  - `aider` is the Aider polyglot `best_pass_rate_2` percentage.


Next steps:
  lanista --json columns                Same glossary as structured JSON
  lanista pareto lm_coding price_input  Use a column as a Pareto axis
```

## How to read the lm_* numbers

Elo ratings are *relative*. They aren't percentages and they aren't directly comparable across leaderboards. A few rules of thumb when you stare at the table from `lanista pick`:

- ~1500 is current frontier (April 2026 vintage). New flagship releases tend to land within ±30 of each other.
- A 30-50 point gap is the smallest difference worth a strong opinion. Sub-10 is noise.
- The `lm_overall` column is the headline. The category columns (`lm_coding`, `lm_writing`, `lm_document`, etc.) are useful when the headline disagrees with the use case — e.g. a model with high `lm_overall` but mediocre `lm_document` is a poor fit for grounded-on-the-attached-PDF tasks.
- `lm_long` is the prompt being long, not the response. There is no "long output" rating in LMArena.

## Why `pdf` shows up twice

A model can list `pdf` in both `modalities` and `caps`. The two columns come from different parts of the index — `modalities` describes input types the provider accepts, `caps` is a curated flag for first-class capabilities. They co-occur because most providers expose PDF either as both or neither. Treat them as a single signal.

## Reproducing

Run `showboat verify docs/columns.md` from the repo root — deliberately *not* in a fenced code block, because `verify` re-executes every fenced block in the page and would otherwise recurse into itself.

The only output that should drift here is if a new column is added to `lanista/columns.py`. `verify` will flag exactly that section.
