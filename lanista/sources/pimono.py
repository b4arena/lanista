"""pi-mono integration.

pi-mono auto-generates ``models.generated.ts`` (every model, every provider
used by coding-agent CLIs) and ``model-resolver.ts`` (default model per
provider). Both are fetched as raw text; a regex-based TS->JSON pass
exploits the generator's predictable shape.

The source emits per-model observations. Coding-agent side-output
(``default``, ``cli``, ``flag`` per provider) is built by
:func:`build_coding_agents` which the orchestrator calls separately.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime, timedelta

from lanista import http
from lanista.source_base import Source

MODELS_URL = (
    "https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/ai/src/models.generated.ts"
)
RESOLVER_URL = (
    "https://raw.githubusercontent.com/badlogic/pi-mono/main/"
    "packages/coding-agent/src/core/model-resolver.ts"
)
COMMITS_URL = (
    "https://api.github.com/repos/badlogic/pi-mono/commits"
    "?path=packages/ai/src/models.generated.ts&per_page=1"
)

# Static CLI-wrapper annotations. Merged onto pi-mono data in build_coding_agents.
# Only fields not derivable from pi-mono itself.
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
    "google-gemini-cli": {"cli": "gemini", "flag": "gemini --model <id>"},
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
    "openrouter": {"note": "Unified gateway; prefix model with provider: 'openai/...'"},
}

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


def _ts_to_json(ts: str) -> str:
    strings: list[str] = []

    def stash(m: re.Match[str]) -> str:
        strings.append(m.group(0))
        return f"\x00{len(strings) - 1}\x00"

    ts = re.sub(r'"(?:[^"\\]|\\.)*"', stash, ts)
    ts = re.sub(r"\s+satisfies\s+Model<[^>]+>", "", ts)
    ts = re.sub(r"//[^\n]*", "", ts)
    ts = re.sub(r"([a-zA-Z_]\w*)\s*:", r'"\1":', ts)
    ts = re.sub(r",(\s*[}\]])", r"\1", ts)
    return re.sub(r"\x00(\d+)\x00", lambda m: strings[int(m.group(1))], ts)


def parse_models(source: str) -> dict:
    """Parse ``models.generated.ts`` -> ``{provider: {id: model_data}}``."""
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
        return json.loads(_ts_to_json(source[start : i + 1]))
    except json.JSONDecodeError as e:
        print(f"  ! pi-mono models parse failed: {e}", file=sys.stderr)
        return {}


def parse_defaults(source: str) -> dict:
    """Parse ``model-resolver.ts`` -> ``{provider: default_model_id}``."""
    m = re.search(r"defaultModelPerProvider[^=]*=\s*\{(.+?)\};", source, re.S)
    if not m:
        return {}
    return dict(re.findall(r'"?([a-zA-Z0-9-]+)"?\s*:\s*"([^"]+)"', m.group(1)))


def fetch_last_commit_date() -> datetime | None:
    """Timestamp of the most recent commit touching models.generated.ts."""
    data = http.fetch_json(COMMITS_URL, timeout=10)
    if not data or not isinstance(data, list) or not data:
        return None
    try:
        return datetime.fromisoformat(data[0]["commit"]["committer"]["date"].replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return None


def fetch_last_commit_age() -> timedelta | None:
    ts = fetch_last_commit_date()
    return datetime.now(UTC) - ts if ts else None


def fetch() -> dict | None:
    """Fetch both TS files and upstream last-commit timestamp into one blob."""
    models_ts = http.fetch_text(MODELS_URL)
    resolver_ts = http.fetch_text(RESOLVER_URL)
    if models_ts is None and resolver_ts is None:
        return None
    last_commit = fetch_last_commit_date()
    return {
        "models_ts": models_ts,
        "resolver_ts": resolver_ts,
        "last_commit_date": last_commit.isoformat() if last_commit else None,
    }


def project(raw: dict) -> dict[str, dict]:
    """Flatten pi-mono's {provider: {id: model}} -> {provider/id: observation}."""
    models_ts = raw.get("models_ts")
    if not models_ts:
        return {}
    parsed = parse_models(models_ts)
    out: dict[str, dict] = {}
    for provider, models in parsed.items():
        for mid, m in models.items():
            key = f"{provider}/{mid}"
            out[key] = {
                "raw": m,
                "extracted": {
                    "provider": provider,
                    "name": m.get("name"),
                    "context_window": m.get("contextWindow"),
                    "max_output": m.get("maxTokens"),
                    "reasoning": m.get("reasoning"),
                    "modalities": m.get("input"),
                    "pricing_per_million": m.get("cost"),
                },
            }
    return out


def build_coding_agents(raw: dict) -> dict:
    """Top-level coding_agents structure — not per-model, lives on the index root."""
    if not raw:
        return {}
    pi_models = parse_models(raw.get("models_ts") or "")
    pi_defaults = parse_defaults(raw.get("resolver_ts") or "")
    out: dict = {}
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


SOURCE = Source(name="pimono", url=MODELS_URL, fetch=fetch, project=project)
