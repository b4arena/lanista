"""Build a self-contained, citeable picker prompt.

The output is LLM-agnostic: paste into Claude, ChatGPT, Gemini, etc. It
bundles a compact catalog table, recent citeable opinion excerpts, the
task, and strict citation instructions. The receiving model must cite
every claim by either a CATALOG column name (e.g. ``lm_coding``) or an
OPINION [ID] that literally appears in the prompt — and must mark picks
that lack supporting opinion with ``[no-opinion-match]``.
"""

from __future__ import annotations

from lanista import index as idx
from lanista.opinions import cache as ocache
from lanista.opinions.base import OpinionEntry

MAX_OPINIONS = 40
MAX_CATALOG_ROWS = 60
EXCERPT_CHARS = 400


def _obs_extracted(obs_list: list[dict], source: str) -> dict:
    for o in obs_list:
        if o.get("source") == source:
            return o.get("extracted") or {}
    return {}


def _lm_rating(ratings: dict, key: str):
    entry = (ratings or {}).get(key) or {}
    return entry.get("rating")


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


def _build_rows(models: dict) -> list[dict]:
    rows: list[dict] = []
    for mid, entry in models.items():
        obs = entry.get("observations") or []
        lm = _obs_extracted(obs, "lmarena").get("lmarena_ratings") or {}
        rows.append(
            {
                "model": mid,
                "price": _fmt_price(entry.get("pricing_per_million")),
                "ctx": entry.get("context_window"),
                "aider": _aider_pass(obs),
                "lm_overall": _lm_rating(lm, "overall"),
                "lm_coding": _lm_rating(lm, "coding"),
                "lm_writing": _lm_rating(lm, "creative_writing"),
                "lm_hard": _lm_rating(lm, "hard_prompts"),
                "lm_long": _lm_rating(lm, "longer_query"),
                "lm_english": _lm_rating(lm, "english"),
                "lm_chinese": _lm_rating(lm, "chinese"),
                "lm_document": _lm_rating(lm, "document/overall"),
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
    headers = [
        "model", "price_$/Mtok", "ctx", "aider",
        "lm_overall", "lm_coding", "lm_writing",
        "lm_hard", "lm_long", "lm_english", "lm_chinese", "lm_document",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for r in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    r["model"][:48],
                    r["price"],
                    _cell(r["ctx"]),
                    _aider_cell(r["aider"]),
                    _cell(r["lm_overall"]),
                    _cell(r["lm_coding"]),
                    _cell(r["lm_writing"]),
                    _cell(r["lm_hard"]),
                    _cell(r["lm_long"]),
                    _cell(r["lm_english"]),
                    _cell(r["lm_chinese"]),
                    _cell(r["lm_document"]),
                ]
            )
            + " |"
        )
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
            f"[{e.id}] {e.source} — {e.date or 'n/a'} — {e.title}\n"
            f"  URL: {e.url}\n"
            f"  > {excerpt}"
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
        f"price is $/Mtok input/output; lm_* columns are LMArena Elo ratings "
        f"by category; '-' means no data):\n"
        f"{_format_catalog_table(rows)}\n\n"
        f"RECENT PRACTITIONER OPINIONS (cite by [ID]):\n"
        f"{_format_opinions(opinions)}\n\n"
        "INSTRUCTIONS:\n"
        f"- Pick top {top_n} models for the TASK.\n"
        "- For each pick, write 2-3 sentences of justification.\n"
        "- Every claim must cite either:\n"
        "    (a) a CATALOG column name in backticks (e.g. `lm_coding`, `aider`, `ctx`), OR\n"
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
