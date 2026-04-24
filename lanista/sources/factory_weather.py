"""StrongDM Software Factory — Weather Report.

RSS changelog of which models are assigned to which roles in StrongDM's
internal agent runtime. High-signal "real-world ops" source: every item
documents a real routing decision with rationale.

Model attribution is regex-based on titles/descriptions. The raw feed is
preserved verbatim in ``sources/factory_weather.json``, so anything the
regex misses can still be recovered by downstream synthesis.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from lanista import http
from lanista.source_base import Source

URL = "https://factory.strongdm.ai/weather-report/feed.xml"

_MODEL_PATTERNS = [
    r"gpt-\d(?:\.\d+)+(?:-codex|-mini)?",
    r"opus-\d\.\d+",
    r"(?:claude-)?sonnet[- ]\d\.\d+",
    r"gemini-\d(?:\.\d+)?(?:-pro|-flash)?(?:-image)?(?:-preview)?",
    r"gpt-realtime-\d\.\d+",
    r"gpt-image-\d+",
]
_MODEL_RE = re.compile("|".join(_MODEL_PATTERNS), re.IGNORECASE)


def _parse_feed(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items: list[dict] = []
    for item in root.iter("item"):
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "guid": (item.findtext("guid") or "").strip(),
                "pubDate": (item.findtext("pubDate") or "").strip(),
                "description": (item.findtext("description") or "").strip(),
            }
        )
    return items


def fetch() -> dict | None:
    text = http.fetch_text(URL)
    if text is None:
        return None
    return {"xml": text, "items": _parse_feed(text)}


def project(raw: dict) -> dict[str, dict]:
    items = raw.get("items") or []
    per_model: dict[str, list[dict]] = {}
    for item in items:
        haystack = " ".join(v for v in (item.get("title"), item.get("description")) if v)
        mentions = {m.lower() for m in _MODEL_RE.findall(haystack)}
        for mid in mentions:
            per_model.setdefault(mid, []).append(item)
    out: dict[str, dict] = {}
    for mid, mentions in per_model.items():
        out[mid] = {
            "raw": {"mentions": mentions},
            "extracted": {
                "mention_count": len(mentions),
                "latest_pubdate": mentions[0].get("pubDate") if mentions else None,
            },
        }
    return out


SOURCE = Source(name="factory_weather", url=URL, fetch=fetch, project=project)
