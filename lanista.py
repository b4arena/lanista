#!/usr/bin/env python3
"""
lanista - LLM model catalog and router.

A lanista owned a gladiator troupe: he knew each fighter's strengths,
weaknesses, and price, and chose which to field for a given match.
This tool does the same for LLMs - fetch metadata from authoritative
sources, merge into a unified index, pick the right model per use case.

Sources:
  - Models dict (~3000 entries):
      1. OpenRouter API             - live prices, context, capabilities
      2. LiteLLM JSON               - capability flags, provider variants
      3. Overlay (model_notes.json) - hand-curated tier/strengths/weaknesses
  - Coding-agent dict (per-provider model lists):
      pi-mono models.generated.ts   - authoritative, maintainer-generated
      pi-mono model-resolver.ts     - per-provider default model IDs
      + static CODING_AGENT_META    - CLI flags/notes not in pi-mono

Usage:
  ./lanista.py fetch                 # fetch all sources + write index
  ./lanista.py show <substr>         # pretty-print matching model records
  ./lanista.py agents [<substr>]     # list coding agents (filter by substr)
  ./lanista.py tier <1|2|3|4>        # list curated models for a given tier

Outputs:
  model_index.json   - merged index (overwritten each fetch, gitignored)
  model_notes.json   - curated overlay (editable, committed)
"""
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
INDEX_PATH = HERE / "model_index.json"
NOTES_PATH = HERE / "model_notes.json"

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
LITELLM_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
PIMONO_MODELS_URL = (
    "https://raw.githubusercontent.com/badlogic/pi-mono/main/"
    "packages/ai/src/models.generated.ts"
)
PIMONO_RESOLVER_URL = (
    "https://raw.githubusercontent.com/badlogic/pi-mono/main/"
    "packages/coding-agent/src/core/model-resolver.ts"
)

# Static CLI-wrapper annotations. Merged onto pi-mono data in build_coding_agents.
# Keys match pi-mono provider names. Only fields not derivable from pi-mono.
CODING_AGENT_META = {
    "anthropic": {
        "cli": "claude-code",
        "flag": "claude --model <id>",
        "note": "Claude Code CLI routes through the anthropic provider",
    },
    "openai-codex": {
        "cli": "codex",
        "flag": "codex --model <id>",
        "note": "Legacy models via 'codex -m <id>' or config.toml",
    },
    "google-gemini-cli": {
        "cli": "gemini",
        "flag": "gemini --model <id>",
    },
    "google-antigravity": {"cli": "antigravity"},
    "google-vertex": {"note": "GCP Vertex AI gateway"},
    "github-copilot": {"cli": "gh copilot / VSCode"},
    "openai": {"note": "Bare API; used by codex and many wrappers"},
    "google": {"note": "Bare Gemini API"},
    "xai": {"cli": "grok-cli"},
    "mistral": {"cli": "mistral-cli"},
    "zai": {"note": "GLM family from Z.AI"},
    "minimax": {"note": "MiniMax M-series"},
    "opencode": {"cli": "opencode"},
    "kimi-coding": {"cli": "kimi"},
    "openrouter": {
        "note": "Unified gateway; prefix model with provider: 'openai/...'",
    },
}

# CLI wrappers that aren't pi-mono providers (they route to other backends).
CLI_WRAPPERS = {
    "aider": {
        "routes_via": "LiteLLM",
        "flag": "aider --model <id>",
        "note": "Accepts any LiteLLM-compatible string (provider/model or bare)",
    },
    "cursor": {
        "routes_via": "settings UI",
        "note": "Configured in Cursor settings, not via CLI flag",
    },
    "claude-code": {
        "routes_via": "anthropic provider",
        "flag": "claude --model <id>",
        "note": "See the 'anthropic' entry in coding_agents for full model list",
    },
}

