"""Regression tests: unpriced resource types must be surfaced, not silently
estimated with the generic default as if it were real pricing data."""

import json

import pytest
from click.testing import CliRunner

from deploydiff.cli import main
from deploydiff.cost_estimator import DEFAULT_PRICING, _load_pricing, estimate_costs
from deploydiff.terraform_parser import parse_terraform_plan


@pytest.fixture
def mixed_plan():
    """One priced instance + one resource type absent from the pricing table."""
    return {
        "format_version": "1.2",
        "resource_changes": [
            {
                "address": "aws_instance.web",
                "type": "aws_instance",
                "name": "web",
                "change": {
                    "actions": ["create"],
                    "after": {"instance_type": "t3.micro"},
                },
            },
            {
                "address": "aws_grafana_workspace.metrics",
                "type": "aws_grafana_workspace",
                "name": "metrics",
                "change": {"actions": ["create"], "after": {}},
            },
        ],
    }


def test_unpriced_type_is_flagged(mixed_plan):
    parsed = parse_terraform_plan(mixed_plan)
    estimates = estimate_costs(parsed)
    by_addr = {e.resource_address: e for e in estimates}
    assert by_addr["aws_instance.web"].used_default_pricing is False
    assert by_addr["aws_grafana_workspace.metrics"].used_default_pricing is True


def test_description_mentions_missing_pricing(mixed_plan):
    parsed = parse_terraform_plan(mixed_plan)
    estimates = estimate_costs(parsed)
    unpriced = [e for e in estimates if e.used_default_pricing]
    assert len(unpriced) == 1
    assert "no pricing data for aws_grafana_workspace" in unpriced[0].description
    assert "generic default" in unpriced[0].description


def test_cli_cost_warns_on_unpriced_types(mixed_plan, tmp_path):
    f = tmp_path / "plan.json"
    f.write_text(json.dumps(mixed_plan))
    result = CliRunner().invoke(main, ["cost", "--tf", str(f)])
    assert result.exit_code == 0, result.output
    assert "no pricing data" in result.output
    assert "aws_grafana_workspace" in result.output
    # The priced row must NOT carry the generic marker.
    web_line = next(line for line in result.output.splitlines() if "aws_instance.web" in line)
    assert "generic est." not in web_line


def test_cli_cost_no_warning_when_all_priced(mixed_plan, tmp_path):
    mixed_plan["resource_changes"] = [mixed_plan["resource_changes"][0]]
    f = tmp_path / "plan.json"
    f.write_text(json.dumps(mixed_plan))
    from deploydiff.cli import main as cli_main

    result = CliRunner().invoke(cli_main, ["cost", "--tf", str(f)])
    assert result.exit_code == 0, result.output
    assert "no pricing data" not in result.output


def test_custom_pricing_entry_clears_flag(mixed_plan, tmp_path):
    pricing_file = tmp_path / "pricing.json"
    pricing_file.write_text(json.dumps({"aws_grafana_workspace": {"default": 9.00}}))
    parsed = parse_terraform_plan(mixed_plan)
    estimates = estimate_costs(parsed, pricing_file=pricing_file)
    by_addr = {e.resource_address: e for e in estimates}
    assert by_addr["aws_grafana_workspace.metrics"].used_default_pricing is False
    assert by_addr["aws_grafana_workspace.metrics"].monthly_cost_after == 9.00


def test_load_pricing_does_not_mutate_defaults():
    pricing = _load_pricing()
    pricing.setdefault("aws_fictitious_thing", {})["default"] = 999.0
    if "aws_instance" in pricing:
        pricing["aws_instance"]["t3.micro"] = 99999.0
    assert "aws_fictitious_thing" not in DEFAULT_PRICING
    assert DEFAULT_PRICING["aws_instance"]["t3.micro"] == 7.50


def test_missing_pricing_file_returns_deep_copy(tmp_path):
    pricing = _load_pricing(tmp_path / "does-not-exist.json")
    pricing["aws_vpc"]["default"] = 12345.0
    assert DEFAULT_PRICING["aws_vpc"]["default"] == 0.00
