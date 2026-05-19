"""Data models for infrastructure changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    CREATE_BEFORE_DELETE = "create_before_delete"
    DELETE_BEFORE_CREATE = "delete_before_create"
    REPLACE = "replace"
    IMPORT = "import"
    NO_OP = "no_op"


class ChangeSource(Enum):
    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    PULUMI = "pulumi"


@dataclass
class ResourceChange:
    """A single resource change in an infrastructure plan."""

    address: str
    action: ChangeAction
    resource_type: str
    resource_name: str
    source: ChangeSource
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    before_sensitive: set[str] = field(default_factory=set)
    after_sensitive: set[str] = field(default_factory=set)
    module_path: str | None = None
    provider: str | None = None
    replacement_triggers: list[str] = field(default_factory=list)

    @property
    def is_destructive(self) -> bool:
        return self.action in (
            ChangeAction.DELETE,
            ChangeAction.REPLACE,
            ChangeAction.CREATE_BEFORE_DELETE,
            ChangeAction.DELETE_BEFORE_CREATE,
        )

    @property
    def is_create(self) -> bool:
        return self.action in (ChangeAction.CREATE, ChangeAction.CREATE_BEFORE_DELETE)

    @property
    def is_update(self) -> bool:
        return self.action == ChangeAction.UPDATE

    @property
    def display_action(self) -> str:
        symbols = {
            ChangeAction.CREATE: "+",
            ChangeAction.READ: "→",
            ChangeAction.UPDATE: "~",
            ChangeAction.DELETE: "-",
            ChangeAction.CREATE_BEFORE_DELETE: "+/-",
            ChangeAction.DELETE_BEFORE_CREATE: "-/+",
            ChangeAction.REPLACE: "⇄",
            ChangeAction.IMPORT: "←",
            ChangeAction.NO_OP: " ",
        }
        return symbols.get(self.action, "?")


@dataclass
class CostEstimate:
    """Cost impact for a resource change."""

    resource_address: str
    monthly_cost_before: float = 0.0
    monthly_cost_after: float = 0.0
    currency: str = "USD"
    description: str = ""

    @property
    def monthly_delta(self) -> float:
        return self.monthly_cost_after - self.monthly_cost_before


@dataclass
class DeployPlan:
    """Parsed infrastructure deployment plan."""

    source: ChangeSource
    changes: list[ResourceChange] = field(default_factory=list)
    cost_estimates: list[CostEstimate] = field(default_factory=list)
    raw_data: dict[str, Any] | None = None
    format_version: str | None = None

    @property
    def creates(self) -> list[ResourceChange]:
        return [c for c in self.changes if c.is_create]

    @property
    def updates(self) -> list[ResourceChange]:
        return [c for c in self.changes if c.is_update]

    @property
    def deletes(self) -> list[ResourceChange]:
        return [c for c in self.changes if c.is_destructive]

    @property
    def total_monthly_delta(self) -> float:
        return sum(e.monthly_delta for e in self.cost_estimates)

    @property
    def destructive_changes(self) -> list[ResourceChange]:
        return [c for c in self.changes if c.is_destructive]
