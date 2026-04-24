"""Routing: string triggers for numeric-tradeoff tasks."""

from __future__ import annotations

from lanista import routing


def test_positive_matches():
    for task in [
        "cheapest model that still hits 70% on aider",
        "best coding quality per dollar",
        "find the sweet spot for coding tasks",
        "fastest model for autocomplete",
        "under $5 per million tokens",
        "pareto of price vs quality",
        "coding quality vs cost trade-off",
    ]:
        assert routing.is_numeric_tradeoff(task), task
        assert routing.suggest_alternative(task) is not None


def test_profile_triggers_point_to_profiles_command():
    for task in [
        "find the sweet spot for coding",
        "flagship model for hard math",
        "budget option under $1",
        "a balanced pick for long context work",
    ]:
        hint = routing.suggest_alternative(task)
        assert hint is not None
        assert "lanista profiles" in hint, task


def test_plain_tradeoff_points_to_pareto_command():
    hint = routing.suggest_alternative("cheapest model that still hits 70% on aider")
    assert hint is not None
    assert "lanista pareto" in hint


def test_negative_matches():
    for task in [
        "write architecture docs for a python service",
        "multi-file TypeScript refactor",
        "summarize a PDF",
        "creative writing for a kids story",
    ]:
        assert not routing.is_numeric_tradeoff(task), task
        assert routing.suggest_alternative(task) is None
