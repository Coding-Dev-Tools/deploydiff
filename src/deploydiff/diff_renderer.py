"""Human-readable diff output renderer using Rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .models import ChangeAction, DeployPlan, ResourceChange


# Action colors for Rich output
ACTION_COLORS: dict[ChangeAction, str] = {
    ChangeAction.CREATE: "green",
    ChangeAction.READ: "cyan",
    ChangeAction.UPDATE: "yellow",
    ChangeAction.DELETE: "red",
    ChangeAction.CREATE_BEFORE_DELETE: "yellow",
    ChangeAction.DELETE_BEFORE_CREATE: "red",
    ChangeAction.REPLACE: "magenta",
    ChangeAction.IMPORT: "cyan",
    ChangeAction.NO_OP: "dim",
}

ACTION_LABELS: dict[ChangeAction, str] = {
    ChangeAction.CREATE: "will be created",
    ChangeAction.READ: "will be read",
    ChangeAction.UPDATE: "will be updated",
    ChangeAction.DELETE: "will be destroyed",
    ChangeAction.CREATE_BEFORE_DELETE: "will be replaced (create-first)",
    ChangeAction.DELETE_BEFORE_CREATE: "will be replaced (delete-first)",
    ChangeAction.REPLACE: "will be replaced",
    ChangeAction.IMPORT: "will be imported",
    ChangeAction.NO_OP: "no changes",
}


def render_plan(plan: DeployPlan, console: Console | None = None, verbose: bool = False) -> None:
    """Render a full deployment plan to the console.

    Args:
        plan: The parsed deployment plan.
        console: Rich Console instance (creates one if None).
        verbose: Show before/after details for each change.
    """
    if console is None:
        console = Console()

    # Header
    source_name = plan.source.value.capitalize()
    console.print()
    console.print(Panel(f"[bold]DeployDiff: {source_name} Plan Preview[/bold]", style="blue"))

    # Summary
    _render_summary(plan, console)

    # Changes grouped by type
    for action, changes in _group_by_action(plan).items():
        if changes:
            _render_action_group(plan, action, changes, console, verbose)

    # Warning for destructive changes
    destructive = plan.destructive_changes
    if destructive:
        console.print()
        console.print(f"[bold red]⚠ {len(destructive)} destructive change(s) detected![/bold red]")

    console.print()


def _render_summary(plan: DeployPlan, console: Console) -> None:
    """Render a summary table of change counts."""
    table = Table(title="Change Summary", box=box.ROUNDED, show_header=True)
    table.add_column("Action", style="bold")
    table.add_column("Count", justify="right")

    creates = len(plan.creates)
    updates = len(plan.updates)
    deletes = len(plan.deletes)
    total = len(plan.changes)

    if creates:
        table.add_row("[green]+ Create[/green]", str(creates))
    if updates:
        table.add_row("[yellow]~ Update[/yellow]", str(updates))
    if deletes:
        table.add_row("[red]- Delete/Replace[/red]", str(deletes))

    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

    console.print(table)
    console.print()


def _render_action_group(
    plan: DeployPlan,
    action: ChangeAction,
    changes: list[ResourceChange],
    console: Console,
    verbose: bool,
) -> None:
    """Render a group of changes of the same action type."""
    color = ACTION_COLORS.get(action, "white")
    label = ACTION_LABELS.get(action, "will change")

    console.print()
    console.print(f"[{color}][bold]{len(changes)} resource(s) {label}:[/bold][/{color}]")

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("", width=3)
    table.add_column("Address", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Provider", style="dim")

    for change in changes:
        symbol = change.display_action
        addr = change.address
        if change.module_path:
            addr = f"{change.module_path}.{addr}"
        table.add_row(
            f"[{color}]{symbol}[/{color}]",
            f"[{color}]{addr}[/{color}]",
            change.resource_type,
            change.provider or "",
        )

    console.print(table)

    # Verbose: show before/after details
    if verbose:
        for change in changes:
            _render_change_details(change, console)


def _render_change_details(change: ResourceChange, console: Console) -> None:
    """Render before/after details for a single resource change."""
    if not change.before and not change.after:
        return

    console.print(f"  [dim]── {change.address} ──[/dim]")

    all_keys = set()
    if change.before:
        all_keys.update(change.before.keys())
    if change.after:
        all_keys.update(change.after.keys())

    for key in sorted(all_keys):
        if key in change.before_sensitive or key in change.after_sensitive:
            console.print(f"    {key}: [dim](sensitive value)[/dim]")
            continue

        before_val = change.before.get(key, "—") if change.before else "—"
        after_val = change.after.get(key, "—") if change.after else "—"

        if before_val == after_val:
            console.print(f"    {key}: {before_val}")
        else:
            console.print(f"    {key}: [red]- {before_val}[/red]  [green]+ {after_val}[/green]")


def _group_by_action(plan: DeployPlan) -> dict[ChangeAction, list[ResourceChange]]:
    """Group changes by action type."""
    groups: dict[ChangeAction, list[ResourceChange]] = {}
    for change in plan.changes:
        groups.setdefault(change.action, []).append(change)
    return groups
