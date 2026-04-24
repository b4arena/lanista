"""BerriAI LiteLLM model_prices_and_context_window.json."""

from __future__ import annotations

from lanista import http
from lanista.source_base import Source

URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
)


def fetch() -> dict | None:
    return http.fetch_json(URL)


def _per_million(v) -> float | None:
    return round(float(v) * 1_000_000, 4) if v else None


def project(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for mid, m in raw.items():
        if mid == "sample_spec" or not isinstance(m, dict):
            continue
        caps = [
            k.removeprefix("supports_")
            for k, v in m.items()
            if k.startswith("supports_") and v is True
        ]
        out[mid] = {
            "raw": m,
            "extracted": {
                "provider": m.get("litellm_provider"),
                "context_window": m.get("max_input_tokens"),
                "max_output": m.get("max_output_tokens"),
                "pricing_per_million": {
                    "input": _per_million(m.get("input_cost_per_token")),
                    "output": _per_million(m.get("output_cost_per_token")),
                },
                "capabilities": caps,
                "mode": m.get("mode"),
            },
        }
    return out


SOURCE = Source(name="litellm", url=URL, fetch=fetch, project=project)
