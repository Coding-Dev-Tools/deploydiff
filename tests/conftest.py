"""Test configuration - mock license checks so tests run without a license."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def _mock_license(monkeypatch):
    """Auto-mock revenueholdings_license so all CLI commands bypass tier checks."""
    mock_require_tier = MagicMock()

    mock_rh_check = MagicMock()
    mock_ci_gate = MagicMock()

    # Patch at the integration module level
    try:
        import revenueholdings_license.integration as integration_mod
        monkeypatch.setattr(integration_mod, "rh_check", mock_rh_check)
        monkeypatch.setattr(integration_mod, "ci_gate", mock_ci_gate)
    except ImportError:
        pass

    # Patch at the license module level
    try:
        import revenueholdings_license.license as license_mod
        monkeypatch.setattr(license_mod, "require_tier", mock_require_tier)
    except ImportError:
        pass

    # Patch at the top-level gate module
    try:
        import revenueholdings_license.gate as gate_mod
        mock_status = MagicMock()
        mock_status.tier = "PRO"
        mock_status.allowed = True
        mock_status.remaining = 999
        mock_status.daily_limit = 999
        mock_status.error = None
        mock_require_license = MagicMock(return_value=mock_status)
        monkeypatch.setattr(gate_mod, "require_license", mock_require_license)
    except (ImportError, AttributeError):
        pass
