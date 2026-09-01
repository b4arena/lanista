"""Build a self-contained, citeable picker prompt.

The output is LLM-agnostic: paste into Claude, ChatGPT, Gemini, etc. It
bundles a compact catalog table, recent citeable opinion excerpts, the
task, and strict citation instructions. The receiving model must cite
every claim by either a CATALOG column name (e.g. ``lm_coding``) or an
OPINION [ID] that literally appears in the prompt — and must mark picks
that lack supporting opinion with ``[no-opinion-match]``.
"""

from __future__ import annotations

from lanista import columns as cols
from lanista import index as idx
from lanista.columns import CAP_SHORT as _CAP_SHORT
from lanista.columns import MODALITY_SHORT as _MODALITY_SHORT
from lanista.opinions import cache as ocache
from lanista.opinions.base import OpinionEntry

MAX_OPINIONS = 40
MAX_CATALOG_ROWS = 60
EXCERPT_CHARS = 400


def _compress_modalities(vals) -> str:
    if not vals:
        return "-"
    out = [_MODALITY_SHORT.get(v, v) for v in vals]
    return "+".join(out)


def _compress_caps(vals) -> str:
    if not vals:
        return "-"
    out = [_CAP_SHORT[v] for v in vals if v in _CAP_SHORT]
    return ",".join(out) if out else "-"


def _obs_extracted(obs_list: list[dict], source: str) -> dict:
    for o in obs_list:
        if o.get("source") == source:
            return o.get("extracted") or {}
    return {}


def _aider_pass(obs_list: list[dict]):
    return _obs_extracted(obs_list, "aider").get("best_pass_rate_2")


def _fmt_price(p: dict | None) -> str:
    if not p:
        return "-"
    i, o = p.get("input"), p.get("output")
    if i is None and o is None:
        return "-"
    return f"{i if i is not None else '?'}/{o if o is not None else '?'}"


def _cell(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.0f}"
    return str(v)


def _aider_cell(v) -> str:
    # Aider's ``best_pass_rate_2`` is already a percentage (e.g. 71.4), so it
    # just needs rounding — not a fraction-to-percent conversion.
    if v is None:
        return "-"
    return f"{v:.0f}%"


def _bench_value(obs: list[dict], source: str, key: str):
    """One benchmark number, whichever of the two source shapes it lives in."""
    ext = _obs_extracted(obs, source)
    if source == "lmarena":
        return ((ext.get("lmarena_ratings") or {}).get(key) or {}).get("rating")
    return (ext.get("aa_evaluations") or {}).get(key)


def _bench_cell(alias: str, v) -> str:
    """Render a benchmark value on its own scale (see columns.SCALES)."""
    if v is None:
        return "-"
    scale = cols.SCALES.get(alias, "elo")
    if scale == "rate":
        return f"{v * 100:.0f}%"
    if scale == "score":
        return f"{v:+.3f}"
    return f"{v:.0f}"


def _build_rows(models: dict) -> list[dict]:
    rows: list[dict] = []
    bench = cols.benchmark_columns()
    for mid, entry in models.items():
        obs = entry.get("observations") or []
        notes = entry.get("notes") or {}
        rows.append(
            {
                "model": mid,
                "price": _fmt_price(entry.get("pricing_per_million")),
                "ctx": entry.get("context_window"),
                "modalities": _compress_modalities(entry.get("modalities")),
                "caps": _compress_caps(entry.get("capabilities")),
                "tier": notes.get("tier") if notes.get("tier") is not None else None,
                "use_for": notes.get("use_for"),
                "aider": _aider_pass(obs),
                **{alias: _bench_value(obs, bench[alias][0], bench[alias][1]) for alias in bench},
            }
        )

    # Prefer lm_overall (whole text leaderboard). Fall back to lm_document when
    # only the small document config is available — keeps the picker useful if
    # HF's datasets-server is 500'ing on the text config.
    def _score(r: dict) -> float:
        return r["lm_overall"] or r["lm_document"] or 0

    rows.sort(key=lambda r: (-_score(r), -(r["aider"] or 0), r["model"]))
    return rows[:MAX_CATALOG_ROWS]


