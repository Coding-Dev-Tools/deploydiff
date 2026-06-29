"""Rollback command generation for infrastructure changes."""

from __future__ import annotations

from .models import ChangeSource, DeployPlan


def generate_rollback_commands(plan: DeployPlan) -> list[str]:
    """Generate rollback commands for a deployment plan.

    Args:
        plan: The parsed deployment plan.

    Returns:
        List of rollback commands as strings.
    """
    if plan.source == ChangeSource.TERRAFORM:
        return _terraform_rollback(plan)
    elif plan.source == ChangeSource.CLOUDFORMATION:
        return _cloudformation_rollback(plan)
    elif plan.source == ChangeSource.PULUMI:
        return _pulumi_rollback(plan)
    return [f"# Rollback not supported for source: {plan.source.value}"]


def _terraform_rollback(plan: DeployPlan) -> list[str]:
    """Generate Terraform rollback commands.

    Strategy: target the reverse of each destructive/create change.
    """
    commands: list[str] = []
    commands.append("# Terraform Rollback Commands")
    commands.append("# Run these in reverse order to undo the deployment")
    commands.append("")

    # For each create, we need to destroy it
    for change in plan.creates:
        commands.append(f"terraform destroy -target={change.address} -auto-approve")

    # For each destructive change (delete/replace), we need to re-apply it
    for change in plan.destructive_changes:
        commands.append(f"terraform apply -target={change.address} -auto-approve")

    # For updates, we can try to revert with the previous state
    for change in plan.updates:
        commands.append(
            f"# To revert {change.address}, restore previous config and run:"
        )
        commands.append(f"terraform apply -target={change.address} -auto-approve")

    if not plan.changes:
        commands.append("# No changes to roll back")

    # Add a full rollback option
    commands.append("")
    commands.append("# Or rollback the entire stack:")
    commands.append("terraform apply -auto-approve  # with previous .tf files")
    commands.append("# OR destroy everything and re-apply from a known good state:")
    commands.append("terraform destroy -auto-approve && terraform apply -auto-approve")

    return commands


def _cloudformation_rollback(plan: DeployPlan) -> list[str]:
    """Generate CloudFormation rollback commands."""
    commands: list[str] = []
    commands.append("# CloudFormation Rollback Commands")
    commands.append("")

    stack_name = ""
    if plan.raw_data:
        stack_name = plan.raw_data.get(
            "StackName", plan.raw_data.get("StackId", "STACK_NAME")
        )

    if not stack_name:
        stack_name = "STACK_NAME"

    for change in plan.creates:
        commands.append(f"# Rollback create: remove {change.address}")

    for change in plan.destructive_changes:
        commands.append(f"# Rollback delete/replace: re-create {change.address}")

    commands.append("")
    commands.append("# Full stack rollback options:")
    commands.append(
        "# Option 1: Roll back the stack update (if update-rollback triggered)"
    )
    commands.append(f"aws cloudformation rollback-stack --stack-name {stack_name}")
    commands.append("")
    commands.append("# Option 2: Delete the stack and recreate from previous template")
    commands.append(f"aws cloudformation delete-stack --stack-name {stack_name}")
    commands.append(
        f"aws cloudformation wait stack-delete-complete --stack-name {stack_name}"
    )
    commands.append(
        f"# Then redeploy with: aws cloudformation create-stack --stack-name {stack_name} ..."
    )

    return commands


def _pulumi_rollback(plan: DeployPlan) -> list[str]:
    """Generate Pulumi rollback commands."""
    commands: list[str] = []
    commands.append("# Pulumi Rollback Commands")
    commands.append("")

    # Pulumi has a built-in rollback via stack history
    commands.append("# Option 1: Cancel the ongoing update")
    commands.append("pulumi cancel")
    commands.append("")

    commands.append("# Option 2: Roll back to the previous stack state")
    commands.append("pulumi stack history  # find the revision to roll back to")
    commands.append("pulumi stack rollback <revision>")
    commands.append("")

    commands.append("# Option 3: Selective resource rollback")
    for change in plan.creates:
        commands.append(f"# Destroy newly created resource: {change.address}")
        commands.append(f"pulumi destroy -t {change.address} --yes")

    for change in plan.updates:
        commands.append(f"# Revert updated resource: {change.address}")
        commands.append(f"pulumi up -t {change.address} --yes  # with reverted code")

    for change in plan.destructive_changes:
        commands.append(f"# Recreate deleted/replaced resource: {change.address}")
        commands.append(f"pulumi up -t {change.address} --yes  # with original code")

    return commands
