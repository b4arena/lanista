"""Sourced public model facts and explicit variant identity.

``lanista/data/model_cards.json`` is packaged, read-only reference data. It is
never copied into the config dir and never written by ``lanista fetch``.

Shape (schema 1)::

    {
      "schema": 1,
      "models": {
        "<canonical-id>": {
          "display_name": "GLM-5.3",
          "facts": {"<name>": {"value": ..., "source": "<url>", "as_of": "YYYY-MM-DD"}},
          "benchmarks": [{"name", "score", "setting", "source", "as_of"}],
          "not_same_as": ["<canonical-id>", ...]
        }
      },
      "variants": {
        "<runtime-id>": {"canonical": "<canonical-id>", "source": "<url>", "note": "..."}
      }
    }

Rules:

* A fact with ``"value": null`` is **unknown** (it must say ``"status": "unknown"``).
  Unknown is never zero.
* A variant entry maps one runtime id to one canonical id. Matching is
  equality after :func:`lanista.aliases.normalize` (case, punctuation and the
  first provider prefix only), so every token such as a build date (``1017``),
  a parameter shape (``816b-a42b``) or a quantization (``nvfp4``) must match.
  Nothing is matched by prefix, substring or suffix peeling.
* Benchmarks are listed only for the exact variant the card describes.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources

from lanista import aliases as al

SCHEMA = 1
FACT_KEYS = ("value", "source", "as_of")


@cache
def load_cards() -> dict:
    ref = resources.files("lanista.data") / "model_cards.json"
    return json.loads(ref.read_text(encoding="utf-8"))


def cards() -> dict[str, dict]:
    return load_cards().get("models") or {}


def variants() -> dict[str, dict]:
    return load_cards().get("variants") or {}


def variant_resolver(blob: dict | None = None) -> dict[str, str]:
    """``{normalized runtime id: canonical}`` from the explicit variant map.

    Canonical ids of every card map to themselves.
    """
    blob = blob if blob is not None else load_cards()
    out: dict[str, str] = {}
    for canonical in blob.get("models") or {}:
        out[al.normalize(canonical)] = canonical
    for runtime_id, spec in (blob.get("variants") or {}).items():
        out[al.normalize(runtime_id)] = spec["canonical"]
    return out


def resolve_variant(runtime_id: str, blob: dict | None = None) -> str | None:
    """Canonical id for an explicitly listed runtime id, else ``None``."""
    return variant_resolver(blob).get(al.normalize(runtime_id))


def protected_ids(blob: dict | None = None) -> set[str]:
    """Normalized ids that fuzzy matching must never land on."""
    return set(variant_resolver(blob))


def unproven() -> dict[str, dict]:
    return load_cards().get("unproven") or {}


def card_for(canonical: str) -> dict | None:
    return cards().get(canonical)


def validate(blob: dict) -> list[str]:
    """Return a list of problems; empty means the file obeys the rules."""
    problems: list[str] = []
    if blob.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA}")
    models = blob.get("models") or {}
    for mid, card in models.items():
        if mid != al.normalize(mid):
            problems.append(f"{mid}: canonical id must be normalized")
        for fname, fact in (card.get("facts") or {}).items():
            where = f"{mid}.facts.{fname}"
            if not isinstance(fact, dict):
                problems.append(f"{where}: must be an object")
                continue
            if fact.get("value") is None:
                if fact.get("status") != "unknown":
                    problems.append(f"{where}: null value needs status 'unknown'")
                continue
            for k in ("source", "as_of"):
                if not fact.get(k):
                    problems.append(f"{where}: missing {k}")
        for i, b in enumerate(card.get("benchmarks") or []):
            for k in ("name", "score", "source", "as_of"):
                if b.get(k) in (None, ""):
                    problems.append(f"{mid}.benchmarks[{i}]: missing {k}")
        for other in card.get("not_same_as") or []:
            if al.normalize(other) == al.normalize(mid):
                problems.append(f"{mid}: not_same_as lists itself")
    proven = {al.normalize(r) for r in blob.get("variants") or {}}
    for rid in blob.get("unproven") or {}:
        if al.normalize(rid) in proven:
            problems.append(f"{rid}: listed both as variant and as unproven")
    for rid, spec in (blob.get("variants") or {}).items():
        can = spec.get("canonical")
        if can not in models:
            problems.append(f"variant {rid}: canonical {can!r} has no card")
        if not spec.get("source"):
            problems.append(f"variant {rid}: missing source")
        bad = set(models.get(can, {}).get("not_same_as") or [])
        if al.normalize(rid) in {al.normalize(b) for b in bad}:
            problems.append(f"variant {rid}: listed as not_same_as {can}")
    return problems
