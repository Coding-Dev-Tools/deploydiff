"""CloudFormation change set parser."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ChangeAction, ChangeSource, DeployPlan, PlanFormatError, ResourceChange

# CloudFormation action mapping
CFN_ACTION_MAP: dict[str, ChangeAction] = {
    "Add": ChangeAction.CREATE,
    "Modify": ChangeAction.UPDATE,
    "Remove": ChangeAction.DELETE,
    "Import": ChangeAction.IMPORT,
}

# CloudFormation replacement mapping
CFN_REPLACEMENT_MAP: dict[str, bool] = {
    "True": True,
    "true": True,
    "Conditional": True,
    "False": False,
    "false": False,
}


def parse_cloudformation_changeset(changeset_json: str | dict[str, Any]) -> DeployPlan:
    """Parse a CloudFormation change set into a DeployPlan.

    Accepts the JSON output of `aws cloudformation describe-change-set`
    or a change set JSON file.

    Args:
        changeset_json: Path to JSON file, raw JSON string, or parsed dict.

    Returns:
        DeployPlan with parsed resource changes.
    """
    if isinstance(changeset_json, str):
        try:
            data = json.loads(changeset_json)
        except json.JSONDecodeError:
            path = Path(changeset_json)
            if not path.is_file():
                raise FileNotFoundError(
                    f"Input is neither valid JSON nor an existing file: {changeset_json!r}"
                ) from None
            with open(path) as f:
                data = json.load(f)
    else:
        data = changeset_json
    if not isinstance(data, dict) or ("Changes" not in data and "changes" not in data):
        raise PlanFormatError("Input does not look like a CloudFormation change set JSON (expected 'Changes' or 'changes' key). Did you pass the right --cfn file?")

    changes: list[ResourceChange] = []
    changes_list = data.get("Changes", data.get("changes", []))


    for change_entry in changes_list:
        resource_change_data = change_entry.get(
            "ResourceChange", change_entry.get("resource_change", {})
        )
        action_str = change_entry.get(
            "Action", resource_change_data.get("Action", "Modify")
        )

        action = CFN_ACTION_MAP.get(action_str, ChangeAction.UPDATE)

        # Check if this is a replacement
        replacement = resource_change_data.get("Replacement", "")
        if CFN_REPLACEMENT_MAP.get(str(replacement), False):
            action = ChangeAction.REPLACE

        resource_type = resource_change_data.get(
            "Type", resource_change_data.get("ResourceType", "unknown")
        )
        resource_name = resource_change_data.get(
            "LogicalResourceId",
            resource_change_data.get("PhysicalResourceId", "unknown"),
        )
        address = resource_change_data.get(
            "LogicalResourceId", f"{resource_type}.{resource_name}"
        )

        # Scope details for update changes
        details = resource_change_data.get("Details", [])

        before = {}
        after = {}
        for detail in details:
            target = detail.get("Target", {})
            attr = target.get("Attribute", "")
            if attr:
                before[attr] = target.get("BeforeValue", "N/A")
                after[attr] = target.get("AfterValue", "N/A")

        resource_change = ResourceChange(
            address=address,
            action=action,
            resource_type=resource_type,
            resource_name=resource_name,
            source=ChangeSource.CLOUDFORMATION,
            before=before or None,
            after=after or None,
            provider="aws",
        )
        changes.append(resource_change)

    return DeployPlan(
        source=ChangeSource.CLOUDFORMATION,
        changes=changes,
        raw_data=data,
    )
