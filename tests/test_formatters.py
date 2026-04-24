"""JSON formatter smoke tests: every shape emits valid JSON."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from lanista.doctor import Check
from lanista.formatters import JsonFormatter
from lanista.index import FetchReport


@pytest.fixture
def fmt() -> JsonFormatter:
    return JsonFormatter()


def _parse_stdout(capsys) -> dict:
    captured = capsys.readouterr().out
    return json.loads(captured)


def test_status_none_emits_no_index(fmt, capsys):
    fmt.status(None)
    payload = _parse_stdout(capsys)
    assert payload["status"] == "no_index"
    assert "index_path" in payload
    assert "sources_dir" in payload


def test_status_ok_counts_tiers_and_sources(fmt, capsys):
    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": {
            "a-1": {"notes": {"tier": 1}},
            "b-2": {"notes": {"tier": 1}},
            "c-3": {"notes": {"tier": 3}},
        },
        "coding_agents": {"x": {}},
        "source_counts": {"openrouter": 300, "gkisokay": 3},
    }
    fmt.status(data)
    payload = _parse_stdout(capsys)
    assert payload["model_count"] == 3
    assert payload["tier_counts"] == {"1": 2, "3": 1}
    assert payload["source_counts"]["openrouter"] == 300


def test_fetch_report_shape(fmt, capsys):
    report = FetchReport(
        source_counts={"openrouter": 300, "litellm": 200, "gkisokay": 18},
        source_errors={"factory_weather": "fetch failed"},
        pimono_age=timedelta(days=12),
        index_path="/tmp/x",
        index_size_kb=42,
        total_models=500,
    )
    fmt.fetch_report(report, stale=False)
    payload = _parse_stdout(capsys)
    assert payload["source_counts"]["openrouter"] == 300
    assert payload["source_errors"]["factory_weather"] == "fetch failed"
    assert payload["pimono_age_days"] == 12
    assert payload["total_models"] == 500


def test_doctor_buckets_by_status(fmt, capsys):
    checks = [
        Check(name="a", status="error", message="bad"),
        Check(name="b", status="warn", message="meh"),
        Check(name="c", status="ok", message="fine"),
        Check(name="d", status="ok", message="fine"),
    ]
    fmt.doctor(checks, fixes_applied=None)
    payload = _parse_stdout(capsys)
    assert payload["summary"] == {"errors": 1, "warnings": 1, "info": 2}
    assert len(payload["errors"]) == 1
    assert len(payload["info"]) == 2


def test_tier_roundtrip(fmt, capsys):
    fmt.tier(2, [{"id": "foo", "strengths": ["fast"], "weaknesses": [], "use_for": None}])
    payload = _parse_stdout(capsys)
    assert payload["tier"] == 2
    assert payload["count"] == 1
    assert payload["models"][0]["id"] == "foo"


def test_next_steps_suppressed_in_json(fmt, capsys):
    fmt.next_steps([("lanista fetch", "do it")])
    assert capsys.readouterr().out == ""
