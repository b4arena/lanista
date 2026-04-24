"""Artificial Analysis — manual-drop slot.

AA's benchmark dashboard is a JS-rendered SPA with no public JSON/API
export. Rather than ship a fragile scraper, lanista treats AA as a
manual-drop source: populate

    ~/.config/lanista/sources/artificial_analysis.json

with a blob shaped

    {"models": {<model_id>: {<arbitrary fields>}, ...}}

and lanista will merge it on the next ``fetch`` like any other source.
Field names are intentionally free-form — whatever you copy from the AA
dashboard will end up in ``observations[].raw`` and be available to
agents for synthesis.

The shipped seed is empty (zero models). Overwrite it when you have data.
"""

from __future__ import annotations

from lanista.source_base import Source


def fetch() -> dict | None:
    return None


def project(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for mid, entry in (raw.get("models") or {}).items():
        extracted = dict(entry) if isinstance(entry, dict) else {}
        out[mid] = {"raw": entry, "extracted": extracted}
    return out


SOURCE = Source(
    name="artificial_analysis",
    url=None,
    fetch=fetch,
    project=project,
    curated=True,
    seed_name="artificial_analysis.seed.json",
)
