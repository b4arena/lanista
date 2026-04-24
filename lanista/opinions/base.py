"""Opinion corpus data shape.

Each entry is one post / story / item in the prose corpus. The ``id`` is
stable (derived from URL + date) so the picker can cite it and the user
can look it up. ``body`` is a trimmed plain-text excerpt — enough for an
LLM to judge relevance, not the full post.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class OpinionEntry:
    id: str
    source: str
    title: str
    url: str
    date: str
    body: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OpinionFetcher:
    name: str
    fetch: Callable[[], list[OpinionEntry]]
