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

try:
    from revenueholdings_license import require_license
except ImportError:
    def require_license(tool):
        def decorator(func):
            return func
        return decorator

console = Console()


@click.group()
@click.version_option(package_name="deploydiff")
def main():
    """DeployDiff - Preview infrastructure changes with cost impact and rollback."""
    require_license("deploydiff")


@main.command()
@click.option("--tf", "terraform_file", type=click.Path(exists=True), help="Terraform plan JSON file")
@click.option("--cfn", "cloudformation_file", type=click.Path(exists=True), help="CloudFormation change set JSON file")
@click.option("--pulumi", "pulumi_file", type=click.Path(exists=True), help="Pulumi preview JSON file")
@click.option("-v", "--verbose", is_flag=True, help="Show before/after details for each change")
def preview(terraform_file, cloudformation_file, pulumi_file, verbose):
    """Preview infrastructure changes from a plan file."""
    plan = _load_plan(terraform_file, cloudformation_file, pulumi_file)
    if plan is None:
        console.print("[red]Error: Provide one of --tf, --cfn, or --pulumi[/red]")
        raise SystemExit(1)

    render_plan(plan, console, verbose=verbose)


@main.command()
@click.option("--tf", "terraform_file", type=click.Path(exists=True), help="Terraform plan JSON file")
@click.option("--cfn", "cloudformation_file", type=click.Path(exists=True), help="CloudFormation change set JSON file")
@click.option("--pulumi", "pulumi_file", type=click.Path(exists=True), help="Pulumi preview JSON file")
@click.option("--pricing", "pricing_file", type=click.Path(exists=True), help="Custom pricing JSON file")
def cost(terraform_file, cloudformation_file, pulumi_file, pricing_file):
    """Estimate monthly cost impact of infrastructure changes."""
    plan = _load_plan(terraform_file, cloudformation_file, pulumi_file)
    if plan is None:
        console.print("[red]Error: Provide one of --tf, --cfn, or --pulumi[/red]")
        raise SystemExit(1)

    estimates = estimate_costs(plan, pricing_file=pricing_file)
    _render_costs(estimates, plan, console)


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
    from click_to_mcp import serve_stdio
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
