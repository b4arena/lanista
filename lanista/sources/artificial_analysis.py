"""Artificial Analysis — independent benchmarks, pricing, and speed.

AA runs its own evaluations rather than aggregating vendor claims, which
makes it the counterweight to LMArena's crowd-vote Elo: same models, a
methodology that can't be gamed by answer style.

This used to be a manual-drop source: a hand-maintained JSON blob of nine
models with one number each. The API supersedes it, so the seed and the
manual code path are gone — a curated file can no longer silently shadow
626 measured models.

The dashboard is a JS-rendered SPA, but AA publishes a free JSON API. It
needs a key (401 without one) — create an account on the Insights Platform,
generate a key, and put it in ``ARTIFICIAL_ANALYSIS_KEY``. The free tier is
capped at 1000 requests/day; ``lanista fetch`` spends one.

Attribution to https://artificialanalysis.ai/ is required by their terms
for any use of this data. lanista carries it in the README and in every
``lanista show`` observation via the ``source`` field.

Two evaluation families matter beyond the headline index:

- ``terminalbench_hard`` / ``terminalbench_v2_1`` — agentic terminal tasks.
- ``tau2`` / ``tau_banking`` — tool-use under a customer-service policy.

Both are *harness-measured*: they score a model driving a scaffold, not a
model answering a prompt. See issue #3 — lanista's index is keyed by model
alone, so these land as plain per-model numbers for now.
"""

from __future__ import annotations

import sys

from lanista import http
from lanista.source_base import Source

API_URL = "https://artificialanalysis.ai/api/v2/data/llms/models"

#: Evaluation keys promoted out of ``evaluations`` into named columns.
#: The rest still ride along in ``extracted["aa_evaluations"]``.
PROMOTED = (
    "artificial_analysis_intelligence_index",
    "artificial_analysis_coding_index",
    "artificial_analysis_math_index",
    "terminalbench_hard",
    "terminalbench_v2_1",
    "tau2",
    "lcr",
    "ifbench",
)


def fetch() -> dict | None:
    headers = http.aa_headers()
    if not headers:
        print(
            "  ! artificial_analysis: no API key. Set ARTIFICIAL_ANALYSIS_KEY "
            "(free at https://artificialanalysis.ai/insights).",
            file=sys.stderr,
        )
        return None
    blob = http.fetch_json(API_URL, headers=headers)
    if not blob or not blob.get("data"):
        return None
    return blob


def _drop_nulls(d: dict | None) -> dict:
    return {k: v for k, v in (d or {}).items() if v is not None}


def _project_api(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in rows:
        # AA's own advice: ids and slugs are stable, display names are not.
        # The slug already matches lanista's canonical shape.
        mid = row.get("slug") or row.get("id")
        if not mid:
            continue
        evals = _drop_nulls(row.get("evaluations"))
        pricing = _drop_nulls(row.get("pricing"))
        extracted: dict = {"aa_evaluations": evals}
        for key in PROMOTED:
            if key in evals:
                extracted[key] = evals[key]
        # Rolled-up index fields (see index._ROLLUP_FIELDS).
        if "artificial_analysis_intelligence_index" in evals:
            extracted["quality_index"] = evals["artificial_analysis_intelligence_index"]
        if row.get("median_output_tokens_per_second") is not None:
            extracted["speed_tokens_per_sec"] = row["median_output_tokens_per_second"]
        if row.get("median_time_to_first_token_seconds") is not None:
            extracted["ttft_sec"] = row["median_time_to_first_token_seconds"]
        if pricing:
            per_m = {}
            if pricing.get("price_1m_input_tokens") is not None:
                per_m["input"] = pricing["price_1m_input_tokens"]
            if pricing.get("price_1m_output_tokens") is not None:
                per_m["output"] = pricing["price_1m_output_tokens"]
            if per_m:
                extracted["pricing_per_million"] = per_m
            if pricing.get("price_1m_blended_3_to_1") is not None:
                extracted["aa_price_blended"] = pricing["price_1m_blended_3_to_1"]
        if row.get("release_date"):
            extracted["aa_release_date"] = row["release_date"]
        creator = (row.get("model_creator") or {}).get("slug")
        if creator:
            extracted["aa_creator"] = creator
        out[mid] = {"raw": row, "extracted": extracted}
    return out


def project(raw: dict) -> dict[str, dict]:
    rows = raw.get("data")
    return _project_api(rows) if isinstance(rows, list) else {}


SOURCE = Source(name="artificial_analysis", url=API_URL, fetch=fetch, project=project)
