"""Unit tests for the LMArena source projection."""

from __future__ import annotations

from lanista.sources import lmarena


def _row(model, category, rating, *, cfg_rank=1):
    return {
        "model_name": model,
        "organization": "openai" if "gpt" in model else "anthropic",
        "license": "Proprietary",
        "rating": rating,
        "rank": cfg_rank,
        "vote_count": 1000,
        "category": category,
        "leaderboard_publish_date": "2026-04-22",
    }


def test_project_groups_by_model_and_flattens_ratings():
    raw = {
        "text": [
            _row("claude-opus-4-7", "overall", 1480.5),
            _row("claude-opus-4-7", "coding", 1502.1),
            _row("claude-opus-4-7", "creative_writing", 1495.0),
            _row("gpt-5.4-high", "overall", 1472.7),
        ],
        "document": [
            _row("claude-opus-4-7", "overall", 1510.0),
        ],
    }

    out = lmarena.project(raw)

    assert set(out) == {"claude-opus-4-7", "gpt-5.4-high"}
    opus = out["claude-opus-4-7"]["extracted"]["lmarena_ratings"]
    assert opus["overall"]["rating"] == 1480.5
    assert opus["coding"]["rating"] == 1502.1
    assert opus["creative_writing"]["rating"] == 1495.0
    # document config is namespaced to avoid collision with text/overall
    assert opus["document/overall"]["rating"] == 1510.0
    assert out["claude-opus-4-7"]["extracted"]["lmarena_publish_date"] == "2026-04-22"


def test_project_preserves_raw_rows_by_config_and_category():
    raw = {"text": [_row("m", "overall", 1400)]}
    out = lmarena.project(raw)
    raw_stored = out["m"]["raw"]["by_config"]["text"]["overall"]
    assert raw_stored["rating"] == 1400
    assert raw_stored["model_name"] == "m"


def test_project_ignores_rows_missing_model_or_category():
    raw = {
        "text": [
            {"model_name": "x", "category": None, "rating": 1},
            {"model_name": None, "category": "overall", "rating": 1},
            _row("ok", "overall", 1000),
        ]
    }
    out = lmarena.project(raw)
    assert list(out) == ["ok"]


def test_project_empty_input_is_safe():
    assert lmarena.project({}) == {}
    assert lmarena.project({"text": []}) == {}
