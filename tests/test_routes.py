"""Private host-local route overlay (routes.local.json). All route ids are fake."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lanista import index as idx
from lanista import model_cards as mc
from lanista import routes as rt
from lanista.cli import app

EXAMPLE = Path(__file__).resolve().parent.parent / "docs" / "routes.local.example.json"
runner = CliRunner()


def _fact(value, note="fake note"):
    return {"value": value, "source_note": note, "as_of": "2026-01-01"}


@pytest.fixture
def xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    return tmp_path


def _write(blob) -> Path:
    p = rt.routes_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(blob) if not isinstance(blob, str) else blob, encoding="utf-8")
    return p


def test_example_file_parses_cleanly():
    ov = rt.parse_overlay(json.loads(EXAMPLE.read_text()), str(EXAMPLE))
    assert ov.loaded and ov.diagnostics == []
    assert all(r.startswith("example-") for r in ov.routes)


def test_missing_file_is_fine(xdg):
    ov = rt.load_overlay()
    assert not ov.present and ov.routes == {}


def test_overlay_adds_cost_and_limits_without_changing_public_facts(xdg):
    _write(
        {
            "schema": 1,
            "routes": {
                "example-gw/glm-5.3": {
                    "canonical": _fact("glm-5-3"),
                    "cost": _fact("budget"),
                    "pricing_per_million": _fact({"input": 0.11, "output": 0.22}),
                    "limits": _fact({"rpm": 10, "tpm": 20000}),
                    "context_window": _fact(65536),
                }
            },
        }
    )
    public_before = copy.deepcopy(mc.card_for("glm-5-3"))
    data = {"models": {"glm-5-3": {"context_window": 1048576, "observations": []}}}
    idx.apply_overlays(data)
    entry = data["models"]["glm-5-3"]

    # public facts untouched
    assert entry["model_card"] == public_before
    assert entry["context_window"] == 1048576
    assert mc.card_for("glm-5-3") == public_before

    route = entry["routes"]["example-gw/glm-5.3"]
    assert route["visibility"] == "private-local"
    f = route["fields"]
    assert f["cost"]["value"] == "budget" and f["cost"]["origin"] == "local"
    assert f["pricing_per_million"]["value"] == {"input": 0.11, "output": 0.22}
    assert f["limits"]["value"] == {"rpm": 10, "tpm": 20000}
    assert f["context_window"] == {**_fact(65536), "origin": "local"}
    # catalog fills model facts the route does not override
    assert f["modalities"]["origin"] == "catalog"
    assert f["modalities"]["value"] == {"input": ["text"], "output": ["text"]}
    assert data["route_overlay"]["route_count"] == 1


def test_unknown_price_is_not_zero_and_never_borrowed(xdg):
    _write(
        {
            "schema": 1,
            "routes": {
                "example-sub/glm-5.3": {
                    "canonical": _fact("glm-5-3"),
                    "cost": _fact("subscription"),
                },
                "example-gw/no-canonical": {"cost": _fact("unknown")},
            },
        }
    )
    sub = rt.resolve_route("example-sub/glm-5.3")
    assert sub["fields"]["cost"]["value"] == "subscription"
    # a subscription is not a token budget: no per-token price, no limits
    for name in ("pricing_per_million", "limits"):
        assert sub["fields"][name] == {"value": None, "status": "unknown", "origin": "unknown"}
    other = rt.resolve_route("example-gw/no-canonical")
    assert other["canonical"] is None
    assert other["fields"]["context_window"]["origin"] == "unknown"


def test_join_is_exact_string_match(xdg):
    _write({"schema": 1, "routes": {"example-gw/glm-5.3": {"canonical": _fact("glm-5-3")}}})
    assert rt.resolve_route("example-gw/glm-5.3") is not None
    for near in ("EXAMPLE-GW/glm-5.3", "example-gw/glm-5-3", "glm-5.3", "example-gw/glm-5.3 "):
        assert rt.resolve_route(near) is None


def test_bad_entries_are_skipped_with_diagnostics(xdg):
    _write(
        {
            "schema": 1,
            "extra": True,
            "routes": {
                "example-gw/a": {
                    "canonical": _fact("glm-5-3"),
                    "cost": _fact("free"),
                    "limits": {"value": {"rpm": -1}, "source_note": "x", "as_of": "2026-01-01"},
                    "context_window": {"value": 1000},
                    "price": _fact(1),
                    "pricing_per_million": "0.1",
                },
            },
        }
    )
    ov = rt.load_overlay()
    assert ov.loaded
    assert set(ov.routes["example-gw/a"]) == {"canonical"}
    text = "\n".join(ov.diagnostics)
    for needle in ("extra", "cost", "limits", "context_window", "price", "pricing_per_million"):
        assert needle in text


def test_invalid_json_disables_overlay(xdg):
    _write("{not json")
    ov = rt.load_overlay()
    assert ov.present and not ov.loaded and ov.routes == {}
    assert "not valid JSON" in ov.diagnostics[0]


def test_fetch_never_touches_the_overlay(xdg, monkeypatch):
    from lanista.source_base import Source

    p = _write({"schema": 1, "routes": {"example-gw/x": {"cost": _fact("budget")}}})
    before = p.read_bytes()
    src = Source(
        name="fake",
        url=None,
        fetch=lambda: {},
        project=lambda _r: {"z-ai/glm-5.3": {"raw": {}, "extracted": {}}},
    )
    monkeypatch.setattr(idx, "SOURCES", [src])
    monkeypatch.setattr(idx.pimono, "fetch_last_commit_date", lambda: None)
    monkeypatch.setattr(idx.pimono, "build_coding_agents", lambda _raw: {})
    idx.run_fetch()
    assert p.read_bytes() == before
    on_disk = (xdg / "cache" / "lanista" / "model_index.json").read_text()
    assert "example-gw" not in on_disk


def test_cli_route_json(xdg):
    _write(json.loads(EXAMPLE.read_text()))
    res = runner.invoke(app, ["--json", "route", "example-gw/glm-5.3"])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.stdout)
    r = payload["routes"]["example-gw/glm-5.3"]
    assert r["canonical"] == "glm-5-3"
    assert r["fields"]["cost"]["value"] == "budget"
    assert payload["overlay"]["loaded"] is True

    miss = runner.invoke(app, ["--json", "route", "example-gw/nope"])
    assert miss.exit_code == 1

    listing = runner.invoke(app, ["--json", "routes"])
    assert listing.exit_code == 0
    assert set(json.loads(listing.stdout)["routes"]) == set(
        json.loads(EXAMPLE.read_text())["routes"]
    )


def test_doctor_reports_overlay_state(xdg):
    from lanista import doctor

    def overlay_check():
        return next(c for c in doctor.run_checks() if c.name == "route overlay")

    assert "not present" in overlay_check().message
    _write(json.loads(EXAMPLE.read_text()))
    c = overlay_check()
    assert c.status == "ok" and "loaded 3" in c.message
    _write("{bad")
    assert overlay_check().status == "warn"
