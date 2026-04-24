"""Tests for the picker prompt builder."""

from __future__ import annotations

from unittest.mock import patch

from lanista import picker
from lanista.opinions.base import OpinionEntry

INDEX = {
    "models": {
        "claude-opus-4-7": {
            "canonical_id": "claude-opus-4-7",
            "context_window": 200_000,
            "pricing_per_million": {"input": 15.0, "output": 75.0},
            "observations": [
                {
                    "source": "lmarena",
                    "extracted": {
                        "lmarena_ratings": {
                            "overall": {"rating": 1480.5, "rank": 5},
                            "coding": {"rating": 1502.0, "rank": 1},
                            "creative_writing": {"rating": 1495.0, "rank": 2},
                            "document/overall": {"rating": 1510.0, "rank": 1},
                        }
                    },
                },
                {"source": "aider", "extracted": {"best_pass_rate_2": 82.0}},
            ],
        },
        "gpt-5.4-high": {
            "canonical_id": "gpt-5.4-high",
            "context_window": 200_000,
            "pricing_per_million": {"input": 5.0, "output": 15.0},
            "observations": [
                {
                    "source": "lmarena",
                    "extracted": {
                        "lmarena_ratings": {
                            "overall": {"rating": 1472.0, "rank": 8},
                        }
                    },
                }
            ],
        },
    }
}

OPINIONS = [
    OpinionEntry(
        id="willison-2026-Apr-22-qwen36-27b",
        source="willison",
        title="Qwen3.6-27B",
        url="https://simonwillison.net/2026/Apr/22/qwen36-27b/",
        date="2026-04-22T16:45:23+00:00",
        body="Flagship-level agentic coding on a 27B model.",
    ),
]


def test_build_prompt_includes_task_catalog_table_and_citation_rules():
    with patch("lanista.picker.idx.load_index", return_value=INDEX), \
         patch("lanista.picker.ocache.load_all", return_value=OPINIONS):
        prompt = picker.build_prompt("write architecture docs", top_n=2)

    assert "TASK: write architecture docs" in prompt
    assert "claude-opus-4-7" in prompt
    assert "gpt-5.4-high" in prompt
    # Per-category LMArena columns surface as table headers.
    assert "lm_coding" in prompt and "lm_writing" in prompt and "lm_document" in prompt
    # Opinion block carries the stable ID + url.
    assert "[willison-2026-Apr-22-qwen36-27b]" in prompt
    assert "https://simonwillison.net/2026/Apr/22/qwen36-27b/" in prompt
    # Citation contract is explicit.
    assert "[no-opinion-match]" in prompt
    assert "Do NOT invent IDs" in prompt
    assert "Pick top 2 models" in prompt


def test_build_prompt_flags_empty_opinion_corpus():
    with patch("lanista.picker.idx.load_index", return_value=INDEX), \
         patch("lanista.picker.ocache.load_all", return_value=[]):
        prompt = picker.build_prompt("t")
    assert "Opinion corpus is EMPTY" in prompt


def test_build_prompt_raises_when_no_index():
    with patch("lanista.picker.idx.load_index", return_value=None):
        try:
            picker.build_prompt("t")
        except RuntimeError as e:
            assert "lanista fetch" in str(e)
        else:
            raise AssertionError("expected RuntimeError")


def test_catalog_row_sorts_by_lm_overall_desc():
    rows = picker._build_rows(INDEX["models"])
    # Opus (1480.5) outranks GPT (1472.0).
    assert rows[0]["model"] == "claude-opus-4-7"
    assert rows[1]["model"] == "gpt-5.4-high"
    assert rows[0]["lm_coding"] == 1502.0
    assert rows[0]["aider"] == 82.0


def test_aider_cell_preserves_percentage_value():
    assert picker._aider_cell(None) == "-"
    assert picker._aider_cell(71.4) == "71%"
    assert picker._aider_cell(100.0) == "100%"
