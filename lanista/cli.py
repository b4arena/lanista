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

import subprocess
import sys

from lanista import doctor as dctr
from lanista import index as idx
from lanista import opinions as ops
from lanista import pareto as prt
from lanista import picker as pkr
from lanista import routing as rt
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
    hint = rt.suggest_alternative(task)
    if hint:
        print(f"# {hint}", file=sys.stderr)


def _resolve_axis(state: CLIState, name: str) -> str:
    if name in prt.COLUMN_ACCESSORS:
        return name
    state.formatter.error(
        f"unknown axis '{name}'",
        hints=[f"Available: {', '.join(prt.available_columns())}"],
    )
    raise typer.Exit(1)


@app.command()
def pareto(
    ctx: typer.Context,
    quality: str = typer.Argument(..., help="Quality axis (e.g. lm_coding, aider)"),
    cost: str = typer.Argument(..., help="Cost axis (e.g. price_input, price_avg, neg_ctx)"),
    csv: bool = typer.Option(False, "--csv", help="Emit CSV to stdout (pipeable)"),
    max_cost: float | None = typer.Option(None, "--max-cost", help="Drop rows whose cost exceeds this"),
    min_quality: float | None = typer.Option(None, "--min-quality", help="Drop rows below this quality"),
    require_cap: str | None = typer.Option(
        None, "--require-cap",
        help="Only include models whose capabilities list contains this (e.g. pdf_input, vision)",
    ),
    min_ctx: int | None = typer.Option(
        None, "--min-ctx", help="Only include models with context_window >= this"
    ),
    limit: int | None = typer.Option(None, "--limit", "-n", help="Cap frontier rows in output"),
) -> None:
    """Deterministic Pareto frontier over QUALITY vs COST."""
    state = _state(ctx)
    data = _require_index(state)
    q = _resolve_axis(state, quality)
    c = _resolve_axis(state, cost)
    models = prt.filter_models(data["models"], require_cap=require_cap, min_ctx=min_ctx)
    pairs = prt.extract_pairs(models, q, c)
    if max_cost is not None:
        pairs = [p for p in pairs if p[2] <= max_cost]
    if min_quality is not None:
        pairs = [p for p in pairs if p[1] >= min_quality]
    frontier_ids = prt.pareto_frontier(pairs)
    if csv:
        print(prt.to_csv(pairs, frontier_ids, quality_name=q, cost_name=c), end="")
        return
    # Human: print frontier sorted by cost asc.
    front = sorted(
        [p for p in pairs if p[0] in frontier_ids],
        key=lambda p: (p[2], -p[1]),
    )
    if limit:
        front = front[:limit]
    if not front:
        state.formatter.error(
            "empty frontier",
            hints=["Try different axes", "Or widen --max-cost"],
        )
        raise typer.Exit(1)
    print(f"Pareto frontier ({q} ↑ vs {c} ↓) — {len(front)} model(s):")
    print(f"  {'model':<40}  {q:>14}  {c:>14}")
    for mid, qv, cv in front:
        print(f"  {mid[:40]:<40}  {qv:>14.2f}  {cv:>14.4f}")
    print()
    print("Next: lanista chart " + f"{q} {c} --out /tmp/pareto.png")


