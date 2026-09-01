"""Single source of truth for catalog column metadata.

The picker prompt, the Pareto CLI, the docs page, and the README all
need to describe the same columns. Defining them once here means there
is no chance of drift between, e.g., ``lanista pick`` claiming ``lm_long``
exists and ``lanista pareto`` rejecting it.

Each block exposes ``(short_or_alias, long_or_key, description)`` tuples
so callers can render any of the three columns without knowing the
others.
"""

from __future__ import annotations

# Column alias -> (LMArena category key as it appears in the source feed,
# human-readable description). Order is the order columns appear in the
# picker catalog table.
LM_CATEGORIES: dict[str, tuple[str, str]] = {
    "lm_overall": (
        "overall",
        "Whole-text leaderboard. Default quality signal lanista uses when sorting the catalog.",
    ),
    "lm_coding": (
        "coding",
        "Head-to-head wins on code-writing prompts.",
    ),
    "lm_writing": (
        "creative_writing",
        "Wins on creative / long-form writing prompts.",
    ),
    "lm_hard": (
        "hard_prompts",
        "Wins on the 'hard prompts' subset (adversarial, multi-step, ambiguous).",
    ),
    "lm_long": (
        "longer_query",
        "Wins when the user prompt itself is long.",
    ),
    "lm_english": (
        "english",
        "Wins on prompts judged to be English.",
    ),
    "lm_chinese": (
        "chinese",
        "Wins on prompts judged to be Chinese.",
    ),
    "lm_document": (
        "document/overall",
        "Wins on prompts that include an attached document (PDF, long text). "
        "Closest LMArena signal for 'can it ground answers in supplied material'.",
    ),
}


# Column alias -> (LMArena agent-leaderboard key, description).
#
# These score a model *driving a coding agent over a session*, not answering
# a prompt — the closest signal lanista has to "how does it behave as an
# agent". Scale is a signed score centred near 0 (leader ~+0.14), NOT the
# ~1500 Elo of LM_CATEGORIES. Never compare a value across the two blocks.
LM_AGENT: dict[str, tuple[str, str]] = {
    "lm_agent": (
        "agent/overall",
        "Overall agent leaderboard. Headline signal for autonomous coding sessions.",
    ),
    "lm_agent_steer": (
        "agent_steerability/overall",
        "Lands user corrections mid-session instead of ploughing on.",
    ),
    "lm_agent_tools": (
        "agent_tool_hallucination/overall",
        "Avoids inventing tools or calling them with made-up arguments.",
    ),
    "lm_agent_finish": (
        "agent_task_outcome_explicit/overall",
        "Actually finishes the task, and says so explicitly when it does.",
    ),
    "lm_agent_recovery": (
        "agent_bash_recovery_steps/overall",
        "Recovers from a failed shell command in few steps.",
    ),
    "lm_agent_sentiment": (
        "agent_praise_complaint/overall",
        "Praise-vs-complaint balance in session feedback.",
    ),
}


# Column alias -> (Artificial Analysis evaluation key, description).
#
# AA runs its own evaluations rather than aggregating vendor claims, so these
# are the independent counterweight to LMArena's crowd votes. Most are 0-1
# pass rates; the two indices are 0-100.
AA_EVALS: dict[str, tuple[str, str]] = {
    "aa_intelligence": (
        "artificial_analysis_intelligence_index",
        "AA Intelligence Index (0-100). Composite across their eval suite. "
        "Also surfaced as the rolled-up `quality_index`.",
    ),
    "aa_coding": (
        "artificial_analysis_coding_index",
        "AA Coding Index (0-100). Composite of their coding evaluations.",
    ),
    "aa_math": (
        "artificial_analysis_math_index",
        "AA Math Index (0-100).",
    ),
    "aa_terminalbench": (
        "terminalbench_hard",
        "Terminal-Bench Hard pass rate. Agentic: the model drives a shell to "
        "complete real tasks. Harness-measured — see issue #3.",
    ),
    "aa_terminalbench_v2": (
        "terminalbench_v2_1",
        "Terminal-Bench v2.1 pass rate. Newer revision, thinner coverage.",
    ),
    "aa_tau2": (
        "tau2",
        "tau-bench 2 pass rate. Tool use under a customer-service policy.",
    ),
    "aa_lcr": (
        "lcr",
        "Long-context reasoning pass rate.",
    ),
    "aa_ifbench": (
        "ifbench",
        "IFBench pass rate. Instruction following.",
    ),
}


