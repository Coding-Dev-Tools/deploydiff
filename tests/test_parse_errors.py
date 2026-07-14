"""Tests for parser error handling: invalid input gives clear FileNotFoundError."""

from __future__ import annotations

import pytest

from deploydiff.cloudformation_parser import parse_cloudformation_changeset
from deploydiff.pulumi_parser import parse_pulumi_preview
from deploydiff.terraform_parser import parse_terraform_plan


class TestParserErrorHandling:
    """Each parser should raise a clear FileNotFoundError when input is neither
    valid JSON nor an existing file path, instead of a cryptic exception."""

    def test_terraform_invalid_string_raises_filenotfound(self):
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_terraform_plan("not-json-and-not-a-file")

    def test_terraform_empty_string_raises_filenotfound(self):
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_terraform_plan("")

    def test_cloudformation_invalid_string_raises_filenotfound(self):
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_cloudformation_changeset("not-json-and-not-a-file")

    def test_pulumi_invalid_string_raises_filenotfound(self):
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_pulumi_preview("not-json-and-not-a-file")

    def test_terraform_truncated_json_raises_filenotfound(self):
        """Truncated JSON (not a file, not parseable) should give clear error."""
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_terraform_plan('{"format_version":')

    def test_cloudformation_empty_string_raises_filenotfound(self):
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_cloudformation_changeset("")

    def test_pulumi_empty_string_raises_filenotfound(self):
        with pytest.raises(FileNotFoundError, match="neither valid JSON nor an existing file"):
            parse_pulumi_preview("")

    def test_terraform_valid_dict_still_works(self):
        """Passing a dict directly should work as before."""
        data = {"format_version": "1.2", "resource_changes": []}
        plan = parse_terraform_plan(data)
        assert len(plan.changes) == 0

    def test_pulumi_valid_dict_still_works(self):
        """Passing a dict directly should work as before."""
        data = {"steps": []}
        plan = parse_pulumi_preview(data)
        assert len(plan.changes) == 0

    def test_cloudformation_valid_dict_still_works(self):
        """Passing a dict directly should work as before."""
        data = {"Changes": []}
        plan = parse_cloudformation_changeset(data)
        assert len(plan.changes) == 0
