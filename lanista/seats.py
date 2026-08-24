"""Seat allowlists: only recommend models a host/rig can actually start.

A *seat* is a named pool of provider-facing pin ids (e.g. the models the
``herdr-agents-collaboration`` skill documents). Pareto/profiles can restrict
to that pool so flagship/balanced/budget never point at an unstartable id.

Matching is normalization-aware (dots/dashes/provider prefixes) and tries a
few common pin suffixes (``-thinking``, ``-high``, …) against the catalog.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources

from lanista import aliases as al
from lanista import paths

# Strip these trailing tokens when a pin has no exact catalog hit.
_SOFT_SUFFIXES = (
    "-thinking",
    "-high",
    "-medium",
    "-low",
    "-preview",
    "-latest",
    "-default",
    "-batch",
)


@dataclass(frozen=True)
class SeatPin:
    provider: str
    pin: str
    engine: str | None = None
    role: str | None = None


@dataclass
class Seat:
    id: str
    description: str = ""
    source: str = ""
    pins: list[SeatPin] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedPin:
    pin: SeatPin
    index_id: str


@dataclass
class SeatMatch:
    """Result of intersecting a seat with the model index."""

    models: dict
    resolved: list[ResolvedPin]
    unresolved: list[SeatPin]
    # index_id -> preferred pin row (first match; provider filter already applied)
    pin_by_index: dict[str, ResolvedPin] = field(default_factory=dict)


def load_seed() -> dict:
    ref = resources.files("lanista.data") / "seats.seed.json"
    return json.loads(ref.read_text(encoding="utf-8"))


def load_seats_blob() -> dict:
    """Load user's seat table, seeding from package data on first run."""
    target = paths.seats_path()
    if not target.exists():
        paths.ensure_parent(target)
        seed = load_seed()
        target.write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
    return json.loads(target.read_text(encoding="utf-8"))


def parse_seats(blob: dict) -> dict[str, Seat]:
    raw = blob.get("seats") or {}
    out: dict[str, Seat] = {}
    for seat_id, body in raw.items():
        if not isinstance(body, dict):
            continue
        pins: list[SeatPin] = []
        for entry in body.get("models") or []:
            if isinstance(entry, str):
                pins.append(SeatPin(provider="*", pin=entry))
                continue
            if not isinstance(entry, dict):
                continue
            pin = entry.get("pin") or entry.get("id")
            provider = entry.get("provider") or "*"
            if not pin:
                continue
            pins.append(
                SeatPin(
                    provider=str(provider),
                    pin=str(pin),
                    engine=entry.get("engine"),
                    role=entry.get("role"),
                )
            )
        out[seat_id] = Seat(
            id=seat_id,
            description=str(body.get("description") or ""),
            source=str(body.get("source") or ""),
            pins=pins,
        )
    return out


def load_seats() -> dict[str, Seat]:
    return parse_seats(load_seats_blob())


def get_seat(seat_id: str) -> Seat | None:
    return load_seats().get(seat_id)


def list_seat_ids() -> list[str]:
    return sorted(load_seats())


def _index_lookup(models: dict) -> dict[str, str]:
    """normalized form -> first index id with that form."""
    lookup: dict[str, str] = {}
    for mid in models:
        n = al.normalize(mid)
        lookup.setdefault(n, mid)
    return lookup


def _candidate_norms(pin: str, resolver: dict[str, str]) -> list[str]:
    """Ordered normalized forms to try for a provider pin."""
    seen: set[str] = set()
    out: list[str] = []

    def add(s: str) -> None:
        n = al.normalize(s)
        if n and n not in seen:
            seen.add(n)
            out.append(n)

    # alias-resolved canonical, then raw pin
    can = al.resolve(pin, resolver)
    add(can)
    add(pin)
    # soft suffix peel
    cur = al.normalize(can)
    changed = True
    while changed:
        changed = False
        for suf in _SOFT_SUFFIXES:
            suf_n = al.normalize(suf).lstrip("-")
            token = f"-{suf_n}"
            if cur.endswith(token) and len(cur) > len(token):
                cur = cur[: -len(token)].rstrip("-")
                add(cur)
                changed = True
                break
    return out


def resolve_pin_to_index(
    pin: str,
    models: dict,
    *,
    resolver: dict[str, str] | None = None,
    lookup: dict[str, str] | None = None,
) -> str | None:
    """Map a provider pin id onto a catalog model id, or None."""
    if resolver is None:
        resolver = al.build_resolver(al.load_aliases().get("aliases") or {})
    if lookup is None:
        lookup = _index_lookup(models)
    # Direct hits first
    if pin in models:
        return pin
    can = al.resolve(pin, resolver)
    if can in models:
        return can
    for norm in _candidate_norms(pin, resolver):
        if norm in models:
            return norm
        hit = lookup.get(norm)
        if hit:
            return hit
    return None


def match_seat(
    models: dict,
    seat: Seat,
    *,
    provider: str | None = None,
) -> SeatMatch:
    """Filter ``models`` to those covered by ``seat`` (optional provider lane)."""
    resolver = al.build_resolver(al.load_aliases().get("aliases") or {})
    lookup = _index_lookup(models)
    resolved: list[ResolvedPin] = []
    unresolved: list[SeatPin] = []
    pin_by_index: dict[str, ResolvedPin] = {}
    want_provider = provider.lower() if provider else None

    for sp in seat.pins:
        if want_provider and sp.provider != "*" and sp.provider.lower() != want_provider:
            continue
        index_id = resolve_pin_to_index(sp.pin, models, resolver=resolver, lookup=lookup)
        if index_id is None:
            unresolved.append(sp)
            continue
        rp = ResolvedPin(pin=sp, index_id=index_id)
        resolved.append(rp)
        pin_by_index.setdefault(index_id, rp)

    allowed = {rp.index_id for rp in resolved}
    filtered = {mid: entry for mid, entry in models.items() if mid in allowed}
    return SeatMatch(
        models=filtered,
        resolved=resolved,
        unresolved=unresolved,
        pin_by_index=pin_by_index,
    )


def format_pin(rp: ResolvedPin | None, index_id: str) -> str:
    """Human/machine pin label for a catalog id."""
    if rp is None:
        return index_id
    prov = rp.pin.provider
    if prov and prov != "*":
        return f"{prov}/{rp.pin.pin}"
    return rp.pin.pin
