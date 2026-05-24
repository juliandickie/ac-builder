"""Integration test for builder.py with mocked AC clients."""
from unittest.mock import MagicMock, patch

import pytest

from ac_builder.builder import BuildOptions, build_sequence


@pytest.fixture
def sample_md(tmp_path):
    md = """
# Test sequence

**Campaign name:** `test-campaign-aunz`

## E1 — Test Email

**Send date:** Mon Apr 27, 2026
**Theme:** lpis

### Subject Line Options

1. **Welcome to LPIS**

### Preview Text

"You're in for the residency"

### Email Body

Hi %FIRSTNAME|TITLECASE%,

Welcome to LPIS.

Not the right fit? [Click here](https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%) to opt out.

%UNSUBSCRIBELINK% %SENDER-INFO%
"""
    p = tmp_path / "sample.md"
    p.write_text(md)
    return p


def test_build_sequence_dry_run_no_api_calls(sample_md):
    options = BuildOptions(
        from_email="x@y.com",
        from_name="X",
        reply_to="x@y.com",
        list_ids=[1],
        theme_name="lpis",
        footer_mode="launch",
        dry_run=True,
    )
    results = build_sequence(sample_md, options)
    assert len(results) == 1
    assert results[0].action == "dry-run"
    assert results[0].email_code == "E1"


def test_build_sequence_creates_via_v1(sample_md):
    options = BuildOptions(
        from_email="x@y.com",
        from_name="X",
        reply_to="x@y.com",
        list_ids=[1],
        theme_name="lpis",
        footer_mode="launch",
        dry_run=False,
    )

    with patch("ac_builder.builder.ACClient") as mock_v3_class, \
         patch("ac_builder.builder.ACV1Client") as mock_v1_class, \
         patch("ac_builder.builder.message_add", return_value=42), \
         patch("ac_builder.builder.campaign_create", return_value=100), \
         patch("ac_builder.builder.ManifestStore") as mock_store_class:

        mock_v3 = MagicMock()
        mock_v3_class.return_value = mock_v3
        mock_v3.paginate.return_value = iter([])

        # campaigns_v3.list_campaigns generator (called via paginate)
        # The builder uses campaigns_v3.list_campaigns(v3) - we patch that helper:
        with patch("ac_builder.builder.campaigns_v3.list_campaigns", return_value=iter([])):
            mock_v1 = MagicMock()
            mock_v1_class.return_value = mock_v1

            mock_store = MagicMock()
            mock_store_class.return_value = mock_store

            results = build_sequence(sample_md, options)

    assert len(results) == 1
    assert results[0].action == "created"
    assert results[0].campaign_id == 100
    assert results[0].message_id == 42
