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

    # Keys are normalized so the differently-named configs merge (see
    # test_configs_with_different_naming_merge_into_one_observation).
    assert set(out) == {"claude-opus-4-7", "gpt-5-4-high"}
    opus = out["claude-opus-4-7"]["extracted"]["lmarena_ratings"]
    assert opus["overall"]["rating"] == 1480.5
    assert opus["coding"]["rating"] == 1502.1
    assert opus["creative_writing"]["rating"] == 1495.0
    # document config is namespaced to avoid collision with text/overall
    assert opus["document/overall"]["rating"] == 1510.0
    assert out["claude-opus-4-7"]["extracted"]["lmarena_publish_date"] == "2026-04-22"


def test_project_preserves_raw_rows_by_config_category_and_variant():
    raw = {"text": [_row("m", "overall", 1400)]}
    out = lmarena.project(raw)
    # Variant-keyed: a model with no parenthesised suffix lands under "default".
    raw_stored = out["m"]["raw"]["by_config"]["text"]["overall"]["default"]
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


def _agent_row(model, score, *, rank=1, cfg_rank=None):
    return {
        "model_name": model,
        "organization": "anthropic",
        "license": "Proprietary",
        "score": score,
        "score_ci_lower": score - 0.01,
        "score_ci_upper": score + 0.01,
        "observation_count": 500.0,
        "session_count": 2000.0,
        "rank": rank,
        "category": "overall",
        "leaderboard_publish_date": "2026-08-31",
    }


def test_agent_config_uses_score_and_session_count():
    out = lmarena.project({"agent": [_agent_row("Claude Opus 5 (High)", 0.1377)]})
    m = out["claude-opus-5"]["extracted"]["lmarena_ratings"]["agent/overall"]
    # Agent rows carry `score`, not `rating`, and sessions, not votes.
    assert m["rating"] == 0.1377
    assert m["votes"] == 2000
    assert m["variant"] == "high"
    assert m["ci"] == [0.1377 - 0.01, 0.1377 + 0.01]


def test_variant_headline_is_best_scoring_and_names_its_variant():
    raw = {
        "agent": [
            _agent_row("Claude Opus 5 (Max)", 0.1161, rank=2),
            _agent_row("Claude Opus 5 (High)", 0.1377, rank=1),
        ]
    }
    ext = lmarena.project(raw)["claude-opus-5"]["extracted"]
    headline = ext["lmarena_ratings"]["agent/overall"]
    assert headline["rating"] == 0.1377
    assert headline["variant"] == "high"
    # Flattening without keeping the breakdown is the mistake issue #3 names.
    assert set(ext["lmarena_variants"]["agent/overall"]) == {"high", "max"}


def test_numeric_suffix_is_a_version_stamp_not_a_variant():
    out = lmarena.project({"agent": [_agent_row("Kimi K2.7 (0813)", 0.05)]})
    assert list(out) == ["kimi-k2-7-0813"]
    assert "variant" not in out["kimi-k2-7-0813"]["extracted"]["lmarena_ratings"]["agent/overall"]


def test_configs_with_different_naming_merge_into_one_observation():
    # `text` publishes slugs, `agent` publishes display names. Both must land
    # on one entry, or every reader takes the first and drops the other.
    raw = {
        "text": [_row("claude-opus-4-8", "coding", 1501.0)],
        "agent": [_agent_row("Claude Opus 4.8", 0.095)],
    }
    out = lmarena.project(raw)
    assert list(out) == ["claude-opus-4-8"]
    ratings = out["claude-opus-4-8"]["extracted"]["lmarena_ratings"]
    assert ratings["coding"]["rating"] == 1501.0
    assert ratings["agent/overall"]["rating"] == 0.095
