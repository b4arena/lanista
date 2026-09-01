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

LMArena agent leaderboard                                                       
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ column             ┃ lmarena_key                         ┃ description       ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ lm_agent           │ agent/overall                       │ Overall agent     │
│                    │                                     │ leaderboard.      │
│                    │                                     │ Headline signal   │
│                    │                                     │ for autonomous    │
│                    │                                     │ coding sessions.  │
│ lm_agent_steer     │ agent_steerability/overall          │ Lands user        │
│                    │                                     │ corrections       │
│                    │                                     │ mid-session       │
│                    │                                     │ instead of        │
│                    │                                     │ ploughing on.     │
│ lm_agent_tools     │ agent_tool_hallucination/overall    │ Avoids inventing  │
│                    │                                     │ tools or calling  │
│                    │                                     │ them with made-up │
│                    │                                     │ arguments.        │
│ lm_agent_finish    │ agent_task_outcome_explicit/overall │ Actually finishes │
│                    │                                     │ the task, and     │
│                    │                                     │ says so           │
│                    │                                     │ explicitly when   │
│                    │                                     │ it does.          │
│ lm_agent_recovery  │ agent_bash_recovery_steps/overall   │ Recovers from a   │
│                    │                                     │ failed shell      │
│                    │                                     │ command in few    │
│                    │                                     │ steps.            │
│ lm_agent_sentiment │ agent_praise_complaint/overall      │ Praise-vs-compla… │
│                    │                                     │ balance in        │
│                    │                                     │ session feedback. │
└────────────────────┴─────────────────────────────────────┴───────────────────┘

Artificial Analysis evaluations                                                 
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ column              ┃ aa_key                                 ┃ description   ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ aa_intelligence     │ artificial_analysis_intelligence_index │ AA            │
│                     │                                        │ Intelligence  │
│                     │                                        │ Index         │
│                     │                                        │ (0-100).      │
│                     │                                        │ Composite     │
│                     │                                        │ across their  │
│                     │                                        │ eval suite.   │
│                     │                                        │ Also surfaced │
│                     │                                        │ as the        │
│                     │                                        │ rolled-up     │
│                     │                                        │ `quality_ind… │
│ aa_coding           │ artificial_analysis_coding_index       │ AA Coding     │
│                     │                                        │ Index         │
│                     │                                        │ (0-100).      │
│                     │                                        │ Composite of  │
│                     │                                        │ their coding  │
│                     │                                        │ evaluations.  │
│ aa_math             │ artificial_analysis_math_index         │ AA Math Index │
│                     │                                        │ (0-100).      │
│ aa_terminalbench    │ terminalbench_hard                     │ Terminal-Ben… │
│                     │                                        │ Hard pass     │
│                     │                                        │ rate.         │
│                     │                                        │ Agentic: the  │
│                     │                                        │ model drives  │
│                     │                                        │ a shell to    │
│                     │                                        │ complete real │
│                     │                                        │ tasks.        │
│                     │                                        │ Harness-meas… │
│                     │                                        │ — see issue   │
│                     │                                        │ #3.           │
│ aa_terminalbench_v2 │ terminalbench_v2_1                     │ Terminal-Ben… │
│                     │                                        │ v2.1 pass     │
│                     │                                        │ rate. Newer   │
│                     │                                        │ revision,     │
│                     │                                        │ thinner       │
│                     │                                        │ coverage.     │
│ aa_tau2             │ tau2                                   │ tau-bench 2   │
│                     │                                        │ pass rate.    │
│                     │                                        │ Tool use      │
│                     │                                        │ under a       │
│                     │                                        │ customer-ser… │
│                     │                                        │ policy.       │
│ aa_lcr              │ lcr                                    │ Long-context  │
│                     │                                        │ reasoning     │
│                     │                                        │ pass rate.    │
│ aa_ifbench          │ ifbench                                │ IFBench pass  │
│                     │                                        │ rate.         │
│                     │                                        │ Instruction   │
│                     │                                        │ following.    │
└─────────────────────┴────────────────────────────────────────┴───────────────┘

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
  - lm_agent_* are signed scores near 0, not Elo. Compare within the column 
only.
  - aa_* come from Artificial Analysis (https://artificialanalysis.ai/). Indices
are 0-100; the rest are 0-1 pass rates.


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
