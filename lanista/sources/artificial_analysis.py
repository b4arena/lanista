"""Artificial Analysis — independent benchmarks, pricing, and speed.

AA runs its own evaluations rather than aggregating vendor claims, which
makes it the counterweight to LMArena's crowd-vote Elo: same models, a
methodology that can't be gamed by answer style.

This used to be a manual-drop source: a hand-maintained JSON blob of nine
models with one number each. The API supersedes it, so the seed and the
manual code path are gone — a curated file can no longer silently shadow
626 measured models.

The dashboard is a JS-rendered SPA, but AA publishes a JSON API. The legacy
``/api/v2/data/llms/models`` endpoint was retired on 2026-11-04 (410 Gone);
this module uses its free replacement, ``/api/v2/language/models/free``
(https://artificialanalysis.ai/data-api/migrate-v2-data). It accepts any
valid key — create an account on the Insights Platform, generate a key, and
put it in ``ARTIFICIAL_ANALYSIS_KEY``. The free tier allows 100 requests per
24h window; the list is paginated (200 per page), so ``lanista fetch`` spends
one request per page (about four).

The free endpoint exposes far fewer evaluations than the legacy one: the
Intelligence Index and six capability indices. Coding, math, Terminal-Bench,
tau2, LCR and IFBench are Pro-only (``/api/v2/language/models``) or gone, so
the matching ``aa_*`` columns stay empty until a Pro key is wired in.

Attribution to https://artificialanalysis.ai/ is required by their terms
for any use of this data. lanista carries it in the README and in every
``lanista show`` observation via the ``source`` field.
"""

from __future__ import annotations

import sys

from lanista import http
from lanista.source_base import Source

API_URL = "https://artificialanalysis.ai/api/v2/language/models/free"
#: Hard stop so a misbehaving ``has_more`` can't burn the daily quota.
MAX_PAGES = 10

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
    rows: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        blob = http.fetch_json(f"{API_URL}?page={page}", headers=headers)
        if not blob or not isinstance(blob.get("data"), list):
            # A failure mid-way returns what we have; a failure on page 1 is None.
            break
        rows.extend(blob["data"])
        if not (blob.get("pagination") or {}).get("has_more"):
            break
    return {"data": rows} if rows else None


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
        # ``performance`` is deprecated and returns null from 2026-12-10;
        # ``performance_v3`` only has means, so it is the fallback.
        perf = row.get("performance") or {}
        perf3 = row.get("performance_v3") or {}
        speed = perf.get("median_output_tokens_per_second")
        if speed is None:
            speed = perf3.get("mean_output_tokens_per_second")
        if speed is not None:
            extracted["speed_tokens_per_sec"] = speed
        ttft = perf.get("median_time_to_first_token_seconds")
        if ttft is None:
            ttft = perf3.get("mean_time_to_first_token_seconds")
        if ttft is not None:
            extracted["ttft_sec"] = ttft
        if pricing:
            per_m = {}
            if pricing.get("price_1m_input_tokens") is not None:
                per_m["input"] = pricing["price_1m_input_tokens"]
            if pricing.get("price_1m_output_tokens") is not None:
                per_m["output"] = pricing["price_1m_output_tokens"]
            if per_m:
                extracted["pricing_per_million"] = per_m
            # The free endpoint has no blended price; derive AA's 3:1 definition.
            if len(per_m) == 2:
                extracted["aa_price_blended"] = (3 * per_m["input"] + per_m["output"]) / 4
        if row.get("release_date"):
            extracted["aa_release_date"] = row["release_date"]
        # The new API has no creator slug, only a display name.
        creator = (row.get("model_creator") or {}).get("name")
        if creator:
            extracted["aa_creator_name"] = creator
        out[mid] = {"raw": row, "extracted": extracted}
    return out


def project(raw: dict) -> dict[str, dict]:
    rows = raw.get("data")
    return _project_api(rows) if isinstance(rows, list) else {}


SOURCE = Source(name="artificial_analysis", url=API_URL, fetch=fetch, project=project)
