"""Column registry: one source of truth, no drift between consumers."""

from __future__ import annotations

import json

from lanista import columns as cols
from lanista import pareto, picker
from lanista.formatters import JsonFormatter


def test_every_lm_category_has_a_pareto_accessor():
    # The point of the registry: a column named in the glossary must be
    # usable as a Pareto axis. Adding one to LM_CATEGORIES alone is enough.
    missing = set(cols.LM_CATEGORIES) - set(pareto.COLUMN_ACCESSORS)
    assert not missing, f"columns without a Pareto accessor: {sorted(missing)}"


def test_accessors_are_bound_per_key():
    # Guards the closure-over-loop-variable trap: each accessor must read
    # its own LMArena key, not the last one in the dict.
    entry = {
        "observations": [
            {
                "source": "lmarena",
                "extracted": {
                    "lmarena_ratings": {
                        key: {"rating": float(i)}
                        for i, (key, _) in enumerate(cols.LM_CATEGORIES.values())
                    }
                },
            }
        ]
    }
    seen = [pareto.COLUMN_ACCESSORS[alias](entry) for alias in cols.LM_CATEGORIES]
    assert seen == [float(i) for i in range(len(cols.LM_CATEGORIES))]


def test_picker_rows_carry_every_lm_category():
    rows = picker._build_rows({"m-1": {"observations": [], "notes": {}}})
    assert rows, "expected one catalog row"
    missing = set(cols.LM_CATEGORIES) - set(rows[0])
    assert not missing, f"columns absent from picker table: {sorted(missing)}"


def test_short_code_maps_invert_cleanly():
    assert cols.CAP_SHORT[cols.CAPS["pdf"][0]] == "pdf"
    assert cols.MODALITY_SHORT[cols.MODALITIES["txt"][0]] == "txt"
    assert len(cols.CAP_SHORT) == len(cols.CAPS)
    assert len(cols.MODALITY_SHORT) == len(cols.MODALITIES)


def test_glossary_covers_every_block():
    g = cols.glossary()
    assert set(g) == {"lm_categories", "lm_agent", "aa_evals", "capabilities", "modalities"}
    assert set(g["lm_categories"]) == set(cols.LM_CATEGORIES)
    assert set(g["capabilities"]) == set(cols.CAPS)
    assert set(g["modalities"]) == set(cols.MODALITIES)
    assert all(m["description"] for m in g["lm_categories"].values())


def test_json_mode_emits_the_glossary(capsys):
    JsonFormatter().columns(cols.glossary(), cols.NOTES)
    payload = json.loads(capsys.readouterr().out)
    assert payload["glossary"]["lm_categories"]["lm_coding"]["lmarena_key"] == "coding"
    assert payload["notes"] == list(cols.NOTES)
