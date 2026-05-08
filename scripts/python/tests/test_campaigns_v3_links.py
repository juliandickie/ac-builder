"""Tests for the campaign links retrieval helper."""
from unittest.mock import MagicMock

import pytest

from ac_builder.api.campaigns_v3 import get_campaign_links


@pytest.fixture
def mock_client():
    return MagicMock()


def test_get_campaign_links_returns_list(mock_client):
    mock_client.get.return_value = {
        "links": [
            {"id": "1", "link": "https://idd.com/sales", "campaignid": "100"},
            {"id": "2", "link": "https://idd.com/not-interested", "campaignid": "100"},
        ]
    }
    links = get_campaign_links(mock_client, campaign_id=100)
    assert len(links) == 2
    assert links[0]["link"] == "https://idd.com/sales"
    mock_client.get.assert_called_once_with("campaigns/100/links")


def test_get_campaign_links_empty(mock_client):
    mock_client.get.return_value = {"links": []}
    assert get_campaign_links(mock_client, campaign_id=1) == []