# Overlay seed. Distilled from Gkisokay LLM Model Stack (April 2026).
# Written to model_notes.json on first run; edit there from then on.
NOTES_SEED = {
    "_schema": "Hand-curated notes. Tier 1=frontier, 4=local/free.",
    "_updated": "2026-04-23",
    "_source": "Gkisokay LLM Model Stack (April 2026)",
    "models": {
        "claude-opus-4-6": {
            "tier": 1,
            "strengths": [
                "#1 agentic terminal coding via Claude Code",
                "Adaptive thinking, agent teams, context compaction",
                "76% long-ctx retrieval @ 1M",
            ],
            "weaknesses": [
                "Community reports inconsistency lately",
                "External dev only - not in internal agent runtimes",
            ],
            "use_for": "Complex external dev via Claude Code, multi-file refactoring",
        },
        "claude-opus-4-7": {
            "tier": 1,
            "strengths": ["Latest Opus", "1M context", "128K output"],
            "weaknesses": ["Premium pricing"],
            "use_for": "Successor to 4.6; use when 4.6 inconsistency bites",
        },
        "gpt-5.4": {
            "tier": 1,
            "strengths": [
                "Superhuman computer use (OSWorld 75%)",
                "Real multi-hour planning",
                "Steerable planner + judge in Codex",
            ],
            "weaknesses": ["$100/month plan for best access"],
            "use_for": "External Codex-driven complex features",
        },
        "glm-5.1": {
            "tier": 1,
            "strengths": [
                "#1 SWE-Pro globally",
                "8-hour autonomous execution",
                "MIT license, open weights",
                "3x cheaper than Opus on input",
            ],
            "weaknesses": ["Benchmarks self-reported by Z.AI (pending independent verification)"],
            "use_for": "Long-horizon agentic coding, sustained optimization loops",
        },
        "minimax-m2.7": {
            "tier": 2,
            "strengths": ["97% skill adherence on 40+ skills", "Multi-agent teams"],
            "weaknesses": ["API only - not open weights"],
            "use_for": "OpenClaw execution backbone, high-volume agent tasks",
        },
        "kimi-k2.5": {
            "tier": 2,
            "strengths": [
                "Long-horizon stability",
                "First open-weight trained for parallel agentic work",
                "384 experts, 1T params / 32B active",
            ],
            "weaknesses": ["~6x more output tokens than peers - budget carefully"],
            "use_for": "Long-horizon task chains, multi-source browsing",
        },
        "grok-4.20": {
            "tier": 2,
            "strengths": [
                "Lowest hallucination rate on market",
                "Native multi-agent API (4-16 parallel)",
                "2M context window, 199 t/s",
            ],
            "weaknesses": [],
            "use_for": "Hallucination-sensitive pipelines, long-context research",
        },
        "deepseek-v3.2": {
            "tier": 2,
            "strengths": [
                "90% of GPT-5.4 performance at 1/50th cost",
                "Open weights, MIT license",
            ],
            "weaknesses": [],
            "use_for": "Cost-floor frontier reasoning, high-volume coding",
        },
        "claude-sonnet-4-6": {
            "tier": 3,
            "strengths": [
                "98% of Opus coding at 1/5 cost",
                "1M context, computer use 94% accuracy",
                "Prompt injection resistance on par with Opus",
            ],
            "weaknesses": ["API only - no $10/mo plan"],
            "use_for": "Daily coding, content automation, Anthropic-ecosystem agents",
        },
        "gpt-5.4-mini": {
            "tier": 3,
            "strengths": [
                "93.4% tool-call reliability",
                "ChatGPT OAuth = no API billing",
                "2x faster than GPT-5 mini, 400K context",
            ],
            "weaknesses": [],
            "use_for": "Hermes conscious layer, 6-9 turn debates",
        },
        "gemini-3.1-pro": {
            "tier": 3,
            "strengths": [
                "Native video+audio in one API call",
                "7.5x cheaper than Opus on input",
                "3 thinking levels",
            ],
            "weaknesses": ["Dropped from Tier 1 - behind new frontier bar on reasoning"],
            "use_for": "Multimodal agents, doc-heavy pipelines",
        },
        "qwen3.6-plus": {
            "tier": 3,
            "strengths": ["FREE via OpenRouter", "1M context", "Near-frontier coding"],
            "weaknesses": ["Free-tier rate limits; preview window may close"],
            "use_for": "Any Tier 3 task at $0",
        },
        "llama-4-maverick": {
            "tier": 3,
            "strengths": [
                "Open weights, Apache 2.0",
                "EU/data sovereignty - self-host at zero marginal cost",
                "9-23x price-perf vs GPT-4o",
            ],
            "weaknesses": [],
            "use_for": "Self-hosted Tier 3, data sovereignty",
        },
        "mistral-small-4": {
            "tier": 3,
            "strengths": [
                "Unifies Magistral + Pixtral + Devstral in one model",
                "Apache 2.0, self-hostable",
                "75% less output verbosity than peers",
            ],
            "weaknesses": [],
            "use_for": "Budget-conscious agents, one-model-replacing-three",
        },
        "qwen3.5-9b": {
            "tier": 4,
            "strengths": [
                "Runs on 16GB RAM",
                "Always-on subconscious loop viable",
                "Beats GPT-OSS-120B at 13x smaller",
                "5GB VRAM @ 4-bit",
            ],
            "weaknesses": [],
            "use_for": "Always-on ideation loop, curation pass",
        },
        "qwen3.5-27b": {
            "tier": 4,
            "strengths": ["32GB RAM local", "Stronger instruction following than 9B"],
            "weaknesses": [],
            "use_for": "Local summarization, routing, complex micro classification",
        },
        "gemma-4-31b": {
            "tier": 4,
            "strengths": [
                "Apache 2.0 commercial",
                "#3 Arena open leaderboard",
                "Dramatic leap over Gemma 3",
            ],
            "weaknesses": ["Slower inference vs Qwen3.5-27B"],
            "use_for": "Local agentic sub-tasks with commercial deployment",
        },
        "deepseek-r1-distill": {
            "tier": 4,
            "strengths": ["94.3% MATH-500", "Best chain-of-thought at $0", "MIT license"],
            "weaknesses": ["OpenRouter free-tier rate limits"],
            "use_for": "Reasoning-heavy micro tasks, math/logic classification",
        },
        "glm-4.5-air": {
            "tier": 4,
            "strengths": [
                "Purpose-built for agent tool use + web browsing",
                "#1 OSS for agent tasks",
            ],
            "weaknesses": ["Not a trimmed general model - narrow focus"],
            "use_for": "Lightweight agentic sub-tasks, web browsing agents",
        },
    },
}


