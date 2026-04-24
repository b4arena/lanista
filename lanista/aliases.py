"""Model-id canonicalization across source naming conventions.

Sources use different model-id shapes:
    OpenRouter:  'anthropic/claude-opus-4-7'
    LiteLLM:     'claude-opus-4.7'
    Gkisokay:    'Claude Opus 4.7'     (title case, spaces, dots)
    Factory:     'opus-4.7'            (dashes + dots)
    Anthropic:   'claude-opus-4-7-20260101' (suffixed with date)

The alias table resolves every known variant to one canonical id. The
canonical form is lowercase with dashes only: ``claude-opus-4-7``.

Unknown ids are passed through :func:`normalize` so that two unknown-but-
equivalent spellings still collapse to the same merged entry (e.g. a new
model ``xyz-corp/foo-1.0`` from OpenRouter and ``foo-1.0`` from LiteLLM
both normalize to ``foo-1-0``).
"""

from __future__ import annotations

import json
import re
from importlib import resources

from lanista import paths


def normalize(s: str) -> str:
    """Lowercase, strip provider prefix, collapse non-alnum to single dashes."""
    if not s:
        return ""
    bare = s.lower().split("/", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "-", bare).strip("-")


def build_resolver(aliases: dict[str, list[str]]) -> dict[str, str]:
    """Flatten ``{canonical: [alts]}`` into ``{normalized_form: canonical}``."""
    resolver: dict[str, str] = {}
    for canonical, alts in aliases.items():
        resolver[normalize(canonical)] = canonical
        for alt in alts:
            resolver[normalize(alt)] = canonical
    return resolver


def resolve(model_id: str, resolver: dict[str, str]) -> str:
    """Return canonical id for ``model_id``, or its normalized form if unknown."""
    norm = normalize(model_id)
    return resolver.get(norm, norm)


def load_seed() -> dict:
    ref = resources.files("lanista.data") / "aliases.seed.json"
    return json.loads(ref.read_text(encoding="utf-8"))


def load_aliases() -> dict:
    """Load user's alias table, seeding from package data on first run."""
    target = paths.aliases_path()
    if not target.exists():
        paths.ensure_parent(target)
        seed = load_seed()
        target.write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
    return json.loads(target.read_text(encoding="utf-8"))
