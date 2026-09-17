"""Test that `lanista show` falls back to normalized matching.

'gemini-3.1-pro' (dots) should match catalog id 'gemini-3-1-pro' (dashes).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from typer.testing import CliRunner

from lanista.cli import app

runner = CliRunner()


def _seed_index(tmp_path, models: dict) -> None:
    index_path = tmp_path / "cache" / "lanista" / "model_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "pimono_last_commit": datetime.now(UTC).isoformat(),
                "models": models,
                "coding_agents": {},
            }
        ),
        encoding="utf-8",
    )


def test_show_raw_substring(tmp_path, monkeypatch):
    """Direct substring match works as before."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    _seed_index(tmp_path, {"gemini-3-1-pro": {"context_window": 1_000_000}})
    result = runner.invoke(app, ["show", "gemini-3-1-pro"])
    assert result.exit_code == 0
    assert "gemini-3-1-pro" in result.output


def test_show_normalized_fallback(tmp_path, monkeypatch):
    """Dotted provider name 'gemini-3.1-pro' matches dashed catalog id."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    _seed_index(tmp_path, {"gemini-3-1-pro": {"context_window": 1_000_000}})
    result = runner.invoke(app, ["show", "gemini-3.1-pro"])
    assert result.exit_code == 0
    assert "gemini-3-1-pro" in result.output


def test_show_no_match_still_errors(tmp_path, monkeypatch):
    """Completely unknown substring still exits 1."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    _seed_index(tmp_path, {"gemini-3-1-pro": {}})
    result = runner.invoke(app, ["show", "nonexistent-model-xyz"])
    assert result.exit_code == 1
    assert "no match" in result.output
