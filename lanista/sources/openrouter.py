"""OpenRouter /api/v1/models — live JSON catalog of every routed model."""

from __future__ import annotations

from lanista import http
from lanista.source_base import Source

URL = "https://openrouter.ai/api/v1/models"


def fetch() -> dict | None:
    return http.fetch_json(URL)


def _per_million(v) -> float | None:
    return round(float(v) * 1_000_000, 4) if v else None


def project(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for m in raw.get("data", []):
        mid = m["id"]
        p = m.get("pricing") or {}
        arch = m.get("architecture") or {}
        tp = m.get("top_provider") or {}
        out[mid] = {
            "raw": m,
            "extracted": {
                "context_window": m.get("context_length"),
                "max_output": tp.get("max_completion_tokens"),
                "pricing_per_million": {
                    "input": _per_million(p.get("prompt")),
                    "output": _per_million(p.get("completion")),
                    "cache_read": _per_million(p.get("input_cache_read")),
                    "cache_write": _per_million(p.get("input_cache_write")),
                },
                "modalities": arch.get("input_modalities"),
                "tokenizer": arch.get("tokenizer"),
            },
        }
    return out


SOURCE = Source(name="openrouter", url=URL, fetch=fetch, project=project)
