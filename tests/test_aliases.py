"""Unit tests for canonical-id resolution across source naming conventions."""

from __future__ import annotations

import json
from importlib import resources

from lanista import aliases


def test_normalize_strips_provider_and_collapses_punctuation():
    assert aliases.normalize("anthropic/claude-opus-4.7") == "claude-opus-4-7"
    assert aliases.normalize("Claude Opus 4.7") == "claude-opus-4-7"
    assert aliases.normalize("opus-4.7") == "opus-4-7"


def test_build_resolver_maps_every_alias_to_canonical():
    resolver = aliases.build_resolver(
        {"claude-opus-4-7": ["anthropic/claude-opus-4-7", "Claude Opus 4.7", "opus-4.7"]}
    )
    assert aliases.resolve("anthropic/claude-opus-4.7", resolver) == "claude-opus-4-7"
    assert aliases.resolve("Claude Opus 4.7", resolver) == "claude-opus-4-7"
    assert aliases.resolve("opus-4.7", resolver) == "claude-opus-4-7"


def test_unknown_ids_pass_through_normalized():
    """Unknown ids still collapse so two unknown-but-equivalent spellings merge."""
    resolver = aliases.build_resolver({})
    assert aliases.resolve("unknown/model-1.0", resolver) == "model-1-0"
    assert aliases.resolve("Model 1.0", resolver) == "model-1-0"


def test_seed_parses_and_is_non_empty():
    ref = resources.files("lanista.data") / "aliases.seed.json"
    data = json.loads(ref.read_text(encoding="utf-8"))
    assert "aliases" in data
    assert data["aliases"], "seed must contain at least one canonical id"


def test_load_aliases_seeds_user_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from lanista.paths import aliases_path

    target = aliases_path()
    assert not target.exists()

    data = aliases.load_aliases()
    assert target.exists()
    assert data.get("aliases")
