"""Sourced model cards and explicit variant identity (no cross-variant merging)."""

from __future__ import annotations

import copy
import json

import pytest

from lanista import index as idx
from lanista import model_cards as mc
from lanista import seats as seatlib
from lanista.source_base import Source

TARGETS = ("glm-5-3", "deepseek-v4-1-flash-1017", "muse-spark-open-816b-a42b")
REQUIRED_FACTS = (
    "architecture",
    "total_params",
    "active_params",
    "input_modalities",
    "output_modalities",
    "context_window",
    "capabilities",
)


def test_packaged_cards_validate():
    assert mc.validate(mc.load_cards()) == []


@pytest.mark.parametrize("canonical", TARGETS)
def test_every_fact_is_sourced_or_unknown(canonical):
    card = mc.card_for(canonical)
    assert card is not None
    facts = card["facts"]
    for name in REQUIRED_FACTS:
        assert name in facts, f"{canonical}: {name} missing (use status unknown)"
    for name, fact in facts.items():
        if fact["value"] is None:
            assert fact["status"] == "unknown", name
        else:
            assert fact["source"].startswith("https://"), name
            assert len(fact["as_of"]) == 10, name
    for b in card["benchmarks"]:
        assert b["source"].startswith("https://")
        assert b["score"] is not None


def test_unknown_is_not_zero():
    glm = mc.card_for("glm-5-3")["facts"]["active_params"]
    assert glm["value"] is None and glm["status"] == "unknown"
    bad = {"schema": 1, "models": {"x": {"facts": {"active_params": {"value": None}}}}}
    assert any("status 'unknown'" in p for p in mc.validate(bad))


@pytest.mark.parametrize(
    "runtime_id, canonical",
    [
        ("zai/glm-5.3", "glm-5-3"),
        ("zai-org/GLM-5.3", "glm-5-3"),
        ("deepseek-ai/DeepSeek-V4.1-Flash-1017", "deepseek-v4-1-flash-1017"),
        ("meta-models/Muse-Spark-Open-816B-A42B", "muse-spark-open-816b-a42b"),
        ("meta-models-muse-spark-open-816b-a42b", "muse-spark-open-816b-a42b"),
    ],
)
def test_explicit_variant_mapping(runtime_id, canonical):
    assert mc.resolve_variant(runtime_id) == canonical


@pytest.mark.parametrize(
    "runtime_id",
    [
        # Muse Spark Open is not Muse Spark 1.x, and the bare name is not a checkpoint.
        "muse-spark-open",
        "meta/muse-spark-1.3",
        "Muse Spark 1.2",
        "muse-spark",
        # quantization must not merge into the BF16 checkpoint
        "meta-models/Muse-Spark-Open-816B-A42B-NVFP4",
        # the earlier build / unproven labels are not the 1017 build
        "deepseek-v4.1-flash",
        "deepseek-v4-1-flash-20261017",
        "deepseek-v4.1-flash-1017-fast",
        "deepseek-flash",
        # siblings of GLM-5.3
        "glm-5.3-flash",
        "glm-5.3-fp4",
        "glm-5.2",
    ],
)
def test_no_cross_variant_mapping(runtime_id):
    assert mc.resolve_variant(runtime_id) is None


def test_every_variant_has_a_source():
    for rid, spec in mc.variants().items():
        assert spec["source"].startswith("https://"), rid


def test_unproven_ids_are_never_variants():
    proven = set(mc.variant_resolver())
    from lanista.aliases import normalize

    for rid in mc.unproven():
        assert normalize(rid) not in proven, rid


def test_validate_rejects_variant_listed_as_not_same_as():
    blob = {
        "schema": 1,
        "models": {"a-1": {"facts": {}, "not_same_as": ["a-1-nvfp4"]}},
        "variants": {"org/A-1-NVFP4": {"canonical": "a-1", "source": "https://x"}},
    }
    assert any("not_same_as" in p for p in mc.validate(blob))


