"""Eugene Yan's blog — RSS 2.0.

Pragmatic, production-focused LLM patterns from a principal applied
scientist. RSS ``<description>`` is a plain-text summary (no HTML), and
``<pubDate>`` is RFC-822; we normalize to ISO-8601 dates.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from lanista import http
from lanista.opinions.base import OpinionEntry

URL = "https://eugeneyan.com/rss/"

_RFC822 = re.compile(r"(\d{1,2})\s+(\w{3})\s+(\d{4})")
_MONTHS = {
    m: f"{i + 1:02d}"
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
}


def _rfc822_to_iso(s: str) -> str:
    m = _RFC822.search(s or "")
    if not m:
        return ""
    day, mon, year = m.groups()
    return f"{year}-{_MONTHS.get(mon[:3], '01')}-{int(day):02d}"


def _text(node, tag: str) -> str:
    el = node.find(tag)
    if el is None:
        return ""
    return el.text or ""


def _stable_id(link: str, iso_date: str) -> str:
    slug = link.rstrip("/").split("/")[-1] or "post"
    return f"eugeneyan-{iso_date or 'undated'}-{slug}"


def fetch() -> list[OpinionEntry]:
    text = http.fetch_text(URL)
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    out: list[OpinionEntry] = []
    for item in root.findall(".//item"):
        title = _text(item, "title").strip()
        link = _text(item, "link").strip()
        desc = _text(item, "description").strip()
        pub = _text(item, "pubDate").strip()
        if not link:
            continue
        iso = _rfc822_to_iso(pub)
        out.append(
            OpinionEntry(
                id=_stable_id(link, iso),
                source="eugeneyan",
                title=title,
                url=link,
                date=iso,
                body=desc[:1200],
            )
        )
    return out
