"""Regression tests: wrong/non-plan JSON must fail loudly, not report 'no changes'."""

import json

import pytest
from click.testing import CliRunner

from deploydiff.cli import main
from deploydiff.cloudformation_parser import parse_cloudformation_changeset
from deploydiff.models import PlanFormatError
from deploydiff.pulumi_parser import parse_pulumi_preview
from deploydiff.terraform_parser import parse_terraform_plan

WRONG_DOCS = [
    {"name": "not-a-plan", "version": "1.0"},
    {"foo": []},
    [1, 2, 3],
]

TF_EMPTY_PLAN = {"format_version": "1.2", "resource_changes": []}
CFN_EMPTY_CHANGESET = {"ChangeSetName": "cs", "Changes": []}
PULUMI_EMPTY = {"steps": []}


@pytest.mark.parametrize("doc", WRONG_DOCS)
def test_terraform_parser_rejects_non_plan(doc):
    with pytest.raises(PlanFormatError):
        parse_terraform_plan(doc)


@pytest.mark.parametrize("doc", WRONG_DOCS)
def test_cfn_parser_rejects_non_plan(doc):
    with pytest.raises(PlanFormatError):
        parse_cloudformation_changeset(doc)


@pytest.mark.parametrize("doc", WRONG_DOCS)
def test_pulumi_parser_rejects_non_plan(doc):
    with pytest.raises(PlanFormatError):
        parse_pulumi_preview(doc)


def test_valid_empty_plans_still_parse():
    assert parse_terraform_plan(TF_EMPTY_PLAN).changes == []
    assert parse_cloudformation_changeset(CFN_EMPTY_CHANGESET).changes == []
    assert parse_pulumi_preview(PULUMI_EMPTY).changes == []


def _write(tmp_path, doc):
    f = tmp_path / "plan.json"
    f.write_text(json.dumps(doc))
    return str(f)


@pytest.mark.parametrize("flag,doc", [
    ("--tf", {"random": True}),
    ("--cfn", {"random": True}),
    ("--pulumi", {"random": True}),
])
def test_cli_exits_1_on_wrong_format(tmp_path, flag, doc):
    result = CliRunner().invoke(main, ["preview", flag, _write(tmp_path, doc)])
    assert result.exit_code == 1
    assert "does not look like" in result.output


def test_cli_still_accepts_valid_empty_plan(tmp_path):
    result = CliRunner().invoke(main, ["preview", "--tf", _write(tmp_path, TF_EMPTY_PLAN)])
    assert result.exit_code == 0, result.output
