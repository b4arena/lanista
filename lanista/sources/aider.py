"""Aider polyglot leaderboard — coding-specific benchmark runs.

Published as YAML in the Aider-AI/aider repo. Each list entry is one
benchmark run (model, pass_rate_1, pass_rate_2, cost, edit_format, ...).
We keep every run under the model's ``raw.runs`` and surface the best
``pass_rate_2`` and run count in ``extracted`` for quick comparisons.
"""

from __future__ import annotations

import yaml

from lanista import http
from lanista.source_base import Source

URL = (
    "https://raw.githubusercontent.com/Aider-AI/aider/main/"
    "aider/website/_data/polyglot_leaderboard.yml"
)


def fetch() -> dict | None:
    text = http.fetch_text(URL)
    if text is None:
        return None
    try:
        entries = yaml.safe_load(text) or []
    except yaml.YAMLError:
        return None
    return {"entries": entries if isinstance(entries, list) else []}


def project(raw: dict) -> dict[str, dict]:
    entries = raw.get("entries") or []
    per_model: dict[str, list[dict]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        model = entry.get("model")
        if not model:
            continue
        per_model.setdefault(model, []).append(entry)

    out: dict[str, dict] = {}
    for model, runs in per_model.items():
        rates = [r.get("pass_rate_2") for r in runs if r.get("pass_rate_2") is not None]
        out[model] = {
            "raw": {"runs": runs},
            "extracted": {
                "run_count": len(runs),
                "best_pass_rate_2": max(rates) if rates else None,
            },
        }
    return out


SOURCE = Source(name="aider", url=URL, fetch=fetch, project=project)
