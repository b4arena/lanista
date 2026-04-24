"""Hacker News — Algolia search for model-family discussion threads.

Stories act as popularity signals (points + comment count) on model
releases and debates. We don't pull comment bodies — the picker treats
an HN entry as evidence that there's active discussion worth linking,
not as a substantive opinion on its own.
"""

from __future__ import annotations

import urllib.parse

from lanista import http
from lanista.opinions.base import OpinionEntry

_ENDPOINT = "https://hn.algolia.com/api/v1/search"
_HITS = 30
_MIN_POINTS = 50

QUERIES: tuple[str, ...] = (
    "claude opus",
    "claude sonnet",
    "gpt-5",
    "gpt-4",
    "gemini pro",
    "qwen",
    "llama",
    "deepseek",
    "grok",
    "mistral",
)


def _url(query: str) -> str:
    params = urllib.parse.urlencode(
        {"query": query, "tags": "story", "hitsPerPage": _HITS}
    )
    return f"{_ENDPOINT}?{params}"


def fetch() -> list[OpinionEntry]:
    seen: set[str] = set()
    out: list[OpinionEntry] = []
    for q in QUERIES:
        data = http.fetch_json(_url(q))
        if not data:
            continue
        for hit in data.get("hits") or []:
            story_id = hit.get("objectID")
            if not story_id or story_id in seen:
                continue
            points = hit.get("points") or 0
            if points < _MIN_POINTS:
                continue
            seen.add(story_id)
            title = hit.get("title") or ""
            created = hit.get("created_at") or ""
            external = hit.get("url") or ""
            permalink = f"https://news.ycombinator.com/item?id={story_id}"
            comments = hit.get("num_comments") or 0
            body_parts = [
                f"{points} points, {comments} comments on Hacker News",
            ]
            if external:
                body_parts.append(f"Linked: {external}")
            out.append(
                OpinionEntry(
                    id=f"hn-{story_id}",
                    source="hn",
                    title=title,
                    url=permalink,
                    date=created[:10],
                    body=". ".join(body_parts),
                )
            )
    return out
