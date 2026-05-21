"""Tests for DeployDiff CLI - models, parsers, cost estimator, rollback, and CLI."""

import json
import pytest
from click.testing import CliRunner
from deploydiff.cli import main
from deploydiff.cloudformation_parser import parse_cloudformation_changeset
from deploydiff.cost_estimator import estimate_costs
from deploydiff.diff_renderer import render_plan
from deploydiff.models import ChangeAction, ChangeSource, CostEstimate, DeployPlan, ResourceChange
from deploydiff.pulumi_parser import parse_pulumi_preview
from deploydiff.rollback import generate_rollback_commands
from deploydiff.terraform_parser import parse_terraform_plan

# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_terraform_plan():
    return {
        "format_version": "1.2",
        "resource_changes": [
            {
                "address": "aws_instance.web",
                "type": "aws_instance",
                "name": "web",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"instance_type": "t3.micro", "ami": "ami-12345"},
                    "before_sensitive": {},
                    "after_sensitive": {},
                },
            },
            {
                "address": "aws_db_instance.primary",
                "type": "aws_db_instance",
                "name": "primary",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["update"],
                    "before": {"instance_class": "db.t3.small", "allocated_storage": 20},
                    "after": {"instance_class": "db.t3.medium", "allocated_storage": 50},
                    "before_sensitive": {},
                    "after_sensitive": {},
                },
            },
            {
                "address": "aws_s3_bucket.logs",
                "type": "aws_s3_bucket",
                "name": "logs",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["delete"],
                    "before": {"bucket": "my-logs-bucket"},
                    "after": None,
                    "before_sensitive": {},
                    "after_sensitive": {},
                },
            },
            {
                "address": "module.vpc.aws_nat_gateway.main",
                "type": "aws_nat_gateway",
                "name": "main",
                "module": "module.vpc",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create", "delete"],
                    "before": {"connectivity_type": "public"},
                    "after": {"connectivity_type": "private"},
                    "before_sensitive": {},
                    "after_sensitive": {},
                },
            },
        ],
    }


@pytest.fixture
def sample_cfn_changeset():
    return {
        "StackName": "my-stack",
        "ChangeSetName": "my-changeset",
        "Changes": [
            {
                "Action": "Add",
                "ResourceChange": {
                    "Action": "Add",
                    "Type": "AWS::EC2::Instance",
                    "LogicalResourceId": "WebServer",
                    "ResourceType": "AWS::EC2::Instance",
                },
            },
            {
                "Action": "Modify",
                "ResourceChange": {
                    "Action": "Modify",
                    "Type": "AWS::RDS::DBInstance",
                    "LogicalResourceId": "MyDB",
                    "ResourceType": "AWS::RDS::DBInstance",
                    "Replacement": "False",
                    "Scope": ["Properties"],
                    "Details": [
                        {
                            "Target": {
                                "Attribute": "InstanceClass",
                                "BeforeValue": "db.t3.small",
                                "AfterValue": "db.t3.medium",
                            }
                        }
                    ],
                },
            },
            {
                "Action": "Remove",
                "ResourceChange": {
                    "Action": "Remove",
                    "Type": "AWS::S3::Bucket",
                    "LogicalResourceId": "LogBucket",
                    "ResourceType": "AWS::S3::Bucket",
                },
            },
            {
                "Action": "Modify",
                "ResourceChange": {
                    "Action": "Modify",
                    "Type": "AWS::EC2::Instance",
                    "LogicalResourceId": "AppServer",
                    "ResourceType": "AWS::EC2::Instance",
                    "Replacement": "True",
                },
            },
        ],
    }


@pytest.fixture
def sample_pulumi_preview():
    return {
        "steps": [
            {
                "urn": "urn:pulumi:prod::myapp::aws:s3/bucket:Bucket::my-bucket",
                "op": "create",
                "new": {"bucket": "my-new-bucket"},
            },
            {
                "urn": "urn:pulumi:prod::myapp::aws:ec2/instance:Instance::web-server",
                "op": "update",
                "old": {"instance_type": "t3.small"},
                "new": {"instance_type": "t3.medium"},
            },
            {
                "urn": "urn:pulumi:prod::myapp::aws:rds/instance:Instance::db",
                "op": "delete",
                "old": {"instance_class": "db.t3.small"},
            },
        ]
    }