@app.command()
def profiles(
    ctx: typer.Context,
    quality: str = typer.Argument(..., help="Quality axis (e.g. lm_coding)"),
    cost: str = typer.Argument(..., help="Cost axis (e.g. price_input, -ctx)"),
    max_cost: float | None = typer.Option(None, "--max-cost", help="Drop rows above this cost"),
    min_quality: float | None = typer.Option(None, "--min-quality", help="Drop rows below this quality"),
    require_cap: str | None = typer.Option(
        None, "--require-cap",
        help="Only include models whose capabilities list contains this (e.g. pdf_input, vision)",
    ),
    min_ctx: int | None = typer.Option(
        None, "--min-ctx", help="Only include models with context_window >= this"
    ),
) -> None:
    """Three anchor picks on the QUALITY×COST frontier: flagship / balanced / budget."""
    state = _state(ctx)
    data = _require_index(state)
    q = _resolve_axis(state, quality)
    c = _resolve_axis(state, cost)
    models = prt.filter_models(data["models"], require_cap=require_cap, min_ctx=min_ctx)
    pairs = prt.extract_pairs(models, q, c)
    if max_cost is not None:
        pairs = [p for p in pairs if p[2] <= max_cost]
    if min_quality is not None:
        pairs = [p for p in pairs if p[1] >= min_quality]
    frontier_ids = prt.pareto_frontier(pairs)
    picks = prt.find_profiles(pairs, frontier_ids)
    if not picks["flagship"]:
        state.formatter.error(
            "empty frontier after filters",
            hints=["Widen --max-cost / --min-ctx", "Drop --require-cap", "Try: lanista pareto " + f"{q} {c}"],
        )
        raise typer.Exit(1)

    def _fmt(label: str, note: str, pick):
        mid, qv, cv = pick
        print(f"{label:<10}  {mid[:42]:<42}  {q}={qv:.2f}  {c}={cv:.4f}")
        if note:
            print(f"            {note}")

    frontier_ct = len(frontier_ids)
    print(f"Frontier has {frontier_ct} non-dominated model(s) over {len(pairs)} candidate(s).")
    filt_bits = []
    if require_cap:
        filt_bits.append(f"require-cap={require_cap}")
    if min_ctx:
        filt_bits.append(f"min-ctx={min_ctx}")
    if max_cost is not None:
        filt_bits.append(f"max-cost={max_cost}")
    if min_quality is not None:
        filt_bits.append(f"min-quality={min_quality}")
    if filt_bits:
        print("Filters: " + ", ".join(filt_bits))
    print()
    _fmt("Flagship", f"max {q} on the frontier", picks["flagship"])
    _fmt("Balanced", f"knee of the curve (normalized distance to ideal)", picks["balanced"])
    _fmt("Budget", f"min {c} on the frontier", picks["budget"])
    if picks["flagship"] == picks["balanced"] == picks["budget"]:
        print()
        print("Note: only one frontier point survived the filters; all three profiles collapse.")
    print()
    print(f"Chart: lanista chart {q} {c} --out /tmp/profiles.png")


@app.command()
def chart(
    ctx: typer.Context,
    quality: str = typer.Argument(..., help="Quality axis"),
    cost: str = typer.Argument(..., help="Cost axis"),
    out: str = typer.Option("chart.png", "--out", "-o", help="Output PNG path"),
    title: str | None = typer.Option(None, "--title", help="Chart title"),
    max_cost: float | None = typer.Option(None, "--max-cost", help="Drop rows whose cost exceeds this"),
    min_quality: float | None = typer.Option(None, "--min-quality", help="Drop rows below this quality"),
    require_cap: str | None = typer.Option(
        None, "--require-cap",
        help="Only include models whose capabilities list contains this (e.g. pdf_input, vision)",
    ),
    min_ctx: int | None = typer.Option(
        None, "--min-ctx", help="Only include models with context_window >= this"
    ),
) -> None:
    """Render a scatter plot of QUALITY vs COST with the frontier highlighted."""
    state = _state(ctx)
    data = _require_index(state)
    q = _resolve_axis(state, quality)
    c = _resolve_axis(state, cost)
    models = prt.filter_models(data["models"], require_cap=require_cap, min_ctx=min_ctx)
    pairs = prt.extract_pairs(models, q, c)
    if max_cost is not None:
        pairs = [p for p in pairs if p[2] <= max_cost]
    if min_quality is not None:
        pairs = [p for p in pairs if p[1] >= min_quality]
    frontier_ids = prt.pareto_frontier(pairs)
    # Two y-series: frontier vs off-frontier (NaN where the row doesn't belong).
    header = f"model,{c},frontier,others\n"
    rows = []
    for mid, qv, cv in pairs:
        if mid in frontier_ids:
            rows.append(f"{mid},{cv},{qv},NaN")
        else:
            rows.append(f"{mid},{cv},NaN,{qv}")
    csv_blob = header + "\n".join(rows) + "\n"
    chart_title = title or f"{q} vs {c} (Pareto frontier highlighted)"
    cmd = [
        "chartroom", "scatter",
        "--csv", "-",
        "-x", c,
        "-y", "frontier",
        "-y", "others",
        "--title", chart_title,
        "--xlabel", c,
        "--ylabel", q,
        "--output", out,
    ]
    try:
        res = subprocess.run(cmd, input=csv_blob, text=True, capture_output=True, check=True)
    except FileNotFoundError as e:
        state.formatter.error(
            "chartroom not found on PATH",
            hints=["Install chartroom: pipx install chartroom"],
        )
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        state.formatter.error(
            f"chartroom failed: {e.stderr.strip() or e.stdout.strip()}",
            hints=["Run: lanista pareto ... --csv | head  (to inspect the data)"],
        )
        raise typer.Exit(1) from e
    print(res.stdout.strip() or out)


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
