"""Tests for V1 campaign endpoints (mocked)."""
from unittest.mock import MagicMock

import pytest

from ac_builder.api.campaigns_v1 import campaign_create, campaign_send


@pytest.fixture
def mock_v1_client():
    return MagicMock()


def test_campaign_create_sets_required_params(mock_v1_client):
    mock_v1_client.call.return_value = {"id": "100", "result_code": 1}
    cid = campaign_create(
        mock_v1_client,
        name="Test Campaign",
        message_id=42,
        list_ids=[1],
    )
    assert cid == 100
    params = mock_v1_client.call.call_args[0][1]
    assert params["type"] == "single"
    assert params["name"] == "Test Campaign"
    assert params["status"] == "0"
    assert params["tracklinks"] == "all"
    assert params["m[42]"] == "100"
    assert params["p[1]"] == "1"


def test_campaign_create_with_tracking_domain(mock_v1_client):
    mock_v1_client.call.return_value = {"id": "1", "result_code": 1}
    campaign_create(
        mock_v1_client,
        name="x",
        message_id=1,
        list_ids=[1],
        track_link_domain="links.idd.com",
    )
    params = mock_v1_client.call.call_args[0][1]
    assert params["tracklinkurl"] == "links.idd.com"


def test_campaign_create_with_sdate(mock_v1_client):
    mock_v1_client.call.return_value = {"id": "1", "result_code": 1}
    campaign_create(
        mock_v1_client,
        name="x",
        message_id=1,
        list_ids=[1],
        sdate="2026-05-15 09:00:00",
    )
    params = mock_v1_client.call.call_args[0][1]
    assert params["sdate"] == "2026-05-15 09:00:00"


def test_campaign_send_one_off(mock_v1_client):
    mock_v1_client.call.return_value = {"result_code": 1}
    campaign_send(
        mock_v1_client,
        email="test@example.com",
        campaign_id=100,
        message_id=42,
    )
    params = mock_v1_client.call.call_args[0][1]
    assert params["email"] == "test@example.com"
    assert params["campaignid"] == "100"
    assert params["messageid"] == "42"
    assert params["type"] == "html"
    assert params["action"] == "send"
