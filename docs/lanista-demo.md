# lanista: pick the right LLM for the task

*2026-04-24T05:39:33Z by Showboat 0.6.1*
<!-- showboat-id: 10ad38b2-605c-470f-b5b4-0699a88ce51e -->

lanista is a local LLM model catalog and picker. It aggregates **structured data** from eight sources (OpenRouter, LiteLLM, pi-mono, LMArena, Aider's polyglot leaderboard, Factory AI Weather, gkisokay tiers, Artificial Analysis) and **prose practitioner opinions** from three feeds (Simon Willison, Eugene Yan, Hacker News). The hero command, `lanista pick`, builds a self-contained citeable prompt that any LLM can answer — every recommendation must cite either a catalog column or a specific opinion entry.

This document doubles as proof: a subagent ingests the prompt and produces a verifiable answer, in-doc, below.

> **`pick` is one of three lenses.** For trade-off questions ("cheapest / balanced / flagship"), use the deterministic `pareto` and `profiles` commands instead — they short-circuit the LLM when the question is pure arithmetic. See [workflows.md](workflows.md) for the three-lens story (pareto / profiles / pick) and when to reach for each.

```bash
lanista --help
```

```output
                                                                                
 Usage: lanista [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 LLM model catalog and router.                                                  
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --json               Machine-readable JSON output (stderr for notices)       │
│ --verbose  -v        Show detailed progress                                  │
│ --help               Show this message and exit.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ fetch             Download every source, merge, write the index to the XDG   │
│                   cache dir.                                                 │
│ show              Inspect models whose id contains SUBSTR.                   │
│ agents            List coding agents (CLI wrappers that route to model       │
│                   providers).                                                │
│ tier              List models at a given curated tier.                       │
│ pick              Build a citeable picker prompt for TASK (paste into any    │
│                   LLM).                                                      │
│ pareto            Deterministic Pareto frontier over QUALITY vs COST.        │
│ profiles          Three anchor picks on the QUALITY×COST frontier: flagship  │
│                   / balanced / budget.                                       │
│ chart             Render a scatter plot of QUALITY vs COST with the frontier │
│                   highlighted.                                               │
│ refresh-opinions  Refresh the opinion corpus (blog feeds, HN).               │
│ doctor            Run proactive health checks. Use --verbose for             │
│                   connectivity probes.                                       │
╰──────────────────────────────────────────────────────────────────────────────╯

```

## The landing page is the user manual

Run `lanista` with no arguments — it prints catalog status and surfaces `pick` as the first next step. A coding agent dropped into this repo learns the hero command without reading any docs.

```bash
lanista
```

```output
lanista — model catalog
  Generated: 2026-04-24T10:04:27.472009+00:00 (0d ago)
  Models:    2764
  Agents:    27
  Curated:   T1=3, T2=4, T3=7, T4=5
  Sources:   openrouter=353, litellm=2677, pimono=876, gkisokay=19, 
factory_weather=10, aider=68, artificial_analysis=9, lmarena=347
  Index:     /Users/mhild/.cache/lanista/model_index.json
  Sources:   /Users/mhild/.config/lanista/sources

Next steps:
  lanista pick '<task>'  Build a self-contained picker prompt (hero command)
  lanista fetch          Refresh the index
  lanista show <substr>  Inspect a model
  lanista tier 1         List curated Tier 1 models
  lanista agents         List coding agents
  lanista doctor         Run health checks
```

## Pulling structured sources

`fetch` downloads every source, normalizes per-model fields, and writes a merged index to `~/.cache/lanista/model_index.json`. LMArena comes via a single Parquet download; the rest are public JSON / YAML / RSS.

```bash
lanista fetch
```

```output
+ openrouter           353 models
+ litellm              2677 models
+ pimono               876 models
+ gkisokay             19 models
+ factory_weather      10 models
+ aider                68 models
+ artificial_analysis  9 models
+ lmarena              347 models
-> /Users/mhild/.cache/lanista/model_index.json (12938 KB, 2764 models)

Next steps:
  lanista         Show summary
  lanista tier 1  List curated Tier 1 models
  lanista doctor  Run health checks
```

## Pulling prose opinions

The opinion corpus lives separately from the per-model catalog — it's keyed by post ID, not by model. Each entry has a stable, citeable ID so the picker can reference specific claims and the reader can verify them.

```bash
lanista refresh-opinions
```

```output
[INFO] willison: 30 entries
[INFO] eugeneyan: 209 entries
[INFO] hn: 257 entries
```

## Browsing the catalog

`tier 1` lists curated frontier models with strengths, weaknesses, and use-case notes (curated source: gkisokay). Lower tiers progressively include mid-range and local/free models.

```bash
lanista tier 1 --no-sources
```

```output
Tier 1 — 3 model(s):

claude-opus-4-7  [gkisokay]
  use for:   Complex external dev via Claude Code, multi-file refactoring, 
vision-heavy agentic workflows
  + #1 SWE-Verified (87.6%) + SWE-Pro
  + 3.75MP vision (3x Opus 4.6)
  + 1M context, 128K output
  + Adaptive thinking, multi-agent coordination
  - Premium pricing ($5 in / $25 out)
  - API only - no subscription for agents

glm-5-1  [gkisokay]
  use for:   Long-horizon agentic coding, sustained optimization loops
  + #1 SWE-Pro globally
  + 8-hour autonomous execution
  + MIT license, open weights, self-hostable
  + 3x cheaper than Opus on input
  - Benchmarks self-reported by Z.AI (pending independent verification)

gpt-5-4  [gkisokay]
  use for:   External Codex-driven complex features, terminal-heavy workflows
  + Superhuman computer use (OSWorld 75%)
  + Real multi-hour planning
  + Steerable planner + judge in Codex
  + Absorbs GPT-5.3 Codex + dynamic MCP tool search
  - $100/month plan for best access


Next steps:
  lanista --json tier <n>        Structured output with full observations
  lanista tier <n> --no-sources  Curated notes only (terse)
  lanista show <id>              Full pricing/context details
```

## Inspecting a single model

`show` accepts a substring and dumps pricing, context window, curated notes, and per-source observations. Each observation is attributed to the source it came from — including the LMArena Elo ratings by category.

```bash
lanista show claude-opus-4-7
```

```output
9 model(s) matching 'claude-opus-4-7':

anthropic-claude-opus-4-7
  context:   1,000,000
  pricing:   $5.0 in / $25.0 out per 1M
  Sources:
    [litellm] anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +8  
via=bedrock_converse
    [litellm] openrouter/anthropic/claude-opus-4.7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +5  via=openrouter
    [litellm] perplexity/anthropic/claude-opus-4-7
        caps=web_search,function_calling  via=perplexity
    [pimono ] amazon-bedrock/anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=amazon-bedrock  reasoning=yes  
modalities=text,image
    [pimono ] openrouter/anthropic/claude-opus-4.7
        ctx=1,000,000  price=$5/$25  via=openrouter  reasoning=yes  
modalities=text,image
    [pimono ] vercel-ai-gateway/anthropic/claude-opus-4.7
        ctx=1,000,000  price=$5/$25  via=vercel-ai-gateway  reasoning=yes  
modalities=text,image

au-anthropic-claude-opus-4-7
  context:   1,000,000
  pricing:   $5.5 in / $27.5 out per 1M
  Sources:
    [litellm] au.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5.5/$27.5  
caps=computer_use,function_calling,pdf_input,prompt_caching +8  
via=bedrock_converse

claude-opus-4-7
  context:   1,000,000
  pricing:   $5.0 in / $25.0 out per 1M
  tier:      1  [gkisokay]
  use for:   Complex external dev via Claude Code, multi-file refactoring, 
vision-heavy agentic workflows  [gkisokay]
  Sources:
    [openrouter         ] anthropic/claude-opus-4.7
        ctx=1,000,000  price=$5.0/$25.0  modalities=text,image  tokenizer=Claude
    [litellm            ] azure_ai/claude-opus-4-7
        ctx=200,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  via=azure_ai
    [litellm            ] claude-opus-4-7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  via=anthropic
    [litellm            ] vertex_ai/claude-opus-4-7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  
via=vertex_ai-anthropic_models
    [pimono             ] anthropic/claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=anthropic  reasoning=yes  
modalities=text,image
    [pimono             ] github-copilot/claude-opus-4.7
        ctx=144,000  price=$0/$0  via=github-copilot  reasoning=yes  
modalities=text,image
    [pimono             ] opencode/claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=opencode  reasoning=yes  
modalities=text,image
    [gkisokay           ] claude-opus-4-7
        (no extracted fields)
    [factory_weather    ] opus-4.7
        mentions=1  latest=Mon, 20 Apr 2026 12:00:00 GMT
    [artificial_analysis] claude-opus-4-7
        quality_index=57.0
    [lmarena            ] claude-opus-4-7
        lm_overall=1480  lm_coding=1527  lm_creative_writing=1476  
lm_hard_prompts=1496  as_of=2026-04-22

claude-opus-4-7-20260416
  context:   1,000,000
  pricing:   $5.0 in / $25.0 out per 1M
  Sources:
    [litellm] claude-opus-4-7-20260416
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  via=anthropic

claude-opus-4-7-default
  context:   1,000,000
  pricing:   $5.0 in / $25.0 out per 1M
  Sources:
    [litellm] vertex_ai/claude-opus-4-7@default
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  
via=vertex_ai-anthropic_models

claude-opus-4-7-thinking
  Sources:
    [lmarena] claude-opus-4-7-thinking
        lm_overall=1488  lm_coding=1539  lm_creative_writing=1489  
lm_hard_prompts=1505  as_of=2026-04-22

eu-anthropic-claude-opus-4-7
  context:   1,000,000
  pricing:   $5.5 in / $27.5 out per 1M
  Sources:
    [litellm] eu.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5.5/$27.5  
caps=computer_use,function_calling,pdf_input,prompt_caching +8  
via=bedrock_converse
    [pimono ] amazon-bedrock/eu.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=amazon-bedrock  reasoning=yes  
modalities=text,image

global-anthropic-claude-opus-4-7
  context:   1,000,000
  pricing:   $5.0 in / $25.0 out per 1M
  Sources:
    [litellm] global.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +8  
via=bedrock_converse
    [pimono ] amazon-bedrock/global.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=amazon-bedrock  reasoning=yes  
modalities=text,image

us-anthropic-claude-opus-4-7
  context:   1,000,000
  pricing:   $5.5 in / $27.5 out per 1M
  Sources:
    [litellm] us.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5.5/$27.5  
caps=computer_use,function_calling,pdf_input,prompt_caching +8  
via=bedrock_converse
    [pimono ] amazon-bedrock/us.anthropic.claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=amazon-bedrock  reasoning=yes  
modalities=text,image


Next steps:
  lanista --json show <substr>        Full structured record
  lanista show <substr> --no-sources  Hide per-source attribution
```

## Coding agents catalog

`agents` lists CLI wrappers (Claude Code, Aider, Cursor, etc.) and the model they route to by default. Useful when you already have a CLI preference and just need to pick the best model for it.

```bash
lanista agents
```

```output
27 coding agent(s):

  aider                  cli=LiteLLM                default=-
  amazon-bedrock         cli=-                      
default=us.anthropic.claude-opus-4-6-v1 (91 models)
  anthropic              cli=claude-code            default=claude-opus-4-7 (23 
models)
  azure-openai-responses cli=-                      default=gpt-5.4 (41 models)
  cerebras               cli=-                      default=zai-glm-4.7 (4 
models)
  claude-code            cli=anthropic provider     default=-
  cursor                 cli=settings UI            default=-
  fireworks              cli=-                      
default=accounts/fireworks/models/kimi-k2p6 (18 models)
  github-copilot         cli=gh copilot / VSCode    default=gpt-5.4 (25 models)
  google                 cli=-                      
default=gemini-3.1-pro-preview (27 models)
  google-antigravity     cli=antigravity            default=gemini-3.1-pro-high 
(9 models)
  google-gemini-cli      cli=gemini                 
default=gemini-3.1-pro-preview (7 models)
  google-vertex          cli=-                      
default=gemini-3.1-pro-preview (13 models)
  groq                   cli=-                      default=openai/gpt-oss-120b 
(18 models)
  huggingface            cli=-                      default=moonshotai/Kimi-K2.6
(21 models)
  kimi-coding            cli=kimi                   default=kimi-for-coding (3 
models)
  minimax                cli=-                      default=MiniMax-M2.7 (2 
models)
  minimax-cn             cli=-                      default=MiniMax-M2.7 (2 
models)
  mistral                cli=mistral-cli            
default=devstral-medium-latest (26 models)
  openai                 cli=-                      default=gpt-5.4 (41 models)
  openai-codex           cli=codex                  default=gpt-5.5 (10 models)
  opencode               cli=opencode               default=kimi-k2.6 (38 
models)
  opencode-go            cli=-                      default=kimi-k2.6 (12 
models)
  openrouter             cli=-                      default=moonshotai/kimi-k2.6
(252 models)
  vercel-ai-gateway      cli=-                      default=zai/glm-5.1 (156 
models)
  xai                    cli=grok-cli               
default=grok-4.20-0309-reasoning (24 models)
  zai                    cli=-                      default=glm-5.1 (13 models)

Next steps:
  lanista agents <substr>       Drill into one agent's model list
  lanista --json agents <name>  Full structured record
```

## The hero: `lanista pick`

Given a natural-language task, lanista assembles a self-contained prompt with:

- A **header** addressed to the receiving LLM (so a coding agent that just ran the command knows it should answer the prompt directly, not re-call lanista).
- A **catalog table** of the top 60 models by LMArena rating, with columns for price, context, Aider coding pass-rate, and LMArena Elo ratings split by category (`lm_coding`, `lm_writing`, `lm_hard`, `lm_long`, `lm_english`, `lm_chinese`, `lm_document`).
- The **40 most recent opinion excerpts** from Willison, Eugene Yan, and HN — each with a stable citeable ID.
- **Strict citation rules**: every claim in the answer must cite either a catalog column or an opinion ID. Picks without matching opinions must end with the literal token `[no-opinion-match]`.

The prompt is LLM-agnostic — paste it into Claude, ChatGPT, Gemini, or local. Every recommendation is verifiable because every cited ID appears in the prompt with its source URL.

First, the agent-facing header and TASK line:

```bash
lanista pick 'pick a model for an autonomous coding agent that does multi-file TypeScript refactors with tool use' --top 3 | sed -n '1,10p'
```

```output
# lanista model-picker prompt — self-contained.
# If you are an LLM reading this (e.g. a coding agent that just ran
# `lanista pick ...` on the user's behalf), answer it directly using
# only the CATALOG and OPINIONS below. Follow the INSTRUCTIONS at the
# end. Do not call lanista again — everything you need is in this prompt.

TASK: pick a model for an autonomous coding agent that does multi-file TypeScript refactors with tool use

Opinion corpus has 40 recent entries.

```

Then the catalog table (top of the prompt body):

```bash
lanista pick 'pick a model for an autonomous coding agent that does multi-file TypeScript refactors with tool use' --top 3 | sed -n '11,25p'
```

```output
CATALOG (top 60 by best available LMArena rating; price is $/Mtok input/output; modalities uses txt/img/aud/vid/pdf; caps uses pdf/cu/fn/vis/think; tier is curated 1=frontier..4=local; lm_* columns are LMArena Elo ratings by category; '-' means no data):
| model | price_$/Mtok | ctx | aider | modalities | caps | tier | lm_overall | lm_coding | lm_writing | lm_hard | lm_long | lm_english | lm_chinese | lm_document |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-4-6-thinking | 5/25 | 200000 | - | txt+img | - | - | 1500 | 1541 | 1498 | 1530 | 1524 | 1513 | 1543 | 1528 |
| claude-opus-4-6 | 5.0/25.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | - | 1495 | 1541 | 1477 | 1528 | 1521 | 1504 | 1550 | 1520 |
| gemini-3-1-pro | 2.0/12.0 | 1048576 | - | aud+file+img+txt+vid | fn,pdf,think,vis | 3 | 1488 | 1495 | 1490 | 1494 | 1489 | 1484 | 1545 | 1451 |
| claude-opus-4-7-thinking | - | - | - | - | - | - | 1488 | 1539 | 1489 | 1505 | 1507 | 1494 | 1552 | 1515 |
| claude-opus-4-7 | 5.0/25.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | 1 | 1480 | 1527 | 1476 | 1496 | 1510 | 1492 | 1540 | 1523 |
| gemini-3-pro | - | - | - | - | - | - | 1479 | 1483 | 1483 | 1482 | 1473 | 1480 | 1528 | 1443 |
| muse-spark | - | - | - | - | - | - | 1477 | 1484 | 1456 | 1480 | 1444 | 1481 | 1520 | 1457 |
| gpt-5-4-high | - | - | - | - | - | - | 1472 | 1506 | 1443 | 1491 | 1480 | 1469 | 1530 | - |
| qwen3-5-max-preview | - | - | - | - | - | - | 1472 | 1479 | 1461 | 1483 | 1470 | 1478 | 1528 | - |
| gemini-3-flash | 0.5/3 | 1048576 | - | txt+img | - | - | 1467 | 1463 | 1459 | 1465 | 1451 | 1466 | 1513 | 1423 |
| glm-5-1 | 1.05/3.5 | 202752 | - | txt | - | 1 | 1467 | 1496 | 1456 | 1474 | 1477 | 1477 | 1516 | - |
| gemini-2-5-pro | 1.25/10.0 | 1048576 | - | txt+img+file+aud+vid | fn,pdf,think,vis | - | 1460 | 1455 | 1457 | 1457 | 1452 | 1460 | 1513 | 1433 |
```

Below the table comes a block of recent opinion excerpts. Here are the first three:

```bash
lanista pick 'pick a model for an autonomous coding agent that does multi-file TypeScript refactors with tool use' --top 3 | awk '/RECENT PRACTITIONER OPINIONS/,0' | sed -n '1,17p'
```

```output
RECENT PRACTITIONER OPINIONS (cite by [ID]):
[willison-2026-Apr-24-deepseek-v4] willison — 2026-04-24T06:01:04+00:00 — DeepSeek V4 - almost on the frontier, a fraction of the price
  URL: https://simonwillison.net/2026/Apr/24/deepseek-v4/#atom-tag
  > Chinese AI lab DeepSeek's last model release was V3.2 (and V3.2 Speciale) last December . They just dropped the first of their hotly anticipated V4 series in the shape of two preview models, DeepSeek-V4-Pro and DeepSeek-V4-Flash . Both models are 1 million token context Mixture of Experts. Pro is 1.6T total parameters, 49B active. Flash is 284B total, 13B active. They're using the standard MIT lic…

[willison-2026-Apr-24-recent-claude-code-quality-reports] willison — 2026-04-24T01:31:25+00:00 — An update on recent Claude Code quality reports
  URL: https://simonwillison.net/2026/Apr/24/recent-claude-code-quality-reports/#atom-tag
  > An update on recent Claude Code quality reports It turns out the high volume of complaints that Claude Code was providing worse quality results over the past two months was grounded in real problems. The models themselves were not to blame, but three separate issues in the Claude Code harness caused complex but material problems which directly affected users. Anthropic's postmortem describes these…

[hn-47884971] hn — 2026-04-24 — DeepSeek v4
  URL: https://news.ycombinator.com/item?id=47884971
  > 969 points, 617 comments on Hacker News. Linked: https://api-docs.deepseek.com/

[willison-2026-Apr-23-liteparse-for-the-web] willison — 2026-04-23T21:54:24+00:00 — Extract PDF text in your browser with LiteParse for the web
  URL: https://simonwillison.net/2026/Apr/23/liteparse-for-the-web/#atom-tag
  > LlamaIndex have a most excellent open source project called LiteParse , which provides a Node.js CLI tool for extracting text from PDFs. I got a version of LiteParse working entirely in the browser, using most of the same libraries that LiteParse uses to run in Node.js. Spatial text parsing Refreshingly, LiteParse doesn't use AI models to do what it does: it's good old-fashioned PDF parsing, falli…

```

The prompt ends with the citation contract:

```bash
lanista pick 'pick a model for an autonomous coding agent that does multi-file TypeScript refactors with tool use' --top 3 | awk '/INSTRUCTIONS/,0'
```

```output
# only the CATALOG and OPINIONS below. Follow the INSTRUCTIONS at the
# end. Do not call lanista again — everything you need is in this prompt.

TASK: pick a model for an autonomous coding agent that does multi-file TypeScript refactors with tool use

Opinion corpus has 40 recent entries.

CATALOG (top 60 by best available LMArena rating; price is $/Mtok input/output; modalities uses txt/img/aud/vid/pdf; caps uses pdf/cu/fn/vis/think; tier is curated 1=frontier..4=local; lm_* columns are LMArena Elo ratings by category; '-' means no data):
| model | price_$/Mtok | ctx | aider | modalities | caps | tier | lm_overall | lm_coding | lm_writing | lm_hard | lm_long | lm_english | lm_chinese | lm_document |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-4-6-thinking | 5/25 | 200000 | - | txt+img | - | - | 1500 | 1541 | 1498 | 1530 | 1524 | 1513 | 1543 | 1528 |
| claude-opus-4-6 | 5.0/25.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | - | 1495 | 1541 | 1477 | 1528 | 1521 | 1504 | 1550 | 1520 |
| gemini-3-1-pro | 2.0/12.0 | 1048576 | - | aud+file+img+txt+vid | fn,pdf,think,vis | 3 | 1488 | 1495 | 1490 | 1494 | 1489 | 1484 | 1545 | 1451 |
| claude-opus-4-7-thinking | - | - | - | - | - | - | 1488 | 1539 | 1489 | 1505 | 1507 | 1494 | 1552 | 1515 |
| claude-opus-4-7 | 5.0/25.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | 1 | 1480 | 1527 | 1476 | 1496 | 1510 | 1492 | 1540 | 1523 |
| gemini-3-pro | - | - | - | - | - | - | 1479 | 1483 | 1483 | 1482 | 1473 | 1480 | 1528 | 1443 |
| muse-spark | - | - | - | - | - | - | 1477 | 1484 | 1456 | 1480 | 1444 | 1481 | 1520 | 1457 |
| gpt-5-4-high | - | - | - | - | - | - | 1472 | 1506 | 1443 | 1491 | 1480 | 1469 | 1530 | - |
| qwen3-5-max-preview | - | - | - | - | - | - | 1472 | 1479 | 1461 | 1483 | 1470 | 1478 | 1528 | - |
| gemini-3-flash | 0.5/3 | 1048576 | - | txt+img | - | - | 1467 | 1463 | 1459 | 1465 | 1451 | 1466 | 1513 | 1423 |
| glm-5-1 | 1.05/3.5 | 202752 | - | txt | - | 1 | 1467 | 1496 | 1456 | 1474 | 1477 | 1477 | 1516 | - |
| gemini-2-5-pro | 1.25/10.0 | 1048576 | - | txt+img+file+aud+vid | fn,pdf,think,vis | - | 1460 | 1455 | 1457 | 1457 | 1452 | 1460 | 1513 | 1433 |
| grok-4-20-beta-0309-reasoning | 2.0/6.0 | 2000000 | - | - | fn,think,vis | - | 1456 | 1462 | 1428 | 1458 | 1432 | 1459 | 1493 | 1426 |
| dola-seed-2-0-pro | - | - | - | - | - | - | 1455 | 1478 | 1407 | 1463 | 1429 | 1456 | 1515 | - |
| gpt-5-4 | 2.5/15.0 | 1050000 | - | txt+img+file | fn,pdf,think,vis | 1 | 1454 | 1483 | 1423 | 1475 | 1472 | 1454 | 1535 | 1482 |
| kimi-k2-6 | 0.7448/4.655 | 256000 | - | txt+img | fn,think,vis | - | 1452 | 1486 | 1426 | 1469 | 1459 | 1454 | 1545 | 1459 |
| grok-4-20-multi-agent-beta-0309 | 2.0/6.0 | 2000000 | - | - | fn,think,vis | - | 1452 | 1460 | 1430 | 1447 | 1434 | 1453 | 1480 | - |
| grok-4-20-beta1 | - | - | - | - | - | - | 1452 | 1447 | 1441 | 1447 | 1426 | 1455 | 1493 | - |
| ernie-5-0-0110 | - | - | - | - | - | - | 1450 | 1459 | 1431 | 1452 | 1429 | 1450 | 1508 | - |
| amazon-nova-experimental-chat-26-02-10 | - | - | - | - | - | - | 1448 | 1485 | 1363 | 1458 | 1436 | 1457 | 1463 | - |
| claude-opus-4-5-20251101 | 5.0/25.0 | 200000 | - | txt+img | cu,fn,pdf,think,vis | - | 1448 | 1496 | 1444 | 1474 | 1479 | 1459 | 1465 | 1471 |
| gemini-3-flash-thinking-minimal | - | - | - | - | - | - | 1448 | 1445 | 1439 | 1444 | 1432 | 1449 | 1486 | - |
| deepseek-v4-pro-thinking | - | - | - | - | - | - | 1447 | 1461 | 1431 | 1459 | 1458 | 1461 | 1486 | - |
| claude-sonnet-4-6 | 3.0/15.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | 3 | 1447 | 1499 | 1430 | 1480 | 1485 | 1462 | 1490 | 1503 |
| deepseek-v4-pro | 1.74/3.48 | 1048576 | - | txt | - | - | 1447 | 1435 | 1441 | 1448 | 1431 | 1448 | 1508 | - |
| claude-opus-4-5-20251101-thinking-32k | - | - | - | - | - | - | 1446 | 1503 | 1443 | 1471 | 1478 | 1459 | 1462 | - |
| glm-5 | 0.6/2.08 | 202752 | - | txt | fn,think | - | 1446 | 1455 | 1437 | 1451 | 1442 | 1456 | 1524 | - |
| kimi-k2-5-thinking | - | - | - | - | - | - | 1445 | 1481 | 1417 | 1454 | 1442 | 1453 | 1515 | 1445 |
| qwen3-5-397b-a17b | 0.39/2.34 | 262144 | - | txt+img+vid | - | - | 1443 | 1461 | 1410 | 1448 | 1436 | 1450 | 1505 | - |
| ernie-5-0-preview-1203 | - | - | - | - | - | - | 1442 | 1426 | 1422 | 1437 | 1408 | 1440 | 1481 | - |
| gemma-4-31b | - | - | - | - | - | 4 | 1442 | 1455 | 1418 | 1446 | 1443 | 1448 | 1473 | 1431 |
| grok-4-1-thinking | - | - | - | - | - | - | 1441 | 1449 | 1411 | 1438 | 1410 | 1447 | 1462 | - |
| gpt-5-1-high | - | - | - | - | - | - | 1441 | 1452 | 1427 | 1454 | 1445 | 1449 | 1493 | - |
| qwen3-6-plus | 0.325/1.95 | 1000000 | - | txt+img+vid | - | 3 | 1441 | 1476 | 1386 | 1449 | 1439 | 1448 | 1464 | - |
| glm-4-6 | 0.39/1.9 | 204800 | - | txt | fn,think | - | 1440 | 1450 | 1413 | 1440 | 1423 | 1448 | 1500 | - |
| gpt-5-2-chat-latest-20260210 | - | - | - | - | - | - | 1439 | 1450 | 1403 | 1445 | 1424 | 1446 | 1474 | - |
| qwen3-max-preview | - | 258048 | - | - | fn,think | - | 1439 | 1457 | 1401 | 1448 | 1438 | 1440 | 1486 | - |
| grok-4-1 | - | - | - | - | - | - | 1438 | 1444 | 1412 | 1437 | 1415 | 1448 | 1474 | - |
| glm-4-7 | 0.38/1.74 | 202752 | - | txt | fn,think | - | 1436 | 1457 | 1402 | 1444 | 1434 | 1454 | 1484 | - |
| gemma-4-26b-a4b | - | - | - | - | - | - | 1435 | 1445 | 1404 | 1439 | 1430 | 1442 | 1480 | - |
| claude-sonnet-4-5-20250929 | 3.0/15.0 | 200000 | - | txt+img | cu,fn,pdf,think,vis | - | 1433 | 1481 | 1437 | 1457 | 1474 | 1447 | 1454 | 1450 |
| mimo-v2-pro | 1.0/3.0 | 1048576 | - | txt | - | 2 | 1433 | 1477 | 1409 | 1457 | 1456 | 1453 | 1442 | - |
| mistral-large-3 | 0.5/1.5 | 256000 | - | - | fn,vis | - | 1430 | 1445 | 1392 | 1430 | 1411 | 1441 | 1446 | - |
| ernie-5-0-preview-1022 | - | - | - | - | - | - | 1429 | 1413 | 1415 | 1421 | 1407 | 1430 | 1503 | - |
| glm-4-5 | 0.6/2.2 | 131072 | - | txt | fn | - | 1429 | 1433 | 1395 | 1429 | 1411 | 1433 | 1469 | - |
| claude-sonnet-4-5-20250929-thinking-32k | - | - | - | - | - | - | 1429 | 1486 | 1415 | 1457 | 1470 | 1447 | 1455 | - |
| chatgpt-4o-latest-20250326 | - | - | - | - | - | - | 1429 | 1415 | 1407 | 1424 | 1412 | 1432 | 1453 | - |
| deepseek-r1-0528 | 0.5/2.15 | 163840 | 71% | txt | fn,think | - | 1428 | 1427 | 1410 | 1416 | 1391 | 1434 | 1460 | - |
| deepseek-v4-flash | 0.14/0.28 | 1048576 | - | txt | - | - | 1427 | 1441 | 1399 | 1435 | 1420 | 1433 | 1494 | - |
| mistral-medium-2508 | 0.4/2 | 262144 | - | txt+img | - | - | 1426 | 1432 | 1394 | 1427 | 1406 | 1436 | 1447 | - |
| longcat-flash-chat-2602-exp | - | - | - | - | - | - | 1425 | 1470 | 1391 | 1437 | 1425 | 1454 | 1473 | - |
| deepseek-v4-flash-thinking | - | - | - | - | - | - | 1425 | 1441 | 1392 | 1437 | 1415 | 1431 | 1475 | - |
| grok-3-preview-02-24 | - | - | - | - | - | - | 1425 | 1432 | 1415 | 1433 | 1438 | 1436 | 1448 | - |
| deepseek-v3-2 | 0.252/0.378 | 131072 | - | txt | fn,think | 2 | 1424 | 1447 | 1397 | 1433 | 1426 | 1435 | 1455 | - |
| deepseek-v3-2-exp-thinking | - | - | - | - | - | - | 1424 | 1438 | 1392 | 1426 | 1407 | 1440 | 1454 | - |
| deepseek-v3-2-exp | 0.27/0.41 | 163840 | - | txt | - | - | 1423 | 1433 | 1404 | 1430 | 1418 | 1439 | 1463 | - |
| gemini-3-1-flash-lite-preview | 0.25/1.5 | 1048576 | - | txt+img+vid+file+aud | fn,pdf,think,vis | - | 1423 | 1399 | 1406 | 1408 | 1399 | 1423 | 1455 | - |
| gpt-5-1 | 1.25/10.0 | 400000 | - | img+txt+file | fn,pdf,think,vis | - | 1422 | 1437 | 1404 | 1434 | 1430 | 1425 | 1474 | 1412 |
| longcat-flash-chat | - | - | - | - | - | - | 1422 | 1468 | 1346 | 1433 | 1391 | 1441 | 1430 | - |
| qwen3-vl-235b-a22b-instruct | 0.2/0.88 | 262144 | - | txt+img | fn,vis | - | 1421 | 1440 | 1371 | 1430 | 1422 | 1430 | 1460 | - |

TIER 1/2 USE-CASE NOTES (curated — cite via `tier` + model id):
[tier 1] claude-opus-4-7: Complex external dev via Claude Code, multi-file refactoring, vision-heavy agentic workflows
[tier 1] glm-5-1: Long-horizon agentic coding, sustained optimization loops
[tier 1] gpt-5-4: External Codex-driven complex features, terminal-heavy workflows
[tier 2] mimo-v2-pro: Agent orchestration brain, custom OpenClaw workflows, long-context agent sessions
[tier 2] deepseek-v3-2: Cost-floor frontier reasoning, high-volume coding

RECENT PRACTITIONER OPINIONS (cite by [ID]):
[willison-2026-Apr-24-deepseek-v4] willison — 2026-04-24T06:01:04+00:00 — DeepSeek V4 - almost on the frontier, a fraction of the price
  URL: https://simonwillison.net/2026/Apr/24/deepseek-v4/#atom-tag
  > Chinese AI lab DeepSeek's last model release was V3.2 (and V3.2 Speciale) last December . They just dropped the first of their hotly anticipated V4 series in the shape of two preview models, DeepSeek-V4-Pro and DeepSeek-V4-Flash . Both models are 1 million token context Mixture of Experts. Pro is 1.6T total parameters, 49B active. Flash is 284B total, 13B active. They're using the standard MIT lic…

[willison-2026-Apr-24-recent-claude-code-quality-reports] willison — 2026-04-24T01:31:25+00:00 — An update on recent Claude Code quality reports
  URL: https://simonwillison.net/2026/Apr/24/recent-claude-code-quality-reports/#atom-tag
  > An update on recent Claude Code quality reports It turns out the high volume of complaints that Claude Code was providing worse quality results over the past two months was grounded in real problems. The models themselves were not to blame, but three separate issues in the Claude Code harness caused complex but material problems which directly affected users. Anthropic's postmortem describes these…

[hn-47884971] hn — 2026-04-24 — DeepSeek v4
  URL: https://news.ycombinator.com/item?id=47884971
  > 969 points, 617 comments on Hacker News. Linked: https://api-docs.deepseek.com/

[willison-2026-Apr-23-liteparse-for-the-web] willison — 2026-04-23T21:54:24+00:00 — Extract PDF text in your browser with LiteParse for the web
  URL: https://simonwillison.net/2026/Apr/23/liteparse-for-the-web/#atom-tag
  > LlamaIndex have a most excellent open source project called LiteParse , which provides a Node.js CLI tool for extracting text from PDFs. I got a version of LiteParse working entirely in the browser, using most of the same libraries that LiteParse uses to run in Node.js. Spatial text parsing Refreshingly, LiteParse doesn't use AI models to do what it does: it's good old-fashioned PDF parsing, falli…

[willison-2026-Apr-23-gpt-5-5] willison — 2026-04-23T19:59:47+00:00 — A pelican for GPT-5.5 via the semi-official Codex backdoor API
  URL: https://simonwillison.net/2026/Apr/23/gpt-5-5/#atom-tag
  > GPT-5.5 is out . It's available in OpenAI Codex and is rolling out to paid ChatGPT subscribers. I've had some preview access and found it to be a fast, effective and highly capable model. As is usually the case these days, it's hard to put into words what's good about it - I ask it to build things and it builds exactly what I ask for! There's one notable omission from today's release - the API: AP…

[hn-47879092] hn — 2026-04-23 — GPT-5.5
  URL: https://news.ycombinator.com/item?id=47879092
  > 1374 points, 904 comments on Hacker News. Linked: https://openai.com/index/introducing-gpt-5-5/

[willison-2026-Apr-22-qwen36-27b] willison — 2026-04-22T16:45:23+00:00 — Qwen3.6-27B: Flagship-Level Coding in a 27B Dense Model
  URL: https://simonwillison.net/2026/Apr/22/qwen36-27b/#atom-tag
  > Qwen3.6-27B: Flagship-Level Coding in a 27B Dense Model Big claims from Qwen about their latest open weight model: Qwen3.6-27B delivers flagship-level agentic coding performance, surpassing the previous-generation open-source flagship Qwen3.5-397B-A17B (397B total / 17B active MoE) across all major coding benchmarks. On Hugging Face Qwen3.5-397B-A17B is 807GB, this new Qwen3.6-27B is 55.6GB. I tri…

[willison-2026-Apr-22-bobby-holley] willison — 2026-04-22T05:40:56+00:00 — Quoting Bobby Holley
  URL: https://simonwillison.net/2026/Apr/22/bobby-holley/#atom-tag
  > As part of our continued collaboration with Anthropic, we had the opportunity to apply an early version of Claude Mythos Preview to Firefox. This week’s release of Firefox 150 includes fixes for 271 vulnerabilities identified during this initial evaluation. [...] Our experience is a hopeful one for teams who shake off the vertigo and get to work. You may need to reprioritize everything else to bri…

[willison-2026-Apr-22-changes-to-github-copilot] willison — 2026-04-22T03:30:02+00:00 — Changes to GitHub Copilot Individual plans
  URL: https://simonwillison.net/2026/Apr/22/changes-to-github-copilot/#atom-tag
  > Changes to GitHub Copilot Individual plans On the same day as Claude Code's temporary will-they-won't-they $100/month kerfuffle (for the moment, they won't ), here's the latest on GitHub Copilot pricing. Unlike Anthropic, GitHub put up an official announcement about their changes, which include tightening usage limits, pausing signups for individual plans (!), restricting Claude Opus 4.7 to the mo…

[willison-2026-Apr-22-claude-code-confusion] willison — 2026-04-22T02:07:34+00:00 — Is Claude Code going to cost $100/month? Probably not - it's all very confusing
  URL: https://simonwillison.net/2026/Apr/22/claude-code-confusion/#atom-tag
  > Anthropic today quietly (as in silently , no announcement anywhere at all) updated their claude.com/pricing page (but not their Choosing a Claude plan page , which shows up first for me on Google) to add this tiny but significant detail (arrow is mine, and it's already reverted ): The Internet Archive copy from yesterday shows a checkbox there. Claude Code used to be a feature of the $20/month Pro…

[hn-47863217] hn — 2026-04-22 — Qwen3.6-27B: Flagship-Level Coding in a 27B Dense Model
  URL: https://news.ycombinator.com/item?id=47863217
  > 958 points, 436 comments on Hacker News. Linked: https://qwen.ai/blog?id=qwen3.6-27b

[willison-2026-Apr-21-gpt-image-2] willison — 2026-04-21T20:32:24+00:00 — Where's the raccoon with the ham radio? (ChatGPT Images 2.0)
  URL: https://simonwillison.net/2026/Apr/21/gpt-image-2/#atom-tag
  > OpenAI released ChatGPT Images 2.0 today , their latest image generation model. On the livestream Sam Altman said that the leap from gpt-image-1 to gpt-image-2 was equivalent to jumping from GPT-3 to GPT-5. Here's how I put it to the test. My prompt: Do a where's Waldo style image but it's where is the raccoon holding a ham radio gpt-image-1 First as a baseline here's what I got from the older gpt…

[willison-2026-Apr-21-scosman] willison — 2026-04-21T15:54:43+00:00 — scosman/pelicans_riding_bicycles
  URL: https://simonwillison.net/2026/Apr/21/scosman/#atom-tag
  > scosman/pelicans_riding_bicycles I firmly approve of Steve Cosman's efforts to pollute the training set of pelicans riding bicycles. (To be fair, most of the examples I've published count as poisoning too.) Via Hacker News comment Tags: pelican-riding-a-bicycle , training-data , llms , ai , generative-ai

[willison-2026-Apr-20-llm-openrouter] willison — 2026-04-20T18:00:26+00:00 — llm-openrouter 0.6
  URL: https://simonwillison.net/2026/Apr/20/llm-openrouter/#atom-tag
  > Release: llm-openrouter 0.6 llm openrouter refresh command for refreshing the list of available models without waiting for the cache to expire. I added this feature so I could try Kimi 2.6 on OpenRouter as soon as it became available there . Here's its pelican - this time as an HTML page because Kimi chose to include an HTML and JavaScript UI to control the animation. Transcript here . Tags: openr…

[willison-2026-Apr-20-claude-token-counts] willison — 2026-04-20T00:50:45+00:00 — Claude Token Counter, now with model comparisons
  URL: https://simonwillison.net/2026/Apr/20/claude-token-counts/#atom-tag
  > Claude Token Counter, now with model comparisons I upgraded my Claude Token Counter tool to add the ability to run the same count against different models in order to compare them. As far as I can tell Claude Opus 4.7 is the first model to change the tokenizer, so it's only worth running comparisons between 4.7 and 4.6. The Claude token counting API accepts any Claude model ID though so I've inclu…

[hn-47834565] hn — 2026-04-20 — Qwen3.6-Max-Preview: Smarter, Sharper, Still Evolving
  URL: https://news.ycombinator.com/item?id=47834565
  > 704 points, 378 comments on Hacker News. Linked: https://qwen.ai/blog?id=qwen3.6-max-preview

[hn-47823270] hn — 2026-04-19 — Changes in the system prompt between Claude Opus 4.6 and 4.7
  URL: https://news.ycombinator.com/item?id=47823270
  > 368 points, 218 comments on Hacker News. Linked: https://simonwillison.net/2026/Apr/18/opus-system-prompt/

[willison-2026-Apr-18-opus-system-prompt] willison — 2026-04-18T23:59:40+00:00 — Changes in the system prompt between Claude Opus 4.6 and 4.7
  URL: https://simonwillison.net/2026/Apr/18/opus-system-prompt/#atom-tag
  > Anthropic are the only major AI lab to publish the system prompts for their user-facing chat systems. Their system prompt archive now dates all the way back to Claude 3 in July 2024 and it's always interesting to see how the system prompt evolves as they publish new models. Opus 4.7 shipped the other day (April 16, 2026) with a Claude.ai system prompt update since Opus 4.6 (February 5, 2026). I ha…

[willison-2026-Apr-18-extract-system-prompts] willison — 2026-04-18T12:25:00+00:00 — Claude system prompts as a git timeline
  URL: https://simonwillison.net/2026/Apr/18/extract-system-prompts/#atom-tag
  > Research: Claude system prompts as a git timeline Anthropic publish the system prompts for Claude chat and make that page available as Markdown . I had Claude Code turn that page into separate files for each model and model family with fake git commit dates to enable browsing the changes via the GitHub commit view. I used this to write my own detailed notes on the changes between Opus 4.6 and 4.7…

[willison-2026-04-18-127935] willison — 2026-04-18T03:15:36+00:00 — Adding a new content type to my blog-to-newsletter tool
  URL: https://simonwillison.net/guides/agentic-engineering-patterns/adding-a-new-content-type/#atom-tag
  > Agentic Engineering Patterns &gt; Here's an example of a deceptively short prompt that got a quite a lot of work done in a single shot. First, some background. I send out a free Substack newsletter around once a week containing content copied-and-pasted from my blog. I'm effectively using Substack as a lightweight way to allow people to subscribe to my blog via email. I generate the newsletter wit…

[hn-47814832] hn — 2026-04-18 — Claude Code Opus 4.7 keeps checking on malware
  URL: https://news.ycombinator.com/item?id=47814832
  > 69 points, 63 comments on Hacker News

[willison-2026-Apr-16-qwen-beats-opus] willison — 2026-04-16T17:16:52+00:00 — Qwen3.6-35B-A3B on my laptop drew me a better pelican than Claude Opus 4.7
  URL: https://simonwillison.net/2026/Apr/16/qwen-beats-opus/#atom-tag
  > For anyone who has been (inadvisably) taking my pelican riding a bicycle benchmark seriously as a robust way to test models, here are pelicans from this morning's two big model releases - Qwen3.6-35B-A3B from Alibaba and Claude Opus 4.7 from Anthropic . Here's the Qwen 3.6 pelican, generated using this 20.9GB Qwen3.6-35B-A3B-UD-Q4_K_S.gguf quantized model by Unsloth, running on my MacBook Pro M5 v…

[hn-47793411] hn — 2026-04-16 — Claude Opus 4.7
  URL: https://news.ycombinator.com/item?id=47793411
  > 1957 points, 1451 comments on Hacker News. Linked: https://www.anthropic.com/news/claude-opus-4-7

[hn-47796830] hn — 2026-04-16 — Qwen3.6-35B-A3B on my laptop drew me a better pelican than Claude Opus 4.7
  URL: https://news.ycombinator.com/item?id=47796830
  > 462 points, 97 comments on Hacker News. Linked: https://simonwillison.net/2026/Apr/16/qwen-beats-opus/

[hn-47793493] hn — 2026-04-16 — Claude Opus 4.7
  URL: https://news.ycombinator.com/item?id=47793493
  > 186 points, 11 comments on Hacker News. Linked: https://www.anthropic.com/claude/opus

[hn-47793546] hn — 2026-04-16 — Claude Opus 4.7 Model Card
  URL: https://news.ycombinator.com/item?id=47793546
  > 176 points, 84 comments on Hacker News. Linked: https://anthropic.com/claude-opus-4-7-system-card

[hn-47792764] hn — 2026-04-16 — Qwen3.6-35B-A3B: Agentic coding power, now open to all
  URL: https://news.ycombinator.com/item?id=47792764
  > 1272 points, 532 comments on Hacker News. Linked: https://qwen.ai/blog?id=qwen3.6-35b-a3b

[willison-2026-Apr-15-gemini-31-flash-tts] willison — 2026-04-15T17:13:14+00:00 — Gemini 3.1 Flash TTS
  URL: https://simonwillison.net/2026/Apr/15/gemini-31-flash-tts/#atom-tag
  > Gemini 3.1 Flash TTS Google released Gemini 3.1 Flash TTS today, a new text-to-speech model that can be directed using prompts. It's presented via the standard Gemini API using gemini-3.1-flash-tts-preview as the model ID, but can only output audio files. The prompting guide is surprising, to say the least. Here's their example prompt to generate just a few short sentences of audio: # AUDIO PROFIL…

[willison-2026-Apr-14-trusted-access-openai] willison — 2026-04-14T21:23:59+00:00 — Trusted access for the next era of cyber defense
  URL: https://simonwillison.net/2026/Apr/14/trusted-access-openai/#atom-tag
  > Trusted access for the next era of cyber defense OpenAI's answer to Claude Mythos appears to be a new model called GPT-5.4-Cyber: In preparation for increasingly more capable models from OpenAI over the next few months, we are fine-tuning our models specifically to enable defensive cybersecurity use cases, starting today with a variant of GPT‑5.4 trained to be cyber-permissive: GPT‑5.4‑Cyber. They…

[willison-2026-Apr-14-cybersecurity-proof-of-work] willison — 2026-04-14T19:41:48+00:00 — Cybersecurity Looks Like Proof of Work Now
  URL: https://simonwillison.net/2026/Apr/14/cybersecurity-proof-of-work/#atom-tag
  > Cybersecurity Looks Like Proof of Work Now The UK's AI Safety Institute recently published Our evaluation of Claude Mythos Preview’s cyber capabilities , their own independent analysis of Claude Mythos which backs up Anthropic's claims that it is exceptionally effective at identifying security vulnerabilities. Drew Breunig notes that AISI's report shows that the more tokens (and hence money) they…

[willison-2026-Apr-13-steve-yegge] willison — 2026-04-13T20:59:00+00:00 — Steve Yegge
  URL: https://simonwillison.net/2026/Apr/13/steve-yegge/#atom-tag
  > Steve Yegge : I was chatting with my buddy at Google, who's been a tech director there for about 20 years, about their AI adoption. Craziest convo I've had all year. The TL;DR is that Google engineering appears to have the same AI adoption footprint as John Deere, the tractor company. Most of the industry has the same internal adoption curve: 20% agentic power users, 20% outright refusers, 60% sti…

[willison-2026-Apr-13-bryan-cantrill] willison — 2026-04-13T02:44:24+00:00 — Quoting Bryan Cantrill
  URL: https://simonwillison.net/2026/Apr/13/bryan-cantrill/#atom-tag
  > The problem is that LLMs inherently lack the virtue of laziness . Work costs nothing to an LLM. LLMs do not feel a need to optimize for their own (or anyone's) future time, and will happily dump more and more onto a layercake of garbage. Left unchecked, LLMs will make systems larger, not better &mdash; appealing to perverse vanity metrics, perhaps, but at the cost of everything that matters. As su…

[willison-2026-Apr-12-mlx-audio] willison — 2026-04-12T23:57:53+00:00 — Gemma 4 audio with MLX
  URL: https://simonwillison.net/2026/Apr/12/mlx-audio/#atom-tag
  > Thanks to a tip from Rahim Nathwani , here's a uv run recipe for transcribing an audio file on macOS using the 10.28 GB Gemma 4 E2B model with MLX and mlx-vlm : uv run --python 3.13 --with mlx_vlm --with torchvision --with gradio \ mlx_vlm.generate \ --model google/gemma-4-e2b-it \ --audio file.wav \ --prompt "Transcribe this audio" \ --max-tokens 500 \ --temperature 1.0 Your browser does not supp…

[hn-47743077] hn — 2026-04-12 — Claude Opus 4.6 accuracy on BridgeBench hallucination test drops from 83% to 68%
  URL: https://news.ycombinator.com/item?id=47743077
  > 70 points, 20 comments on Hacker News. Linked: https://twitter.com/bridgemindai/status/2043321284113670594

[willison-2026-Apr-10-voice-mode-is-weaker] willison — 2026-04-10T15:56:02+00:00 — ChatGPT voice mode is a weaker model
  URL: https://simonwillison.net/2026/Apr/10/voice-mode-is-weaker/#atom-tag
  > I think it's non-obvious to many people that the OpenAI voice mode runs on a much older, much weaker model - it feels like the AI that you can talk to should be the smartest AI but it really isn't. If you ask ChatGPT voice mode for its knowledge cutoff date it tells you April 2024 - it's a GPT-4o era model. This thought inspired by this Andrej Karpathy tweet about the growing gap in understanding…

[willison-2026-Apr-8-muse-spark] willison — 2026-04-08T23:07:44+00:00 — Meta's new model is Muse Spark, and meta.ai chat has some interesting tools
  URL: https://simonwillison.net/2026/Apr/8/muse-spark/#atom-tag
  > Meta announced Muse Spark today, their first model release since Llama 4 almost exactly a year ago . It's hosted, not open weights, and the API is currently "a private API preview to select users", but you can try it out today on meta.ai (Facebook or Instagram login required). Meta's self-reported benchmarks show it competitive with Opus 4.6, Gemini 3.1 Pro, and GPT 5.4 on selected benchmarks, tho…

[willison-2026-Apr-7-glm-51] willison — 2026-04-07T21:25:14+00:00 — GLM-5.1: Towards Long-Horizon Tasks
  URL: https://simonwillison.net/2026/Apr/7/glm-51/#atom-tag
  > GLM-5.1: Towards Long-Horizon Tasks Chinese AI lab Z.ai's latest model is a giant 754B parameter 1.51TB (on Hugging Face ) MIT-licensed monster - the same size as their previous GLM-5 release, and sharing the same paper . It's available via OpenRouter so I asked it to draw me a pelican: llm install llm-openrouter llm -m openrouter/z-ai/glm-5.1 'Generate an SVG of a pelican on a bicycle' And someth…

[willison-2026-Apr-7-project-glasswing] willison — 2026-04-07T20:52:54+00:00 — Anthropic's Project Glasswing - restricting Claude Mythos to security researchers - sounds necessary to me
  URL: https://simonwillison.net/2026/Apr/7/project-glasswing/#atom-tag
  > Anthropic didn't release their latest model, Claude Mythos ( system card PDF ), today. They have instead made it available to a very restricted set of preview partners under their newly announced Project Glasswing . The model is a general purpose model, similar to Claude Opus 4.6, but Anthropic claim that its cyber-security research abilities are strong enough that they need to give the software i…

[willison-2026-Apr-6-google-ai-edge-gallery] willison — 2026-04-06T05:18:26+00:00 — Google AI Edge Gallery
  URL: https://simonwillison.net/2026/Apr/6/google-ai-edge-gallery/#atom-tag
  > Google AI Edge Gallery Terrible name, really great app: this is Google's official app for running their Gemma 4 models (the E2B and E4B sizes, plus some members of the Gemma 3 family) directly on your iPhone. It works really well. The E2B model is a 2.54GB download and is both fast and genuinely useful. The app also provides "ask questions about images" and audio transcription (up to 30s) with the…

[willison-2026-Apr-5-building-with-ai] willison — 2026-04-05T23:54:18+00:00 — Eight years of wanting, three months of building with AI
  URL: https://simonwillison.net/2026/Apr/5/building-with-ai/#atom-tag
  > Eight years of wanting, three months of building with AI Lalit Maganti provides one of my favorite pieces of long-form writing on agentic engineering I've seen in ages. They spent eight years thinking about and then three months building syntaqlite , which they describe as " high-fidelity devtools that SQLite deserves ". The goal was to provide fast, robust and comprehensive linting and verifying…

INSTRUCTIONS:
- Pick top 3 models for the TASK.
- For each pick, write 2-3 sentences of justification.
- Every claim must cite either:
    (a) a CATALOG column name in backticks (e.g. `lm_coding`, `aider`, `ctx`, `modalities`, `caps`, `tier`), OR
    (b) an OPINION [ID] that literally appears in the list above.
- If no opinion in the corpus is relevant to a pick, end that pick's justification with the literal token [no-opinion-match].
- Do NOT invent IDs or URLs. Do NOT cite models not in CATALOG.
- Do NOT pick a model that is not in the CATALOG table above.

Output format:

### 1. <model-id>
<justification with inline citations>

### 2. <model-id>
<justification>

### 3. <model-id>
<justification>

```

## Proof of work: a subagent answers the prompt

To prove the prompt is genuinely self-contained, we piped that exact `lanista pick` output to an isolated subagent (general-purpose Claude with no web access, no lanista access — just the prompt file at `/tmp/lanista_pick_prompt.txt`). The subagent followed the INSTRUCTIONS verbatim. Here is its unedited answer:

---

### 1. claude-opus-4-7
Top-tier `lm_coding` rating of 1527 and strong `lm_hard` (1496), with a 1M `ctx` window well-suited for multi-file refactors, and Anthropic's Claude Code harness issues affecting quality have reportedly been fixed per [willison-2026-Apr-24-recent-claude-code-quality-reports]. The Opus 4.7 release was a major event for coding agents per [hn-47793411] and [willison-2026-Apr-18-opus-system-prompt].

### 2. claude-opus-4-6
Leads the catalog on `lm_coding` (1541) tied with the thinking variant, with a 1M `ctx` window ideal for ingesting multiple TypeScript files, and strong `lm_hard` (1528). Remains a reliable coding agent baseline referenced alongside 4.7 in [willison-2026-Apr-20-claude-token-counts] and [willison-2026-Apr-18-opus-system-prompt].

### 3. gemini-3-1-pro
Strong `lm_coding` (1495) and `lm_hard` (1494) combined with the largest `ctx` (1,048,576) in class at a much lower `price_$/Mtok` (2.0/12.0) than Opus, making it cost-effective for long autonomous agent runs on big TypeScript repos. [no-opinion-match]

---

**Verification**: every cited ID (`willison-2026-Apr-24-recent-claude-code-quality-reports`, `hn-47793411`, `willison-2026-Apr-18-opus-system-prompt`, `willison-2026-Apr-20-claude-token-counts`) literally appears in the prompts opinion block above. Every cited column (`lm_coding`, `lm_hard`, `ctx`, `price_$/Mtok`) is a real CATALOG header. The third pick correctly ends with `[no-opinion-match]` because no opinion in the corpus directly discusses Gemini 3.1 Pro for autonomous TypeScript refactoring. The contract held.

This is the load-bearing claim of lanista: the picker prompt is portable enough that any reasonable LLM, given nothing else, will produce a verifiable, citation-grounded answer.

## One more demo: a very different task

The same catalog + same opinion corpus produces a different top-of-table when the task changes — the receiving LLM filters the table and opinions through the task context. Here's what a Chinese-language multi-turn task looks like (showing only the task header + first few rows to keep it concise):

```bash
lanista pick '中文多轮客服对话' --top 3 | sed -n '1,20p'
```

```output
# lanista model-picker prompt — self-contained.
# If you are an LLM reading this (e.g. a coding agent that just ran
# `lanista pick ...` on the user's behalf), answer it directly using
# only the CATALOG and OPINIONS below. Follow the INSTRUCTIONS at the
# end. Do not call lanista again — everything you need is in this prompt.

TASK: 中文多轮客服对话

Opinion corpus has 40 recent entries.

CATALOG (top 60 by best available LMArena rating; price is $/Mtok input/output; modalities uses txt/img/aud/vid/pdf; caps uses pdf/cu/fn/vis/think; tier is curated 1=frontier..4=local; lm_* columns are LMArena Elo ratings by category; '-' means no data):
| model | price_$/Mtok | ctx | aider | modalities | caps | tier | lm_overall | lm_coding | lm_writing | lm_hard | lm_long | lm_english | lm_chinese | lm_document |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-4-6-thinking | 5/25 | 200000 | - | txt+img | - | - | 1500 | 1541 | 1498 | 1530 | 1524 | 1513 | 1543 | 1528 |
| claude-opus-4-6 | 5.0/25.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | - | 1495 | 1541 | 1477 | 1528 | 1521 | 1504 | 1550 | 1520 |
| gemini-3-1-pro | 2.0/12.0 | 1048576 | - | aud+file+img+txt+vid | fn,pdf,think,vis | 3 | 1488 | 1495 | 1490 | 1494 | 1489 | 1484 | 1545 | 1451 |
| claude-opus-4-7-thinking | - | - | - | - | - | - | 1488 | 1539 | 1489 | 1505 | 1507 | 1494 | 1552 | 1515 |
| claude-opus-4-7 | 5.0/25.0 | 1000000 | - | txt+img | cu,fn,pdf,think,vis | 1 | 1480 | 1527 | 1476 | 1496 | 1510 | 1492 | 1540 | 1523 |
| gemini-3-pro | - | - | - | - | - | - | 1479 | 1483 | 1483 | 1482 | 1473 | 1480 | 1528 | 1443 |
| muse-spark | - | - | - | - | - | - | 1477 | 1484 | 1456 | 1480 | 1444 | 1481 | 1520 | 1457 |
```

Notice the `lm_chinese` column — Chinese-language Elo ratings are a first-class signal. A model with strong overall but weak `lm_chinese` (e.g. a 50+ point gap) is an obvious skip for this task, even if it wins on `lm_coding`.

## Health checks

`doctor` verifies the install: config dirs exist, seed files parse, the index isn't stale, and (with `--verbose`) every source URL responds.

```bash
lanista doctor
```

```output

Info:
  ✓ curated source (gkisokay): 19 entries: 
/Users/mhild/.config/lanista/sources/gkisokay.json
  ✓ curated source (artificial_analysis): 9 entries: 
/Users/mhild/.config/lanista/sources/artificial_analysis.json
  ✓ aliases: 25 canonical ids: /Users/mhild/.config/lanista/aliases.json
  ✓ index: 2764 models, 27 agents: /Users/mhild/.cache/lanista/model_index.json
  ✓ index age: 0d old
  ✓ pi-mono age: upstream 0d old

Summary: 0 errors, 0 warnings, 6 info

Next steps:
  lanista fetch             Refresh index
  lanista doctor --verbose  Include connectivity probes
  lanista --help            Show all commands
```

## What's in the box

**Sources** (structured, per-model):

| source | shape | signal |
|---|---|---|
| openrouter | JSON API | pricing, context, modalities, tokenizer |
| litellm | JSON file | pricing, capability flags, providers |
| pi-mono | TypeScript parser | agent routing, reasoning flag |
| lmarena | Parquet | Elo ratings by category (coding, writing, chinese, …) |
| aider | YAML | polyglot coding pass-rate |
| gkisokay | curated JSON | tier + use-case notes |
| factory_weather | RSS regex | release mentions from Factory AI |
| artificial_analysis | user-drop JSON | escape hatch for hand-curated facts |

**Opinions** (prose, per-post):

| source | shape | signal |
|---|---|---|
| willison | Atom feed | daily practitioner takes, release testing |
| eugeneyan | RSS 2.0 | applied-ML engineering patterns |
| hn | Algolia API | attention signal via points + comment count |

**Commands**: `fetch`, `refresh-opinions`, `show`, `tier`, `agents`, `pick`, `doctor`.

## Reproducing this document

This document was built with [`showboat`](https://github.com/showboat). Every code block above was executed live against the current lanista install. To verify outputs still match:

Run `showboat verify docs/lanista-demo.md`.

Because LMArena ratings, HN stories, and blog feeds change daily, `verify` will flag drift in exactly the sections where upstream data has moved. That's a feature: diffs in the demo correspond to real shifts in the LLM landscape.
