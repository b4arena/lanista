"""Unit tests for lanista.doctor — pure logic, no network (connectivity probe off)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta


def _write_index(path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _fresh_index(extra: dict | None = None) -> dict:
    base = {
        "generated_at": datetime.now(UTC).isoformat(),
        "pimono_last_commit": datetime.now(UTC).isoformat(),
        "models": {"foo-bar": {}},
        "coding_agents": {"anthropic": {}},
    }
    if extra:
        base.update(extra)
    return base


def test_missing_index_is_error(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    from lanista.doctor import run_checks

    checks = run_checks(verbose=False)
    by_name = {c.name: c for c in checks}
    assert by_name["index"].status == "error"
    assert "missing" in by_name["index"].message


def test_corrupt_index_is_fixable(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    from lanista.doctor import apply_fixes, run_checks
    from lanista.paths import index_path

    idx = index_path()
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text("not json {[")

    checks = run_checks(verbose=False)
    idx_check = next(c for c in checks if c.name == "index")
    assert idx_check.status == "error"
    assert idx_check.fixable is True

    applied = apply_fixes(checks)
    assert any("deleted corrupt index" in line for line in applied)
    assert not idx.exists()


def test_corrupt_curated_source_is_reseeded(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    from lanista.doctor import apply_fixes, run_checks
    from lanista.paths import source_path

    gk = source_path("gkisokay", curated=True)
    gk.parent.mkdir(parents=True, exist_ok=True)
    gk.write_text("not json {[")

    checks = run_checks(verbose=False)
    curated_checks = [c for c in checks if c.name.startswith("curated source")]
    broken = next(c for c in curated_checks if "gkisokay" in c.name)
    assert broken.status == "error"
    assert broken.fixable is True

    apply_fixes(checks)
    reseeded = json.loads(gk.read_text(encoding="utf-8"))
    assert reseeded.get("models"), "reseeded gkisokay must have models"


def test_stale_index_triggers_warning(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    from lanista.doctor import run_checks
    from lanista.paths import index_path

    old = datetime.now(UTC) - timedelta(days=45)
    _write_index(
        index_path(),
        _fresh_index({"generated_at": old.isoformat()}),
    )

    checks = run_checks(verbose=False)
    age_check = next(c for c in checks if c.name == "index age")
    assert age_check.status == "warn"
    assert "45d" in age_check.message


def test_pimono_age_uses_cached_timestamp(tmp_path, monkeypatch):
    """With a fresh pimono_last_commit in the index, no GitHub call is made."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    import lanista.doctor as d

    def _explode():
        raise AssertionError("doctor must not hit GitHub when index has pimono_last_commit")

    monkeypatch.setattr(d.pimono, "fetch_last_commit_age", _explode)

    from lanista.paths import index_path

    _write_index(index_path(), _fresh_index())
    checks = d.run_checks(verbose=False)
    pi = next(c for c in checks if c.name == "pi-mono age")
    assert pi.status == "ok"


def test_healthy_state_yields_no_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    from lanista.aliases import load_aliases
    from lanista.doctor import run_checks
    from lanista.paths import index_path

    load_aliases()  # seed aliases.json
    _write_index(index_path(), _fresh_index())

    checks = run_checks(verbose=False)
    assert not [c for c in checks if c.status == "error"]
