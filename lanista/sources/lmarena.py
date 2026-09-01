"""LMArena leaderboard — per-category Elo ratings via Parquet.

We download each config's ``latest`` Parquet file in a single request. This
uses HuggingFace's Resolver quota (3000/5min anonymous, 5000 with HF_TOKEN)
instead of the API quota (500/5min anonymous), which is what the old paginated
``/rows`` approach burned through. One HTTP call per config also sidesteps the
transient 500s the datasets-server has been returning on the ``text`` config.

Configs pulled:
- ``document`` — head-to-head votes on document-generation tasks (~21 rows).
  The closest LMArena has to "which model writes docs best".
- ``text`` — the full text leaderboard split across categories: ``overall``,
  ``english``, ``chinese``, ``coding``, ``creative_writing``, ``hard_prompts``,
  ``longer_query``, ``math``, ``multi_turn``, ``instruction_following`` (~8500
  rows; one row per (model, category)).
- ``agent`` and its five per-signal siblings — the agent leaderboard behind
  https://arena.ai/leaderboard/agent. These score a model *driving a coding
  agent over a session*, not answering a prompt: steerability, tool
  hallucination, whether the task actually finished, how many steps it took
  to recover from a failed shell command, and praise-vs-complaint sentiment.

Two scales live in ``lmarena_ratings`` as a result. The ``text``/``document``
configs report Elo (~1500 at the frontier); the ``agent`` configs report a
signed score around 0 (a +0.14 leader, negatives at the bottom). Compare
within a column, never across.

Model names carry a parenthesised variant — ``Claude Opus 5 (High)``,
``mimo-v2-flash (thinking)``. That is a runtime setting, not a distinct
model, so :func:`_split_variant` folds it into the base id and keeps the
per-variant numbers under ``lmarena_variants``. A purely numeric suffix
(``Kimi K2.7 (0813)``) is a version stamp and stays part of the identity.

``webdev`` used to be here but HF stopped publishing its Parquet in 2026-04.
Re-add if upstream revives.
"""

from __future__ import annotations

import io
import re
import sys

import polars as pl

from lanista import aliases, http
from lanista.source_base import Source

_PARQUET_BASE = "https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset/parquet"
CONFIGS: tuple[str, ...] = (
    "document",
    "text",
    "agent",
    "agent_steerability",
    "agent_tool_hallucination",
    "agent_task_outcome_explicit",
    "agent_bash_recovery_steps",
    "agent_praise_complaint",
)


def _parquet_url(config: str) -> str:
    return f"{_PARQUET_BASE}/{config}/latest/0.parquet"


def _fetch_parquet(config: str) -> list[dict]:
    url = _parquet_url(config)
    data = http.fetch_bytes(url, headers=http.hf_headers())
    if not data:
        return []
    try:
        df = pl.read_parquet(io.BytesIO(data))
    except (pl.exceptions.ComputeError, OSError) as e:
        print(f"  ! parquet parse {url}: {e}", file=sys.stderr)
        return []
    return df.to_dicts()


def fetch() -> dict | None:
    blob: dict[str, list[dict]] = {}
    for cfg in CONFIGS:
        rows = _fetch_parquet(cfg)
        if rows:
            blob[cfg] = rows
    return blob or None


def _key_for(config: str, category: str) -> str:
    return category if config == "text" else f"{config}/{category}"


_VARIANT_RE = re.compile(r"^(?P<base>.+?)\s*\((?P<variant>[^()]+)\)$")


def _split_variant(model_name: str) -> tuple[str, str | None]:
    """Split ``"Claude Opus 5 (High)"`` into ``("Claude Opus 5", "high")``.

    A purely numeric suffix is a version stamp (``Kimi K2.7 (0813)``), not a
    runtime setting, so it stays part of the model identity.
    """
    m = _VARIANT_RE.match(model_name.strip())
    if not m:
        return model_name.strip(), None
    variant = m.group("variant").strip()
    if variant.isdigit():
        return model_name.strip(), None
    return m.group("base").strip(), variant.lower()


def _score_of(row: dict) -> float | None:
    """Elo from text/document rows, signed score from agent rows."""
    v = row.get("rating")
    return row.get("score") if v is None else v


def _sample_of(row: dict) -> int | None:
    """Vote count (text/document) or session count (agent)."""
    for key in ("vote_count", "session_count", "observation_count"):
        v = row.get(key)
        if v is not None:
            return int(v)
    return None


def _measure(row: dict, variant: str | None) -> dict:
    out = {
        "rating": _score_of(row),
        "rank": row.get("rank"),
        "votes": _sample_of(row),
    }
    if variant:
        out["variant"] = variant
    ci_lo, ci_hi = row.get("score_ci_lower"), row.get("score_ci_upper")
    if ci_lo is not None or ci_hi is not None:
        out["ci"] = [ci_lo, ci_hi]
    return out


def _better(new: dict, old: dict | None) -> bool:
    if old is None:
        return True
    a, b = new.get("rating"), old.get("rating")
    if a is None:
        return False
    return b is None or a > b


def project(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for cfg, rows in raw.items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            model = row.get("model_name")
            cat = row.get("category")
            if not model or not cat:
                continue
            base, variant = _split_variant(model)
            # Configs disagree on naming: ``text`` publishes slugs
            # (``claude-opus-4-8``), ``agent`` publishes display names
            # (``Claude Opus 4.8``). Keying on the normalized form merges them
            # into one observation — otherwise the index gets two entries both
            # tagged source="lmarena", and every reader takes the first and
            # silently drops the other's ratings.
            mid = aliases.normalize(base)
            entry = out.setdefault(
                mid,
                {
                    "raw": {"by_config": {}},
                    "extracted": {
                        "lmarena_display_name": base,
                        "lmarena_ratings": {},
                        "lmarena_variants": {},
                        "lmarena_publish_date": row.get("leaderboard_publish_date"),
                        "lmarena_organization": row.get("organization"),
                    },
                },
            )
            key = _key_for(cfg, cat)
            measure = _measure(row, variant)
            entry["raw"]["by_config"].setdefault(cfg, {}).setdefault(cat, {})[
                variant or "default"
            ] = row
            entry["extracted"]["lmarena_variants"].setdefault(key, {})[variant or "default"] = (
                measure
            )
            # Headline is the best-scoring variant, and it says which one it
            # was — flattening without recording the setting is the mistake
            # issue #3 calls out in the Aider projection.
            ratings = entry["extracted"]["lmarena_ratings"]
            if _better(measure, ratings.get(key)):
                ratings[key] = measure
    return out


SOURCE = Source(name="lmarena", url=_PARQUET_BASE, fetch=fetch, project=project)