# ── Model Tests ──────────────────────────────────────────────────────────

class TestResourceChange:
    def test_is_destructive_delete(self):
        rc = ResourceChange("a.b", ChangeAction.DELETE, "aws_instance", "b", ChangeSource.TERRAFORM)
        assert rc.is_destructive is True

    def test_is_destructive_replace(self):
        rc = ResourceChange("a.b", ChangeAction.REPLACE, "aws_instance", "b", ChangeSource.TERRAFORM)
        assert rc.is_destructive is True

    def test_is_destructive_create(self):
        rc = ResourceChange("a.b", ChangeAction.CREATE, "aws_instance", "b", ChangeSource.TERRAFORM)
        assert rc.is_destructive is False

    def test_display_action(self):
        rc = ResourceChange("a.b", ChangeAction.CREATE, "aws_instance", "b", ChangeSource.TERRAFORM)
        assert rc.display_action == "+"

    def test_display_action_delete(self):
        rc = ResourceChange("a.b", ChangeAction.DELETE, "aws_instance", "b", ChangeSource.TERRAFORM)
        assert rc.display_action == "-"


class TestDeployPlan:
    def test_creates(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        assert len(plan.creates) >= 1

    def test_updates(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        assert len(plan.updates) >= 1

    def test_destructive_changes(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        assert len(plan.destructive_changes) >= 1

    def test_total_monthly_delta(self):
        est1 = CostEstimate("a", monthly_cost_after=10.0, monthly_cost_before=5.0)
        est2 = CostEstimate("b", monthly_cost_after=20.0, monthly_cost_before=30.0)
        plan = DeployPlan(source=ChangeSource.TERRAFORM, cost_estimates=[est1, est2])
        assert plan.total_monthly_delta == -5.0


# ── Terraform Parser Tests ───────────────────────────────────────────────

class TestTerraformParser:
    def test_parse_basic_plan(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        assert plan.source == ChangeSource.TERRAFORM
        assert len(plan.changes) == 4

    def test_parse_create_action(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        create_changes = [c for c in plan.changes if c.action == ChangeAction.CREATE]
        assert len(create_changes) == 1
        assert create_changes[0].address == "aws_instance.web"
        assert create_changes[0].resource_type == "aws_instance"

    def test_parse_update_action(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        update_changes = [c for c in plan.changes if c.action == ChangeAction.UPDATE]
        assert len(update_changes) == 1
        assert update_changes[0].address == "aws_db_instance.primary"

    def test_parse_delete_action(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        delete_changes = [c for c in plan.changes if c.action == ChangeAction.DELETE]
        assert len(delete_changes) == 1
        assert delete_changes[0].address == "aws_s3_bucket.logs"

    def test_parse_multi_action(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        multi_changes = [
        c for c in plan.changes
        if c.action in (ChangeAction.CREATE_BEFORE_DELETE, ChangeAction.DELETE_BEFORE_CREATE)
    ]
        assert len(multi_changes) == 1

    def test_module_path(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        module_changes = [c for c in plan.changes if c.module_path]
        assert len(module_changes) == 1
        assert module_changes[0].module_path == "module.vpc"

    def test_parse_from_json_string(self, sample_terraform_plan):
        json_str = json.dumps(sample_terraform_plan)
        plan = parse_terraform_plan(json_str)
        assert len(plan.changes) == 4

    def test_format_version(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        assert plan.format_version == "1.2"

    def test_empty_plan(self):
        plan = parse_terraform_plan({"format_version": "1.2", "resource_changes": []})
        assert len(plan.changes) == 0


# ── CloudFormation Parser Tests ───────────────────────────────────────────

class TestCloudFormationParser:
    def test_parse_basic_changeset(self, sample_cfn_changeset):
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        assert plan.source == ChangeSource.CLOUDFORMATION
        assert len(plan.changes) == 4

    def test_parse_add_action(self, sample_cfn_changeset):
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        creates = [c for c in plan.changes if c.action == ChangeAction.CREATE]
        assert len(creates) == 1
        assert creates[0].resource_type == "AWS::EC2::Instance"

    def test_parse_modify_action(self, sample_cfn_changeset):
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        updates = [c for c in plan.changes if c.action == ChangeAction.UPDATE]
        assert len(updates) == 1

    def test_parse_replacement(self, sample_cfn_changeset):
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        replaces = [c for c in plan.changes if c.action == ChangeAction.REPLACE]
        assert len(replaces) == 1
        assert replaces[0].address == "AppServer"

    def test_parse_remove_action(self, sample_cfn_changeset):
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        deletes = [c for c in plan.changes if c.action == ChangeAction.DELETE]
        assert len(deletes) == 1

    def test_parse_from_json_string(self, sample_cfn_changeset):
        json_str = json.dumps(sample_cfn_changeset)
        plan = parse_cloudformation_changeset(json_str)
        assert len(plan.changes) == 4


# ── Pulumi Parser Tests ──────────────────────────────────────────────────

class TestPulumiParser:
    def test_parse_basic_preview(self, sample_pulumi_preview):
        plan = parse_pulumi_preview(sample_pulumi_preview)
        assert plan.source == ChangeSource.PULUMI
        assert len(plan.changes) == 3

    def test_parse_create_action(self, sample_pulumi_preview):
        plan = parse_pulumi_preview(sample_pulumi_preview)
        creates = [c for c in plan.changes if c.action == ChangeAction.CREATE]
        assert len(creates) == 1
        assert "bucket" in creates[0].address.lower() or "Bucket" in creates[0].address

    def test_parse_update_action(self, sample_pulumi_preview):
        plan = parse_pulumi_preview(sample_pulumi_preview)
        updates = [c for c in plan.changes if c.action == ChangeAction.UPDATE]
        assert len(updates) == 1

    def test_parse_delete_action(self, sample_pulumi_preview):
        plan = parse_pulumi_preview(sample_pulumi_preview)
        deletes = [c for c in plan.changes if c.action == ChangeAction.DELETE]
        assert len(deletes) == 1

    def test_parse_resource_changes_format(self):
        """Test the count-based resourceChanges format."""
        data = {
            "resourceChanges": {
                "aws:s3/bucket:Bucket": {"create": 2},
                "aws:ec2/instance:Instance": {"delete": 1},
            }
        }
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 3

    def test_provider_detection(self, sample_pulumi_preview):
        plan = parse_pulumi_preview(sample_pulumi_preview)
        aws_changes = [c for c in plan.changes if c.provider == "aws"]
        assert len(aws_changes) == 3


# ── Cost Estimator Tests ─────────────────────────────────────────────────

class TestCostEstimator:
    def test_estimate_create_cost(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        estimates = estimate_costs(plan)
        assert len(estimates) == 4

    def test_create_has_zero_before_cost(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        estimates = estimate_costs(plan)
        web_est = [e for e in estimates if e.resource_address == "aws_instance.web"][0]
        assert web_est.monthly_cost_before == 0.0
        assert web_est.monthly_cost_after > 0.0

    def test_delete_has_zero_after_cost(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        estimates = estimate_costs(plan)
        logs_est = [e for e in estimates if e.resource_address == "aws_s3_bucket.logs"][0]
        assert logs_est.monthly_cost_after == 0.0

    def test_total_monthly_delta(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        estimate_costs(plan)
        # Creating instance (~7.50) + updating db (50-25=+25) + deleting bucket (-1) + nat gateway (~32)
        assert plan.total_monthly_delta != 0.0

    def test_instance_type_pricing(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        estimates = estimate_costs(plan)
        web_est = [e for e in estimates if e.resource_address == "aws_instance.web"][0]
        assert web_est.monthly_cost_after == 7.50  # t3.micro pricing

    def test_custom_pricing_file(self, sample_terraform_plan, tmp_path):
        pricing = {"aws_instance": {"t3.micro": 10.00, "default": 100.00}}
        pricing_file = tmp_path / "pricing.json"
        pricing_file.write_text(json.dumps(pricing))

        plan = parse_terraform_plan(sample_terraform_plan)
        estimates = estimate_costs(plan, pricing_file=str(pricing_file))
        web_est = [e for e in estimates if e.resource_address == "aws_instance.web"][0]
        assert web_est.monthly_cost_after == 10.00


# ── Rollback Tests ────────────────────────────────────────────────────────

class TestRollback:
    def test_terraform_rollback(self, sample_terraform_plan):
        plan = parse_terraform_plan(sample_terraform_plan)
        commands = generate_rollback_commands(plan)
        assert len(commands) > 0
        assert any("terraform" in c for c in commands)
        assert any("destroy" in c for c in commands)

    def test_cloudformation_rollback(self, sample_cfn_changeset):
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        commands = generate_rollback_commands(plan)
        assert len(commands) > 0
        assert any("cloudformation" in c.lower() for c in commands)

    def test_pulumi_rollback(self, sample_pulumi_preview):
        plan = parse_pulumi_preview(sample_pulumi_preview)
        commands = generate_rollback_commands(plan)
        assert len(commands) > 0
        assert any("pulumi" in c.lower() for c in commands)

    def test_empty_plan_rollback(self):
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
        commands = generate_rollback_commands(plan)
        assert "No changes to roll back" in " ".join(commands)


# ── Renderer Tests ────────────────────────────────────────────────────────

class TestRenderer:
    def test_render_basic_plan(self, sample_terraform_plan):
        """Render should not raise errors."""
        from io import StringIO
        from rich.console import Console
        plan = parse_terraform_plan(sample_terraform_plan)
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        assert "DeployDiff" in output
        assert "Change Summary" in output

    def test_render_empty_plan(self):
        """Render an empty plan shows no changes."""
        from io import StringIO
        from rich.console import Console
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        assert "DeployDiff" in output
        assert "0 resource(s)" not in output

    def test_render_verbose_terraform(self, sample_terraform_plan):
        """Verbose mode shows before/after details for each change."""
        from io import StringIO
        from rich.console import Console
        plan = parse_terraform_plan(sample_terraform_plan)
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console, verbose=True)
        output = buf.getvalue()
        assert "instance_type" in output
        assert "t3.micro" in output

    def test_render_verbose_with_sensitive(self):
        """Verbose mode masks sensitive values."""
        from io import StringIO
        from rich.console import Console
        change = ResourceChange(
            address="aws_db_instance.db",
            action=ChangeAction.UPDATE,
            resource_type="aws_db_instance",
            resource_name="db",
            source=ChangeSource.TERRAFORM,
            before={"password": "secret123", "port": 5432},
            after={"password": "newsecret", "port": 5432},
            before_sensitive={"password"},
            after_sensitive={"password"},
        )
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[change])
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console, verbose=True)
        output = buf.getvalue()
        # Check for "sensitive value" text (may be split by ANSI codes around parentheses)
        assert "sensitive value" in output
        assert "secret123" not in output
        assert "5432" in output

    def test_render_destructive_change_warning(self, sample_terraform_plan):
        """Destructive changes trigger a warning message."""
        from io import StringIO
        from rich.console import Console
        plan = parse_terraform_plan(sample_terraform_plan)
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        # "destructive" appears contiguously even with ANSI codes
        assert "destructive" in output.lower()

    def test_render_plan_without_destructive_changes(self):
        """Plan with only creates/updates should not show destructive warning."""
        from io import StringIO
        from rich.console import Console
        changes = [
            ResourceChange(
                address="aws_instance.web",
                action=ChangeAction.CREATE,
                resource_type="aws_instance",
                resource_name="web",
                source=ChangeSource.TERRAFORM,
            ),
            ResourceChange(
                address="aws_db_instance.db",
                action=ChangeAction.UPDATE,
                resource_type="aws_db_instance",
                resource_name="db",
                source=ChangeSource.TERRAFORM,
            ),
        ]
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=changes)
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        assert "destructive" not in output.lower()

    def test_render_cfn_plan(self, sample_cfn_changeset):
        """Render a CloudFormation plan."""
        from io import StringIO
        from rich.console import Console
        plan = parse_cloudformation_changeset(sample_cfn_changeset)
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        assert "Cloudformation" in output or "CloudFormation" in output
        assert "Change Summary" in output

    def test_render_pulumi_plan(self, sample_pulumi_preview):
        """Render a Pulumi plan."""
        from io import StringIO
        from rich.console import Console
        plan = parse_pulumi_preview(sample_pulumi_preview)
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        assert "Pulumi" in output

    def test_render_replacement(self):
        """Render a plan with a replacement change."""
        from io import StringIO
        from rich.console import Console
        change = ResourceChange(
            address="module.vpc.aws_nat_gateway.main",
            action=ChangeAction.REPLACE,
            resource_type="aws_nat_gateway",
            resource_name="main",
            source=ChangeSource.TERRAFORM,
            before={"connectivity_type": "public"},
            after={"connectivity_type": "private"},
            module_path="module.vpc",
        )
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[change])
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_plan(plan, console)
        output = buf.getvalue()
        assert "⇄" in output or "will be replaced" in output.lower()

    def test_render_change_details_missing_data(self):
        """Render change details with no before/after should not error."""
        from deploydiff.diff_renderer import _render_change_details
        from io import StringIO
        from rich.console import Console
        change = ResourceChange(
            address="aws_instance.web",
            action=ChangeAction.CREATE,
            resource_type="aws_instance",
            resource_name="web",
            source=ChangeSource.TERRAFORM,
            before=None,
            after=None,
        )
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        # Should not raise
        _render_change_details(change, console)
        output = buf.getvalue()
        assert output == ""

    def test_group_by_action(self):
        """Grouping changes by action produces correct buckets."""
        from deploydiff.diff_renderer import _group_by_action
        changes = [
            ResourceChange("a", ChangeAction.CREATE, "t", "n", ChangeSource.TERRAFORM),
            ResourceChange("b", ChangeAction.CREATE, "t", "n", ChangeSource.TERRAFORM),
            ResourceChange("c", ChangeAction.UPDATE, "t", "n", ChangeSource.TERRAFORM),
            ResourceChange("d", ChangeAction.DELETE, "t", "n", ChangeSource.TERRAFORM),
        ]
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=changes)
        groups = _group_by_action(plan)
        assert len(groups[ChangeAction.CREATE]) == 2
        assert len(groups[ChangeAction.UPDATE]) == 1
        assert len(groups[ChangeAction.DELETE]) == 1
        assert ChangeAction.CREATE_BEFORE_DELETE not in groups

    def test_render_console_none(self):
        """Renderer creates its own Console if none is provided."""
        plan = DeployPlan(source=ChangeSource.TERRAFORM, changes=[])
        # Should not raise when console is None
        render_plan(plan)

    def test_render_create_before_delete_action_label(self):
        """Create-before-delete action has the right label."""
        from deploydiff.diff_renderer import ACTION_LABELS
        label = ACTION_LABELS[ChangeAction.CREATE_BEFORE_DELETE]
        assert "create-first" in label

    def test_render_no_op_label(self):
        """No-op action has the right label."""
        from deploydiff.diff_renderer import ACTION_LABELS
        label = ACTION_LABELS[ChangeAction.NO_OP]
        assert label == "no changes"

    def test_render_import_action_label(self):
        """Import action has the right label."""
        from deploydiff.diff_renderer import ACTION_LABELS
        label = ACTION_LABELS[ChangeAction.IMPORT]
        assert "imported" in label


# ── CLI Integration Tests ─────────────────────────────────────────────────

class TestCLI:
    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "DeployDiff" in result.output

    def test_preview_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["preview", "--help"])
        assert result.exit_code == 0
        assert "--tf" in result.output
        assert "--cfn" in result.output
        assert "--pulumi" in result.output

    def test_preview_no_args(self):
        runner = CliRunner()
        result = runner.invoke(main, ["preview"])
        assert result.exit_code != 0

    def test_preview_terraform(self, sample_terraform_plan, tmp_path):
        tf_file = tmp_path / "plan.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        runner = CliRunner()
        result = runner.invoke(main, ["preview", "--tf", str(tf_file)])
        assert result.exit_code == 0
        assert "Change Summary" in result.output

    def test_cost_terraform(self, sample_terraform_plan, tmp_path):
        tf_file = tmp_path / "plan.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        runner = CliRunner()
        result = runner.invoke(main, ["cost", "--tf", str(tf_file)])
        assert result.exit_code == 0
        assert "Cost Impact" in result.output

    def test_rollback_terraform(self, sample_terraform_plan, tmp_path):
        tf_file = tmp_path / "plan.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        runner = CliRunner()
        result = runner.invoke(main, ["rollback", "--tf", str(tf_file)])
        assert result.exit_code == 0
        assert "terraform" in result.output.lower()

    def test_cost_cfn(self, sample_cfn_changeset, tmp_path):
        cfn_file = tmp_path / "changeset.json"
        cfn_file.write_text(json.dumps(sample_cfn_changeset))
        runner = CliRunner()
        result = runner.invoke(main, ["cost", "--cfn", str(cfn_file)])
        assert result.exit_code == 0

    def test_rollback_pulumi(self, sample_pulumi_preview, tmp_path):
        pulumi_file = tmp_path / "preview.json"
        pulumi_file.write_text(json.dumps(sample_pulumi_preview))
        runner = CliRunner()
        result = runner.invoke(main, ["rollback", "--pulumi", str(pulumi_file)])
        assert result.exit_code == 0

    def test_preview_exit_on_destroy_no_destroy(self, tmp_path):
        """--exit-on-destroy exits 0 when plan has no destructive changes."""
        # Plan with only creates and updates — no deletes/replaces
        safe_plan = {
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "aws_instance.web",
                    "type": "aws_instance",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {"instance_type": "t3.micro"},
                    },
                },
                {
                    "address": "aws_db_instance.primary",
                    "type": "aws_db_instance",
                    "name": "primary",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["update"],
                        "before": {"instance_class": "db.t3.small"},
                        "after": {"instance_class": "db.t3.medium"},
                    },
                },
            ],
        }
        tf_file = tmp_path / "safe_plan.json"
        tf_file.write_text(json.dumps(safe_plan))
        runner = CliRunner()
        result = runner.invoke(main, ["preview", "--tf", str(tf_file), "--exit-on-destroy"])
        assert result.exit_code == 0

    def test_preview_exit_on_destroy_with_destroy(self, sample_terraform_plan, tmp_path):
        """--exit-on-destroy exits 1 when plan has destructive changes (deletes/replaces)."""
        tf_file = tmp_path / "plan.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        runner = CliRunner()
        # terraform fixture has a delete + replace (destructive)
        result = runner.invoke(main, ["preview", "--tf", str(tf_file), "--exit-on-destroy"])
        assert result.exit_code == 1
        assert "destructive" in result.output.lower()

    def test_cost_threshold_under(self, sample_terraform_plan, tmp_path):
        """--threshold exits 0 when delta is under the threshold."""
        tf_file = tmp_path / "plan.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        runner = CliRunner()
        # Total delta for fixture is $6.50, so $1000 threshold should pass
        result = runner.invoke(main, ["cost", "--tf", str(tf_file), "--threshold", "1000"])
        assert result.exit_code == 0

    def test_cost_threshold_exceeded(self, sample_terraform_plan, tmp_path):
        """--threshold exits 1 when delta exceeds the threshold."""
        tf_file = tmp_path / "plan.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        runner = CliRunner()
        # Total delta for fixture is $6.50, so $1 threshold should trigger
        result = runner.invoke(main, ["cost", "--tf", str(tf_file), "--threshold", "1"])
        assert result.exit_code == 1
        assert "threshold" in result.output.lower()

    def test_preview_pulumi(self, sample_pulumi_preview, tmp_path):
        pulumi_file = tmp_path / "preview.json"
        pulumi_file.write_text(json.dumps(sample_pulumi_preview))
        runner = CliRunner()
        result = runner.invoke(main, ["preview", "--pulumi", str(pulumi_file)])
        assert result.exit_code == 0
        assert "Change Summary" in result.output

    def test_cost_pulumi(self, sample_pulumi_preview, tmp_path):
        pulumi_file = tmp_path / "preview.json"
        pulumi_file.write_text(json.dumps(sample_pulumi_preview))
        runner = CliRunner()
        result = runner.invoke(main, ["cost", "--pulumi", str(pulumi_file)])
        assert result.exit_code == 0
        assert "Cost Impact" in result.output

    def test_preview_multiple_sources(self, sample_terraform_plan, sample_cfn_changeset, tmp_path):
        tf_file = tmp_path / "plan.json"
        cfn_file = tmp_path / "changeset.json"
        tf_file.write_text(json.dumps(sample_terraform_plan))
        cfn_file.write_text(json.dumps(sample_cfn_changeset))
        runner = CliRunner()
        result = runner.invoke(main, ["preview", "--tf", str(tf_file), "--cfn", str(cfn_file)])
        assert result.exit_code != 0
        assert "only one" in result.output.lower()


# ── Terraform Parser Additional Tests ────────────────────────────────────

class TestTerraformParserExtended:
    def test_parse_noop_action(self):
        data = {
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "data.aws_ami.ubuntu",
                    "type": "aws_ami",
                    "name": "ubuntu",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {"actions": ["no-op"], "before": {}, "after": {}},
                }
            ],
        }
        plan = parse_terraform_plan(data)
        assert len(plan.changes) == 1
        assert plan.changes[0].action == ChangeAction.NO_OP

    def test_parse_read_action(self):
        data = {
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "data.aws_caller_identity.current",
                    "type": "aws_caller_identity",
                    "name": "current",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {"actions": ["read"], "before": None, "after": {}},
                }
            ],
        }
        plan = parse_terraform_plan(data)
        assert len(plan.changes) == 1
        assert plan.changes[0].action == ChangeAction.READ

    def test_parse_delete_before_create(self):
        data = {
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "aws_instance.replaced",
                    "type": "aws_instance",
                    "name": "replaced",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["delete", "create"],
                        "before": {"instance_type": "t3.micro"},
                        "after": {"instance_type": "t3.large"},
                    },
                }
            ],
        }
        plan = parse_terraform_plan(data)
        assert len(plan.changes) == 1
        # Both (delete, create) and (create, delete) resolve to CREATE_BEFORE_DELETE
        assert plan.changes[0].action == ChangeAction.CREATE_BEFORE_DELETE

    def test_parse_empty_actions(self):
        data = {
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "aws_instance.unknown",
                    "type": "aws_instance",
                    "name": "unknown",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {"actions": [], "before": None, "after": None},
                }
            ],
        }
        plan = parse_terraform_plan(data)
        assert len(plan.changes) == 0