def _format_catalog_table(rows: list[dict]) -> str:
    # Headers and cells both come from columns.PICKER_COLUMNS. Listing them
    # twice by hand is how the table and the glossary drift apart.
    fixed = ["model", "price_$/Mtok", "ctx", "aider", "modalities", "caps", "tier"]
    headers = [*fixed, *cols.PICKER_COLUMNS]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for r in rows:
        cells = [
            r["model"][:48],
            r["price"],
            _cell(r["ctx"]),
            _aider_cell(r["aider"]),
            r["modalities"],
            r["caps"],
            _cell(r["tier"]),
            *(_bench_cell(alias, r.get(alias)) for alias in cols.PICKER_COLUMNS),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _format_tier_notes(rows: list[dict]) -> str:
    lines: list[str] = []
    for r in rows:
        tier = r.get("tier")
        use_for = r.get("use_for")
        if tier is None or not use_for or tier > 2:
            continue
        lines.append(f"[tier {tier}] {r['model']}: {use_for}")
    if not lines:
        return "(none — run `lanista fetch` or no tier-1/2 notes present)"
    return "\n".join(lines)


def _select_opinions(entries: list[OpinionEntry], limit: int) -> list[OpinionEntry]:
    return sorted(entries, key=lambda e: e.date or "", reverse=True)[:limit]


def _format_opinions(entries: list[OpinionEntry]) -> str:
    if not entries:
        return "(none — run `lanista refresh-opinions` to populate)"
    parts = []
    for e in entries:
        excerpt = e.body.replace("\n", " ").strip()
        if len(excerpt) > EXCERPT_CHARS:
            excerpt = excerpt[:EXCERPT_CHARS].rstrip() + "…"
        parts.append(
            f"[{e.id}] {e.source} — {e.date or 'n/a'} — {e.title}\n  URL: {e.url}\n  > {excerpt}"
        )
    return "\n\n".join(parts)


def build_prompt(task: str, *, top_n: int = 3) -> str:
    data = idx.load_index()
    if data is None:
        raise RuntimeError("no index yet — run `lanista fetch` first")
    rows = _build_rows(data.get("models") or {})
    opinions = _select_opinions(ocache.load_all(), MAX_OPINIONS)
    corpus_note = (
        f"Opinion corpus has {len(opinions)} recent entries."
        if opinions
        else "Opinion corpus is EMPTY — every pick must end with [no-opinion-match]."
    )

    return (
        "# lanista model-picker prompt — self-contained.\n"
        "# If you are an LLM reading this (e.g. a coding agent that just ran\n"
        "# `lanista pick ...` on the user's behalf), answer it directly using\n"
        "# only the CATALOG and OPINIONS below. Follow the INSTRUCTIONS at the\n"
        "# end. Do not call lanista again — everything you need is in this prompt.\n\n"
        f"TASK: {task}\n\n"
        f"{corpus_note}\n\n"
        f"CATALOG (top {len(rows)} by best available LMArena rating; "
        f"price is $/Mtok input/output; modalities uses txt/img/aud/vid/pdf; "
        f"caps uses pdf/cu/fn/vis/think; tier is curated 1=frontier..4=local; "
        f"lm_* columns are LMArena Elo ratings by category; '-' means no data):\n"
        f"{_format_catalog_table(rows)}\n\n"
        f"TIER 1/2 USE-CASE NOTES (curated — cite via `tier` + model id):\n"
        f"{_format_tier_notes(rows)}\n\n"
        f"RECENT PRACTITIONER OPINIONS (cite by [ID]):\n"
        f"{_format_opinions(opinions)}\n\n"
        "INSTRUCTIONS:\n"
        f"- Pick top {top_n} models for the TASK.\n"
        "- For each pick, write 2-3 sentences of justification.\n"
        "- Every claim must cite either:\n"
        "    (a) a CATALOG column name in backticks (e.g. `lm_coding`, `aider`, `ctx`, "
        "`modalities`, `caps`, `tier`), OR\n"
        "    (b) an OPINION [ID] that literally appears in the list above.\n"
        "- If no opinion in the corpus is relevant to a pick, end that pick's "
        "justification with the literal token [no-opinion-match].\n"
        "- Do NOT invent IDs or URLs. Do NOT cite models not in CATALOG.\n"
        "- Do NOT pick a model that is not in the CATALOG table above.\n\n"
        "Output format:\n\n"
        "### 1. <model-id>\n"
        "<justification with inline citations>\n\n"
        "### 2. <model-id>\n"
        "<justification>\n\n"
        f"### {top_n}. <model-id>\n"
        "<justification>\n"
    )
