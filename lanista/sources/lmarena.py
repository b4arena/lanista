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

``webdev`` used to be here but HF stopped publishing its Parquet in 2026-04.
Re-add if upstream revives.
"""

from __future__ import annotations

import io
import sys

import polars as pl

from lanista import http
from lanista.source_base import Source

_PARQUET_BASE = (
    "https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset/parquet"
)
CONFIGS: tuple[str, ...] = ("document", "text")


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
            entry = out.setdefault(
                model,
                {
                    "raw": {"by_config": {}},
                    "extracted": {
                        "lmarena_ratings": {},
                        "lmarena_publish_date": row.get("leaderboard_publish_date"),
                        "lmarena_organization": row.get("organization"),
                    },
                },
            )
            entry["raw"]["by_config"].setdefault(cfg, {})[cat] = row
            entry["extracted"]["lmarena_ratings"][_key_for(cfg, cat)] = {
                "rating": row.get("rating"),
                "rank": row.get("rank"),
                "votes": row.get("vote_count"),
            }
    return out


SOURCE = Source(name="lmarena", url=_PARQUET_BASE, fetch=fetch, project=project)