def fetch_json(url: str, timeout: int = 20):
    """GET a JSON URL. Return parsed dict, or None on failure (prints reason)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "model-index/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  ! {url}: {e}", file=sys.stderr)
        return None


def load_notes() -> dict:
    """Load overlay; seed it on first run."""
    if not NOTES_PATH.exists():
        NOTES_PATH.write_text(json.dumps(NOTES_SEED, indent=2) + "\n")
        print(f"  * seeded {NOTES_PATH.name} with Gkisokay stack")
    return json.loads(NOTES_PATH.read_text())


def _to_per_million(v):
    return round(float(v) * 1_000_000, 4) if v else None


def normalize_openrouter(data: dict) -> dict:
    out = {}
    for m in data.get("data", []):
        mid = m["id"]
        p = m.get("pricing", {}) or {}
        arch = m.get("architecture") or {}
        tp = m.get("top_provider") or {}
        out[mid] = {
            "id": mid,
            "provider": mid.split("/")[0] if "/" in mid else None,
            "bare_name": mid.split("/", 1)[1] if "/" in mid else mid,
            "context_window": m.get("context_length"),
            "max_output": tp.get("max_completion_tokens"),
            "pricing_per_million": {
                "input": _to_per_million(p.get("prompt")),
                "output": _to_per_million(p.get("completion")),
                "cache_read": _to_per_million(p.get("input_cache_read")),
                "cache_write": _to_per_million(p.get("input_cache_write")),
            },
            "modalities": arch.get("input_modalities"),
            "tokenizer": arch.get("tokenizer"),
            "sources": ["openrouter"],
        }
    return out


def normalize_litellm(data: dict) -> dict:
    out = {}
    for mid, m in data.items():
        if mid == "sample_spec" or not isinstance(m, dict):
            continue
        caps = [
            k.removeprefix("supports_")
            for k, v in m.items()
            if k.startswith("supports_") and v is True
        ]
        out[mid] = {
            "id": mid,
            "provider": m.get("litellm_provider"),
            "context_window": m.get("max_input_tokens"),
            "max_output": m.get("max_output_tokens"),
            "pricing_per_million": {
                "input": _to_per_million(m.get("input_cost_per_token")),
                "output": _to_per_million(m.get("output_cost_per_token")),
            },
            "capabilities": caps,
            "mode": m.get("mode"),
            "sources": ["litellm"],
        }
    return out


def fetch_text(url: str, timeout: int = 20):
    """GET a URL as raw text. Return string, or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "model-index/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! {url}: {e}", file=sys.stderr)
        return None