# Short code -> (canonical capability name in the index, description).
CAPS: dict[str, tuple[str, str]] = {
    "pdf": (
        "pdf_input",
        "Provider accepts PDF files directly as input (no client-side parsing).",
    ),
    "cu": (
        "computer_use",
        "Anthropic-style 'Computer Use' — model can drive a screen/keyboard/mouse.",
    ),
    "fn": (
        "function_calling",
        "Native tool / function calling.",
    ),
    "vis": (
        "vision",
        "Image input.",
    ),
    "think": (
        "reasoning",
        "Exposed extended-thinking / reasoning mode.",
    ),
}


# Short code -> (canonical modality name in the index, description).
MODALITIES: dict[str, tuple[str, str]] = {
    "txt": ("text", "Text input."),
    "img": ("image", "Image input."),
    "aud": ("audio", "Audio input."),
    "vid": ("video", "Video input."),
    "pdf": ("pdf", "PDF input. May co-occur with the `pdf` capability."),
}


# Inverse maps used by picker.py to compress raw catalog values into the
# short codes shown in the prompt table.
CAP_SHORT: dict[str, str] = {long: short for short, (long, _) in CAPS.items()}
MODALITY_SHORT: dict[str, str] = {long: short for short, (long, _) in MODALITIES.items()}


# Free-text caveats that belong with the glossary rather than with any one
# column. Kept here so the CLI, the docs page, and any future consumer read
# the same wording.
NOTES: tuple[str, ...] = (
    "lm_* values are Elo ratings (relative, not %). ~1500 is current frontier; "
    "30-50 pt gaps are meaningful, sub-10 is noise.",
    "`tier` is curated: 1=frontier, 2=workhorse, 3=practical, 4=local-only.",
    "`aider` is the Aider polyglot `best_pass_rate_2` percentage.",
    "lm_agent_* are signed scores near 0, not Elo. Compare within the column only.",
    "aa_* come from Artificial Analysis (https://artificialanalysis.ai/). "
    "Indices are 0-100; the rest are 0-1 pass rates.",
)


#: alias -> how a cell should be rendered. Four scales coexist in the catalog
#: table and a naive ``f"{v:.0f}"`` turns every agent score and pass rate into
#: "0".
SCALES: dict[str, str] = {
    **dict.fromkeys(LM_CATEGORIES, "elo"),
    **dict.fromkeys(LM_AGENT, "score"),
    "aa_intelligence": "index",
    "aa_coding": "index",
    "aa_math": "index",
    "aa_terminalbench": "rate",
    "aa_terminalbench_v2": "rate",
    "aa_tau2": "rate",
    "aa_lcr": "rate",
    "aa_ifbench": "rate",
}


#: Benchmark columns shown in the ``lanista pick`` catalog table, in order.
#: The registry holds 22; the prompt stays legible at 11. Everything else is
#: still reachable as a Pareto axis and listed by ``lanista columns``.
PICKER_COLUMNS: tuple[str, ...] = (
    *LM_CATEGORIES,
    "lm_agent",
    "aa_coding",
    "aa_terminalbench",
)


def benchmark_columns() -> dict[str, tuple[str, str, str]]:
    """Every benchmark column as ``alias -> (source, source key, description)``.

    Lets a consumer look up where a column's number comes from without
    knowing which of the three blocks it lives in.
    """
    out: dict[str, tuple[str, str, str]] = {}
    for alias, (key, desc) in LM_CATEGORIES.items():
        out[alias] = ("lmarena", key, desc)
    for alias, (key, desc) in LM_AGENT.items():
        out[alias] = ("lmarena", key, desc)
    for alias, (key, desc) in AA_EVALS.items():
        out[alias] = ("artificial_analysis", key, desc)
    return out


def glossary() -> dict[str, dict[str, dict[str, str]]]:
    """The three column blocks as one nested, JSON-serializable payload.

    Shape is ``{block: {short: {canonical_key: value, "description": str}}}``.
    Both formatter modes render from this, so ``lanista columns`` and
    ``lanista --json columns`` can never describe different column sets.
    """
    return {
        "lm_categories": {
            alias: {"lmarena_key": key, "description": desc}
            for alias, (key, desc) in LM_CATEGORIES.items()
        },
        "lm_agent": {
            alias: {"lmarena_key": key, "description": desc}
            for alias, (key, desc) in LM_AGENT.items()
        },
        "aa_evals": {
            alias: {"aa_key": key, "description": desc} for alias, (key, desc) in AA_EVALS.items()
        },
        "capabilities": {
            short: {"capability": name, "description": desc} for short, (name, desc) in CAPS.items()
        },
        "modalities": {
            short: {"modality": name, "description": desc}
            for short, (name, desc) in MODALITIES.items()
        },
    }
