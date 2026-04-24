"""Pareto frontier: deterministic skyline over quality/cost pairs."""

from __future__ import annotations

from lanista import pareto


def test_frontier_drops_strictly_dominated():
    # B dominates A and C on both axes (higher q, lower c).
    pairs = [("A", 10.0, 5.0), ("B", 20.0, 4.0), ("C", 15.0, 10.0)]
    assert pareto.pareto_frontier(pairs) == {"B"}

def test_classic_three_point_case():
    # Higher-quality is better; lower-cost is better.
    # A: cheap+bad, B: mid+mid, C: premium+expensive, D: dominated (low q, high c)
    pairs = [
        ("A", 10.0, 1.0),
        ("B", 15.0, 5.0),
        ("C", 20.0, 10.0),
        ("D", 12.0, 8.0),
    ]
    front = pareto.pareto_frontier(pairs)
    assert front == {"A", "B", "C"}


def test_ties_on_both_axes_are_kept():
    pairs = [("A", 10.0, 5.0), ("B", 10.0, 5.0)]
    assert pareto.pareto_frontier(pairs) == {"A", "B"}


def test_equal_quality_lower_cost_dominates():
    pairs = [("A", 10.0, 3.0), ("B", 10.0, 5.0)]
    assert pareto.pareto_frontier(pairs) == {"A"}


def test_extract_pairs_skips_missing_values():
    models = {
        "has-both": {
            "pricing_per_million": {"input": 2.0, "output": 10.0},
            "observations": [
                {"source": "lmarena", "extracted": {"lmarena_ratings": {"coding": {"rating": 1500}}}},
            ],
        },
        "no-price": {
            "observations": [
                {"source": "lmarena", "extracted": {"lmarena_ratings": {"coding": {"rating": 1400}}}},
            ],
        },
        "no-rating": {"pricing_per_million": {"input": 1.0, "output": 2.0}, "observations": []},
    }
    pairs = pareto.extract_pairs(models, "lm_coding", "price_input")
    assert pairs == [("has-both", 1500.0, 2.0)]


def test_filter_models_by_capability():
    models = {
        "a": {"capabilities": ["pdf_input", "vision"]},
        "b": {"capabilities": ["vision"]},
        "c": {"capabilities": []},
        "d": {},
    }
    out = pareto.filter_models(models, require_cap="pdf_input")
    assert set(out.keys()) == {"a"}


def test_filter_models_by_min_ctx():
    models = {
        "a": {"context_window": 200_000},
        "b": {"context_window": 32_000},
        "c": {},
    }
    out = pareto.filter_models(models, min_ctx=128_000)
    assert set(out.keys()) == {"a"}


def test_profiles_picks_three_anchors():
    # Frontier: A (cheapest, worst), C (mid), E (priciest, best).
    pairs = [
        ("A", 1000.0, 0.1),
        ("C", 1400.0, 1.0),
        ("E", 1500.0, 5.0),
    ]
    frontier = pareto.pareto_frontier(pairs)
    assert frontier == {"A", "C", "E"}
    picks = pareto.find_profiles(pairs, frontier)
    assert picks["flagship"][0] == "E"
    assert picks["budget"][0] == "A"
    # Balanced should land on C (the knee — neither extreme).
    assert picks["balanced"][0] == "C"


def test_profiles_collapses_when_frontier_has_one_point():
    pairs = [("A", 100.0, 1.0), ("B", 50.0, 10.0)]  # A dominates B.
    frontier = pareto.pareto_frontier(pairs)
    assert frontier == {"A"}
    picks = pareto.find_profiles(pairs, frontier)
    assert picks["flagship"][0] == "A"
    assert picks["balanced"][0] == "A"
    assert picks["budget"][0] == "A"


def test_profiles_empty_frontier_returns_none():
    picks = pareto.find_profiles([], set())
    assert picks == {"flagship": None, "balanced": None, "budget": None}


def test_knee_prefers_elbow_over_extremes():
    # Two near-extremes plus a clear elbow in the middle.
    pairs = [
        ("cheap", 1000.0, 0.01),
        ("elbow", 1450.0, 0.30),
        ("premium", 1500.0, 10.0),
    ]
    frontier = pareto.pareto_frontier(pairs)
    picks = pareto.find_profiles(pairs, frontier)
    # Elbow wins: it keeps most of the quality for a fraction of the premium cost.
    assert picks["balanced"][0] == "elbow"


def test_to_csv_marks_frontier():
    pairs = [("A", 10.0, 1.0), ("B", 5.0, 10.0)]
    csv = pareto.to_csv(pairs, {"A"}, quality_name="lm_coding", cost_name="price_input")
    assert csv.startswith("model,lm_coding,price_input,on_frontier\n")
    assert "A,10.0,1.0,true" in csv
    assert "B,5.0,10.0,false" in csv
