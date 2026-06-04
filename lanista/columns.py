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
        "Wins on prompts that include an attached document (PDF, long text). Closest LMArena signal for 'can it ground answers in supplied material'.",
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
MODALITY_SHORT: dict[str, str] = {
    long: short for short, (long, _) in MODALITIES.items()
}