def ts_to_json(ts: str) -> str:
    """Convert a TS object literal (pi-mono auto-gen format) to JSON.

    Works because the source is machine-generated with a predictable shape:
    bare-identifier keys, double-quoted strings, no template literals,
    'satisfies Model<...>' clauses attached to each model block.
    """
    strings: list = []

    def stash(m):
        strings.append(m.group(0))
        return f"\x00{len(strings) - 1}\x00"

    ts = re.sub(r'"(?:[^"\\]|\\.)*"', stash, ts)
    ts = re.sub(r"\s+satisfies\s+Model<[^>]+>", "", ts)
    ts = re.sub(r"//[^\n]*", "", ts)
    ts = re.sub(r"([a-zA-Z_]\w*)\s*:", r'"\1":', ts)
    ts = re.sub(r",(\s*[}\]])", r"\1", ts)
    return re.sub(r"\x00(\d+)\x00", lambda m: strings[int(m.group(1))], ts)


def parse_pimono_models(source: str) -> dict:
    """Parse pi-mono models.generated.ts -> {provider: {id: model_data}}."""
    m = re.search(r"export const MODELS\s*=\s*\{", source)
    if not m:
        return {}
    start = m.end() - 1
    depth, i = 0, start
    while i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    try:
        return json.loads(ts_to_json(source[start:i + 1]))
    except json.JSONDecodeError as e:
        print(f"  ! pi-mono models parse failed: {e}", file=sys.stderr)
        return {}


def parse_pimono_defaults(source: str) -> dict:
    """Parse model-resolver.ts -> {provider: default_model_id}."""
    m = re.search(
        r"defaultModelPerProvider[^=]*=\s*\{(.+?)\};", source, re.S,
    )
    if not m:
        return {}
    return dict(re.findall(r'"?([a-zA-Z0-9-]+)"?\s*:\s*"([^"]+)"', m.group(1)))


def build_coding_agents(pi_models: dict, pi_defaults: dict) -> dict:
    """Combine pi-mono model data with CODING_AGENT_META annotations."""
    out = {}
    for provider, models in sorted(pi_models.items()):
        meta = CODING_AGENT_META.get(provider, {})
        options = {}
        for mid, m in models.items():
            options[mid] = {
                "name": m.get("name"),
                "context_window": m.get("contextWindow"),
                "max_tokens": m.get("maxTokens"),
                "reasoning": m.get("reasoning"),
                "input_modalities": m.get("input"),
                "cost_per_million": m.get("cost"),
            }
        out[provider] = {
            "default": pi_defaults.get(provider),
            "cli": meta.get("cli"),
            "flag": meta.get("flag"),
            "note": meta.get("note"),
            "model_count": len(options),
            "options": options,
            "source": "pi-mono",
        }
    for name, info in CLI_WRAPPERS.items():
        if name not in out:
            out[name] = {**info, "source": "manual"}
    return out


def merge_model(base: dict, add: dict) -> dict:
    """Merge add into base. Existing non-null values win; missing fields filled in."""
    out = dict(base)
    for k, v in add.items():
        if k == "sources":
            existing = out.get("sources", []) or []
            out["sources"] = existing + [s for s in v if s not in existing]
        elif isinstance(v, dict):
            merged = dict(v)
            merged.update(out.get(k) or {})
            for sk, sv in v.items():
                if merged.get(sk) is None and sv is not None:
                    merged[sk] = sv
            out[k] = merged
        elif out.get(k) is None:
            out[k] = v
    return out


def match_overlay_key(model_id: str, overlay_keys):
    """Fuzzy match model id to overlay key. 'anthropic/claude-opus-4.6' -> 'claude-opus-4-6'."""
    bare = model_id.split("/", 1)[-1].lower()
    variants = {bare, bare.replace(".", "-"), bare.replace("-", ".")}
    for k in overlay_keys:
        kl = k.lower()
        if kl in variants or kl.replace(".", "-") == bare.replace(".", "-"):
            return k
    return None


