"""ActiveCampaign V1 API client.

V1 is form-encoded (not JSON). Endpoints follow the pattern:
    {AC_API_URL}/admin/api.php?api_action={action}&api_key={key}&api_output=json

Body is application/x-www-form-urlencoded. Response is wrapped in a
{"result_code": 0|1, "result_message": "..."} envelope where result_code=0 is
FAILURE (inverted from HTTP convention).

Rate limit: 5 req/sec/account (shared with V3). This client implements
exponential backoff on 429/5xx responses.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ACV1Error(Exception):
    """Raised on V1 API failure (HTTP non-2xx OR result_code=0)."""

    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message)


_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
_NO_RETRY_STATUS_CODES = {400, 403, 404, 422}
_MAX_RETRIES = 5
_INITIAL_BACKOFF_S = 1.0
_MAX_BACKOFF_S = 32.0


class ACV1Client:
    """Form-encoded V1 API client."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        load_dotenv()
        raw_url = (api_url or os.getenv("AC_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("AC_API_KEY", "")

        if not raw_url:
            raise ValueError("AC_API_URL not set")
        if not self.api_key:
            raise ValueError("AC_API_KEY not set")

        if raw_url.endswith("/api/3"):
            raw_url = raw_url[:-6]
        self.api_url = raw_url

        self.session = requests.Session()

    def call(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call a V1 endpoint."""
        url = f"{self.api_url}/admin/api.php?api_action={action}&api_key={self.api_key}&api_output=json"

        encoded_params: dict[str, str | list[str]] = {}
        for k, v in params.items():
            if isinstance(v, (list, tuple)):
                encoded_params[k] = [str(x) for x in v]
            else:
                encoded_params[k] = str(v)
        body = urlencode(encoded_params, doseq=True)

        backoff = _INITIAL_BACKOFF_S
        last_error_msg = ""
        for attempt in range(_MAX_RETRIES):
            try:
                response = self.session.post(
                    url,
                    data=body,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30,
                )
            except requests.RequestException as exc:
                last_error_msg = f"network error: {exc}"
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, _MAX_BACKOFF_S)
                    continue
                raise ACV1Error(last_error_msg) from exc

            if response.status_code in _NO_RETRY_STATUS_CODES:
                raise ACV1Error(
                    f"V1 {action}: HTTP {response.status_code}",
                    status_code=response.status_code,
                    body=response.text,
                )

            if response.status_code in _RETRY_STATUS_CODES:
                last_error_msg = f"HTTP {response.status_code}"
                logger.warning("V1 %s attempt %d failed (%s), retrying", action, attempt + 1, last_error_msg)
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, _MAX_BACKOFF_S)
                    continue
                raise ACV1Error(
                    f"V1 {action}: {last_error_msg} after {_MAX_RETRIES} retries",
                    status_code=response.status_code,
                    body=response.text,
                )

            if not response.ok:
                raise ACV1Error(
                    f"V1 {action}: HTTP {response.status_code}",
                    status_code=response.status_code,
                    body=response.text,
                )

            try:
                data = response.json()
            except ValueError:
                raise ACV1Error(
                    f"V1 {action}: response not JSON",
                    body=response.text,
                )

            if isinstance(data, dict) and data.get("result_code") == 0:
                raise ACV1Error(
                    f"V1 {action}: {data.get('result_message', 'failed')}",
                    body=data,
                )

            return data

        raise ACV1Error(f"V1 {action} exhausted retries: {last_error_msg}")
