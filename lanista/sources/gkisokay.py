"""Gkisokay LLM Model Stack — quarterly hand-curated tier/use-case chart.

Curated source: no live fetch. The shipped seed is copied to the user's
config dir on first run; after that the user's copy is authoritative.
Re-running ``lanista fetch`` reads the user's file without overwriting.

Source: https://x.com/gkisokay (see _source field in the seed file).
"""

from __future__ import annotations

from lanista.source_base import Source


def fetch() -> dict | None:
    # Curated sources are loaded from the user's config file, not fetched.
    return None


def project(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for mid, entry in (raw.get("models") or {}).items():
        out[mid] = {"raw": entry, "extracted": dict(entry)}
    return out


SOURCE = Source(
    name="gkisokay",
    url=None,
    fetch=fetch,
    project=project,
    curated=True,
    seed_name="gkisokay.seed.json",
)
