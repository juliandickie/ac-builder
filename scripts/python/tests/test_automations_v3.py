"""Tests for V3 automation endpoints."""
from unittest.mock import MagicMock

import pytest

from ac_builder.api.automations_v3 import (
    activate_automation,
    create_automation,
    get_automation,
    list_automations,
)


@pytest.fixture
def mock_client():
    return MagicMock()


def test_create_automation_posts_to_automations(mock_client):
    mock_client.post.return_value = {"automation": {"id": "99", "name": "Test"}}
    automation_dict = {"name": "Test", "status": "0", "triggers": [], "actions": []}
    response = create_automation(mock_client, automation_dict)
    assert response["automation"]["id"] == "99"
    mock_client.post.assert_called_once_with("automations", json={"automation": automation_dict})


def test_activate_automation_patches_status_to_1(mock_client):
    mock_client.patch.return_value = {"automation": {"id": "99", "status": "1"}}
    activate_automation(mock_client, automation_id=99)
    mock_client.patch.assert_called_once_with(
        "automations/99",
        json={"automation": {"status": "1"}},
    )


def test_get_automation_returns_full_response(mock_client):
    mock_client.get.return_value = {"automation": {"id": "12", "name": "X", "triggers": [], "actions": []}}
    result = get_automation(mock_client, 12)
    assert result["automation"]["id"] == "12"
    mock_client.get.assert_called_once_with("automations/12")
