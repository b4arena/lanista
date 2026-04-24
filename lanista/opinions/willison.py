"""Simon Willison's LLM-tagged Atom feed.

Feed URL yields only entries tagged ``llms`` — practitioner-grade sentiment
on newly released models, local-inference nuances, and model-versus-model
comparisons. The feed is plain Atom XML with html-encoded ``<summary>``.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from lanista import http
from lanista.opinions.base import OpinionEntry

URL = "https://simonwillison.net/tags/llms.atom"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"/(\d{4})/([A-Za-z]+)/(\d+)/([^/#?]+)")


def _strip_html(html: str) -> str:
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()


def _text(node, path) -> str:
    el = node.find(path, ATOM)
    if el is None:
        return ""
    return el.text or ""


def _stable_id(link: str, published: str) -> str:
    m = _SLUG_RE.search(link)
    if m:
        year, mon, day, slug = m.groups()
        return f"willison-{year}-{mon}-{day}-{slug}"
    return f"willison-{(published or 'unknown')[:10]}-{abs(hash(link)) % 10**6}"


def fetch() -> list[OpinionEntry]:
    text = http.fetch_text(URL)
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    out: list[OpinionEntry] = []
    for e in root.findall("a:entry", ATOM):
        title = _text(e, "a:title").strip()
        published = _text(e, "a:published").strip()
        summary_html = _text(e, "a:summary")
        link_el = e.find("a:link", ATOM)
        link = link_el.get("href") if link_el is not None else ""
        if not link:
            continue
        body = _strip_html(summary_html)[:1200]
        out.append(
            OpinionEntry(
                id=_stable_id(link, published),
                source="willison",
                title=title,
                url=link,
                date=published,
                body=body,
            )
        )
    return out
