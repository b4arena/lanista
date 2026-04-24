"""Low-level HTTP helpers shared by every source fetcher.

Each helper accepts an optional ``headers`` mapping which is merged over a
default ``User-Agent``. ``hf_headers()`` returns a Bearer-token header when
``HF_TOKEN`` or ``HUGGINGFACE_TOKEN`` is in the environment — authenticated
HuggingFace requests get a 2x anonymous rate-limit budget (500 → 1000 API
calls per 5-minute window per IP).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

USER_AGENT = "lanista/0.1"


def _merge_headers(extra: dict | None) -> dict:
    h = {"User-Agent": USER_AGENT}
    if extra:
        h.update(extra)
    return h


def hf_headers() -> dict:
    """Bearer token from ``HF_TOKEN`` or ``HUGGINGFACE_TOKEN``, else empty."""
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def fetch_json(url: str, timeout: int = 20, headers: dict | None = None) -> dict | None:
    """GET a JSON URL. Return parsed value, or None on failure (reason to stderr)."""
    try:
        req = urllib.request.Request(url, headers=_merge_headers(headers))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  ! {url}: {e}", file=sys.stderr)
        return None


def fetch_text(url: str, timeout: int = 20, headers: dict | None = None) -> str | None:
    """GET a URL as raw text. Return str, or None on failure."""
    try:
        req = urllib.request.Request(url, headers=_merge_headers(headers))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! {url}: {e}", file=sys.stderr)
        return None


def fetch_bytes(url: str, timeout: int = 60, headers: dict | None = None) -> bytes | None:
    """GET a URL as raw bytes. Default timeout is longer — for file downloads."""
    try:
        req = urllib.request.Request(url, headers=_merge_headers(headers))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! {url}: {e}", file=sys.stderr)
        return None
