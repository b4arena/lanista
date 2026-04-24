"""On-disk cache for opinion feeds under ``$XDG_CACHE_HOME/lanista/opinions/``."""

from __future__ import annotations

import json

from lanista import paths
from lanista.opinions.base import OpinionEntry


def _dir():
    return paths.ensure_dir(paths.cache_dir() / "opinions")


def save(name: str, entries: list[OpinionEntry]) -> None:
    path = _dir() / f"{name}.json"
    payload = {"entries": [e.to_dict() for e in entries]}
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def load(name: str) -> list[OpinionEntry]:
    path = _dir() / f"{name}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [OpinionEntry(**e) for e in data.get("entries", [])]


def load_all() -> list[OpinionEntry]:
    out: list[OpinionEntry] = []
    d = paths.cache_dir() / "opinions"
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for e in data.get("entries", []):
            try:
                out.append(OpinionEntry(**e))
            except TypeError:
                continue
    return out
