"""Seat allowlists: pin → catalog matching and provider filters."""

from __future__ import annotations

from lanista import seats as seatlib
from lanista.seats import Seat, SeatPin


def test_parse_seats_from_blob():
    blob = {
        "seats": {
            "demo": {
                "description": "demo seat",
                "models": [
                    {"provider": "github-copilot", "pin": "gpt-5.4-mini", "role": "daily"},
                    {"provider": "xai", "pin": "grok-4.6", "engine": "pi"},
                    "bare-id",
                ],
            }
        }
    }
    parsed = seatlib.parse_seats(blob)
    assert "demo" in parsed
    seat = parsed["demo"]
    assert seat.description == "demo seat"
    assert len(seat.pins) == 3
    assert seat.pins[0].pin == "gpt-5.4-mini"
    assert seat.pins[2].provider == "*"
    assert seat.pins[2].pin == "bare-id"


def test_resolve_pin_normalizes_dots_and_aliases():
    models = {
        "gpt-5-4-mini": {"pricing_per_million": {"input": 0.75}},
        "claude-opus-4-6": {},
        "gpt-oss-120b": {},
    }
    assert seatlib.resolve_pin_to_index("gpt-5.4-mini", models) == "gpt-5-4-mini"
    assert seatlib.resolve_pin_to_index("claude-opus-4.6", models) == "claude-opus-4-6"
    # soft suffix peel
    assert (
        seatlib.resolve_pin_to_index("claude-opus-4-6-thinking", models) == "claude-opus-4-6"
    )
    assert seatlib.resolve_pin_to_index("gpt-oss-120b-medium", models) == "gpt-oss-120b"
    assert seatlib.resolve_pin_to_index("totally-missing", models) is None


def test_match_seat_filters_provider_and_models():
    models = {
        "gpt-5-4-mini": {"x": 1},
        "grok-4-6": {"x": 2},
        "claude-sonnet-5": {"x": 3},
        "other": {"x": 9},
    }
    seat = Seat(
        id="herdr-agents",
        pins=[
            SeatPin("github-copilot", "gpt-5.4-mini"),
            SeatPin("xai", "grok-4.6"),
            SeatPin("github-copilot", "claude-sonnet-5"),
            SeatPin("github-copilot", "does-not-exist"),
        ],
    )
    all_match = seatlib.match_seat(models, seat)
    assert set(all_match.models) == {"gpt-5-4-mini", "grok-4-6", "claude-sonnet-5"}
    assert len(all_match.unresolved) == 1
    assert all_match.unresolved[0].pin == "does-not-exist"

    copilot = seatlib.match_seat(models, seat, provider="github-copilot")
    assert set(copilot.models) == {"gpt-5-4-mini", "claude-sonnet-5"}
    assert "grok-4-6" not in copilot.models
    assert seatlib.format_pin(copilot.pin_by_index["gpt-5-4-mini"], "gpt-5-4-mini") == (
        "github-copilot/gpt-5.4-mini"
    )


def test_seed_contains_herdr_agents():
    blob = seatlib.load_seed()
    assert "herdr-agents" in blob["seats"]
    models = blob["seats"]["herdr-agents"]["models"]
    providers = {m["provider"] for m in models}
    assert {"github-copilot", "xai", "openai-codex", "agy"} <= providers
    pins = {m["pin"] for m in models}
    assert "gpt-5.4-mini" in pins
    assert "grok-4.6" in pins
    assert "claude-sonnet-4-6" in pins
