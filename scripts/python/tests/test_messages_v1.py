"""Tests for V1 message endpoints (mocked)."""
from unittest.mock import MagicMock

import pytest

from ac_builder.api.messages_v1 import message_add, message_delete


@pytest.fixture
def mock_v1_client():
    return MagicMock()


def test_message_add_sets_required_params(mock_v1_client):
    mock_v1_client.call.return_value = {"id": "42", "result_code": 1}
    msg_id = message_add(
        mock_v1_client,
        subject="Hi",
        fromemail="x@y.com",
        fromname="X",
        reply2="x@y.com",
        html="<p>HTML</p>",
        text="Text",
        list_ids=[1, 2],
    )
    assert msg_id == 42

    call_args = mock_v1_client.call.call_args
    action = call_args[0][0]
    params = call_args[0][1]
    assert action == "message_add"
    assert params["format"] == "mime"
    assert params["htmlconstructor"] == "html"
    assert params["textconstructor"] == "html"
    assert params["html"] == "<p>HTML</p>"
    assert params["text"] == "Text"
    assert params["subject"] == "Hi"
    assert params["fromemail"] == "x@y.com"
    assert params["fromname"] == "X"
    assert params["reply2"] == "x@y.com"
    assert params["p[1]"] == "1"
    assert params["p[2]"] == "1"


def test_message_delete(mock_v1_client):
    mock_v1_client.call.return_value = {"result_code": 1}
    message_delete(mock_v1_client, message_id=42)
    call_args = mock_v1_client.call.call_args
    assert call_args[0][0] == "message_delete"
    assert call_args[0][1] == {"id": "42"}
