"""Typer CLI wired to dual-mode formatters + agentic-cli patterns.

- Pattern 1: no-arg -> status + next-step hints
- Pattern 5: global ``--verbose`` for progress tracing
- Pattern 6: global ``--json`` switches every command to structured output
- Pattern 7: informative errors with suggestions (including ``lanista doctor``)
- Pattern 11: ``doctor`` with ✗/⚠/✓ symbols, ``--verbose`` connectivity probes,
  and a hidden ``--fix`` that re-seeds corrupt overlay / removes corrupt index
"""

from __future__ import annotations

from dataclasses import dataclass

import typer

from lanista import doctor as dctr
from lanista import index as idx
from lanista import opinions as ops
from lanista import picker as pkr
from lanista.formatters import BaseFormatter, OutputMode, get_formatter
from lanista.index import STALE_AFTER

app = typer.Typer(
    help="LLM model catalog and router.",
    no_args_is_help=False,
    add_completion=False,
)


@dataclass
class CLIState:
    formatter: BaseFormatter
    verbose: bool = False


def _state(ctx: typer.Context) -> CLIState:
    return ctx.obj


def _require_index(state: CLIState) -> dict:
    data = idx.load_index()
    if data is None:
        state.formatter.error(
            "no index yet",
            hints=[
                "Run: lanista fetch",
                "Or:  lanista doctor   (to see all health issues)",
            ],
        )
        raise typer.Exit(1)
    return data


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_out: bool = typer.Option(
        False, "--json", help="Machine-readable JSON output (stderr for notices)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
) -> None:
    """LLM model catalog — curate, fetch, query."""
    mode = OutputMode.JSON if json_out else OutputMode.HUMAN
    ctx.obj = CLIState(formatter=get_formatter(mode), verbose=verbose)
    if ctx.invoked_subcommand is not None:
        return
    ctx.obj.formatter.status(idx.load_index())


@app.command()
def fetch(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show per-source progress"),
) -> None:
    """Download every source, merge, write the index to the XDG cache dir."""
    state = _state(ctx)
    effective_verbose = state.verbose or verbose
    info_cb = state.formatter.info if effective_verbose else None
    report = idx.run_fetch(info=info_cb)
    stale = report.pimono_age is not None and report.pimono_age > STALE_AFTER
    state.formatter.fetch_report(report, stale=stale)


@app.command()
def show(
    ctx: typer.Context,
    substr: str = typer.Argument(..., help="Substring to match in model ids"),
    sources: bool = typer.Option(
        True,
        "--sources/--no-sources",
        "-s/-S",
        help="Show per-source observations with attribution (default on)",
    ),
) -> None:
    """Inspect models whose id contains SUBSTR."""
    state = _state(ctx)
    data = _require_index(state)
    hits = {k: v for k, v in data["models"].items() if substr.lower() in k.lower()}
    if not hits:
        state.formatter.error(
            f"no match for '{substr}'",
            hints=[
                "Try: lanista tier 1    (browse curated models)",
                "Or:  lanista doctor    (if you expected matches)",
            ],
        )
        raise typer.Exit(1)
    state.formatter.models(substr, hits, show_sources=sources)


@app.command()
def agents(
    ctx: typer.Context,
    filter_str: str | None = typer.Argument(None, help="Filter substring"),
) -> None:
    """List coding agents (CLI wrappers that route to model providers)."""
    state = _state(ctx)
    data = _require_index(state)
    all_agents = data.get("coding_agents", {})
    if filter_str:
        all_agents = {k: v for k, v in all_agents.items() if filter_str.lower() in k.lower()}
        if not all_agents:
            state.formatter.error(
                f"no agent matching '{filter_str}'",
                hints=[
                    "Try: lanista agents    (list all agents)",
                    "Or:  lanista doctor    (if you expected matches)",
                ],
            )
            raise typer.Exit(1)
    state.formatter.agents(all_agents, filtered=bool(filter_str))


@app.command()
def tier(
    ctx: typer.Context,
    level: int = typer.Argument(..., min=1, max=4, help="Curated tier: 1=frontier, 4=local/free"),
    sources: bool = typer.Option(
        True,
        "--sources/--no-sources",
        "-s/-S",
        help="Show per-source observations with attribution (default on)",
    ),
) -> None:
    """List models at a given curated tier."""
    state = _state(ctx)
    data = _require_index(state)
    results = []
    for mid, rec in data["models"].items():
        notes = rec.get("notes") or {}
        if notes.get("tier") == level:
            results.append(
                {
                    "id": mid,
                    "strengths": notes.get("strengths", []),
                    "weaknesses": notes.get("weaknesses", []),
                    "use_for": notes.get("use_for"),
                    "pricing_per_million": rec.get("pricing_per_million"),
                    "context_window": rec.get("context_window"),
                    "observations": rec.get("observations") or [],
                    "source_names": rec.get("sources") or [],
                }
            )
    state.formatter.tier(level, results, show_sources=sources)


@app.command()
def pick(
    ctx: typer.Context,
    task: str = typer.Argument(..., help="Natural-language task description"),
    top_n: int = typer.Option(3, "--top", "-n", min=1, max=10, help="How many models to recommend"),
) -> None:
    """Build a citeable picker prompt for TASK (paste into any LLM)."""
    state = _state(ctx)
    _require_index(state)
    try:
        prompt = pkr.build_prompt(task, top_n=top_n)
    except RuntimeError as e:
        state.formatter.error(str(e), hints=["Run: lanista fetch"])
        raise typer.Exit(1) from e
    print(prompt)


@app.command(name="refresh-opinions")
def refresh_opinions(ctx: typer.Context) -> None:
    """Refresh the opinion corpus (blog feeds, HN)."""
    state = _state(ctx)
    counts = ops.refresh_all()
    for name, n in counts.items():
        state.formatter.info(f"{name}: {n} entries")


@app.command()
def doctor(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Include connectivity probes"),
    fix: bool = typer.Option(False, "--fix", hidden=True),
) -> None:
    """Run proactive health checks. Use --verbose for connectivity probes."""
    state = _state(ctx)
    effective_verbose = state.verbose or verbose
    checks = dctr.run_checks(verbose=effective_verbose)
    fixes_applied: list[str] | None = None
    if fix:
        fixes_applied = dctr.apply_fixes(checks)
        checks = dctr.run_checks(verbose=effective_verbose)
    state.formatter.doctor(checks, fixes_applied=fixes_applied)
    if any(c.status == "error" for c in checks):
        raise typer.Exit(1)
