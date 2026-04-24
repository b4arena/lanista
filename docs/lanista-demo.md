# lanista: pick the right LLM for the task

*2026-04-24T05:19:58Z by Showboat 0.6.1*
<!-- showboat-id: 5593cfc5-d205-4fe6-818d-93da32829f25 -->

lanista is a local LLM model catalog and picker. It aggregates **structured data** from eight sources (OpenRouter, LiteLLM, pi-mono, LMArena, Aider's polyglot leaderboard, Factory AI Weather, gkisokay tiers, Artificial Analysis) and **prose practitioner opinions** from three feeds (Simon Willison, Eugene Yan, Hacker News). The hero command, `lanista pick`, builds a citeable prompt that any LLM can answer — every recommendation must cite either a catalog column or a specific opinion entry.

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
│ refresh-opinions  Refresh the opinion corpus (blog feeds, HN).               │
│ doctor            Run proactive health checks. Use --verbose for             │
│                   connectivity probes.                                       │
╰──────────────────────────────────────────────────────────────────────────────╯

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
+ artificial_analysis  0 models
+ lmarena              347 models
-> /Users/mhild/.cache/lanista/model_index.json (12934 KB, 2759 models)

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

`show` accepts a substring and dumps pricing, context window, curated notes, and per-source observations. Each observation is attributed to the source it came from — including the new LMArena Elo ratings by category.

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
    [openrouter     ] anthropic/claude-opus-4.7
        ctx=1,000,000  price=$5.0/$25.0  modalities=text,image  tokenizer=Claude
    [litellm        ] azure_ai/claude-opus-4-7
        ctx=200,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  via=azure_ai
    [litellm        ] claude-opus-4-7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  via=anthropic
    [litellm        ] vertex_ai/claude-opus-4-7
        ctx=1,000,000  price=$5.0/$25.0  
caps=computer_use,function_calling,pdf_input,prompt_caching +7  
via=vertex_ai-anthropic_models
    [pimono         ] anthropic/claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=anthropic  reasoning=yes  
modalities=text,image
    [pimono         ] github-copilot/claude-opus-4.7
        ctx=144,000  price=$0/$0  via=github-copilot  reasoning=yes  
modalities=text,image
    [pimono         ] opencode/claude-opus-4-7
        ctx=1,000,000  price=$5/$25  via=opencode  reasoning=yes  
modalities=text,image
    [gkisokay       ] claude-opus-4-7
        (no extracted fields)
    [factory_weather] opus-4.7
        mentions=1  latest=Mon, 20 Apr 2026 12:00:00 GMT
    [lmarena        ] claude-opus-4-7
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

- A **catalog table** of the top 60 models by LMArena rating, with columns for price, context, Aider coding pass-rate, and LMArena Elo ratings split by category (`lm_coding`, `lm_writing`, `lm_hard`, `lm_long`, `lm_english`, `lm_chinese`, `lm_document`).
- The **40 most recent opinion excerpts** from Willison, Eugene Yan, and HN — each with a stable citeable ID.
- **Strict citation rules**: every claim in the answer must cite either a catalog column or an opinion ID. Picks without matching opinions must end with the literal token `[no-opinion-match]`.

The prompt is LLM-agnostic — paste it into Claude, ChatGPT, Gemini, or local. Every recommendation is verifiable because every cited ID appears in the prompt with its source URL.

```bash
lanista pick 'write architecture documents for a microservices migration' --top 3 | sed -n '1,20p'
```

```output
TASK: write architecture documents for a microservices migration

Opinion corpus has 40 recent entries.

CATALOG (top 60 by best available LMArena rating; price is $/Mtok input/output; lm_* columns are LMArena Elo ratings by category; '-' means no data):
| model | price_$/Mtok | ctx | aider | lm_overall | lm_coding | lm_writing | lm_hard | lm_long | lm_english | lm_chinese | lm_document |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-4-6-thinking | 5/25 | 200000 | - | 1500 | 1541 | 1498 | 1530 | 1524 | 1513 | 1543 | 1528 |
| claude-opus-4-6 | 5.0/25.0 | 1000000 | - | 1495 | 1541 | 1477 | 1528 | 1521 | 1504 | 1550 | 1520 |
| gemini-3-1-pro | 2.0/12.0 | 1048576 | - | 1488 | 1495 | 1490 | 1494 | 1489 | 1484 | 1545 | 1451 |
| claude-opus-4-7-thinking | - | - | - | 1488 | 1539 | 1489 | 1505 | 1507 | 1494 | 1552 | 1515 |
| claude-opus-4-7 | 5.0/25.0 | 1000000 | - | 1480 | 1527 | 1476 | 1496 | 1510 | 1492 | 1540 | 1523 |
| gemini-3-pro | - | - | - | 1479 | 1483 | 1483 | 1482 | 1473 | 1480 | 1528 | 1443 |
| muse-spark | - | - | - | 1477 | 1484 | 1456 | 1480 | 1444 | 1481 | 1520 | 1457 |
| gpt-5-4-high | - | - | - | 1472 | 1506 | 1443 | 1491 | 1480 | 1469 | 1530 | - |
| qwen3-5-max-preview | - | - | - | 1472 | 1479 | 1461 | 1483 | 1470 | 1478 | 1528 | - |
| gemini-3-flash | 0.5/3 | 1048576 | - | 1467 | 1463 | 1459 | 1465 | 1451 | 1466 | 1513 | 1423 |
| glm-5-1 | 1.05/3.5 | 202752 | - | 1467 | 1496 | 1456 | 1474 | 1477 | 1477 | 1516 | - |
| gemini-2-5-pro | 1.25/10.0 | 1048576 | - | 1460 | 1455 | 1457 | 1457 | 1452 | 1460 | 1513 | 1433 |
| grok-4-20-beta-0309-reasoning | 2.0/6.0 | 2000000 | - | 1456 | 1462 | 1428 | 1458 | 1432 | 1459 | 1493 | 1426 |
```

Below the table comes a block of recent opinion excerpts. Here are the first three:

```bash
lanista pick 'write architecture documents' --top 3 | awk '/RECENT PRACTITIONER OPINIONS/,0' | sed -n '1,17p'
```

```output
RECENT PRACTITIONER OPINIONS (cite by [ID]):
[willison-2026-Apr-24-recent-claude-code-quality-reports] willison — 2026-04-24T01:31:25+00:00 — An update on recent Claude Code quality reports
  URL: https://simonwillison.net/2026/Apr/24/recent-claude-code-quality-reports/#atom-tag
  > An update on recent Claude Code quality reports It turns out the high volume of complaints that Claude Code was providing worse quality results over the past two months was grounded in real problems. The models themselves were not to blame, but three separate issues in the Claude Code harness caused complex but material problems which directly affected users. Anthropic's postmortem describes these…

[willison-2026-Apr-23-liteparse-for-the-web] willison — 2026-04-23T21:54:24+00:00 — Extract PDF text in your browser with LiteParse for the web
  URL: https://simonwillison.net/2026/Apr/23/liteparse-for-the-web/#atom-tag
  > LlamaIndex have a most excellent open source project called LiteParse , which provides a Node.js CLI tool for extracting text from PDFs. I got a version of LiteParse working entirely in the browser, using most of the same libraries that LiteParse uses to run in Node.js. Spatial text parsing Refreshingly, LiteParse doesn't use AI models to do what it does: it's good old-fashioned PDF parsing, falli…

[willison-2026-Apr-23-gpt-5-5] willison — 2026-04-23T19:59:47+00:00 — A pelican for GPT-5.5 via the semi-official Codex backdoor API
  URL: https://simonwillison.net/2026/Apr/23/gpt-5-5/#atom-tag
  > GPT-5.5 is out . It's available in OpenAI Codex and is rolling out to paid ChatGPT subscribers. I've had some preview access and found it to be a fast, effective and highly capable model. As is usually the case these days, it's hard to put into words what's good about it - I ask it to build things and it builds exactly what I ask for! There's one notable omission from today's release - the API: AP…

[hn-47879092] hn — 2026-04-23 — GPT-5.5
  URL: https://news.ycombinator.com/item?id=47879092
  > 1218 points, 831 comments on Hacker News. Linked: https://openai.com/index/introducing-gpt-5-5/

```

The prompt ends with the citation contract:

```bash
lanista pick 'write architecture documents' --top 3 | awk '/INSTRUCTIONS/,0'
```

```output
INSTRUCTIONS:
- Pick top 3 models for the TASK.
- For each pick, write 2-3 sentences of justification.
- Every claim must cite either:
    (a) a CATALOG column name in backticks (e.g. `lm_coding`, `aider`, `ctx`), OR
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

## One more demo: a very different task

The same catalog + same opinion corpus produces a different top-of-table when the task changes — the receiving LLM filters the table and opinions through the task context. Here's what a Chinese-language multi-turn task looks like (showing only the task header + first few rows to keep it concise):

```bash
lanista pick '中文多轮客服对话' --top 3 | sed -n '1,15p'
```

```output
TASK: 中文多轮客服对话

Opinion corpus has 40 recent entries.

CATALOG (top 60 by best available LMArena rating; price is $/Mtok input/output; lm_* columns are LMArena Elo ratings by category; '-' means no data):
| model | price_$/Mtok | ctx | aider | lm_overall | lm_coding | lm_writing | lm_hard | lm_long | lm_english | lm_chinese | lm_document |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-4-6-thinking | 5/25 | 200000 | - | 1500 | 1541 | 1498 | 1530 | 1524 | 1513 | 1543 | 1528 |
| claude-opus-4-6 | 5.0/25.0 | 1000000 | - | 1495 | 1541 | 1477 | 1528 | 1521 | 1504 | 1550 | 1520 |
| gemini-3-1-pro | 2.0/12.0 | 1048576 | - | 1488 | 1495 | 1490 | 1494 | 1489 | 1484 | 1545 | 1451 |
| claude-opus-4-7-thinking | - | - | - | 1488 | 1539 | 1489 | 1505 | 1507 | 1494 | 1552 | 1515 |
| claude-opus-4-7 | 5.0/25.0 | 1000000 | - | 1480 | 1527 | 1476 | 1496 | 1510 | 1492 | 1540 | 1523 |
| gemini-3-pro | - | - | - | 1479 | 1483 | 1483 | 1482 | 1473 | 1480 | 1528 | 1443 |
| muse-spark | - | - | - | 1477 | 1484 | 1456 | 1480 | 1444 | 1481 | 1520 | 1457 |
| gpt-5-4-high | - | - | - | 1472 | 1506 | 1443 | 1491 | 1480 | 1469 | 1530 | - |
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
  ✓ curated source (artificial_analysis): 0 entries: 
/Users/mhild/.config/lanista/sources/artificial_analysis.json
  ✓ aliases: 25 canonical ids: /Users/mhild/.config/lanista/aliases.json
  ✓ index: 2759 models, 27 agents: /Users/mhild/.cache/lanista/model_index.json
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

```
showboat verify docs/lanista-demo.md
```

Because LMArena ratings, HN stories, and blog feeds change daily, `verify` will flag drift in exactly the sections where upstream data has moved. That's a feature: diffs in the demo correspond to real shifts in the LLM landscape.
