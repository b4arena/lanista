"""Deterministic Pareto-frontier shortcuts over the model index.

For quality/cost trade-offs the answer is pure arithmetic, not an LLM
judgement call. This module exposes a column registry so the CLI can
accept free-form axis names like ``lm_coding`` / ``price_input``, compute
the skyline, and hand the result to ``chartroom`` for visualization.

Costs are "lower is better"; qualities are "higher is better". The
pseudo-cost ``-ctx`` flips context-window semantics so that "more ctx"
behaves like "less cost" on the same axis — convenient for mixed charts.
"""

from __future__ import annotations

from collections.abc import Callable


def _ext(entry: dict, source: str) -> dict:
    for o in entry.get("observations") or []:
        if o.get("source") == source:
            return o.get("extracted") or {}
    return {}


def _lm(entry: dict, key: str):
    r = (_ext(entry, "lmarena").get("lmarena_ratings") or {}).get(key) or {}
    return r.get("rating")


def _aider(entry: dict):
    return _ext(entry, "aider").get("best_pass_rate_2")


def _price(entry: dict, side: str):
    p = entry.get("pricing_per_million") or {}
    v = p.get(side)
    return float(v) if v is not None else None


def _price_avg(entry: dict):
    i = _price(entry, "input")
    o = _price(entry, "output")
    if i is None or o is None:
        return None
    return (i + o) / 2


def _neg_ctx(entry: dict):
    c = entry.get("context_window")
    if not c:
        return None
    return 1.0 / float(c)


def _quality_index(entry: dict):
    v = entry.get("quality_index")
    return float(v) if v is not None else None


def _speed(entry: dict):
    v = entry.get("speed_tokens_per_sec")
    return float(v) if v is not None else None


def _neg_ttft(entry: dict):
    v = entry.get("ttft_sec")
    if v is None:
        return None
    return float(v)


COLUMN_ACCESSORS: dict[str, Callable[[dict], float | None]] = {
    # quality axes
    "lm_overall": lambda e: _lm(e, "overall"),
    "lm_coding": lambda e: _lm(e, "coding"),
    "lm_writing": lambda e: _lm(e, "creative_writing"),
    "lm_hard": lambda e: _lm(e, "hard_prompts"),
    "lm_long": lambda e: _lm(e, "longer_query"),
    "lm_chinese": lambda e: _lm(e, "chinese"),
    "lm_document": lambda e: _lm(e, "document/overall"),
    "aider": _aider,
    "quality_index": _quality_index,
    "speed_tokens_per_sec": _speed,
    # cost axes (lower is better)
    "price_input": lambda e: _price(e, "input"),
    "price_output": lambda e: _price(e, "output"),
    "price_avg": _price_avg,
    "neg_ctx": _neg_ctx,
    "neg_ttft_sec": _neg_ttft,
    # Legacy alias — Typer parses a leading dash as a flag so the CLI
    # prefers the neg_* form; the hyphen form still works for library use.
    "-ctx": _neg_ctx,
    "-ttft_sec": _neg_ttft,
}


def available_columns() -> list[str]:
    return sorted(COLUMN_ACCESSORS.keys())


def extract_pairs(
    models: dict, quality: str, cost: str
) -> list[tuple[str, float, float]]:
    q_fn = COLUMN_ACCESSORS[quality]
    c_fn = COLUMN_ACCESSORS[cost]
    out: list[tuple[str, float, float]] = []
    for mid, entry in models.items():
        q = q_fn(entry)
        c = c_fn(entry)
        if q is None or c is None:
            continue
        out.append((mid, float(q), float(c)))
    return out


def pareto_frontier(pairs: list[tuple[str, float, float]]) -> set[str]:
    """Return ids that are NOT dominated on (quality↑, cost↓)."""
    frontier: set[str] = set()
    for mid, q, c in pairs:
        dominated = False
        for other_id, oq, oc in pairs:
            if other_id == mid:
                continue
            if oq >= q and oc <= c and (oq > q or oc < c):
                dominated = True
                break
        if not dominated:
            frontier.add(mid)
    return frontier


def filter_models(
    models: dict,
    *,
    require_cap: str | None = None,
    min_ctx: int | None = None,
) -> dict:
    """Drop models that don't satisfy a capability or context-window gate."""
    out = {}
    for mid, entry in models.items():
        if require_cap:
            caps = entry.get("capabilities") or []
            if require_cap not in caps:
                continue
        if min_ctx is not None:
            ctx = entry.get("context_window")
            if not ctx or ctx < min_ctx:
                continue
        out[mid] = entry
    return out


def _knee_index(
    frontier: list[tuple[str, float, float]],
) -> int:
    """Index of the frontier point closest to the ideal corner (max q, min c).

    Both axes are min-max normalized to [0, 1] over the frontier (not the full
    pair set) — the knee is "best compromise *among non-dominated options*".
    """
    if len(frontier) == 1:
        return 0
    qs = [q for _, q, _ in frontier]
    cs = [c for _, _, c in frontier]
    q_min, q_max = min(qs), max(qs)
    c_min, c_max = min(cs), max(cs)
    q_span = (q_max - q_min) or 1.0
    c_span = (c_max - c_min) or 1.0
    best_i = 0
    best_dist = float("inf")
    for i, (_, q, c) in enumerate(frontier):
        qn = (q - q_min) / q_span
        cn = (c - c_min) / c_span
        # Ideal = (qn=1, cn=0); distance²
        d = (1 - qn) ** 2 + cn**2
        if d < best_dist:
            best_dist = d
            best_i = i
    return best_i


def find_profiles(
    pairs: list[tuple[str, float, float]],
    frontier_ids: set[str],
) -> dict[str, tuple[str, float, float] | None]:
    """Return {flagship, balanced, budget} anchor points on the frontier.

    All three may collapse to the same model when the frontier has one point;
    the caller decides how to present collapses.
    """
    frontier = [p for p in pairs if p[0] in frontier_ids]
    if not frontier:
        return {"flagship": None, "balanced": None, "budget": None}
    flagship = max(frontier, key=lambda p: (p[1], -p[2]))
    budget = min(frontier, key=lambda p: (p[2], -p[1]))
    balanced = frontier[_knee_index(frontier)]
    return {"flagship": flagship, "balanced": balanced, "budget": budget}


def to_csv(
    pairs: list[tuple[str, float, float]],
    frontier_ids: set[str],
    *,
    quality_name: str = "quality",
    cost_name: str = "cost",
) -> str:
    lines = [f"model,{quality_name},{cost_name},on_frontier"]
    for mid, q, c in pairs:
        lines.append(f"{mid},{q},{c},{'true' if mid in frontier_ids else 'false'}")
    return "\n".join(lines) + "\n"
