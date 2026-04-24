"""Orchestrate a full fetch: run every source, merge by alias, write index.

Each source in :data:`lanista.sources.SOURCES` runs independently. Fetched
sources write their raw blob to ``sources_cache_dir()``; curated sources
are seeded from package data into ``sources_config_dir()`` on first run
and read from there thereafter. Source failures are recorded in
``FetchReport.source_errors`` and skipped — other sources still proceed.

The merged index per model:

    {
      "canonical_id": "claude-opus-4-7",
      "observations": [
        {"source": "openrouter", "source_model_id": "...", "raw": {...}, "extracted": {...}},
        {"source": "gkisokay", ...},
        ...
      ],
      # rolled-up for backwards compat + quick reads:
      "sources": ["gkisokay", "litellm", "openrouter"],
      "context_window": 200000,
      "pricing_per_million": {...},
      "notes": {...}            # gkisokay's extracted entry, if present
    }
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from importlib import resources

from lanista import aliases as aliases_mod
from lanista import paths
from lanista.source_base import Source
from lanista.sources import SOURCES, pimono

STALE_AFTER = timedelta(days=30)

InfoCallback = Callable[[str], None]

_ROLLUP_FIELDS = (
    "context_window",
    "max_output",
    "pricing_per_million",
    "modalities",
    "capabilities",
    "tokenizer",
)


@dataclass
class FetchReport:
    source_counts: dict[str, int] = field(default_factory=dict)
    source_errors: dict[str, str] = field(default_factory=dict)
    pimono_last_commit: datetime | None = None
    pimono_age: timedelta | None = None
    index_path: str = ""
    index_size_kb: int = 0
    total_models: int = 0


def _seed_curated(source: Source) -> None:
    target = paths.source_path(source.name, curated=True)
    if target.exists():
        return
    seed_name = source.seed_name or f"{source.name}.seed.json"
    seed_ref = resources.files("lanista.data") / seed_name
    paths.ensure_parent(target)
    if seed_ref.is_file():
        target.write_text(seed_ref.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        target.write_text(json.dumps({"models": {}}, indent=2) + "\n", encoding="utf-8")


def _load_source(source: Source, log: InfoCallback) -> tuple[dict | None, str | None]:
    if source.curated:
        _seed_curated(source)
        path = paths.source_path(source.name, curated=True)
        log(f"reading curated {source.name}: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8")), None
        except (json.JSONDecodeError, OSError) as e:
            return None, f"read failure: {e}"
    log(f"fetching {source.name}...")
    raw = source.fetch()
    if raw is None:
        return None, "fetch failed"
    path = paths.source_path(source.name, curated=False)
    paths.ensure_parent(path)
    # default=str covers non-JSON natives like YAML dates (Aider) and
    # anything else a fetcher might accidentally hand us.
    path.write_text(json.dumps(raw, indent=2, default=str) + "\n", encoding="utf-8")
    return raw, None


def _rollup(obs_list: list[dict], field_name: str):
    for obs in obs_list:
        val = (obs.get("extracted") or {}).get(field_name)
        if val not in (None, {}, []):
            return val
    return None


def run_fetch(info: InfoCallback | None = None) -> FetchReport:
    log = info or (lambda _msg: None)
    report = FetchReport()
    now_iso = datetime.now(UTC).isoformat()

    resolver = aliases_mod.build_resolver(
        aliases_mod.load_aliases().get("aliases", {})
    )

    models: dict[str, dict] = {}
    pimono_raw: dict | None = None

    for source in SOURCES:
        raw, err = _load_source(source, log)
        if err:
            report.source_errors[source.name] = err
            continue
        if source.name == "pimono":
            pimono_raw = raw
        items = source.project(raw or {})
        report.source_counts[source.name] = len(items)
        for source_mid, item in items.items():
            canonical = aliases_mod.resolve(source_mid, resolver)
            entry = models.setdefault(
                canonical,
                {"canonical_id": canonical, "observations": []},
            )
            entry["observations"].append(
                {
                    "source": source.name,
                    "fetched_at": now_iso,
                    "source_model_id": source_mid,
                    "raw": item.get("raw"),
                    "extracted": item.get("extracted") or {},
                }
            )

    for entry in models.values():
        obs = entry["observations"]
        entry["sources"] = sorted({o["source"] for o in obs})
        for f in _ROLLUP_FIELDS:
            val = _rollup(obs, f)
            if val is not None:
                entry[f] = val
        gk = next((o for o in obs if o["source"] == "gkisokay"), None)
        if gk:
            entry["notes"] = gk.get("extracted") or {}

    coding_agents = pimono.build_coding_agents(pimono_raw or {})

    log("checking pi-mono staleness...")
    report.pimono_last_commit = pimono.fetch_last_commit_date()
    if report.pimono_last_commit:
        report.pimono_age = datetime.now(UTC) - report.pimono_last_commit

    output = {
        "generated_at": now_iso,
        "pimono_last_commit": (
            report.pimono_last_commit.isoformat() if report.pimono_last_commit else None
        ),
        "sources": {s.name: (s.url or "curated") for s in SOURCES},
        "source_counts": report.source_counts,
        "source_errors": report.source_errors,
        "aliases_path": str(paths.aliases_path()),
        "coding_agents": coding_agents,
        "model_count": len(models),
        "models": dict(sorted(models.items())),
    }
    idx_path = paths.ensure_parent(paths.index_path())
    idx_path.write_text(json.dumps(output, indent=2, default=str) + "\n", encoding="utf-8")
    report.index_path = str(idx_path)
    report.index_size_kb = idx_path.stat().st_size // 1024
    report.total_models = len(models)
    return report


def load_index() -> dict | None:
    p = paths.index_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
