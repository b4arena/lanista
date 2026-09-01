"""Smoke tests for source projectors and shipped seed files."""

from __future__ import annotations

import json
from importlib import resources

from lanista.sources import (
    aider,
    artificial_analysis,
    factory_weather,
    gkisokay,
    litellm,
    openrouter,
    pimono,
)


def test_openrouter_projection_flattens_pricing_and_context():
    raw = {
        "data": [
            {
                "id": "anthropic/claude-opus-4-7",
                "context_length": 200000,
                "pricing": {"prompt": "0.000015", "completion": "0.000075"},
                "architecture": {"input_modalities": ["text", "image"], "tokenizer": "claude"},
                "top_provider": {"max_completion_tokens": 128000},
            }
        ]
    }
    out = openrouter.project(raw)
    entry = out["anthropic/claude-opus-4-7"]
    assert entry["raw"]["id"] == "anthropic/claude-opus-4-7"
    ex = entry["extracted"]
    assert ex["context_window"] == 200000
    assert ex["pricing_per_million"]["input"] == 15.0
    assert ex["pricing_per_million"]["output"] == 75.0
    assert ex["modalities"] == ["text", "image"]


def test_litellm_projection_collects_supports_flags():
    raw = {
        "sample_spec": {"ignored": True},
        "claude-opus-4.7": {
            "max_input_tokens": 200000,
            "input_cost_per_token": 1.5e-5,
            "output_cost_per_token": 7.5e-5,
            "supports_tool_calling": True,
            "supports_vision": True,
            "supports_fake": False,
            "litellm_provider": "anthropic",
        },
    }
    out = litellm.project(raw)
    ex = out["claude-opus-4.7"]["extracted"]
    assert "tool_calling" in ex["capabilities"]
    assert "vision" in ex["capabilities"]
    assert "fake" not in ex["capabilities"]
    assert ex["pricing_per_million"]["input"] == 15.0


def test_factory_weather_regex_extracts_known_models():
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
      <item>
        <title>Switched UX Ideation from gemini-3-pro-image-preview to gpt-image-2</title>
        <description>Testing opus-4.7 vs opus-4.6 for planning.</description>
        <pubDate>Mon, 21 Apr 2026 00:00:00 +0000</pubDate>
      </item>
    </channel></rss>"""
    raw = {"xml": sample_xml, "items": factory_weather._parse_feed(sample_xml)}
    out = factory_weather.project(raw)
    assert "opus-4.7" in out
    assert "opus-4.6" in out
    assert out["opus-4.7"]["extracted"]["mention_count"] == 1


def test_aider_projection_keeps_best_pass_rate_per_model():
    raw = {
        "entries": [
            {"model": "foo", "pass_rate_2": 40.0},
            {"model": "foo", "pass_rate_2": 55.5},
            {"model": "bar", "pass_rate_2": 70.0},
            {"model": "baz"},  # no pass_rate_2, still creates entry
        ]
    }
    out = aider.project(raw)
    assert out["foo"]["extracted"]["best_pass_rate_2"] == 55.5
    assert out["foo"]["extracted"]["run_count"] == 2
    assert out["bar"]["extracted"]["best_pass_rate_2"] == 70.0
    assert out["baz"]["extracted"]["best_pass_rate_2"] is None


def test_gkisokay_projection_preserves_entry():
    raw = {
        "models": {
            "claude-opus-4-7": {
                "tier": 1,
                "strengths": ["x"],
                "weaknesses": [],
                "use_for": "y",
            }
        }
    }
    out = gkisokay.project(raw)
    assert out["claude-opus-4-7"]["raw"]["tier"] == 1
    assert out["claude-opus-4-7"]["extracted"]["use_for"] == "y"


def test_artificial_analysis_projects_api_rows():
    raw = {
        "status": 200,
        "data": [
            {
                "id": "b8fc61f7",
                "name": "Claude Opus 5 (Adaptive Reasoning, Max Effort)",
                "slug": "claude-opus-5",
                "release_date": "2026-07-24",
                "model_creator": {"slug": "anthropic"},
                "evaluations": {
                    "artificial_analysis_intelligence_index": 63.1,
                    "artificial_analysis_coding_index": 78,
                    "artificial_analysis_math_index": None,
                    "terminalbench_v2_1": 0.89,
                },
                "pricing": {
                    "price_1m_input_tokens": 5,
                    "price_1m_output_tokens": 25,
                    "price_1m_blended_3_to_1": 10,
                },
                "median_output_tokens_per_second": 48.766,
                "median_time_to_first_token_seconds": 36.304,
            }
        ],
    }
    ex = artificial_analysis.project(raw)["claude-opus-5"]["extracted"]
    # Keyed by slug, not the display name — AA's own guidance, and the slug
    # already matches lanista's canonical shape.
    assert ex["quality_index"] == 63.1
    assert ex["speed_tokens_per_sec"] == 48.766
    assert ex["ttft_sec"] == 36.304
    assert ex["pricing_per_million"] == {"input": 5, "output": 25}
    assert ex["aa_release_date"] == "2026-07-24"
    assert ex["aa_creator"] == "anthropic"
    # Nulls are dropped so a missing eval is absent, never a None column.
    assert "artificial_analysis_math_index" not in ex["aa_evaluations"]
    assert ex["aa_evaluations"]["terminalbench_v2_1"] == 0.89


def test_artificial_analysis_empty_input_is_safe():
    assert artificial_analysis.project({"data": []}) == {}
    assert artificial_analysis.project({}) == {}


def test_pimono_parse_models_roundtrip():
    ts = """
    export const MODELS = {
      anthropic: {
        "claude-opus-4-7": {
          name: "Claude Opus 4.7",
          contextWindow: 1000000,
          maxTokens: 128000,
          reasoning: true,
          input: ["text", "image"],
          cost: {input: 15, output: 75}
        } satisfies Model<"anthropic">,
      }
    };
    """
    parsed = pimono.parse_models(ts)
    assert parsed["anthropic"]["claude-opus-4-7"]["name"] == "Claude Opus 4.7"
    assert parsed["anthropic"]["claude-opus-4-7"]["contextWindow"] == 1000000


def test_gkisokay_seed_parses_and_has_tiers():
    ref = resources.files("lanista.data") / "gkisokay.seed.json"
    data = json.loads(ref.read_text(encoding="utf-8"))
    assert data.get("models"), "gkisokay seed must have models"
    for mid, entry in data["models"].items():
        assert entry.get("tier") in {1, 2, 3, 4}, f"{mid} has invalid tier"


def test_artificial_analysis_is_no_longer_curated():
    """The API replaced the hand-maintained seed.

    A leftover ``curated=True`` would make lanista read a nine-model file from
    the user's config dir instead of fetching 600+ measured models.
    """
    assert artificial_analysis.SOURCE.curated is False
    assert not (resources.files("lanista.data") / "artificial_analysis.seed.json").is_file()