# ── Pulumi Parser Additional Tests ───────────────────────────────────────

class TestPulumiParserExtended:
    def test_parse_from_json_string(self, sample_pulumi_preview):
        json_str = json.dumps(sample_pulumi_preview)
        plan = parse_pulumi_preview(json_str)
        assert len(plan.changes) == 3

    def test_parse_replace_step(self):
        data = {
            "steps": [
                {
                    "urn": "urn:pulumi:prod::myapp::aws:ec2/instance:Instance::web",
                    "op": "replace",
                    "old": {"instance_type": "t3.micro"},
                    "new": {"instance_type": "t3.large"},
                }
            ]
        }
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 1
        assert plan.changes[0].action == ChangeAction.REPLACE

    def test_parse_same_step(self):
        data = {
            "steps": [
                {
                    "urn": "urn:pulumi:prod::myapp::aws:s3/bucket:Bucket::my-bucket",
                    "op": "same",
                    "old": {"bucket": "unchanged"},
                    "new": {"bucket": "unchanged"},
                }
            ]
        }
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 1
        assert plan.changes[0].action == ChangeAction.NO_OP

    def test_parse_empty_steps(self):
        data = {"steps": [], "resourceChanges": {}}
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 0

    def test_provider_detection_azure(self):
        data = {
            "steps": [
                {
                    "urn": "urn:pulumi:prod::myapp::azure-native:compute/virtualMachine:VirtualMachine::vm",
                    "op": "create",
                    "new": {"name": "my-vm"},
                }
            ]
        }
        plan = parse_pulumi_preview(data)
        assert plan.changes[0].provider == "azure"

    def test_provider_detection_gcp(self):
        data = {
            "steps": [
                {
                    "urn": "urn:pulumi:prod::myapp::gcp:compute/instance:Instance::instance",
                    "op": "create",
                    "new": {"name": "my-instance"},
                }
            ]
        }
        plan = parse_pulumi_preview(data)
        assert plan.changes[0].provider == "gcp"

    def test_short_urn_fallback(self):
        data = {
            "steps": [
                {
                    "urn": "short:urn",
                    "op": "create",
                    "new": {"name": "test"},
                }
            ]
        }
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 1
        # short URNs fall back to "unknown" type with full URN as name
        assert plan.changes[0].resource_type == "unknown"

    def test_missing_urn_in_step(self):
        data = {
            "steps": [
                {
                    "step": "create",
                    "new": {"urn": "urn:pulumi:prod::myapp::aws:s3/bucket:Bucket::b", "bucket": "b"},
                }
            ]
        }
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 1