def cmd_fetch():
    print("-> fetching sources")
    or_data = fetch_json(OPENROUTER_URL)
    ll_data = fetch_json(LITELLM_URL)
    pi_models_src = fetch_text(PIMONO_MODELS_URL)
    pi_resolver_src = fetch_text(PIMONO_RESOLVER_URL)
    notes = load_notes()
    overlay = notes.get("models", {})

    models: dict = {}
    if or_data:
        or_models = normalize_openrouter(or_data)
        print(f"  + openrouter: {len(or_models)} models")
        models = or_models
    if ll_data:
        ll_models = normalize_litellm(ll_data)
        print(f"  + litellm:    {len(ll_models)} models")
        for mid, rec in ll_models.items():
            models[mid] = merge_model(models[mid], rec) if mid in models else rec

    pi_models = parse_pimono_models(pi_models_src) if pi_models_src else {}
    pi_defaults = parse_pimono_defaults(pi_resolver_src) if pi_resolver_src else {}
    if pi_models:
        total = sum(len(m) for m in pi_models.values())
        print(f"  + pi-mono:    {len(pi_models)} providers, {total} models")
    coding_agents = build_coding_agents(pi_models, pi_defaults)

    overlay_hits = 0
    for mid, rec in models.items():
        key = match_overlay_key(mid, list(overlay.keys()))
        if key:
            rec["notes"] = overlay[key]
            overlay_hits += 1
    print(f"  + overlay:    {overlay_hits} matched / {len(overlay)} curated")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "openrouter": OPENROUTER_URL,
            "litellm": LITELLM_URL,
            "pimono_models": PIMONO_MODELS_URL,
            "pimono_resolver": PIMONO_RESOLVER_URL,
            "overlay": NOTES_PATH.name,
        },
        "coding_agents": coding_agents,
        "model_count": len(models),
        "models": dict(sorted(models.items())),
    }
    INDEX_PATH.write_text(json.dumps(output, indent=2) + "\n")
    kb = INDEX_PATH.stat().st_size // 1024
    print(f"  -> {INDEX_PATH.name} ({len(models)} models, {kb} KB)")


def cmd_show(substr: str):
    if not INDEX_PATH.exists():
        sys.exit("No index yet. Run: model_index.py fetch")
    idx = json.loads(INDEX_PATH.read_text())
    hits = {k: v for k, v in idx["models"].items() if substr.lower() in k.lower()}
    if not hits:
        sys.exit(f"No match for '{substr}'")
    print(json.dumps(hits, indent=2))


def cmd_agents(filter_str=None):
    if not INDEX_PATH.exists():
        sys.exit("No index yet. Run: model_index.py fetch")
    idx = json.loads(INDEX_PATH.read_text())
    agents = idx.get("coding_agents", {})
    if filter_str:
        agents = {
            k: v for k, v in agents.items() if filter_str.lower() in k.lower()
        }
        if not agents:
            sys.exit(f"No agent matching '{filter_str}'")
    print(json.dumps(agents, indent=2))


def cmd_tier(tier: str):
    if not INDEX_PATH.exists():
        sys.exit("No index yet. Run: model_index.py fetch")
    try:
        tier_n = int(tier)
    except ValueError:
        sys.exit("Tier must be 1-4")
    idx = json.loads(INDEX_PATH.read_text())
    results = []
    for mid, rec in idx["models"].items():
        notes = rec.get("notes") or {}
        if notes.get("tier") == tier_n:
            results.append({
                "id": mid,
                "strengths": notes.get("strengths", []),
                "weaknesses": notes.get("weaknesses", []),
                "use_for": notes.get("use_for"),
                "pricing_per_million": rec.get("pricing_per_million"),
                "context_window": rec.get("context_window"),
            })
    print(json.dumps(
        {"tier": tier_n, "count": len(results), "models": results},
        indent=2,
    ))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "fetch":
        cmd_fetch()
    elif cmd == "show" and len(sys.argv) >= 3:
        cmd_show(sys.argv[2])
    elif cmd == "agents":
        cmd_agents(sys.argv[2] if len(sys.argv) >= 3 else None)
    elif cmd == "tier" and len(sys.argv) >= 3:
        cmd_tier(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