def test_seat_peel_never_lands_on_a_protected_variant():
    models = {"deepseek-v4-1-flash-1017": {}, "gemini-3-7-flash": {}}
    # an explicit id still resolves
    assert (
        seatlib.resolve_pin_to_index("deepseek-v4.1-flash-1017", models)
        == "deepseek-v4-1-flash-1017"
    )
    # but a suffixed pin is not peeled onto the 1017 checkpoint
    assert seatlib.resolve_pin_to_index("deepseek-v4.1-flash-1017-latest", models) is None
    # unprotected ids keep the old soft-suffix behaviour
    assert seatlib.resolve_pin_to_index("gemini-3.7-flash-high", models) == "gemini-3-7-flash"


def _fake_source(ids: list[str]) -> Source:
    def project(_raw: dict) -> dict:
        return {i: {"raw": {}, "extracted": {"context_window": 1000}} for i in ids}

    return Source(name="fake", url=None, fetch=lambda: {"x": 1}, project=project)


@pytest.fixture
def xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(idx.pimono, "fetch_last_commit_date", lambda: None)
    monkeypatch.setattr(idx.pimono, "build_coding_agents", lambda _raw: {})
    return tmp_path


def test_fetch_merges_only_proven_variants(xdg, monkeypatch):
    ids = [
        "together_ai/meta-models/Muse-Spark-Open-816B-A42B",
        "together_ai/meta-models/Muse-Spark-Open-816B-A42B-NVFP4",
        "nebius/meta-models/muse-spark-open",
        "meta/muse-spark-open",
        "meta/muse-spark-1.3",
        "together_ai/deepseek-ai/DeepSeek-V4.1-Flash-1017",
        "deepseek/deepseek-v4.1-flash-1017",
        "deepseek/deepseek-v4.1-flash",
        "together_ai/zai-org/GLM-5.3",
        "z-ai/glm-5.3",
        "z-ai/glm-5.3-flash",
    ]
    monkeypatch.setattr(idx, "SOURCES", [_fake_source(ids)])
    idx.run_fetch()
    models = idx.load_index()["models"]

    muse = models["muse-spark-open-816b-a42b"]
    assert {o["source_model_id"] for o in muse["observations"]} == {
        "together_ai/meta-models/Muse-Spark-Open-816B-A42B"
    }
    assert "muse-spark-open" in models  # kept apart: identity unproven
    assert "model_card" not in models["muse-spark-open"]
    assert "model_card" not in models["muse-spark-1-3"]
    assert "model_card" not in models["meta-models-muse-spark-open-816b-a42b-nvfp4"]

    ds = models["deepseek-v4-1-flash-1017"]
    assert {o["source_model_id"] for o in ds["observations"]} == {
        "together_ai/deepseek-ai/DeepSeek-V4.1-Flash-1017",
        "deepseek/deepseek-v4.1-flash-1017",
    }
    assert "model_card" not in models["deepseek-v4-1-flash"]

    glm = models["glm-5-3"]
    assert {o["source_model_id"] for o in glm["observations"]} == {
        "together_ai/zai-org/GLM-5.3",
        "z-ai/glm-5.3",
    }
    assert "model_card" not in models["glm-5-3-flash"]


def test_benchmarks_attach_only_to_proven_variant(xdg):
    data = {
        "models": {"muse-spark-open": {}, "muse-spark-1-3": {}, "muse-spark-open-816b-a42b": {}}
    }
    idx.apply_overlays(data)
    assert data["models"]["muse-spark-open-816b-a42b"]["model_card"]["benchmarks"]
    assert "model_card" not in data["models"]["muse-spark-open"]
    assert "model_card" not in data["models"]["muse-spark-1-3"]


def test_index_file_on_disk_stays_public(xdg, monkeypatch):
    monkeypatch.setattr(idx, "SOURCES", [_fake_source(["z-ai/glm-5.3"])])
    idx.run_fetch()
    on_disk = json.loads((xdg / "cache" / "lanista" / "model_index.json").read_text())
    assert "model_card" not in on_disk["models"]["glm-5-3"]
    assert "route_overlay" not in on_disk
    before = copy.deepcopy(mc.card_for("glm-5-3"))
    idx.load_index()
    assert mc.card_for("glm-5-3") == before
