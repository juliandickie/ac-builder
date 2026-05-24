"""Tests for the V1 API client (no live AC calls - all mocked)."""
from unittest.mock import MagicMock, patch

import pytest

from ac_builder.api.v1_client import ACV1Client, ACV1Error


@pytest.fixture
def client():
    return ACV1Client(api_url="https://test.api-us1.com", api_key="testkey")


def test_v1_client_url_construction(client):
    assert client.api_url == "https://test.api-us1.com"


def test_v1_call_success(client):
    with patch("ac_builder.api.v1_client.requests.Session.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"result_code": 1, "result_message": "ok", "id": "42"}
        mock_post.return_value = mock_response

        result = client.call("message_add", {"subject": "Hi"})
        assert result["id"] == "42"

        call_args = mock_post.call_args
        url = call_args[0][0]
        assert "api_action=message_add" in url
        assert "api_key=testkey" in url
        assert "api_output=json" in url


def test_v1_call_returns_result_code_zero_raises(client):
    with patch("ac_builder.api.v1_client.requests.Session.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"result_code": 0, "result_message": "Field X is not allowed"}
        mock_post.return_value = mock_response

        with pytest.raises(ACV1Error) as exc_info:
            client.call("message_add", {"bad": "param"})
        assert "Field X is not allowed" in str(exc_info.value)


def test_v1_call_400_no_retry(client):
    with patch("ac_builder.api.v1_client.requests.Session.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_response.text = "bad request"
        mock_post.return_value = mock_response

        with pytest.raises(ACV1Error):
            client.call("message_add", {})
        assert mock_post.call_count == 1


def test_v1_call_429_retries(client):
    with patch("ac_builder.api.v1_client.requests.Session.post") as mock_post, \
         patch("ac_builder.api.v1_client.time.sleep"):
        rate_limited = MagicMock(status_code=429, ok=False, text="rate limit")
        success = MagicMock(status_code=200, ok=True)
        success.json.return_value = {"result_code": 1, "id": "99"}
        mock_post.side_effect = [rate_limited, rate_limited, success]

        result = client.call("test", {})
        assert result["id"] == "99"
        assert mock_post.call_count == 3


def test_v1_call_500_retries(client):
    with patch("ac_builder.api.v1_client.requests.Session.post") as mock_post, \
         patch("ac_builder.api.v1_client.time.sleep"):
        server_error = MagicMock(status_code=500, ok=False, text="server error")
        success = MagicMock(status_code=200, ok=True)
        success.json.return_value = {"result_code": 1, "id": "1"}
        mock_post.side_effect = [server_error, success]

        result = client.call("test", {})
        assert result["id"] == "1"


def test_v1_call_form_encodes_list_params(client):
    with patch("ac_builder.api.v1_client.requests.Session.post") as mock_post:
        mock_response = MagicMock(status_code=200, ok=True)
        mock_response.json.return_value = {"result_code": 1}
        mock_post.return_value = mock_response

        client.call("message_add", {"subject": "Hi", "p[1]": "1", "p[2]": "1"})
        body = mock_post.call_args[1]["data"]
        assert "p%5B1%5D=1" in body or "p[1]=1" in body
