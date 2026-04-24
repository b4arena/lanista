"""Opinion corpus — prose feeds for the picker prompt.

Unlike ``lanista.sources`` (per-model structured catalog data), opinion
fetchers return a flat list of ``OpinionEntry`` — one per blog post, HN
story, etc. Each entry has a stable, citeable ID.
"""

from __future__ import annotations

from lanista.opinions import cache, eugeneyan, hn, willison
from lanista.opinions.base import OpinionEntry, OpinionFetcher

FETCHERS: tuple[OpinionFetcher, ...] = (
    OpinionFetcher(name="willison", fetch=willison.fetch),
    OpinionFetcher(name="eugeneyan", fetch=eugeneyan.fetch),
    OpinionFetcher(name="hn", fetch=hn.fetch),
)


def refresh_all() -> dict[str, int]:
    """Fetch every source, persist to cache, return per-source entry counts."""
    counts: dict[str, int] = {}
    for f in FETCHERS:
        entries = f.fetch()
        cache.save(f.name, entries)
        counts[f.name] = len(entries)
    return counts


__all__ = ["OpinionEntry", "OpinionFetcher", "FETCHERS", "refresh_all", "cache"]
