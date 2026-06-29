"""Test configuration - mock license checks so tests run without a license."""

import sys
from unittest.mock import MagicMock

import pytest

# Replace revenueholdings_license with a mock BEFORE any src imports resolve it
_mock_rl = MagicMock()
_mock_rl.require_license = MagicMock(return_value=None)
_mock_rl.require_tier = MagicMock(return_value=None)
sys.modules["revenueholdings_license"] = _mock_rl
sys.modules.setdefault("revenueholdings_license.integration", _mock_rl)
sys.modules.setdefault("revenueholdings_license.rate_limiter", MagicMock())


@pytest.fixture(autouse=True)
def _mock_license(monkeypatch):
    """Ensure license checks stay mocked even if a test reimports."""
    monkeypatch.setattr(
        "revenueholdings_license.require_license", MagicMock(return_value=None)
    )
    monkeypatch.setattr(
        "revenueholdings_license.require_tier", MagicMock(return_value=None)
    )
