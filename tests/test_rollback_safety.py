"""Regression tests for rollback command generation safety/correctness."""

from deploydiff.models import (
    ChangeAction,
    ChangeSource,
    DeployPlan,
    ResourceChange,
)
from deploydiff.rollback import generate_rollback_commands


def _tf_change(address, action):
    return ResourceChange(
        address=address,
        action=action,
        resource_type="aws_instance",
        resource_name=address.split(".")[-1],
        source=ChangeSource.TERRAFORM,
    )


def test_empty_plan_returns_only_noop_message():
    plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
    commands = generate_rollback_commands(plan)
    assert commands == ["# No changes to roll back"]
    # The dangerous blanket destroy-everything suggestion must not appear.
    assert not any("destroy -auto-approve &&" in c for c in commands)


def test_read_and_noop_only_plans_return_noop_message():
    for action in (ChangeAction.READ, ChangeAction.NO_OP):
        plan = DeployPlan(
            source=ChangeSource.TERRAFORM,
            changes=[_tf_change("data.aws_ami.current", action)],
        )
        assert generate_rollback_commands(plan) == ["# No changes to roll back"]


def test_create_before_delete_not_double_commanded():
    """A create-first replacement must not produce both destroy and apply
    for the same resource (contradictory rollback commands)."""
    change = _tf_change("aws_instance.web", ChangeAction.CREATE_BEFORE_DELETE)
    plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[change])
    commands = generate_rollback_commands(plan)
    destroys = [c for c in commands if c.startswith("terraform destroy -target=aws_instance.web")]
    applies = [c for c in commands if c.startswith("terraform apply -target=aws_instance.web")]
    assert destroys == [], "replacement should not be destroyed on rollback"
    assert len(applies) == 1


def test_delete_before_create_and_replace_use_one_restore_command():
    for action in (ChangeAction.DELETE_BEFORE_CREATE, ChangeAction.REPLACE):
        change = _tf_change("aws_instance.web", action)
        commands = generate_rollback_commands(
            DeployPlan(source=ChangeSource.TERRAFORM, changes=[change])
        )
        restores = [c for c in commands if "-target=aws_instance.web" in c]
        assert len(restores) == 1
        assert not any("destroy -target=aws_instance.web" in c for c in commands)


def test_pure_create_gets_destroy_pure_delete_gets_apply():
    created = _tf_change("aws_instance.new", ChangeAction.CREATE)
    deleted = _tf_change("aws_instance.old", ChangeAction.DELETE)
    plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[created, deleted])
    commands = generate_rollback_commands(plan)
    assert "terraform destroy -target=aws_instance.new -auto-approve" in commands
    assert any(
        c.startswith("terraform apply -target=aws_instance.old") for c in commands
    )
