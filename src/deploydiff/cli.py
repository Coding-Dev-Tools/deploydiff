"""DeployDiff CLI - infrastructure change preview with cost impact and rollback."""

from __future__ import annotations

import click
from rich.console import Console

from .cloudformation_parser import parse_cloudformation_changeset
from .cost_estimator import estimate_costs
from .diff_renderer import render_plan
from .models import CostEstimate, DeployPlan
from .pulumi_parser import parse_pulumi_preview
from .rollback import generate_rollback_commands
from .terraform_parser import parse_terraform_plan

console = Console()


@click.group()
@click.version_option(package_name="deploydiff")
def main():
    """DeployDiff - Preview infrastructure changes with cost impact and rollback."""
    try:
        from revenueholdings_license import require_license
        require_license("deploydiff")
    except ImportError:
        import warnings
        warnings.warn("revenueholdings-license not installed; license checks skipped", stacklevel=2)
    pass


@main.command()
@click.option("--tf", "terraform_file", type=click.Path(exists=True), help="Terraform plan JSON file")
@click.option("--cfn", "cloudformation_file", type=click.Path(exists=True), help="CloudFormation change set JSON file")
@click.option("--pulumi", "pulumi_file", type=click.Path(exists=True), help="Pulumi preview JSON file")
@click.option("-v", "--verbose", is_flag=True, help="Show before/after details for each change")
@click.option(
    "--exit-on-destroy",
    is_flag=True,
    help="Exit with code 1 if the plan contains destructive changes (deletes or replaces)",
)
def preview(terraform_file, cloudformation_file, pulumi_file, verbose, exit_on_destroy):
    """Preview infrastructure changes from a plan file."""
    plan = _load_plan(terraform_file, cloudformation_file, pulumi_file)
    if plan is None:
        console.print("[red]Error: Provide one of --tf, --cfn, or --pulumi[/red]")
        raise SystemExit(1)

    render_plan(plan, console, verbose=verbose)

    if exit_on_destroy and plan.destructive_changes:
        console.print(
            f"\n[red]Plan contains {len(plan.destructive_changes)} destructive change(s). "
            f"Exiting with code 1 (--exit-on-destroy).[/red]"
        )
        raise SystemExit(1)


@main.command()
@click.option("--tf", "terraform_file", type=click.Path(exists=True), help="Terraform plan JSON file")
@click.option("--cfn", "cloudformation_file", type=click.Path(exists=True), help="CloudFormation change set JSON file")
@click.option("--pulumi", "pulumi_file", type=click.Path(exists=True), help="Pulumi preview JSON file")
@click.option("--pricing", "pricing_file", type=click.Path(exists=True), help="Custom pricing JSON file")
@click.option(
    "--threshold",
    type=float,
    default=None,
    help="Exit with code 1 if total monthly cost delta exceeds this value (e.g. 500 for $500)",
)
def cost(terraform_file, cloudformation_file, pulumi_file, pricing_file, threshold):
    """Estimate monthly cost impact of infrastructure changes."""
    plan = _load_plan(terraform_file, cloudformation_file, pulumi_file)
    if plan is None:
        console.print("[red]Error: Provide one of --tf, --cfn, or --pulumi[/red]")
        raise SystemExit(1)

    estimates = estimate_costs(plan, pricing_file=pricing_file)
    _render_costs(estimates, plan, console)

    if threshold is not None and plan.total_monthly_delta > threshold:
        console.print(
            f"\n[red]Total monthly cost increase of ${plan.total_monthly_delta:.2f} "
            f"exceeds threshold of ${threshold:.2f}. "
            f"Exiting with code 1 (--threshold).[/red]"
        )
        raise SystemExit(1)


@main.command()
@click.option("--tf", "terraform_file", type=click.Path(exists=True), help="Terraform plan JSON file")
@click.option("--cfn", "cloudformation_file", type=click.Path(exists=True), help="CloudFormation change set JSON file")
@click.option("--pulumi", "pulumi_file", type=click.Path(exists=True), help="Pulumi preview JSON file")
def rollback(terraform_file, cloudformation_file, pulumi_file):
    """Generate rollback commands for infrastructure changes."""
    plan = _load_plan(terraform_file, cloudformation_file, pulumi_file)
    if plan is None:
        console.print("[red]Error: Provide one of --tf, --cfn, or --pulumi[/red]")
        raise SystemExit(1)

    commands = generate_rollback_commands(plan)
    for cmd in commands:
        console.print(cmd)


@main.command()
def mcp():
    """Run as an MCP (Model Context Protocol) server over stdio.

    AI coding agents (Claude Code, Cursor, etc.) use this to interact
    with deploydiff tools directly.
    """
    try:
        from click_to_mcp import serve_stdio
    except ImportError:
        print("Error: click-to-mcp is required for MCP support. Install with: pip install click-to-mcp")
        raise SystemExit(1) from None
    serve_stdio(main, name="deploydiff")


def _load_plan(
    terraform_file: str | None,
    cloudformation_file: str | None,
    pulumi_file: str | None,
) -> DeployPlan | None:
    """Load a deployment plan from the specified file."""
    sources = [terraform_file, cloudformation_file, pulumi_file]
    provided = [s for s in sources if s is not None]

    if len(provided) == 0:
        return None
    if len(provided) > 1:
        console.print("[red]Error: Provide only one source file (--tf, --cfn, or --pulumi)[/red]")
        raise SystemExit(1)

    if terraform_file:
        return parse_terraform_plan(terraform_file)
    elif cloudformation_file:
        return parse_cloudformation_changeset(cloudformation_file)
    elif pulumi_file:
        return parse_pulumi_preview(pulumi_file)

    return None


def _render_costs(estimates: list[CostEstimate], plan: DeployPlan, console: Console) -> None:
    """Render cost estimates to the console."""
    from rich import box
    from rich.table import Table

    table = Table(title="Cost Impact Estimate", box=box.ROUNDED, show_header=True)
    table.add_column("Resource", style="bold")
    table.add_column("Before ($/mo)", justify="right")
    table.add_column("After ($/mo)", justify="right")
    table.add_column("Delta ($/mo)", justify="right")

    for est in estimates:
        delta = est.monthly_delta
        if delta > 0:
            delta_str = f"[red]+${delta:.2f}[/red]"
        elif delta < 0:
            delta_str = f"[green]-${abs(delta):.2f}[/green]"
        else:
            delta_str = "$0.00"

        table.add_row(
            est.resource_address,
            f"${est.monthly_cost_before:.2f}",
            f"${est.monthly_cost_after:.2f}",
            delta_str,
        )

    console.print(table)

    total = plan.total_monthly_delta
    if total > 0:
        console.print(f"\n[bold red]Total monthly increase: +${total:.2f}[/bold red]")
    elif total < 0:
        console.print(f"\n[bold green]Total monthly decrease: -${abs(total):.2f}[/bold green]")
    else:
        console.print("\n[bold]Total monthly change: $0.00[/bold]")
