"""Source abstraction.

Every source (OpenRouter, LiteLLM, Gkisokay, ...) implements the same contract:

    fetch()    -> raw blob (whatever shape the upstream publishes), or ``None``
    project()  -> {source_model_id: {"raw": ..., "extracted": ...}}

``raw`` preserves the original per-model entry verbatim so an agent / LLM
can reason over the native fields. ``extracted`` is a best-effort normalized
view (pricing_per_million, context_window, benchmarks, ...) for callers that
want a quick comparable read without re-parsing each source's schema.

Curated sources (``curated=True``) have ``fetch`` return ``None`` and instead
rely on a seed file shipped under ``lanista/data/<name>.seed.json`` that is
copied to the user's config dir on first run.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Source:
    name: str
    url: str | None
    fetch: Callable[[], dict | None]
    project: Callable[[dict], dict[str, dict]]
    curated: bool = False
    # When curated=True, seed_name identifies the package-data seed to copy
    # to the user's config on first run. Defaults to ``<name>.seed.json``.
    seed_name: str | None = None
