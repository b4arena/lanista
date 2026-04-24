"""Doctor: proactive health checks + opt-in auto-fix.

Checks run in a fixed order and return a list of :class:`Check` records.
The formatter layer renders them; this module is pure logic.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from importlib import resources
from typing import Literal

from lanista import paths
from lanista.http import fetch_text
from lanista.sources import SOURCES, pimono
from lanista.sources.litellm import URL as LITELLM_URL
from lanista.sources.openrouter import URL as OPENROUTER_URL

STALE_AFTER = timedelta(days=30)

Status = Literal["ok", "warn", "error"]


@dataclass
class Check:
    name: str
    status: Status
    message: str
    fix_hint: str | None = None
    fixable: bool = False
    fix_action: Callable[[], None] | None = field(default=None, repr=False)
    fix_description: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "fix_hint": self.fix_hint,
            "fixable": self.fixable,
        }


def _curated_sources_with_seeds() -> list[tuple[str, str | None]]:
    """Curated source name + its seed file (if any) from the registry."""
    return [(s.name, s.seed_name or f"{s.name}.seed.json") for s in SOURCES if s.curated]


def _reseed_curated(name: str, seed_name: str | None) -> Callable[[], None]:
    def _do() -> None:
        target = paths.source_path(name, curated=True)
        paths.ensure_parent(target)
        if seed_name and (resources.files("lanista.data") / seed_name).is_file():
            seed_ref = resources.files("lanista.data") / seed_name
            target.write_text(seed_ref.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            target.write_text(json.dumps({"models": {}}, indent=2) + "\n", encoding="utf-8")

    return _do


def _check_curated_sources() -> list[Check]:
    out: list[Check] = []
    for name, seed_name in _curated_sources_with_seeds():
        p = paths.source_path(name, curated=True)
        if not p.exists():
            out.append(
                Check(
                    name=f"curated source ({name})",
                    status="ok",
                    message=f"not yet seeded (will be created on next fetch): {p}",
                )
            )
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            out.append(
                Check(
                    name=f"curated source ({name})",
                    status="error",
                    message=f"parse error: {e}",
                    fix_hint="re-seed from package data",
                    fixable=True,
                    fix_action=_reseed_curated(name, seed_name),
                    fix_description=f"re-seeded {name} at {p}",
                )
            )
            continue
        if not isinstance(data, dict):
            out.append(
                Check(
                    name=f"curated source ({name})",
                    status="error",
                    message=f"invalid shape (not a JSON object): {p}",
                )
            )
            continue
        model_count = len(data.get("models") or {})
        out.append(
            Check(
                name=f"curated source ({name})",
                status="ok",
                message=f"{model_count} entries: {p}",
            )
        )
    return out


def _check_aliases() -> Check:
    p = paths.aliases_path()
    if not p.exists():
        return Check(
            name="aliases",
            status="ok",
            message=f"not yet seeded (will be created on next fetch): {p}",
        )
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return Check(
            name="aliases",
            status="error",
            message=f"parse error: {e}",
            fix_hint=f"delete {p} and run lanista fetch to re-seed",
        )
    count = len(data.get("aliases") or {})
    return Check(name="aliases", status="ok", message=f"{count} canonical ids: {p}")


def _check_index() -> tuple[Check, dict | None]:
    p = paths.index_path()
    if not p.exists():
        return (
            Check(
                name="index",
                status="error",
                message=f"missing: {p}",
                fix_hint="run: lanista fetch",
            ),
            None,
        )
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:

        def _fix() -> None:
            p.unlink()

        return (
            Check(
                name="index",
                status="error",
                message=f"corrupt index (JSON parse error): {e}",
                fix_hint="delete corrupt index, then run: lanista fetch",
                fixable=True,
                fix_action=_fix,
                fix_description=f"deleted corrupt index at {p}",
            ),
            None,
        )
    missing = [k for k in ("models", "coding_agents", "generated_at") if k not in data]
    if missing:
        return (
            Check(
                name="index",
                status="error",
                message=f"malformed index (missing keys: {', '.join(missing)})",
                fix_hint="run: lanista fetch",
            ),
            data,
        )
    return (
        Check(
            name="index",
            status="ok",
            message=f"{len(data['models'])} models, {len(data['coding_agents'])} agents: {p}",
        ),
        data,
    )


def _check_index_age(data: dict | None) -> Check | None:
    if data is None:
        return None
    try:
        gen = datetime.fromisoformat(data["generated_at"])
    except (KeyError, ValueError):
        return Check(
            name="index age",
            status="warn",
            message="missing or unparseable generated_at",
        )
    age = datetime.now(UTC) - gen
    if age > STALE_AFTER:
        return Check(
            name="index age",
            status="warn",
            message=f"{age.days}d old (>{STALE_AFTER.days}d threshold)",
            fix_hint="run: lanista fetch",
        )
    return Check(name="index age", status="ok", message=f"{age.days}d old")


def _check_pimono_age(data: dict | None) -> Check:
    last_commit: str | None = (data or {}).get("pimono_last_commit") if data else None
    if last_commit is None:
        age = pimono.fetch_last_commit_age()
        if age is None:
            return Check(
                name="pi-mono age",
                status="warn",
                message="could not determine (GitHub API unavailable)",
            )
    else:
        try:
            ts = datetime.fromisoformat(last_commit)
            age = datetime.now(UTC) - ts
        except ValueError:
            return Check(
                name="pi-mono age",
                status="warn",
                message=f"unparseable pimono_last_commit: {last_commit}",
            )
    if age > STALE_AFTER:
        return Check(
            name="pi-mono age",
            status="warn",
            message=f"models.generated.ts is {age.days}d old on upstream main",
            fix_hint="check upstream pi-mono for a refresh",
        )
    return Check(name="pi-mono age", status="ok", message=f"upstream {age.days}d old")


def _check_connectivity(verbose: bool) -> list[Check]:
    if not verbose:
        return []
    targets = [
        ("openrouter", OPENROUTER_URL),
        ("litellm", LITELLM_URL),
        ("pi-mono", pimono.MODELS_URL),
    ]
    results: list[Check] = []
    for name, url in targets:
        ok = fetch_text(url, timeout=5) is not None
        results.append(
            Check(
                name=f"connectivity ({name})",
                status="ok" if ok else "warn",
                message="reachable" if ok else f"unreachable: {url}",
                fix_hint=None if ok else "check network; source may be temporarily down",
            )
        )
    return results


def run_checks(verbose: bool = False) -> list[Check]:
    checks: list[Check] = []
    checks.extend(_check_curated_sources())
    checks.append(_check_aliases())
    idx_check, idx_data = _check_index()
    checks.append(idx_check)
    age_check = _check_index_age(idx_data)
    if age_check:
        checks.append(age_check)
    checks.append(_check_pimono_age(idx_data))
    checks.extend(_check_connectivity(verbose))
    return checks


def apply_fixes(checks: list[Check]) -> list[str]:
    fixed: list[str] = []
    for c in checks:
        if c.fixable and c.fix_action is not None:
            try:
                c.fix_action()
                fixed.append(c.fix_description or c.name)
            except Exception as e:  # noqa: BLE001
                fixed.append(f"[failed: {c.name}] {e}")
    return fixed
