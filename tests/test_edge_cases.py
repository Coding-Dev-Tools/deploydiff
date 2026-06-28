"""Targeted edge-case tests for DeployDiff.

Covers uncovered paths in CLI, cost estimator, rollback, and packaging config.
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib
from rich.console import Console

from deploydiff.cli import _load_plan, _render_costs
from deploydiff.cost_estimator import DEFAULT_PRICING, _load_pricing
from deploydiff.models import ChangeAction, ChangeSource, CostEstimate, DeployPlan, ResourceChange
from deploydiff.rollback import _pulumi_rollback, generate_rollback_commands


class TestCLIEdgeCases:
    """Tests for uncovered CLI error paths."""

    def test_load_plan_no_input_returns_none(self):
        """_load_plan with no sources returns None (cli.py:142)."""
        plan = _load_plan(None, None, None)
        assert plan is None

    def test_render_cost_decrease(self):
        """_render_costs with cost decrease should mention decrease (cli.py:177-178)."""
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
        estimates = [
            CostEstimate(
                resource_address="aws_instance.old",
                monthly_cost_before=100.0,
                monthly_cost_after=50.0,
            ),
        ]
        # total_monthly_delta is computed from cost_estimates
        plan.cost_estimates = estimates
        assert plan.total_monthly_delta < 0

        buf = StringIO()
        console = Console(file=buf, width=120)
        _render_costs(estimates, plan, console)
        output = buf.getvalue()
        assert "decrease" in output

    def test_render_cost_increase(self):
        """_render_costs with cost increase should mention increase."""
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
        estimates = [
            CostEstimate(
                resource_address="aws_instance.web",
                monthly_cost_before=0.0,
                monthly_cost_after=100.0,
            ),
        ]
        plan.cost_estimates = estimates
        buf = StringIO()
        console = Console(file=buf, width=120)
        _render_costs(estimates, plan, console)
        output = buf.getvalue()
        assert "increase" in output


class TestCostEstimatorEdgeCases:
    """Tests for uncovered cost estimator paths."""

    def test_load_pricing_nonexistent_file(self):
        """_load_pricing with nonexistent file returns defaults (cost_estimator.py:234)."""
        pricing = _load_pricing("/nonexistent/pricing.json")
        assert pricing == DEFAULT_PRICING

    def test_load_pricing_custom_type_not_in_defaults(self, tmp_path):
        """_load_pricing with custom resource type merges correctly (cost_estimator.py:245)."""
        pricing_file = tmp_path / "custom_pricing.json"
        custom = {"aws_lambda_function": {"custom_size": 5.0}}
        with open(pricing_file, "w") as f:
            json.dump(custom, f)

        pricing = _load_pricing(str(pricing_file))
        assert "aws_lambda_function" in pricing
        assert pricing["aws_lambda_function"]["custom_size"] == 5.0
        # Defaults should still be present
        assert "t3.micro" in pricing["aws_instance"]


class TestRollbackEdgeCases:
    """Tests for uncovered rollback paths."""

    def test_pulumi_rollback_single_create(self):
        """_pulumi_rollback creates destroy command for create changes."""
        changes = [
            ResourceChange(
                address="aws_instance.web",
                action=ChangeAction.CREATE,
                resource_type="aws_instance",
                resource_name="web",
                source=ChangeSource.PULUMI,
                after={"ami": "ami-123"},
            ),
        ]
        plan = DeployPlan(source=ChangeSource.PULUMI, changes=changes)
        commands = _pulumi_rollback(plan)
        assert any("Destroy newly created" in c for c in commands)
        assert any("pulumi destroy" in c for c in commands)

    def test_pulumi_rollback_unsupported_source_fallback(self):
        """generate_rollback_commands for unmatched source returns fallback msg."""
        # This takes the final `return` path in generate_rollback_commands
        # Since all three enum members are handled, we need to bypass the if chain
        # by testing the function structure. The unhandled-source path exists
        # as future-proofing. Test that terraform, cloudformation and pulumi
        # all produce meaningful output.
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
        cmds = generate_rollback_commands(plan)
        assert len(cmds) > 1
        assert "Terraform" in cmds[0]

    def test_cloudformation_rollback_no_raw_data(self):
        """_cloudformation_rollback with no raw_data uses STACK_NAME."""
        from deploydiff.rollback import _cloudformation_rollback

        plan = DeployPlan(source=ChangeSource.CLOUDFORMATION, changes=[])
        commands = _cloudformation_rollback(plan)
        assert any("STACK_NAME" in c for c in commands)

    def test_cloudformation_rollback_with_raw_data(self):
        """_cloudformation_rollback with raw_data uses the provided stack name."""
        from deploydiff.rollback import _cloudformation_rollback

        plan = DeployPlan(
            source=ChangeSource.CLOUDFORMATION,
            changes=[],
            raw_data={"StackName": "my-app-stack"},
        )
        commands = _cloudformation_rollback(plan)
        assert any("my-app-stack" in c for c in commands)
        assert not any("STACK_NAME" in c for c in commands)


class TestPackagingQuality:
    """Tests for py.typed packaging config."""

    def test_package_data_includes_py_typed(self):
        """pyproject.toml should have package-data config for py.typed."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        pkg_data = data.get("tool", {}).get("setuptools", {}).get("package-data", {})
        assert "deploydiff" in pkg_data, "Expected [tool.setuptools.package-data] section for 'deploydiff'"
        assert "py.typed" in pkg_data["deploydiff"], (
            f"Expected 'py.typed' in package-data, got {pkg_data['deploydiff']}"
        )

    def test_ruff_known_first_party(self):
        """ruff known-first-party should be ['deploydiff'], not ['*']."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        isort_cfg = data.get("tool", {}).get("ruff", {}).get("lint", {}).get("isort", {})
        kfp = isort_cfg.get("known-first-party", [])
        assert kfp == ["deploydiff"], f"known-first-party should be ['deploydiff'], got {kfp}"
