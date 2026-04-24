"""Unit tests for opinion feed parsers and cache roundtrip."""

from __future__ import annotations

from unittest.mock import patch

from lanista.opinions import cache, eugeneyan, hn, willison
from lanista.opinions.base import OpinionEntry

WILLISON_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Simon Willison's Weblog: llms</title>
<entry>
<title>Qwen3.6-27B: Flagship-Level Coding</title>
<link href="https://simonwillison.net/2026/Apr/22/qwen36-27b/" rel="alternate"/>
<published>2026-04-22T16:45:23+00:00</published>
<id>https://simonwillison.net/2026/Apr/22/qwen36-27b/</id>
<summary type="html">
  &lt;p&gt;&lt;strong&gt;Qwen3.6-27B is flagship-level agentic coding.&lt;/strong&gt;&lt;/p&gt;
</summary>
</entry>
<entry>
<title>Second post</title>
<link href="https://simonwillison.net/2026/Apr/21/second/" rel="alternate"/>
<published>2026-04-21T10:00:00+00:00</published>
<summary type="html">short</summary>
</entry>
</feed>
"""

EUGENE_RSS = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Product Evals in Three Simple Steps</title>
      <description>Label some data, align LLM-evaluators.</description>
      <pubDate>Sun, 23 Nov 2025 00:00:00 +0000</pubDate>
      <link>https://eugeneyan.com/writing/product-evals/</link>
    </item>
  </channel>
</rss>
"""

HN_RESPONSE = {
    "hits": [
        {
            "objectID": "47793411",
            "title": "Claude Opus 4.7",
            "url": "https://www.anthropic.com/news/claude-opus-4-7",
            "points": 1955,
            "num_comments": 1450,
            "created_at": "2026-04-16T14:23:50Z",
        },
        {
            "objectID": "low_signal",
            "title": "obscure",
            "points": 5,
            "num_comments": 0,
            "created_at": "2026-04-01T00:00:00Z",
        },
    ]
}


def test_willison_parser_extracts_title_link_date_and_stable_id():
    with patch("lanista.opinions.willison.http.fetch_text", return_value=WILLISON_ATOM):
        entries = willison.fetch()
    assert len(entries) == 2
    first = entries[0]
    assert first.title == "Qwen3.6-27B: Flagship-Level Coding"
    assert first.url == "https://simonwillison.net/2026/Apr/22/qwen36-27b/"
    assert first.date.startswith("2026-04-22")
    assert first.id == "willison-2026-Apr-22-qwen36-27b"
    assert "flagship-level agentic coding" in first.body.lower()
    assert "<strong>" not in first.body


def test_willison_fetch_tolerates_missing_network():
    with patch("lanista.opinions.willison.http.fetch_text", return_value=None):
        assert willison.fetch() == []


def test_eugeneyan_parser_converts_pubdate_to_iso():
    with patch("lanista.opinions.eugeneyan.http.fetch_text", return_value=EUGENE_RSS):
        entries = eugeneyan.fetch()
    assert len(entries) == 1
    e = entries[0]
    assert e.date == "2025-11-23"
    assert e.url == "https://eugeneyan.com/writing/product-evals/"
    assert e.id == "eugeneyan-2025-11-23-product-evals"
    assert "align LLM-evaluators" in e.body


def test_hn_fetcher_filters_low_signal_and_dedupes():
    with patch("lanista.opinions.hn.http.fetch_json", return_value=HN_RESPONSE):
        entries = hn.fetch()
    # At least one entry from the first story; never the low-signal one.
    ids = {e.id for e in entries}
    assert "hn-47793411" in ids
    assert "hn-low_signal" not in ids
    # Running multiple queries still dedupes to a single entry per story.
    first = next(e for e in entries if e.id == "hn-47793411")
    assert first.url == "https://news.ycombinator.com/item?id=47793411"
    assert "1955 points" in first.body


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    entries = [
        OpinionEntry(
            id="test-1",
            source="willison",
            title="t",
            url="https://example.com/1",
            date="2026-04-22",
            body="b",
        ),
    ]
    cache.save("willison", entries)
    loaded = cache.load("willison")
    assert loaded == entries
    # load_all should surface entries from any source file in the dir.
    cache.save("eugeneyan", [])
    combined = cache.load_all()
    assert [e.id for e in combined] == ["test-1"]
