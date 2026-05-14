"""Pulumi preview parser."""

from __future__ import annotations

import json
from typing import Any

from .models import ChangeAction, ChangeSource, DeployPlan, ResourceChange

# Pulumi step mapping
PULUMI_STEP_MAP: dict[str, ChangeAction] = {
    "create": ChangeAction.CREATE,
    "update": ChangeAction.UPDATE,
    "delete": ChangeAction.DELETE,
    "replace": ChangeAction.REPLACE,
    "create-replacement": ChangeAction.CREATE_BEFORE_DELETE,
    "delete-replaced": ChangeAction.DELETE_BEFORE_CREATE,
    "read": ChangeAction.READ,
    "refresh": ChangeAction.READ,
    "import": ChangeAction.IMPORT,
    "same": ChangeAction.NO_OP,
    "diff": ChangeAction.UPDATE,
}


def parse_pulumi_preview(preview_json: str | dict[str, Any]) -> DeployPlan:
    """Parse a Pulumi preview JSON output into a DeployPlan.

    Accepts the JSON output of `pulumi preview --json`
    or a Pulumi preview JSON file.

    Args:
        preview_json: Path to JSON file, raw JSON string, or parsed dict.

    Returns:
        DeployPlan with parsed resource changes.
    """
    if isinstance(preview_json, str):
        try:
            data = json.loads(preview_json)
        except json.JSONDecodeError:
            with open(preview_json, "r") as f:
                data = json.load(f)
    else:
        data = preview_json

    changes: list[ResourceChange] = []

    # Pulumi preview JSON has a "steps" array
    steps = data.get("steps", [])

    # Also support the resource-oriented format
    resources = data.get("resourceChanges", data.get("resources", {}))

    # Process steps-based format
    for step in steps:
        urn = step.get("urn", step.get("old", {}).get("urn", "unknown"))
        step_type = step.get("step", step.get("op", "same"))

        action = PULUMI_STEP_MAP.get(step_type, ChangeAction.UPDATE)

        # Extract resource type and name from URN
        resource_type, resource_name = _parse_pulumi_urn(urn)

        old_state = step.get("old", {})
        new_state = step.get("new", {})

        before = {k: v for k, v in old_state.items() if k not in ("urn", "id")} if old_state else None
        after = {k: v for k, v in new_state.items() if k not in ("urn", "id")} if new_state else None

        provider = _extract_provider_from_type(resource_type)

        resource_change = ResourceChange(
            address=urn,
            action=action,
            resource_type=resource_type,
            resource_name=resource_name,
            source=ChangeSource.PULUMI,
            before=before,
            after=after,
            provider=provider,
        )
        changes.append(resource_change)

    # Process resource-changes-based format (count-based)
    if not steps and isinstance(resources, dict):
        for resource_type, counts in resources.items():
            for action_str, count in counts.items():
                action = PULUMI_STEP_MAP.get(action_str, ChangeAction.UPDATE)
                for i in range(count):
                    resource_change = ResourceChange(
                        address=f"{resource_type}[{i}]",
                        action=action,
                        resource_type=resource_type,
                        resource_name=f"{resource_type}-{i}",
                        source=ChangeSource.PULUMI,
                        provider=_extract_provider_from_type(resource_type),
                    )
                    changes.append(resource_change)

    return DeployPlan(
        source=ChangeSource.PULUMI,
        changes=changes,
        raw_data=data,
    )


def _parse_pulumi_urn(urn: str) -> tuple[str, str]:
    """Extract resource type and name from a Pulumi URN.

    URN format: urn:pulumi:stack::project::type::name
    Type may contain colons (e.g., aws:s3/bucket:Bucket).
    """
    parts = urn.split("::")
    if len(parts) >= 4:
        return parts[-2], parts[-1]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return "unknown", urn


def _extract_provider_from_type(resource_type: str) -> str:
    """Guess the cloud provider from a Pulumi resource type."""
    lower = resource_type.lower()
    if "aws" in lower:
        return "aws"
    if "azure" in lower or "azure-native" in lower:
        return "azure"
    if "gcp" in lower or "google-native" in lower:
        return "gcp"
    return "unknown"
