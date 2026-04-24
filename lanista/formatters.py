"""Output formatters: dual-mode (human / JSON) per agentic-cli Pattern 6.

JSON mode keeps stdout strictly machine-consumable — all human-meant messaging
(progress, warnings, errors, next-steps) goes to stderr or is suppressed.
Human mode uses Rich for colors and structured tables on stdout.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from rich.console import Console

from lanista import paths

if TYPE_CHECKING:
    from datetime import datetime

    from lanista.doctor import Check
    from lanista.index import FetchReport


class OutputMode(StrEnum):
    HUMAN = "human"
    JSON = "json"


class BaseFormatter(ABC):
    @abstractmethod
    def status(self, data: dict | None) -> None: ...
    @abstractmethod
    def fetch_report(self, report: FetchReport, stale: bool) -> None: ...
    @abstractmethod
    def models(self, query: str, hits: dict, show_sources: bool = True) -> None: ...
    @abstractmethod
    def agents(self, agents: dict, filtered: bool = False) -> None: ...
    @abstractmethod
    def tier(self, level: int, results: list[dict], show_sources: bool = False) -> None: ...
    @abstractmethod
    def doctor(self, checks: list[Check], fixes_applied: list[str] | None = None) -> None: ...
    @abstractmethod
    def info(self, message: str) -> None: ...
    @abstractmethod
    def warning(self, message: str) -> None: ...
    @abstractmethod
    def error(self, message: str, hints: list[str] | None = None) -> None: ...
    @abstractmethod
    def next_steps(self, hints: list[tuple[str, str]]) -> None: ...


def _format_observation_facts(source: str, extracted: dict) -> str:
    """One-line summary of the per-source ``extracted`` dict, keyed by source."""
    parts: list[str] = []
    cw = extracted.get("context_window")
    if cw:
        parts.append(f"ctx={cw:,}")
    pricing = extracted.get("pricing_per_million") or {}
    inp, out = pricing.get("input"), pricing.get("output")
    if inp is not None or out is not None:
        parts.append(f"price=${inp if inp is not None else '?'}/${out if out is not None else '?'}")
    if source == "litellm":
        caps = extracted.get("capabilities") or []
        if caps:
            shown = ",".join(caps[:4])
            tail = f" +{len(caps) - 4}" if len(caps) > 4 else ""
            parts.append(f"caps={shown}{tail}")
        if extracted.get("provider"):
            parts.append(f"via={extracted['provider']}")
    elif source == "openrouter":
        mods = extracted.get("modalities") or []
        if mods:
            parts.append(f"modalities={','.join(mods)}")
        if extracted.get("tokenizer"):
            parts.append(f"tokenizer={extracted['tokenizer']}")
    elif source == "pimono":
        if extracted.get("provider"):
            parts.append(f"via={extracted['provider']}")
        if extracted.get("reasoning"):
            parts.append("reasoning=yes")
        mods = extracted.get("modalities") or []
        if mods:
            parts.append(f"modalities={','.join(mods)}")
    elif source == "factory_weather":
        parts.append(f"mentions={extracted.get('mention_count', '?')}")
        if extracted.get("latest_pubdate"):
            parts.append(f"latest={extracted['latest_pubdate']}")
    elif source == "aider":
        rate = extracted.get("best_pass_rate_2")
        if rate is not None:
            parts.append(f"pass_rate_2={rate}%")
        if extracted.get("run_count"):
            parts.append(f"runs={extracted['run_count']}")
    elif source == "artificial_analysis":
        for k, v in list(extracted.items())[:4]:
            parts.append(f"{k}={v}")
    elif source == "lmarena":
        ratings = extracted.get("lmarena_ratings") or {}
        overall = (ratings.get("overall") or {}).get("rating")
        if overall is not None:
            parts.append(f"lm_overall={overall:.0f}")
        for cat in ("coding", "creative_writing", "hard_prompts"):
            r = (ratings.get(cat) or {}).get("rating")
            if r is not None:
                parts.append(f"lm_{cat}={r:.0f}")
        pub = extracted.get("lmarena_publish_date")
        if pub:
            parts.append(f"as_of={pub}")
    return "  ".join(parts) if parts else "(no extracted fields)"


def _age_days(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        from datetime import UTC
        from datetime import datetime as _dt

        gen: datetime = _dt.fromisoformat(iso)
        return (_dt.now(UTC) - gen).days
    except ValueError:
        return None


class HumanFormatter(BaseFormatter):
    SYMBOL = {"ok": "✓", "warn": "⚠", "error": "✗"}
    COLOR = {"ok": "green", "warn": "yellow", "error": "red"}
    LABEL = {"ok": "Info", "warn": "Warnings", "error": "Errors"}

    def __init__(self) -> None:
        self.out = Console()
        self.err = Console(stderr=True)

    def status(self, data: dict | None) -> None:
        if data is None:
            self.out.print("[yellow]No index yet.[/yellow]")
            self.out.print(f"  Sources:  {paths.sources_config_dir()}")
            self.out.print(f"  Index:    {paths.index_path()} [dim](missing)[/dim]")
            self.next_steps(
                [
                    ("lanista fetch", "Download sources and build the index"),
                    ("lanista doctor", "Run health checks"),
                    ("lanista --help", "Show all commands"),
                ]
            )
            return

        generated = data.get("generated_at", "?")
        age = _age_days(generated)
        age_line = f" [dim]({age}d ago)[/dim]" if age is not None else ""

        models = data.get("models", {})
        tier_counts: dict[int, int] = {}
        for rec in models.values():
            t = (rec.get("notes") or {}).get("tier")
            if t is not None:
                tier_counts[t] = tier_counts.get(t, 0) + 1

        self.out.print("[bold]lanista — model catalog[/bold]")
        self.out.print(f"  Generated: {generated}{age_line}")
        self.out.print(f"  Models:    {len(models)}")
        self.out.print(f"  Agents:    {len(data.get('coding_agents', {}))}")
        if tier_counts:
            tiers = ", ".join(f"T{t}={n}" for t, n in sorted(tier_counts.items()))
            self.out.print(f"  Curated:   {tiers}")
        counts = data.get("source_counts") or {}
        if counts:
            self.out.print(
                "  Sources:   " + ", ".join(f"{n}={c}" for n, c in counts.items())
            )
        self.out.print(f"  Index:     {paths.index_path()}")
        self.out.print(f"  Sources:   {paths.sources_config_dir()}")

        self.next_steps(
            [
                ("lanista pick '<task>'", "Build a self-contained picker prompt (hero command)"),
                ("lanista fetch", "Refresh the index"),
                ("lanista show <substr>", "Inspect a model"),
                ("lanista tier 1", "List curated Tier 1 models"),
                ("lanista agents", "List coding agents"),
                ("lanista doctor", "Run health checks"),
            ]
        )

    def fetch_report(self, report: FetchReport, stale: bool) -> None:
        name_width = max((len(n) for n in report.source_counts), default=10)
        for name, count in report.source_counts.items():
            err = report.source_errors.get(name)
            if err:
                self.out.print(
                    f"[red]![/red] {name.ljust(name_width)}  "
                    f"[dim]{count} models ({err})[/dim]"
                )
            else:
                self.out.print(
                    f"[green]+[/green] {name.ljust(name_width)}  {count} models"
                )
        for name, err in report.source_errors.items():
            if name in report.source_counts:
                continue
            self.out.print(f"[red]x[/red] {name.ljust(name_width)}  [red]{err}[/red]")
        self.out.print(
            f"[green]->[/green] {report.index_path} "
            f"[dim]({report.index_size_kb} KB, {report.total_models} models)[/dim]"
        )
        if stale and report.pimono_age is not None:
            self.warning(
                f"pi-mono models.generated.ts last updated {report.pimono_age.days}d ago "
                "(>30d). Consider checking upstream for a refresh."
            )
        self.next_steps(
            [
                ("lanista", "Show summary"),
                ("lanista tier 1", "List curated Tier 1 models"),
                ("lanista doctor", "Run health checks"),
            ]
        )

    def _render_observations(self, observations: list[dict], skip: str | None = None) -> None:
        obs = [o for o in (observations or []) if o.get("source") != skip]
        if not obs:
            return
        label = "Sources" if skip is None else f"Other sources ({len(obs)})"
        self.out.print(f"  [bold]{label}:[/bold]")
        src_width = max(len(o.get("source", "?")) for o in obs)
        for o in obs:
            src = o.get("source", "?").ljust(src_width)
            src_id = o.get("source_model_id", "?")
            self.out.print(
                f"    [dim]\\[[/dim][cyan]{src}[/cyan][dim]][/dim] [dim]{src_id}[/dim]"
            )
            facts = _format_observation_facts(o.get("source", ""), o.get("extracted") or {})
            self.out.print(f"        {facts}")

    def models(self, query: str, hits: dict, show_sources: bool = True) -> None:
        self.out.print(f"[bold]{len(hits)} model(s) matching '{query}':[/bold]\n")
        for mid, rec in hits.items():
            self.out.print(f"[cyan]{mid}[/cyan]")
            ctx = rec.get("context_window")
            pricing = rec.get("pricing_per_million") or {}
            notes = rec.get("notes") or {}
            if ctx:
                self.out.print(f"  context:   {ctx:,}")
            if pricing.get("input") or pricing.get("output"):
                self.out.print(
                    f"  pricing:   ${pricing.get('input') or '?'} in / "
                    f"${pricing.get('output') or '?'} out per 1M"
                )
            if notes:
                self.out.print(f"  tier:      {notes.get('tier', '?')}  [dim]\\[gkisokay][/dim]")
                if notes.get("use_for"):
                    self.out.print(
                        f"  use for:   {notes['use_for']}  [dim]\\[gkisokay][/dim]"
                    )
            if show_sources:
                self._render_observations(rec.get("observations") or [], skip=None)
            self.out.print("")
        self.next_steps(
            [
                ("lanista --json show <substr>", "Full structured record"),
                ("lanista show <substr> --no-sources", "Hide per-source attribution"),
            ]
        )

    def agents(self, agents: dict, filtered: bool = False) -> None:
        if filtered:
            self._agents_detailed(agents)
        else:
            self._agents_compact(agents)

    def _agents_compact(self, agents: dict) -> None:
        self.out.print(f"[bold]{len(agents)} coding agent(s):[/bold]\n")
        for name, a in sorted(agents.items()):
            default = a.get("default") or "-"
            cli = a.get("cli") or a.get("routes_via") or "-"
            count = a.get("model_count")
            count_str = f" ({count} models)" if count else ""
            self.out.print(f"  [cyan]{name:<22}[/cyan] cli={cli:<22} default={default}{count_str}")
        self.next_steps(
            [
                ("lanista agents <substr>", "Drill into one agent's model list"),
                ("lanista --json agents <name>", "Full structured record"),
            ]
        )

    def _agents_detailed(self, agents: dict) -> None:
        self.out.print(f"[bold]{len(agents)} coding agent(s):[/bold]\n")
        meta_labels = ["cli", "flag", "default", "routes_via", "note"]
        label_pad = max(len(lbl) for lbl in meta_labels) + 1
        for name, a in sorted(agents.items()):
            self.out.print(f"[cyan]{name}[/cyan]")
            for key in meta_labels:
                val = a.get(key)
                if val:
                    self.out.print(f"  {(key + ':').ljust(label_pad)}  {val}")
            options = a.get("options") or {}
            if not options:
                self.out.print("")
                continue
            self.out.print(f"  {len(options)} model(s) [dim](costs per 1M tokens)[/dim]:")
            id_width = max(len(mid) for mid in options)
            for mid, m in options.items():
                ctx = m.get("context_window")
                ctx_str = f"ctx={ctx:>9,}" if ctx else "ctx=        -"
                cost = m.get("cost_per_million") or {}
                if cost:
                    cost_str = f"${cost.get('input', '?')} in / ${cost.get('output', '?')} out"
                else:
                    cost_str = "cost: -"
                reasoning = " [dim]·[/dim] [green]reasoning[/green]" if m.get("reasoning") else ""
                self.out.print(
                    f"    [cyan]{mid.ljust(id_width)}[/cyan]  "
                    f"{ctx_str}  [dim]·[/dim]  {cost_str}{reasoning}"
                )
            self.out.print("")
        self.next_steps(
            [
                ("lanista show <model-id>", "Pricing + curated notes for a model"),
                ("lanista --json agents <name>", "Full structured record"),
            ]
        )

    def tier(self, level: int, results: list[dict], show_sources: bool = False) -> None:
        self.out.print(f"[bold]Tier {level} — {len(results)} model(s):[/bold]\n")
        for m in results:
            self.out.print(f"[cyan]{m['id']}[/cyan]  [dim]\\[gkisokay][/dim]")
            if m.get("use_for"):
                self.out.print(f"  use for:   {m['use_for']}")
            for s in m.get("strengths") or []:
                self.out.print(f"  [green]+[/green] {s}")
            for w in m.get("weaknesses") or []:
                self.out.print(f"  [red]-[/red] {w}")
            if show_sources:
                self._render_observations(m.get("observations") or [], skip="gkisokay")
            self.out.print("")
        self.next_steps(
            [
                ("lanista --json tier <n>", "Structured output with full observations"),
                ("lanista tier <n> --no-sources", "Curated notes only (terse)"),
                ("lanista show <id>", "Full pricing/context details"),
            ]
        )

    def doctor(self, checks: list[Check], fixes_applied: list[str] | None = None) -> None:
        buckets: dict[str, list[Check]] = {"error": [], "warn": [], "ok": []}
        for c in checks:
            buckets[c.status].append(c)

        for status in ("error", "warn", "ok"):
            items = buckets[status]
            if not items:
                continue
            color = self.COLOR[status]
            sym = self.SYMBOL[status]
            self.out.print(f"\n[bold {color}]{self.LABEL[status]}:[/bold {color}]")
            for c in items:
                self.out.print(f"  [{color}]{sym}[/{color}] [bold]{c.name}[/bold]: {c.message}")
                if c.fix_hint:
                    self.out.print(f"    [dim]->[/dim] {c.fix_hint}")

        if fixes_applied:
            self.out.print("\n[bold green]Applied fixes:[/bold green]")
            for fix in fixes_applied:
                self.out.print(f"  [green]✓[/green] {fix}")

        self.out.print(
            f"\n[bold]Summary:[/bold] "
            f"{len(buckets['error'])} errors, "
            f"{len(buckets['warn'])} warnings, "
            f"{len(buckets['ok'])} info"
        )

        fixable = [c for c in checks if c.fixable]
        if fixable and fixes_applied is None:
            self.out.print(
                f"\nRun [cyan]lanista doctor --fix[/cyan] to auto-fix {len(fixable)} issue(s)."
            )

        self.next_steps(
            [
                ("lanista fetch", "Refresh index"),
                ("lanista doctor --verbose", "Include connectivity probes"),
                ("lanista --help", "Show all commands"),
            ]
        )

    def info(self, message: str) -> None:
        self.err.print(f"[dim][INFO][/dim] {message}")

    def warning(self, message: str) -> None:
        self.err.print(f"[yellow]⚠  {message}[/yellow]")

    def error(self, message: str, hints: list[str] | None = None) -> None:
        self.err.print(f"[red]✗ Error:[/red] {message}")
        for h in hints or []:
            self.err.print(f"  {h}")

    def next_steps(self, hints: list[tuple[str, str]]) -> None:
        self.out.print("\n[bold]Next steps:[/bold]")
        width = max((len(cmd) for cmd, _ in hints), default=0)
        for cmd, desc in hints:
            self.out.print(f"  [cyan]{cmd.ljust(width)}[/cyan]  {desc}")


class JsonFormatter(BaseFormatter):
    """Emit one JSON object to stdout per command. All notices go to stderr."""

    def __init__(self) -> None:
        self.err = Console(stderr=True)

    def _emit(self, payload: Any) -> None:
        print(json.dumps(payload, indent=2, default=str))

    def status(self, data: dict | None) -> None:
        if data is None:
            self._emit(
                {
                    "status": "no_index",
                    "index_path": str(paths.index_path()),
                    "sources_dir": str(paths.sources_config_dir()),
                }
            )
            return
        models = data.get("models", {})
        tier_counts: dict[str, int] = {}
        for rec in models.values():
            t = (rec.get("notes") or {}).get("tier")
            if t is not None:
                tier_counts[str(t)] = tier_counts.get(str(t), 0) + 1
        self._emit(
            {
                "status": "ok",
                "generated_at": data.get("generated_at"),
                "age_days": _age_days(data.get("generated_at")),
                "model_count": len(models),
                "agent_count": len(data.get("coding_agents", {})),
                "tier_counts": tier_counts,
                "source_counts": data.get("source_counts") or {},
                "index_path": str(paths.index_path()),
                "sources_dir": str(paths.sources_config_dir()),
            }
        )

    def fetch_report(self, report: FetchReport, stale: bool) -> None:
        self._emit(
            {
                "source_counts": report.source_counts,
                "source_errors": report.source_errors,
                "pimono_age_days": (report.pimono_age.days if report.pimono_age else None),
                "pimono_stale": stale,
                "total_models": report.total_models,
                "index_path": report.index_path,
                "index_size_kb": report.index_size_kb,
            }
        )

    def models(self, query: str, hits: dict, show_sources: bool = True) -> None:
        # JSON output always includes full observations; flag is ignored here.
        self._emit({"query": query, "count": len(hits), "models": hits})

    def agents(self, agents: dict, filtered: bool = False) -> None:
        # JSON always emits the full structure; filter presence is irrelevant.
        self._emit(agents)

    def tier(self, level: int, results: list[dict], show_sources: bool = False) -> None:
        # JSON output always includes full observations; flag is ignored here.
        self._emit({"tier": level, "count": len(results), "models": results})

    def doctor(self, checks: list[Check], fixes_applied: list[str] | None = None) -> None:
        self._emit(
            {
                "errors": [c.to_dict() for c in checks if c.status == "error"],
                "warnings": [c.to_dict() for c in checks if c.status == "warn"],
                "info": [c.to_dict() for c in checks if c.status == "ok"],
                "summary": {
                    "errors": sum(1 for c in checks if c.status == "error"),
                    "warnings": sum(1 for c in checks if c.status == "warn"),
                    "info": sum(1 for c in checks if c.status == "ok"),
                },
                "fixes_applied": fixes_applied or [],
            }
        )

    def info(self, message: str) -> None:
        self.err.print(f"[INFO] {message}")

    def warning(self, message: str) -> None:
        self.err.print(f"[WARN] {message}")

    def error(self, message: str, hints: list[str] | None = None) -> None:
        self.err.print(f"[ERROR] {message}")
        for h in hints or []:
            self.err.print(f"  {h}")

    def next_steps(self, hints: list[tuple[str, str]]) -> None:
        # JSON mode: suppress. Hints are a human affordance.
        return


def get_formatter(mode: OutputMode) -> BaseFormatter:
    return JsonFormatter() if mode == OutputMode.JSON else HumanFormatter()
