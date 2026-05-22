"""Terraform plan JSON parser."""

from __future__ import annotations

import json
from typing import Any

from .models import ChangeAction, ChangeSource, DeployPlan, ResourceChange

# Terraform plan action mapping
TF_ACTION_MAP: dict[str, ChangeAction] = {
    "create": ChangeAction.CREATE,
    "read": ChangeAction.READ,
    "update": ChangeAction.UPDATE,
    "delete": ChangeAction.DELETE,
    "create_before_delete": ChangeAction.CREATE_BEFORE_DELETE,
    "delete_before_create": ChangeAction.DELETE_BEFORE_CREATE,
    "no-op": ChangeAction.NO_OP,
}


def parse_terraform_plan(plan_json: str | dict[str, Any]) -> DeployPlan:
    """Parse a Terraform plan JSON output into a DeployPlan.

    Args:
        plan_json: Path to plan JSON file, raw JSON string, or parsed dict.

    Returns:
        DeployPlan with parsed resource changes.
    """
    if isinstance(plan_json, str):
        try:
            data = json.loads(plan_json)
        except json.JSONDecodeError:
            # Try as file path
            with open(plan_json) as f:
                data = json.load(f)
    else:
        data = plan_json

    format_version = data.get("format_version", "")
    changes: list[ResourceChange] = []

    # Parse planned changes
    data.get("planned_values", {})
    resource_changes = data.get("resource_changes", [])

    for rc in resource_changes:
        change = rc.get("change", {})
        action_strs = change.get("actions", [])

        # Use the primary action
        primary_action = _resolve_primary_action(action_strs)
        if primary_action is None:
            continue

        # Build address from type and name
        rc_type = rc.get("type", "unknown")
        rc_name = rc.get("name", "unknown")
        rc_module = rc.get("module", "")
        address = rc.get("address", f"{rc_type}.{rc_name}")

        # Provider
        provider = rc.get("provider_name", "")

        # Get before/after values
        before = change.get("before", {})
        after = change.get("after", {})
        before_sensitive = (
            set(change.get("before_sensitive", {}).keys())
            if isinstance(change.get("before_sensitive"), dict)
            else set()
        )
        after_sensitive = (
            set(change.get("after_sensitive", {}).keys())
            if isinstance(change.get("after_sensitive"), dict)
            else set()
        )

        resource_change = ResourceChange(
            address=address,
            action=primary_action,
            resource_type=rc_type,
            resource_name=rc_name,
            source=ChangeSource.TERRAFORM,
            before=before,
            after=after,
            before_sensitive=before_sensitive,
            after_sensitive=after_sensitive,
            module_path=rc_module if rc_module else None,
            provider=provider,
        )
        changes.append(resource_change)

    # Parse output changes
    data.get("output_changes", {})
    # We track these as metadata but don't create ResourceChange entries

    return DeployPlan(
        source=ChangeSource.TERRAFORM,
        changes=changes,
        raw_data=data,
        format_version=format_version,
    )


def _resolve_primary_action(actions: list[str]) -> ChangeAction | None:
    """Resolve a list of Terraform actions to a single ChangeAction."""
    if not actions:
        return None

    # Multi-action cases — preserve original order to distinguish
    # [create, delete] = create before delete, [delete, create] = delete before create
    if len(actions) == 2:
        if actions == ["create", "delete"]:
            return ChangeAction.CREATE_BEFORE_DELETE
        if actions == ["delete", "create"]:
            return ChangeAction.DELETE_BEFORE_CREATE

    # Single action
    action_str = actions[0] if actions else "no-op"
    return TF_ACTION_MAP.get(action_str)
