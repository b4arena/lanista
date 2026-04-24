"""Nudge users toward deterministic commands when they'd be better.

When a task clearly reads as a numeric trade-off ("cheapest ... under $X",
"best coding per dollar", ...) we don't want to spin up an LLM to answer
it — we want to hand back a ``lanista pareto`` invocation. This module
is intentionally string-matching, not ML: the false-positive cost is a
stderr comment line, so the bar for matching is low.
"""

from __future__ import annotations

_FRONTIER_TRIGGERS = (
    "pareto",
    "under $",
    "per dollar",
    "per-dollar",
    "trade-off",
    "tradeoff",
    "vs price",
    "vs cost",
    "quality per",
    "cheapest",
    "fastest",
)

_PROFILE_TRIGGERS = (
    "sweet spot",
    "sweet-spot",
    "balanced",
    "balance between",
    "flagship",
    "best value",
    "good enough",
    "budget",
)


def is_numeric_tradeoff(task: str) -> bool:
    t = task.lower()
    return any(trigger in t for trigger in _FRONTIER_TRIGGERS + _PROFILE_TRIGGERS)


def _wants_profile(task: str) -> bool:
    t = task.lower()
    return any(trigger in t for trigger in _PROFILE_TRIGGERS)


def suggest_alternative(task: str) -> str | None:
    if not is_numeric_tradeoff(task):
        return None
    if _wants_profile(task):
        return (
            "Tip: this looks like a trade-off with multiple acceptable answers. "
            "Try: lanista profiles lm_coding price_input"
        )
    return (
        "Tip: this looks like a numeric trade-off. "
        "Try: lanista pareto lm_coding price_input"
    )
