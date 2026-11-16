"""Host-local private route overlay: ``$XDG_CONFIG_HOME/lanista/routes.local.json``.

A *route* is the exact runtime id a harness is started with (for example
``example-gw/glm-5.3``). Routes carry access facts that belong to one host or
one gateway: cost class, per-token price, rate limits, context overrides.
Public model knowledge lives in :mod:`lanista.model_cards`; this file only
adds to it and never changes it.

The file is hand-written. ``lanista fetch`` and the seeders never create or
write it. See ``docs/routes.md`` for the schema and
``docs/routes.local.example.json`` for an example with fake values.

Ownership (agreed with vega, see vega ``docs/design/lanista-catalog.md``):

* vega ``seats.local.json`` owns provider + tier -> route id.
* this file owns route id -> canonical id plus the route facts below.
* Join key: the route id string, compared exactly. No alias or normalize.
* Precedence per field: this file > public catalog > unknown.
  Unknown is never 0. Route cost/price/limits have no catalog fallback:
  a vendor list price is a fact of the model, not of some other route.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date

from lanista import model_cards as mc
from lanista import paths

SCHEMA = 1
VISIBILITY = "private-local"
COST_CLASSES = ("subscription", "budget", "unknown")

PRICE_KEYS = ("input", "output")
LIMIT_KEYS = ("rpm", "tpm")
MODALITIES = ("text", "image", "audio", "video", "file")
CAPABILITIES = (
    "reasoning",
    "function_calling",
    "vision",
    "json",
    "structured_output",
    "streaming",
    "prompt_caching",
)

# field name -> True when the public catalog may fill an ABSENT field (model
# facts), False when only this file can (route-specific access facts).
# Route capabilities are never inherited: a card lists what the model can do,
# not what a gateway exposes.
ROUTE_FIELDS: dict[str, bool] = {
    "canonical": False,
    "cost": False,
    "pricing_per_million": False,
    "limits": False,
    "capabilities": False,
    "context_window": True,
    "max_output": True,
    "modalities": True,
}
FIELD_KEYS = {"value", "source_note", "as_of"}


def routes_path():
    return paths.config_dir() / "routes.local.json"


@dataclass
class Overlay:
    path: str
    present: bool = False
    loaded: bool = False
    routes: dict[str, dict] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "path": self.path,
            "present": self.present,
            "loaded": self.loaded,
            "route_count": len(self.routes),
            "diagnostics": list(self.diagnostics),
        }


def _is_number(v) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v) and v >= 0


def _check_numbers(value, allowed: tuple[str, ...], extra: tuple[str, ...] = ()) -> str | None:
    if not isinstance(value, dict) or not value:
        return "must be a non-empty object"
    for k, v in value.items():
        if k in extra:
            if not isinstance(v, str) or not v:
                return f"{k} must be a non-empty string"
            continue
        if k not in allowed:
            return f"unknown key {k!r} (allowed: {', '.join(allowed + extra)})"
        if v is not None and not _is_number(v):
            return f"{k} must be a finite number >= 0 or null"
    return None


def _check_value(name: str, value) -> str | None:
    """Return a problem string, or None when ``value`` is acceptable."""
    if value is None:
        return None  # explicit unknown
    if name == "canonical":
        return None if isinstance(value, str) and value else "must be a non-empty string"
    if name == "cost":
        return None if value in COST_CLASSES else f"must be one of {', '.join(COST_CLASSES)}"
    if name in ("context_window", "max_output"):
        ok = isinstance(value, int) and not isinstance(value, bool) and value > 0
        return None if ok else "must be a positive integer"
    if name == "pricing_per_million":
        return _check_numbers(value, PRICE_KEYS, extra=("currency",))
    if name == "limits":
        return _check_numbers(value, LIMIT_KEYS)
    if name == "modalities":
        if not isinstance(value, dict) or not value:
            return "must be a non-empty object with input/output lists"
        for k, v in value.items():
            if k not in ("input", "output"):
                return f"unknown key {k!r} (allowed: input, output)"
            if not isinstance(v, list) or not v:
                return f"{k} must be a non-empty list"
            bad = [m for m in v if m not in MODALITIES]
            if bad:
                return f"{k} has unknown modality {bad[0]!r} (allowed: {', '.join(MODALITIES)})"
        return None
    if name == "capabilities":
        if not isinstance(value, dict) or not value:
            return "must be a non-empty object of capability -> true/false/null"
        for k, v in value.items():
            if k not in CAPABILITIES:
                return f"unknown capability {k!r} (allowed: {', '.join(CAPABILITIES)})"
            if v is not None and not isinstance(v, bool):
                return f"{k} must be true, false or null"
        return None
    return "unknown field"


def _check_provenance(fact: dict) -> str | None:
    """source_note/as_of: non-empty strings, as_of an ISO date. Required unless value is null."""
    for k in ("source_note", "as_of"):
        if k in fact and (not isinstance(fact[k], str) or not fact[k].strip()):
            return f"{k} must be a non-empty string"
    if fact["value"] is not None and not (fact.get("source_note") and fact.get("as_of")):
        return "source_note and as_of required"
    if "as_of" in fact:
        try:
            date.fromisoformat(fact["as_of"])
        except ValueError:
            return "as_of must be an ISO date (YYYY-MM-DD)"
    return None


def parse_overlay(blob: object, path: str = "") -> Overlay:
    """Validate a parsed overlay. Bad entries are skipped with a diagnostic."""
    ov = Overlay(path=path, present=True)
    if not isinstance(blob, dict):
        ov.diagnostics.append("top level must be an object; overlay disabled")
        return ov
    if blob.get("schema") != SCHEMA:
        ov.diagnostics.append(f"schema must be {SCHEMA}; overlay disabled")
        return ov
    for key in blob:
        if key not in ("schema", "routes") and not key.startswith("_"):
            ov.diagnostics.append(f"unknown top-level key {key!r} ignored")
    raw = blob.get("routes")
    if not isinstance(raw, dict):
        ov.diagnostics.append("'routes' must be an object; overlay disabled")
        return ov
    ov.loaded = True
    for route_id, body in raw.items():
        if not route_id or not isinstance(body, dict):
            ov.diagnostics.append(f"route {route_id!r}: must be a non-empty id with an object")
            continue
        fields: dict[str, dict] = {}
        for fname, fact in body.items():
            where = f"route {route_id}: {fname}"
            if fname.startswith("_"):
                continue
            if fname not in ROUTE_FIELDS:
                ov.diagnostics.append(f"{where}: unknown field, skipped")
                continue
            if not isinstance(fact, dict) or set(fact) - FIELD_KEYS or "value" not in fact:
                ov.diagnostics.append(f"{where}: expected {{value, source_note, as_of}}, skipped")
                continue
            problem = _check_provenance(fact) or _check_value(fname, fact["value"])
            if problem:
                ov.diagnostics.append(f"{where}: {problem}, skipped")
                continue
            fields[fname] = dict(fact)
        ov.routes[route_id] = fields
    return ov


def load_overlay() -> Overlay:
    """Read the overlay file. A missing file is fine; it is optional."""
    p = routes_path()
    if not p.exists():
        return Overlay(path=str(p))
    try:
        blob = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return Overlay(path=str(p), present=True, diagnostics=[f"not valid JSON ({e}); disabled"])
    return parse_overlay(blob, str(p))


def _unknown() -> dict:
    return {"value": None, "status": "unknown", "origin": "unknown"}


def _catalog_fact(canonical: str | None, fname: str) -> dict | None:
    if not canonical:
        return None
    card = mc.card_for(canonical) or {}
    facts = card.get("facts") or {}
    if fname == "modalities":
        fin, fout = facts.get("input_modalities"), facts.get("output_modalities")
        if not (fin and fin.get("value") is not None) or not (fout and fout.get("value")):
            return None
        return {
            "value": {"input": fin["value"], "output": fout["value"]},
            "source": fin.get("source"),
            "as_of": fin.get("as_of"),
            "origin": "catalog",
        }
    fact = facts.get(fname)
    if not fact or fact.get("value") is None:
        return None
    return {**fact, "origin": "catalog"}


def resolve_route(route_id: str, overlay: Overlay | None = None) -> dict | None:
    """Effective facts for one route id, or ``None`` when it is not in the overlay.

    The join is exact string equality on ``route_id``. Each field carries
    ``origin``: ``local`` (this file), ``catalog`` (public model card) or
    ``unknown``. A field absent locally inherits from the card where allowed;
    a field set locally to ``null`` masks the card and stays unknown.
    """
    ov = overlay if overlay is not None else load_overlay()
    local = ov.routes.get(route_id)
    if local is None:
        return None
    can_fact = local.get("canonical")
    canonical = can_fact.get("value") if can_fact else None
    out_fields: dict[str, dict] = {}
    for fname, catalog_ok in ROUTE_FIELDS.items():
        fact = local.get(fname)
        if fact is not None:
            # Present locally, even as an explicit null: the local entry masks the
            # catalog. null stays unknown (origin local), never falls back.
            if fact.get("value") is None:
                out_fields[fname] = {**fact, "status": "unknown", "origin": "local"}
            else:
                out_fields[fname] = {**fact, "origin": "local"}
            continue
        cat = _catalog_fact(canonical, fname) if catalog_ok else None
        out_fields[fname] = cat or _unknown()
    return {
        "route_id": route_id,
        "visibility": VISIBILITY,
        "canonical": canonical,
        "has_public_card": bool(canonical and mc.card_for(canonical)),
        "fields": out_fields,
        "overlay_path": ov.path,
    }


def resolve_all(overlay: Overlay | None = None) -> dict[str, dict]:
    ov = overlay if overlay is not None else load_overlay()
    return {rid: resolve_route(rid, ov) for rid in sorted(ov.routes)}  # type: ignore[misc]
